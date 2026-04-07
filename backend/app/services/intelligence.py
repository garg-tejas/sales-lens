from __future__ import annotations

import json
import logging

from textblob import TextBlob

from app.config import settings
from app.services.llm import chat_with_fallback

logger = logging.getLogger("saleslens.intelligence")

OBJECTION_KEYWORDS = (
    "price",
    "expensive",
    "not sure",
    "later",
    "competitor",
    "budget",
    "risk",
    "concerned",
    "hesitant",
    "need to think",
    "not interested",
    "too much",
    "over budget",
)
ACTION_PREFIXES = (
    "we will",
    "i will",
    "next step",
    "follow up",
    "send",
    "schedule",
    "let me",
    "i'll",
    "we'll",
    "going to",
)

LLM_INTELLIGENCE_PROMPT = """\
You are an expert sales call analyst. Analyze the following sales call transcript and return a JSON object with this exact structure:

{{
  "objections": [
    {{"text": "the objection text", "timestamp": 12.5, "speaker": "Customer", "severity": "high|medium|low"}}
  ],
  "action_items": [
    {{"text": "the action item text", "timestamp": 45.0, "speaker": "Agent", "priority": "high|medium|low"}}
  ],
  "key_topics": ["topic1", "topic2"],
  "summary": "A concise 2-3 sentence summary of the call.",
  "call_score": {{
    "total": 72,
    "breakdown": {{
      "rapport": 80,
      "needs_discovery": 65,
      "objection_handling": 70,
      "next_steps": 60
    }}
  }}
}}

Rules:
- Objections: Identify explicit and implicit objections from the customer. Include the exact text and timestamp.
- Action items: Identify concrete next steps, commitments, or follow-ups from either party.
- Key topics: Extract 3-7 key topics discussed.
- Summary: 2-3 sentence executive summary.
- Call score: 0-100 overall, with breakdown for rapport, needs discovery, objection handling, and next steps clarity.
- If a section has nothing, return an empty list.

Transcript:
{transcript}
"""


def detect_objections(segments: list[dict]) -> list[dict]:
    objections = []
    for s in segments:
        t = s["text"].lower()
        if any(k in t for k in OBJECTION_KEYWORDS):
            objections.append(
                {
                    "timestamp": s["start_time"],
                    "speaker": s["speaker"],
                    "text": s["text"],
                }
            )
    return objections


def sentiment_timeline(segments: list[dict]) -> list[dict]:
    out = []
    for s in segments:
        score = TextBlob(s["text"]).sentiment.polarity
        label = "neutral"
        if score > 0.15:
            label = "positive"
        elif score < -0.15:
            label = "negative"
        out.append({"timestamp": s["start_time"], "score": score, "label": label})
    return out


def extract_actions(segments: list[dict]) -> list[dict]:
    actions = []
    for s in segments:
        t = s["text"].strip()
        low = t.lower()
        if any(low.startswith(p) or p in low for p in ACTION_PREFIXES):
            actions.append(
                {"speaker": s["speaker"], "text": t, "timestamp": s["start_time"]}
            )
    return actions


def compute_call_score(
    segments: list[dict], objections: list[dict], actions: list[dict]
) -> dict:
    agent_words = 0
    customer_words = 0
    for s in segments:
        n = len(s["text"].split())
        if s["speaker"] == "Agent":
            agent_words += n
        else:
            customer_words += n

    ratio = agent_words / max(customer_words, 1)
    ratio_score = max(0, 40 - abs(1.2 - ratio) * 20)
    objection_score = max(0, 30 - min(len(objections), 6) * 4)
    action_score = min(len(actions) * 10, 30)
    total = round(max(0, min(100, ratio_score + objection_score + action_score)))

    return {
        "total": total,
        "reasoning": {
            "talk_listen_ratio": ratio,
            "objection_impact": len(objections),
            "next_steps_clarity": len(actions),
        },
    }


def llm_intelligence(segments: list[dict]) -> dict:
    transcript = "\n".join(
        f"[{s['start_time']:.1f}s] {s['speaker']}: {s['text']}" for s in segments
    )
    prompt = LLM_INTELLIGENCE_PROMPT.format(transcript=transcript)

    try:
        answer, model = chat_with_fallback(
            messages=[{"role": "user", "content": prompt}],
            primary_model=settings.hf_model_analysis,
            secondary_model=settings.hf_model_qa,
        )
        result = json.loads(answer)
        logger.info("LLM intelligence completed with model=%s", model)
        return result
    except Exception:
        logger.exception("LLM intelligence failed – falling back to rule-based")
        return {}


def run_intelligence(segments: list[dict]) -> dict:
    if settings.use_llm_intelligence:
        llm_result = llm_intelligence(segments)
        if llm_result:
            sentiment = sentiment_timeline(segments)
            return {
                "objections": llm_result.get("objections", []),
                "action_items": llm_result.get("action_items", []),
                "sentiment_timeline": sentiment,
                "call_score": llm_result.get(
                    "call_score",
                    compute_call_score(
                        segments,
                        llm_result.get("objections", []),
                        llm_result.get("action_items", []),
                    ),
                ),
                "summary": llm_result.get("summary", ""),
                "key_topics": llm_result.get("key_topics", []),
            }

    objections = detect_objections(segments)
    sentiment = sentiment_timeline(segments)
    actions = extract_actions(segments)
    score = compute_call_score(segments, objections, actions)

    return {
        "objections": objections,
        "action_items": actions,
        "sentiment_timeline": sentiment,
        "call_score": score,
        "summary": "",
        "key_topics": [],
    }


LLM_ROLE_PROMPT = """\
You are analyzing a sales call transcript to identify speaker roles.

The transcript uses these speaker labels: {speaker_labels}

Your task: map each speaker label to one of these roles:
- "Agent" — the salesperson / representative selling something
- "Customer" — the prospect / buyer being pitched to

Return ONLY a JSON object mapping each speaker label to a role. No explanation, no markdown.

Example:
{{"SPEAKER_00": "Agent", "SPEAKER_01": "Customer"}}

Transcript:
{transcript}
"""


def identify_roles(segments: list[dict]) -> dict[str, str]:
    speaker_labels = sorted(set(s["speaker"] for s in segments))

    if len(speaker_labels) <= 1:
        return {speaker_labels[0]: "Agent"} if speaker_labels else {}

    transcript = "\n".join(
        f"[{s['speaker']} @ {s['start_time']:.0f}s] {s['text']}" for s in segments[:100]
    )

    prompt = LLM_ROLE_PROMPT.format(
        speaker_labels=", ".join(speaker_labels),
        transcript=transcript,
    )

    try:
        answer, model = chat_with_fallback(
            messages=[{"role": "user", "content": prompt}],
            primary_model=settings.hf_model_analysis,
            secondary_model=settings.hf_model_qa,
        )
        result = json.loads(answer)
        logger.info("LLM role identification completed with model=%s", model)
        return {k: v for k, v in result.items() if v in ("Agent", "Customer")}
    except Exception:
        logger.exception("LLM role identification failed")
        return {}

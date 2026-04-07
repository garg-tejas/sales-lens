from textblob import TextBlob


OBJECTION_KEYWORDS = ("price", "expensive", "not sure", "later", "competitor", "budget", "risk")
ACTION_PREFIXES = ("we will", "i will", "next step", "follow up", "send", "schedule")


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
            actions.append({"speaker": s["speaker"], "text": t, "timestamp": s["start_time"]})
    return actions


def compute_call_score(segments: list[dict], objections: list[dict], actions: list[dict]) -> dict:
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

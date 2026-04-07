from __future__ import annotations

from app.services.intelligence import run_intelligence
from app.services.rag import build_or_load_index, chunk_transcript


class CallProcessingGraph:
    """Orchestrator: insights -> rag_index -> finalize."""

    def __init__(self, segments: list[dict], call_id: str) -> None:
        self.state: dict = {
            "segments": segments,
            "call_id": call_id,
            "objections": [],
            "sentiment": [],
            "actions": [],
            "score": {},
            "summary": "",
            "key_topics": [],
            "index_ready": False,
        }

    def insights_node(self) -> None:
        result = run_intelligence(self.state["segments"])
        self.state["objections"] = result.get("objections", [])
        self.state["sentiment"] = result.get("sentiment_timeline", [])
        self.state["actions"] = result.get("action_items", [])
        score = result.get("call_score", {})
        score["summary"] = result.get("summary", "")
        score["key_topics"] = result.get("key_topics", [])
        self.state["score"] = score

    def rag_index_node(self) -> None:
        chunks = chunk_transcript(self.state["segments"])
        build_or_load_index(self.state["call_id"], chunks)
        self.state["index_ready"] = True

    def run(self) -> dict:
        self.insights_node()
        self.rag_index_node()
        return self.state

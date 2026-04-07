from app.services.intelligence import compute_call_score, detect_objections, extract_actions, sentiment_timeline
from app.services.rag import build_or_load_index, chunk_transcript


class CallProcessingGraph:
    """
    Lightweight LangGraph-style orchestrator:
    transcribe_done -> insights_node -> rag_index_node -> finalize
    """

    def __init__(self, segments: list[dict], call_id: str) -> None:
        self.state = {
            "segments": segments,
            "call_id": call_id,
            "objections": [],
            "sentiment": [],
            "actions": [],
            "score": {},
            "index_ready": False,
        }

    def insights_node(self) -> None:
        segments = self.state["segments"]
        objections = detect_objections(segments)
        sentiment = sentiment_timeline(segments)
        actions = extract_actions(segments)
        score = compute_call_score(segments, objections, actions)
        self.state["objections"] = objections
        self.state["sentiment"] = sentiment
        self.state["actions"] = actions
        self.state["score"] = score

    def rag_index_node(self) -> None:
        chunks = chunk_transcript(self.state["segments"])
        build_or_load_index(self.state["call_id"], chunks)
        self.state["index_ready"] = True

    def run(self) -> dict:
        self.insights_node()
        self.rag_index_node()
        return self.state

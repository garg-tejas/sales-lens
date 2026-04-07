import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.db import Base, SessionLocal, engine, get_db
from app.models import Call, Insight, Transcript
from app.schemas import CallOut, QueryRequest, UploadResponse
from app.services.orchestrator import CallProcessingGraph
from app.services.rag import query_transcript
from app.services.redis_state import append_event, get_events_since, get_state, set_state
from app.services.transcription import stream_segments, transcribe_segments

app = FastAPI(title="SalesLens API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/calls/upload", response_model=UploadResponse)
async def upload_call(file: UploadFile = File(...), db: Session = Depends(get_db)) -> UploadResponse:
    call = Call(filename=file.filename, language="auto", duration=0.0)
    db.add(call)
    db.commit()
    db.refresh(call)

    out_path = Path(settings.upload_dir) / f"{call.id}_{file.filename}"
    content = await file.read()
    out_path.write_bytes(content)
    set_state(str(call.id), {"status": "queued", "progress": 0, "segments": []})
    return UploadResponse(call_id=call.id, status="queued")


@app.websocket("/calls/{call_id}/stream")
async def stream_call(call_id: str, websocket: WebSocket) -> None:
    await websocket.accept()
    since_seq = int(websocket.query_params.get("since_seq", "0"))
    state = get_state(call_id)
    if not state:
        await websocket.send_json({"type": "error", "message": "Unknown call_id"})
        await websocket.close()
        return
    if since_seq > 0:
        for past_event in get_events_since(call_id, since_seq):
            await websocket.send_json(past_event)
        if state.get("status") == "completed":
            await websocket.close()
            return

    upload_candidates = list(Path(settings.upload_dir).glob(f"{call_id}_*"))
    if not upload_candidates:
        await websocket.send_json({"type": "error", "message": "Audio file not found"})
        await websocket.close()
        return

    processing_event = {"type": "status", "status": "processing", "progress": 1}
    seq = append_event(call_id, processing_event)
    processing_event["seq"] = seq
    await websocket.send_json(processing_event)
    audio_path = str(upload_candidates[0])
    segments, language = transcribe_segments(audio_path)
    set_state(call_id, {"status": "processing", "progress": 10, "segments": [], "last_seq": 0})

    db = SessionLocal()
    try:
        call = db.get(Call, uuid.UUID(call_id))
        if call:
            call.language = language or "auto"
            if segments:
                call.duration = float(segments[-1]["end_time"])
            db.commit()

        for event in stream_segments(segments):
            seg = event["segment"]
            if not event.get("is_partial", False):
                db.add(
                    Transcript(
                        call_id=uuid.UUID(call_id),
                        speaker=seg["speaker"],
                        text=seg["text"],
                        start_time=seg["start_time"],
                        end_time=seg["end_time"],
                    )
                )
                db.commit()
            seq = append_event(call_id, event)
            event_with_seq = {**event, "seq": seq}
            await websocket.send_json(event_with_seq)
            set_state(call_id, {"status": "processing", "progress": event["progress"], "last_seq": seq})

        pipeline_state = CallProcessingGraph(segments=segments, call_id=call_id).run()
        objections = pipeline_state["objections"]
        sentiment = pipeline_state["sentiment"]
        actions = pipeline_state["actions"]
        score = pipeline_state["score"]

        insight = db.query(Insight).filter(Insight.call_id == uuid.UUID(call_id)).first()
        if insight is None:
            insight = Insight(
                call_id=uuid.UUID(call_id),
                objections=objections,
                action_items=actions,
                sentiment_timeline=sentiment,
                call_score=score,
            )
            db.add(insight)
        else:
            insight.objections = objections
            insight.action_items = actions
            insight.sentiment_timeline = sentiment
            insight.call_score = score
        db.commit()
    finally:
        db.close()

    completed_event = {"type": "status", "status": "completed", "progress": 100}
    seq = append_event(call_id, completed_event)
    completed_event_with_seq = {**completed_event, "seq": seq}
    set_state(call_id, {"status": "completed", "progress": 100, "segments": segments, "last_seq": seq})
    await websocket.send_json(completed_event_with_seq)
    done_event = {"type": "completed"}
    done_seq = append_event(call_id, done_event)
    await websocket.send_json({**done_event, "seq": done_seq})
    await websocket.close()


@app.get("/calls/{call_id}/insights")
def get_insights(call_id: str, db: Session = Depends(get_db)) -> dict:
    insight = db.query(Insight).filter(Insight.call_id == uuid.UUID(call_id)).first()
    if not insight:
        raise HTTPException(status_code=404, detail="Insights not ready")
    return {
        "objections": insight.objections or [],
        "action_items": insight.action_items or [],
        "sentiment_timeline": insight.sentiment_timeline or [],
        "call_score": insight.call_score or {},
    }


@app.post("/calls/{call_id}/query")
def query_call(call_id: str, req: QueryRequest, db: Session = Depends(get_db)) -> dict:
    transcripts = db.query(Transcript).filter(Transcript.call_id == uuid.UUID(call_id)).order_by(Transcript.start_time).all()
    if not transcripts:
        raise HTTPException(status_code=404, detail="Transcript not found")
    segments = [
        {
            "speaker": t.speaker,
            "text": t.text,
            "start_time": t.start_time,
            "end_time": t.end_time,
        }
        for t in transcripts
    ]
    return query_transcript(call_id, req.question, segments)


@app.get("/calls", response_model=list[CallOut])
def list_calls(db: Session = Depends(get_db)) -> list[CallOut]:
    rows = db.execute(select(Call).order_by(Call.created_at.desc())).scalars().all()
    return [CallOut.model_validate(r, from_attributes=True) for r in rows]

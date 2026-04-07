# SalesLens Backend

Real-time sales call intelligence API built with FastAPI. Transcribes audio, identifies speakers, detects objections, extracts action items, and powers RAG-based Q&A.

## Quick Start

```bash
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

OpenAPI docs at `http://localhost:8000/docs`

## Architecture

```
POST /calls/upload          →  save audio, create DB record
WS   /calls/{id}/stream     →  transcribe → diarize → stream → analyze → insights
GET  /calls/{id}/insights   →  return computed analysis
POST /calls/{id}/query      →  RAG Q&A against transcript
GET  /calls                 →  list all past calls
```

## Pipeline

1. **Transcription** — faster-whisper (medium, CUDA, beam=5, VAD filter)
2. **Diarization** — pyannote/speaker-diarization-3.1 forced to 2 speakers
3. **Role identification** — LLM maps speaker labels to Agent/Customer
4. **Intelligence** — LLM detects objections, action items, topics, scoring
5. **RAG indexing** — sentence-transformers embeddings + FAISS vector store

## Configuration

Copy `.env.example` to `.env` and set your values:

| Variable | Default | Description |
|---|---|---|
| `HF_TOKEN` | | HuggingFace token (required for diarization + LLM) |
| `WHISPER_MODEL_SIZE` | `medium` | Whisper model size (`tiny`, `base`, `small`, `medium`, `large-v3`) |
| `USE_LLM_INTELLIGENCE` | `true` | Use LLM for objection/action/score analysis |
| `HF_MODEL_ANALYSIS` | `Qwen/Qwen3.5-9B:together` | Primary LLM via HuggingFace Router |
| `HF_MODEL_QA` | `Qwen/Qwen3.5-9B:together` | Fallback LLM for Q&A |

## Dependencies

- **GPU required** — CUDA 13.0 for Whisper, pyannote, and embeddings
- **PostgreSQL** — persistent storage for calls, transcripts, insights
- **Redis** — WebSocket event caching for reconnection support

## Storage

| Path | Contents |
|---|---|
| `./storage/uploads/` | Uploaded audio files |
| `./storage/indexes/` | FAISS vector indexes for RAG |

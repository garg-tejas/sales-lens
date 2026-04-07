from collections.abc import Generator

from faster_whisper import WhisperModel
from pyannote.audio import Pipeline

from app.config import settings


def infer_speaker(text: str, idx: int) -> str:
    # Placeholder role mapping for MVP; can be replaced with pyannote labels.
    if any(k in text.lower() for k in ("price", "cost", "budget", "expensive")):
        return "Customer"
    return "Agent" if idx % 2 == 0 else "Customer"


def apply_diarization(audio_path: str, segments: list[dict]) -> list[dict]:
    """
    Best-effort pyannote diarization.
    Falls back silently to heuristic labels when pipeline/model auth is unavailable.
    """
    if not settings.hf_token:
        return segments
    try:
        pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=settings.hf_token)
        diarization = pipeline(audio_path)
    except Exception:
        return segments

    speaker_windows = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        speaker_windows.append((float(turn.start), float(turn.end), str(speaker)))
    if not speaker_windows:
        return segments

    canonical = {}
    speaker_duration = {}
    speaker_customer_signals = {}

    for s, e, label in speaker_windows:
        speaker_duration[label] = speaker_duration.get(label, 0.0) + (e - s)
        speaker_customer_signals.setdefault(label, 0)

    customer_cues = ("price", "cost", "budget", "expensive", "not sure", "too much", "competitor")
    for seg in segments:
        midpoint = (seg["start_time"] + seg["end_time"]) / 2.0
        selected = None
        for s, e, label in speaker_windows:
            if s <= midpoint <= e:
                selected = label
                break
        if selected is None:
            continue
        low = seg["text"].lower()
        if any(c in low for c in customer_cues):
            speaker_customer_signals[selected] = speaker_customer_signals.get(selected, 0) + 1
        seg["_diarized_label"] = selected

    labels = list(speaker_duration.keys())
    if not labels:
        return segments

    labels_sorted = sorted(
        labels,
        key=lambda l: (speaker_customer_signals.get(l, 0), -speaker_duration.get(l, 0.0)),
        reverse=True,
    )

    customer_label = labels_sorted[0]
    canonical[customer_label] = "Customer"
    remaining = [l for l in labels if l != customer_label]
    if remaining:
        agent_label = max(remaining, key=lambda l: speaker_duration.get(l, 0.0))
        canonical[agent_label] = "Agent"
    for l in labels:
        canonical.setdefault(l, "Customer")

    for seg in segments:
        label = seg.pop("_diarized_label", None)
        if label is not None:
            seg["speaker"] = canonical.get(label, seg["speaker"])
    return segments


def transcribe_segments(audio_path: str) -> tuple[list[dict], str]:
    model = WhisperModel(settings.whisper_model_size)
    segments, info = model.transcribe(audio_path, vad_filter=True, language=None)

    out = []
    for idx, seg in enumerate(segments):
        out.append(
            {
                "speaker": infer_speaker(seg.text, idx),
                "text": seg.text.strip(),
                "start_time": float(seg.start),
                "end_time": float(seg.end),
            }
        )
    out = apply_diarization(audio_path, out)
    return out, getattr(info, "language", "auto")


def stream_segments(segments: list[dict]) -> Generator[dict, None, None]:
    total = max(len(segments), 1)
    for idx, segment in enumerate(segments, start=1):
        words = segment["text"].split()
        rolling = []
        for w in words:
            rolling.append(w)
            partial_text = " ".join(rolling)
            yield {
                "type": "transcript_segment",
                "is_partial": True,
                "progress": int(((idx - 1) / total) * 100),
                "segment": {
                    "speaker": segment["speaker"],
                    "text": partial_text,
                    "start_time": segment["start_time"],
                    "end_time": segment["end_time"],
                },
            }
        yield {
            "type": "transcript_segment",
            "is_partial": False,
            "progress": int((idx / total) * 100),
            "segment": segment,
        }

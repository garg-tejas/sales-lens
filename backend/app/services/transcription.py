from __future__ import annotations

import logging
from collections.abc import Generator

import torch

from app.config import settings
from app.services.intelligence import identify_roles
from app.services.models import get_diarization, get_whisper

logger = logging.getLogger("saleslens.transcription")

TURN_MERGE_GAP = 0.4


def _merge_turns(
    turns: list[tuple[float, float, str]],
    gap: float = TURN_MERGE_GAP,
) -> list[tuple[float, float, str]]:
    if not turns:
        return []

    turns.sort(key=lambda t: t[0])
    merged = [turns[0]]

    for start, end, label in turns[1:]:
        prev_start, prev_end, prev_label = merged[-1]
        if label == prev_label and (start - prev_end) <= gap:
            merged[-1] = (prev_start, max(prev_end, end), prev_label)
        else:
            merged.append((start, end, label))

    return merged


def apply_diarization(audio_path: str, segments: list[dict]) -> list[dict]:
    pipeline = get_diarization()
    if pipeline is None:
        return segments

    try:
        diarization = pipeline(audio_path, min_num_speakers=2, max_num_speakers=2)
    except Exception:
        logger.exception("Diarization failed – falling back to heuristic")
        return segments

    raw_turns = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        raw_turns.append((float(turn.start), float(turn.end), str(speaker)))

    if not raw_turns:
        return segments

    speaker_windows = _merge_turns(raw_turns)

    role_map = identify_roles(segments)

    if not role_map:
        labels = sorted(set(label for _, _, label in speaker_windows))
        if len(labels) >= 2:
            role_map = {labels[0]: "Agent", labels[1]: "Customer"}
            for i, label in enumerate(labels[2:], start=3):
                role_map[label] = f"Speaker {i}"
        elif labels:
            role_map[labels[0]] = "Agent"

    for seg in segments:
        midpoint = (seg["start_time"] + seg["end_time"]) / 2.0
        selected = None
        for s, e, label in speaker_windows:
            if s <= midpoint <= e:
                selected = label
                break
        if selected is not None:
            seg["speaker"] = role_map.get(selected, seg["speaker"])

    return segments


def transcribe_segments(audio_path: str) -> tuple[list[dict], str]:
    model = get_whisper()

    with torch.inference_mode():
        segments_raw, info = model.transcribe(
            audio_path,
            vad_filter=settings.whisper_vad_filter,
            language=None,
            beam_size=settings.whisper_beam_size,
            initial_prompt=settings.whisper_initial_prompt,
        )

        out = []
        for seg in segments_raw:
            text = seg.text.strip()
            if text:
                out.append(
                    {
                        "speaker": "Speaker",
                        "text": text,
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

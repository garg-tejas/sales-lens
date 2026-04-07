"""
Model manager: pre-loads and caches GPU models at startup so they stay resident
in VRAM across requests.  All inference runs under torch.inference_mode().
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import torch

from app.config import settings

if TYPE_CHECKING:
    from faster_whisper import WhisperModel
    from pyannote.audio import Pipeline
    from sentence_transformers import SentenceTransformer

logger = logging.getLogger("saleslens.models")

_whisper: WhisperModel | None = None
_diarization: Pipeline | None = None
_embedder: SentenceTransformer | None = None


def get_whisper() -> WhisperModel:
    global _whisper
    if _whisper is None:
        from faster_whisper import WhisperModel

        logger.info(
            "Loading Whisper model: size=%s device=%s compute=%s",
            settings.whisper_model_size,
            settings.whisper_device,
            settings.whisper_compute_type,
        )
        _whisper = WhisperModel(
            settings.whisper_model_size,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
            cpu_threads=4,
            num_workers=4,
        )
        logger.info("Whisper model loaded and cached on %s", settings.whisper_device)
    return _whisper


def get_diarization() -> Pipeline | None:
    global _diarization
    if not settings.hf_token:
        return None
    if _diarization is None:
        from pyannote.audio import Pipeline

        logger.info(
            "Loading diarization pipeline: %s on %s",
            settings.diarization_model,
            settings.diarization_device,
        )
        try:
            _diarization = Pipeline.from_pretrained(
                settings.diarization_model,
                use_auth_token=settings.hf_token,
            )
            _diarization.to(torch.device(settings.diarization_device))
            logger.info(
                "Diarization pipeline loaded and cached on %s",
                settings.diarization_device,
            )
        except Exception:
            logger.exception(
                "Failed to load diarization pipeline – falling back to heuristic"
            )
            return None
    return _diarization


def get_embedder() -> SentenceTransformer:
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer

        logger.info(
            "Loading embedding model: %s on %s",
            settings.embedding_model,
            settings.embedding_device,
        )
        _embedder = SentenceTransformer(
            settings.embedding_model, device=settings.embedding_device
        )
        logger.info(
            "Embedding model loaded and cached on %s", settings.embedding_device
        )
    return _embedder


def clear_gpu_cache() -> None:
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        logger.debug(
            "GPU cache cleared. Allocated: %.1f MB",
            torch.cuda.memory_allocated() / 1024**2,
        )

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "dev"
    api_port: int = 8000
    database_url: str = (
        "postgresql+psycopg://postgres:postgres@localhost:5432/saleslens"
    )
    redis_url: str = "redis://localhost:6379/0"
    hf_token: str = ""
    hf_router_base_url: str = "https://router.huggingface.co/v1"
    hf_model_analysis: str = "Qwen/Qwen3.5-9B:together"
    hf_model_qa: str = "Qwen/Qwen3.5-9B:together"
    whisper_model_size: str = "medium"
    whisper_device: str = "cuda"
    whisper_compute_type: str = "float16"
    whisper_beam_size: int = 5
    whisper_vad_filter: bool = True
    whisper_initial_prompt: str = (
        "The following is a sales call conversation between a sales agent and a customer. "
        "Use proper punctuation and capitalization."
    )
    diarization_device: str = "cuda"
    diarization_model: str = "pyannote/speaker-diarization-3.1"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_device: str = "cuda"
    embedding_dim: int = 384
    upload_dir: str = "./storage/uploads"
    index_dir: str = "./storage/indexes"
    transcript_chunk_size: int = 800
    use_llm_intelligence: bool = True
    max_gpu_memory_mb: int = 0


settings = Settings()

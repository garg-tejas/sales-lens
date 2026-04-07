from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "dev"
    api_port: int = 8000
    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/saleslens"
    redis_url: str = "redis://localhost:6379/0"
    hf_token: str = ""
    hf_router_base_url: str = "https://router.huggingface.co/v1"
    hf_model_analysis: str = "Qwen/Qwen3.5-9B:together"
    hf_model_qa: str = "Qwen/Qwen3.5-9B:together"
    whisper_model_size: str = "small"
    upload_dir: str = "./storage/uploads"
    index_dir: str = "./storage/indexes"
    transcript_chunk_size: int = 800


settings = Settings()

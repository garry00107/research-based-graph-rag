from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # NVIDIA API
    nvidia_api_key: str
    
    # Vector Database
    chroma_persist_dir: str = "./chroma_db"
    
    # Redis Cache
    redis_url: str = "redis://localhost:6379"
    redis_enabled: bool = False
    
    # Server
    host: str = "127.0.0.1"
    port: int = 8002
    
    # Performance
    batch_size: int = 32
    max_workers: int = 4
    
    # Sheet RAG Settings
    sheet_rag_enabled: bool = True
    sheet_rag_layers: list = ["sentence", "paragraph", "section", "summary"]
    cross_validation_threshold: float = 0.5
    cross_validation_min_layers: int = 2
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()

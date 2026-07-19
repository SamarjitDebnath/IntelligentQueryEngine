from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BACKEND_DIR / "data"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Google Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    # Embeddings used for the few-shot example selector
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Local storage
    sqlite_path: Path = DATA_DIR / "store_inventory.db"
    chroma_persist_dir: Path = DATA_DIR / "chroma"

    # SQLDatabaseChain behaviour
    sql_chain_verbose: bool = True
    few_shot_examples_k: int = 3

    # API
    cors_origins: list[str] = ["http://localhost:5173"]

    @property
    def sqlite_uri(self) -> str:
        return f"sqlite:///{self.sqlite_path}"


settings = Settings()

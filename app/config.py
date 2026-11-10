import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _as_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    app_name: str = "文心 · 高考满分作文智能工坊"
    api_key: str = os.getenv("DEEPSEEK_API_KEY", "").strip()
    base_url: str = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com").strip()
    model: str = os.getenv("MODEL_NAME", "deepseek-chat").strip()
    temperature: float = float(os.getenv("TEMPERATURE", "0.8"))
    max_tokens: int = int(os.getenv("MAX_TOKENS", "2600"))
    demo_mode: bool = _as_bool(os.getenv("DEMO_MODE"), default=not api_key)

    @property
    def has_api_key(self) -> bool:
        return bool(self.api_key)


settings = Settings()

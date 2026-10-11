"""Explicit module-local settings. Never search ancestor .env files."""
import os
from pathlib import Path

from dotenv import dotenv_values
from pydantic import BaseModel, Field, SecretStr


class LiveSettings(BaseModel):
    api_key: SecretStr = Field(repr=False)
    model: str
    project_root: Path

    @classmethod
    def load(cls, project_root: Path):
        root = project_root.resolve()
        values = dotenv_values(root / ".env", interpolate=False)
        key = os.environ.get("OPENAI_API_KEY", values.get("OPENAI_API_KEY") or "").strip()
        model = os.environ.get("OPENAI_MODEL", values.get("OPENAI_MODEL") or "").strip()
        if not key or not model or model.lower() in {"your_model", "model_name"}:
            raise ValueError("Set OPENAI_API_KEY and OPENAI_MODEL in routiq-ai-coach/.env before enabling live mode.")
        if key.startswith("API-"):
            raise ValueError("OPENAI_API_KEY has an added API- prefix. Replace it with a new key copied exactly from OpenAI.")
        if not model.replace("-", "").replace("_", "").replace(".", "").isalnum():
            raise ValueError("OPENAI_MODEL must be an OpenAI model ID, without a provider URL or prefix.")
        return cls(api_key=SecretStr(key), model=model, project_root=root)

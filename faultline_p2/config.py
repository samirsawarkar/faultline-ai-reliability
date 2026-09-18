"""Central configuration and API provider gateway for FAULTLINE Phase 2.

Loads settings from .env at repository root and provides centralized access
to the OpenAI-compatible endpoint (e.g. aicredits.in) and the configured model ladder.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

from dotenv import load_dotenv
import openai

# Locate and load root .env
_REPO_ROOT = Path(__file__).resolve().parent.parent
_ENV_PATH = _REPO_ROOT / ".env"
load_dotenv(_ENV_PATH)

AICREDITS_BASE_URL: str = os.getenv("AICREDITS_BASE_URL", "https://aicredits.in/v1")
AICREDITS_API_KEY: str = os.getenv("AICREDITS_API_KEY", "")

_MODELS_PATH = Path(__file__).resolve().parent / "models.json"


def _load_model_ladder() -> Dict[str, Dict[str, Any]]:
    if not _MODELS_PATH.exists():
        return {}
    with open(_MODELS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    ladder: Dict[str, Dict[str, Any]] = {}
    for rung, spec in data.items():
        spec_copy = dict(spec)
        env_val = os.getenv(f"MODEL_{rung}")
        if env_val:
            spec_copy["model"] = env_val
        ladder[rung] = spec_copy
    return ladder


# Default ladder mapping loaded from models.json (environment variables override model id)
MODEL_LADDER: Dict[str, Dict[str, Any]] = _load_model_ladder()


def get_openai_client() -> openai.OpenAI:
    """Returns an authenticated OpenAI client configured for the central provider."""
    return openai.OpenAI(
        base_url=AICREDITS_BASE_URL,
        api_key=AICREDITS_API_KEY,
    )


def get_model_spec(rung: str) -> Dict[str, Any]:
    """Retrieve model specification for a given ladder rung."""
    if rung not in MODEL_LADDER:
        raise KeyError(f"Unknown rung '{rung}'. Available rungs: {list(MODEL_LADDER.keys())}")
    return MODEL_LADDER[rung]


def get_model_id(rung: str) -> str:
    """Retrieve the exact model endpoint identifier for a given ladder rung."""
    return get_model_spec(rung)["model"]

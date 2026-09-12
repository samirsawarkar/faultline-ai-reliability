"""Central configuration and API provider gateway for FAULTLINE Phase 2.

Loads settings from .env at repository root and provides centralized access
to the OpenAI-compatible endpoint (e.g. aicredits.in) and the configured model ladder.
"""
from __future__ import annotations

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

# Default ladder mapping from environment variables
MODEL_LADDER: Dict[str, Dict[str, Any]] = {
    "R1": {
        "model": os.getenv("MODEL_R1", "qwen/qwen3.7-flash"),
        "name": "qwen3.7-flash",
        "input_price_per_m": 0.10,
        "output_price_per_m": 0.20,
    },
    "R2": {
        "model": os.getenv("MODEL_R2", "z-ai/glm-5.3-flash"),
        "name": "glm-5.3-flash",
        "input_price_per_m": 0.075,
        "output_price_per_m": 0.25,
    },
    "R3": {
        "model": os.getenv("MODEL_R3", "qwen/qwen3.8-flash"),
        "name": "qwen3.8-flash",
        "input_price_per_m": 0.14,
        "output_price_per_m": 0.28,
    },
    "R4": {
        "model": os.getenv("MODEL_R4", "openai/gpt-5.6-luna"),
        "name": "gpt-5.6-luna",
        "input_price_per_m": 0.20,
        "output_price_per_m": 0.60,
    },
    "R5": {
        "model": os.getenv("MODEL_R5", "google/gemini-3.7-flash"),
        "name": "gemini-3.7-flash",
        # PROVISIONAL: Placeholder estimate until pre-flight measures gemini-3.7-flash
        "input_price_per_m": 0.15,
        "output_price_per_m": 0.50,
    },
    "R6": {
        "model": os.getenv("MODEL_R6", "deepseek/deepseek-v4-pro"),
        "name": "deepseek-v4-pro",
        "input_price_per_m": 0.435,
        "output_price_per_m": 0.87,
    },
}


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

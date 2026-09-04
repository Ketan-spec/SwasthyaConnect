"""
SwasthyaConnect — Smart Model Selector
=======================================
Detects which Ollama models are installed on this machine
and returns the best available model for each use case.

Priority order (best first for this Intel i7 16GB CPU-only laptop):
  Medical extraction: qwen2.5:3b > qwen2.5:1.5b > mistral > qwen2:0.5b
  Chat/copilot:       qwen2.5:3b > qwen2.5:1.5b > mistral > qwen2:0.5b
"""

import urllib.request
import json
from typing import Optional, List

_EXTRACTION_PRIORITY = [
    "qwen2.5:3b",
    "qwen2.5:1.5b",
    "mistral",
    "qwen2.5:0.5b",
    "qwen2:0.5b",
]

_CHAT_PRIORITY = [
    "qwen2.5:3b",
    "qwen2.5:1.5b",
    "mistral",
    "qwen2.5:0.5b",
    "qwen2:0.5b",
]

_cached_models: Optional[List[str]] = None


def get_installed_models() -> List[str]:
    """Returns list of model names currently installed in Ollama."""
    global _cached_models
    if _cached_models is not None:
        return _cached_models

    try:
        req = urllib.request.Request(
            "http://localhost:11434/api/tags",
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            _cached_models = [m["name"] for m in data.get("models", [])]
            return _cached_models
    except Exception:
        _cached_models = []
        return []


def get_best_extraction_model() -> str:
    """
    Returns the best available model for medical report extraction.
    Falls back down the priority list until a match is found.
    """
    installed = get_installed_models()
    for preferred in _EXTRACTION_PRIORITY:
        if preferred in installed:
            print(f"[ModelSelector] Using extraction model: {preferred}")
            return preferred
    # Last resort: return first installed model
    if installed:
        print(f"[ModelSelector] Warning: No preferred model installed. Using: {installed[0]}")
        return installed[0]
    return "qwen2.5:3b"  # Return target even if not installed (will fail at inference)


def get_best_chat_model() -> str:
    """
    Returns the best available model for chat/copilot use.
    """
    installed = get_installed_models()
    for preferred in _CHAT_PRIORITY:
        if preferred in installed:
            return preferred
    if installed:
        return installed[0]
    return "qwen2.5:3b"


def invalidate_cache():
    """Call this after installing a new model to re-detect."""
    global _cached_models
    _cached_models = None


def get_model_status() -> dict:
    """Returns a dict showing which models are installed and what will be used."""
    installed = get_installed_models()
    return {
        "installed_models": installed,
        "extraction_model": get_best_extraction_model(),
        "chat_model": get_best_chat_model(),
        "target_installed": "qwen2.5:3b" in installed,
    }

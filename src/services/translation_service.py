"""
SwasthyaConnect — Translation Service (Ollama-powered)
======================================================
Uses the already-running Ollama model to translate text between
English and Indian languages. No extra dependencies needed.
"""

import json
import urllib.request
import urllib.error
from typing import Dict, Optional

SUPPORTED_LANGS: Dict[str, str] = {
    "en": "English",
    "hi": "Hindi (हिंदी)",
    "mr": "Marathi (मराठी)",
    "ta": "Tamil (தமிழ்)",
    "bn": "Bengali (বাংলা)",
    "te": "Telugu (తెలుగు)",
    "kn": "Kannada (ಕನ್ನಡ)",
    "gu": "Gujarati (ગુજરાતી)",
}

_LANG_FULL_NAME = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "ta": "Tamil",
    "bn": "Bengali",
    "te": "Telugu",
    "kn": "Kannada",
    "gu": "Gujarati",
}


def _get_model_name() -> str:
    """Returns the best available Ollama model for translation."""
    try:
        from src.services.model_selector import get_best_chat_model
        return get_best_chat_model()
    except Exception:
        return "qwen2.5:3b"


def translate_text(text: str, target_lang: str, source_lang: str = "en", model_name: Optional[str] = None) -> str:
    """
    Translate text from source_lang to target_lang using Ollama.
    
    Args:
        text: The text to translate.
        target_lang: Target language code (e.g., 'hi', 'mr').
        source_lang: Source language code (default 'en').
        model_name: Override Ollama model name.
    
    Returns:
        Translated text string.
    """
    if not text or not text.strip():
        return text
    
    # No translation needed if same language
    if target_lang == source_lang:
        return text
    
    if target_lang not in _LANG_FULL_NAME:
        return text
    
    src_name = _LANG_FULL_NAME.get(source_lang, "English")
    tgt_name = _LANG_FULL_NAME.get(target_lang, "Hindi")
    
    if model_name is None:
        model_name = _get_model_name()
    
    # Split long text into manageable chunks (~500 words)
    chunks = _split_text(text, max_words=400)
    translated_chunks = []
    
    for chunk in chunks:
        translated = _translate_chunk(chunk, src_name, tgt_name, model_name)
        translated_chunks.append(translated)
    
    return "\n".join(translated_chunks)


def translate_summary_fields(summary_json: dict, target_lang: str, model_name: Optional[str] = None) -> dict:
    """
    Translate human-readable fields in a medical summary JSON.
    Returns a new dict with translated values (original structure preserved).
    """
    if target_lang == "en":
        return summary_json
    
    import copy
    translated = copy.deepcopy(summary_json)
    
    if model_name is None:
        model_name = _get_model_name()
    
    tgt_name = _LANG_FULL_NAME.get(target_lang, "Hindi")
    
    # Fields to translate
    _translate_field(translated, "summary", "patient_overview", tgt_name, model_name)
    _translate_list(translated, "overall_summary_bullets", tgt_name, model_name)
    _translate_list(translated, "diagnosis", tgt_name, model_name)
    _translate_list(translated, "symptoms", tgt_name, model_name)
    _translate_list(translated, "impression_in_simple_words", tgt_name, model_name)
    _translate_list(translated, "next_steps", tgt_name, model_name)
    _translate_list(translated, "key_findings", tgt_name, model_name)
    _translate_list(translated, "urgent_warning_signs", tgt_name, model_name)
    _translate_list(translated, "disclaimer", tgt_name, model_name)
    
    # Glossary meanings
    glossary = translated.get("glossary", [])
    for item in glossary:
        if isinstance(item, dict) and item.get("meaning_simple"):
            item["meaning_simple"] = _translate_chunk(item["meaning_simple"], "English", tgt_name, model_name)
    
    # Abnormal values meanings
    abn = translated.get("abnormal_values_explained", translated.get("abnormal_values", []))
    for item in abn:
        if isinstance(item, dict) and item.get("meaning_simple"):
            item["meaning_simple"] = _translate_chunk(item["meaning_simple"], "English", tgt_name, model_name)
    
    return translated


def _translate_field(obj: dict, parent_key: str, field_key: str, tgt_name: str, model_name: str):
    """Translate a nested field in a dict."""
    parent = obj.get(parent_key, {})
    if isinstance(parent, dict) and parent.get(field_key):
        val = parent[field_key]
        if isinstance(val, str) and val.strip():
            parent[field_key] = _translate_chunk(val, "English", tgt_name, model_name)


def _translate_list(obj: dict, key: str, tgt_name: str, model_name: str):
    """Translate a list of strings in a dict."""
    items = obj.get(key, [])
    if not items:
        return
    # Batch all strings into one translation call for speed
    strings = [s for s in items if isinstance(s, str) and s.strip()]
    if not strings:
        return
    
    combined = "\n---\n".join(strings)
    translated = _translate_chunk(combined, "English", tgt_name, model_name)
    parts = translated.split("\n---\n") if "---" in translated else translated.split("\n")
    
    # Map back
    idx = 0
    for i, item in enumerate(items):
        if isinstance(item, str) and item.strip():
            if idx < len(parts):
                items[i] = parts[idx].strip()
                idx += 1


def _split_text(text: str, max_words: int = 400) -> list:
    """Split text into chunks of approximately max_words."""
    words = text.split()
    if len(words) <= max_words:
        return [text]
    
    chunks = []
    current = []
    for word in words:
        current.append(word)
        if len(current) >= max_words:
            chunks.append(" ".join(current))
            current = []
    if current:
        chunks.append(" ".join(current))
    return chunks


def _translate_chunk(text: str, src_name: str, tgt_name: str, model_name: str) -> str:
    """Translate a single chunk of text via Ollama."""
    prompt = f"""Translate the following text from {src_name} to {tgt_name}.
Rules:
- Return ONLY the translated text, nothing else.
- Do NOT add explanations, notes, or commentary.
- Preserve formatting (bullet points, line breaks).
- Keep medical terms, drug names, and numbers as-is (do not translate them).
- If a word has no translation, keep the original.

Text to translate:
{text}"""

    try:
        url = "http://localhost:11434/api/generate"
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 1024,
                "top_p": 0.9,
            }
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get("response", text).strip()
    except Exception as e:
        print(f"[Translation] Error: {e}")
        return text  # Return original on failure

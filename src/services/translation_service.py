"""
SwasthyaConnect — Multilingual Translation Service (Offline NLLB-200 + Ollama Fallback)
=======================================================================================
Provides zero-hallucination, 100% offline neural translation across Indian languages
using Meta's NLLB-200 (No Language Left Behind) Seq2Seq architecture, with a seamless
fallback to local Ollama.
"""

import json
import logging
import urllib.request
import urllib.error
from typing import Dict, Optional, List

logger = logging.getLogger(__name__)

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

# Mapping ISO codes to Meta NLLB BCP-47 language codes
_NLLB_CODES = {
    "en": "eng_Latn",
    "hi": "hin_Deva",
    "mr": "mar_Deva",
    "ta": "tam_Taml",
    "bn": "ben_Beng",
    "te": "tel_Telu",
    "kn": "kan_Knda",
    "gu": "guj_Gujr",
    "ml": "mal_Mlym",
    "pa": "pan_Guru",
    "ur": "urd_Arab",
}

# Global in-memory cache for NLLB model
_nllb_tokenizer = None
_nllb_model = None
_nllb_available = True


def _get_nllb_engine():
    """Lazily loads and returns the offline NLLB-200 tokenizer and model."""
    global _nllb_tokenizer, _nllb_model, _nllb_available

    if not _nllb_available:
        return None, None

    if _nllb_tokenizer is not None and _nllb_model is not None:
        return _nllb_tokenizer, _nllb_model

    try:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
        model_name = "facebook/nllb-200-distilled-600M"
        
        logger.info("[Translation] Loading offline NLLB-200 model...")
        _nllb_tokenizer = AutoTokenizer.from_pretrained(model_name)
        _nllb_model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        logger.info("[Translation] NLLB-200 loaded successfully.")
        return _nllb_tokenizer, _nllb_model
    except Exception as e:
        logger.warning(f"[Translation] Could not load NLLB-200: {e}. Falling back to Ollama.")
        _nllb_available = False
        return None, None


def _translate_chunk_nllb(text: str, target_lang: str, source_lang: str = "en") -> Optional[str]:
    """Translates text using the offline NLLB-200 model."""
    tokenizer, model = _get_nllb_engine()
    if tokenizer is None or model is None:
        return None

    tgt_code = _NLLB_CODES.get(target_lang)
    if not tgt_code:
        return None

    try:
        inputs = tokenizer(text, return_tensors="pt")
        target_token_id = tokenizer.convert_tokens_to_ids(tgt_code)
        
        tokens = model.generate(
            **inputs,
            forced_bos_token_id=target_token_id,
            max_length=512
        )
        return tokenizer.decode(tokens[0], skip_special_tokens=True).strip()
    except Exception as e:
        logger.error(f"[Translation] NLLB inference error: {e}")
        return None


def _get_model_name() -> str:
    """Returns the best available Ollama model for translation."""
    try:
        from src.services.model_selector import get_best_chat_model
        return get_best_chat_model()
    except Exception:
        return "qwen2.5:3b"


def translate_text(text: str, target_lang: str, source_lang: str = "en", model_name: Optional[str] = None) -> str:
    """
    Translate text from source_lang to target_lang.
    Prioritizes the 100% offline, zero-hallucination NLLB-200 model,
    falling back to local Ollama if needed.
    """
    if not text or not text.strip():
        return text

    if target_lang == source_lang:
        return text

    if target_lang not in _LANG_FULL_NAME:
        return text

    # Split into lines/paragraphs to retain formatting
    lines = text.split("\n")
    translated_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            translated_lines.append("")
            continue

        # Try offline NLLB-200 first (zero hallucination, offline)
        trans = _translate_chunk_nllb(stripped, target_lang, source_lang)
        if trans:
            translated_lines.append(trans)
            continue

        # Fallback: Ollama
        src_name = _LANG_FULL_NAME.get(source_lang, "English")
        tgt_name = _LANG_FULL_NAME.get(target_lang, "Hindi")
        if model_name is None:
            model_name = _get_model_name()
        
        trans_ollama = _translate_chunk_ollama(stripped, src_name, tgt_name, model_name)
        translated_lines.append(trans_ollama)

    return "\n".join(translated_lines)


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
    _translate_field(translated, "summary", "patient_overview", target_lang)
    _translate_list(translated, "overall_summary_bullets", target_lang)
    _translate_list(translated, "diagnosis", target_lang)
    _translate_list(translated, "symptoms", target_lang)
    _translate_list(translated, "impression_in_simple_words", target_lang)
    _translate_list(translated, "next_steps", target_lang)
    _translate_list(translated, "key_findings", target_lang)
    _translate_list(translated, "urgent_warning_signs", target_lang)
    _translate_list(translated, "disclaimer", target_lang)

    # Glossary meanings
    glossary = translated.get("glossary", [])
    for item in glossary:
        if isinstance(item, dict) and item.get("meaning_simple"):
            item["meaning_simple"] = translate_text(item["meaning_simple"], target_lang)

    # Abnormal values meanings
    abn = translated.get("abnormal_values_explained", translated.get("abnormal_values", []))
    for item in abn:
        if isinstance(item, dict) and item.get("meaning_simple"):
            item["meaning_simple"] = translate_text(item["meaning_simple"], target_lang)

    return translated


def _translate_field(obj: dict, parent_key: str, field_key: str, target_lang: str):
    """Translate a nested field in a dict."""
    parent = obj.get(parent_key, {})
    if isinstance(parent, dict) and parent.get(field_key):
        val = parent[field_key]
        if isinstance(val, str) and val.strip():
            parent[field_key] = translate_text(val, target_lang)


def _translate_list(obj: dict, key: str, target_lang: str):
    """Translate a list of strings in a dict."""
    items = obj.get(key, [])
    if not items:
        return
    for i, item in enumerate(items):
        if isinstance(item, str) and item.strip():
            items[i] = translate_text(item, target_lang)


def _translate_chunk_ollama(text: str, src_name: str, tgt_name: str, model_name: str) -> str:
    """Translate a single chunk of text via Ollama as fallback."""
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
        logger.error(f"[Translation Ollama] Error: {e}")
        return text

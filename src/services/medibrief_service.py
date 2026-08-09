import os
import json
import urllib.request
import urllib.error
import re
from typing import Dict, Any, List

def lang_name(code: str) -> str:
    return {"en": "English", "hi": "Hindi", "mr": "Marathi"}.get(code, "English")

class MedibriefService:
    @staticmethod
    def generate_json_summary(report_text: str, requested_language: str, confidence: str, extraction_notes: List[str], model_name: str = "qwen2.5:3b") -> Dict[str, Any]:
        """
        Uses local Ollama API to generate structured medical summaries using strict extraction rules.
        No hallucination. No inference. Only explicit values from the report text.
        """
        prompt = f"""========================
STRICT RULES (CRITICAL)
=======================

1. DO NOT hallucinate.
2. DO NOT infer missing values.
3. DO NOT assume medical conditions.
4. DO NOT generate abnormal values unless explicitly derivable by rule.
5. DO NOT confuse medical fields (e.g., BP is NOT heart rate).
6. DO NOT create placeholder text like "bullet 1", "unknown term", etc.
7. If a value is not present -> return null.
8. If unsure -> return null, not guesses.

========================
EXTRACTION RULES
========================

- Extract ONLY explicitly written values from the report.
- Preserve original numbers and units exactly.
- Do NOT modify or reinterpret values.
- Separate each vital sign correctly:
    - Blood Pressure = systolic/diastolic (e.g., 128/84 mmHg)
    - Heart Rate = bpm only
    - SpO2 = percentage
    - Temperature = degrees F or C

========================
ABNORMAL VALUE RULES (NO AI GUESSING)
========================

You are NOT allowed to decide abnormalities using reasoning.
ONLY mark abnormal if: value exceeds standard medical range AND value is explicitly present.
If no valid numeric value exists -> DO NOT generate abnormal entry.

Reference ranges:
- Heart Rate: normal 60-100 bpm. Abnormal if <60 or >100.
- Blood Pressure: abnormal if systolic >140 mmHg or diastolic >90 mmHg.
- SpO2: abnormal if <95%.

If value format is invalid -> ignore it.

========================
GLOSSARY RULES
========================

- Extract ONLY real medical terms present in text.
- If no complex term exists -> return empty array [].
- DO NOT invent glossary items.

========================
FINAL RULE
========================

If any instruction conflicts with creativity or reasoning:
-> ALWAYS prefer strict extraction over explanation.

Output language for patient-facing text: {lang_name(requested_language)}

========================
MANDATORY JSON OUTPUT FORMAT
========================

Return ONLY valid JSON. No markdown. No prose. No ```json blocks.

  {{
    "meta": {{ }},
    "summary": {{
      "patient_overview": null,
      "key_findings": []
    }},
    "vitals": {{
      "blood_pressure": null,
      "heart_rate": null,
      "temperature": null,
      "spO2": null,
      "weight": null,
      "bmi": null
    }},
    "diagnosis": [],
    "symptoms": [],
    "medications": [
      {{
        "name": null,
        "dosage": null,
        "frequency": null,
        "duration": null
      }}
    ],
    "abnormal_values": [],
    "medical_terms": [],
    "overall_summary_bullets": [],
    "impression_in_simple_words": [],
    "next_steps": [],
    "urgent_warning_signs": [],
    "report_date": null,
    "disclaimer": ["This is an AI-extracted summary. It is not medical advice."]
  }}

========================
MEDICAL REPORT TEXT (extract from below ONLY)
========================

{report_text}
"""
        json_schema = {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "object",
                    "properties": {
                        "patient_overview": {"type": ["string", "null"]},
                        "key_findings": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "vitals": {
                    "type": "object",
                    "properties": {
                        "blood_pressure": {"type": ["string", "null"]},
                        "heart_rate": {"type": ["string", "null"]},
                        "temperature": {"type": ["string", "null"]},
                        "spO2": {"type": ["string", "null"]},
                        "weight": {"type": ["string", "null"]},
                        "bmi": {"type": ["string", "null"]}
                    }
                },
                "diagnosis": {"type": "array", "items": {"type": "string"}},
                "symptoms": {"type": "array", "items": {"type": "string"}},
                "medications": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": ["string", "null"]},
                            "dosage": {"type": ["string", "null"]},
                            "frequency": {"type": ["string", "null"]},
                            "duration": {"type": ["string", "null"]}
                        }
                    }
                },
                "abnormal_values": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "test": {"type": ["string", "null"]},
                            "value": {"type": ["string", "null"]},
                            "unit": {"type": ["string", "null"]},
                            "reference_range": {"type": ["string", "null"]},
                            "flag": {"type": ["string", "null"]},
                            "meaning_simple": {"type": ["string", "null"]}
                        }
                    }
                },
                "medical_terms": {"type": "array", "items": {"type": "string"}},
                "overall_summary_bullets": {"type": "array", "items": {"type": "string"}},
                "impression_in_simple_words": {"type": "array", "items": {"type": "string"}},
                "next_steps": {"type": "array", "items": {"type": "string"}},
                "urgent_warning_signs": {"type": "array", "items": {"type": "string"}},
                "report_date": {"type": ["string", "null"]},
                "disclaimer": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["summary", "vitals", "diagnosis", "symptoms", "medications", "abnormal_values", "medical_terms", "overall_summary_bullets", "impression_in_simple_words", "next_steps", "urgent_warning_signs", "report_date", "disclaimer"]
        }

        try:
            url = "http://localhost:11434/api/generate"
            payload = {
                "model": model_name,
                "prompt": prompt,
                "format": json_schema,
                "stream": False,
                "options": {
                    "temperature": 0.0,
                    "seed": 42
                }
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=1200) as response:
                result = json.loads(response.read().decode('utf-8'))
                response_text = result.get("response", "{}").strip()
                # Strip markdown fences if present
                if response_text.startswith("```"):
                    response_text = response_text.split("\n", 1)[-1]
                if response_text.endswith("```"):
                    response_text = response_text.rsplit("\n", 1)[0]
                obj = json.loads(response_text)
                # Add meta information
                obj.setdefault("meta", {})
                obj["meta"]["requested_language"] = requested_language
                obj["meta"]["language_name"] = lang_name(requested_language)
                obj["meta"]["confidence"] = confidence
                obj["meta"]["extraction_notes"] = extraction_notes
                obj["meta"]["model_used"] = f"ollama-{model_name}"
                # Bridge legacy keys for UI compatibility
                obj.setdefault("key_findings", obj.get("summary", {}).get("key_findings", []))
                vitals = obj.get("vitals", {})
                obj.setdefault("vital_signs", [v for v in [
                    f"Blood Pressure: {vitals.get('blood_pressure')}" if vitals.get('blood_pressure') else None,
                    f"Heart Rate: {vitals.get('heart_rate')}" if vitals.get('heart_rate') else None,
                    f"Temperature: {vitals.get('temperature')}" if vitals.get('temperature') else None,
                    f"SpO2: {vitals.get('spO2')}" if vitals.get('spO2') else None,
                    f"Weight: {vitals.get('weight')}" if vitals.get('weight') else None,
                    f"BMI: {vitals.get('bmi')}" if vitals.get('bmi') else None,
                ] if v])
                obj.setdefault("abnormal_values_explained", obj.get("abnormal_values", []))
                obj.setdefault("glossary", [
                    {"term": t, "meaning_simple": ""} if isinstance(t, str) else t
                    for t in obj.get("medical_terms", [])
                ])
                obj.setdefault("medications_or_treatments_mentioned", [
                    " ".join(filter(None, [m.get("name"), m.get("dosage"), m.get("frequency"), m.get("duration")])).strip()
                    for m in obj.get("medications", []) if m.get("name")
                ])
                obj.setdefault("impression_in_simple_words", obj.get("diagnosis", []))
                return obj
        except urllib.error.URLError as e:
            raise ValueError(f"Could not connect to local Ollama. Ensure Ollama is running and '{model_name}' is installed. Error: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to parse Ollama JSON response: {str(e)}")

    @staticmethod
    def _rule_based_summarizer(text: str) -> Dict[str, Any]:
        """Fallback summariser that extracts bullet points based on medical keywords."""
        keywords = ["diagnosis", "prescribed", "blood pressure", "sugar", "cholesterol", "symptom", "recommend"]
        sentences = re.split(r"[.!?]\s+", text)
        bullets = [s.strip() for s in sentences if any(k in s.lower() for k in keywords)]
        if not bullets:
            bullets = sentences[:5]
        return {"overall_summary_bullets": bullets, "source": "rule_based"}

    @staticmethod
    def summarize_report(report_text: str, requested_language: str = "en", confidence: str = "high", extraction_notes: List[str] = None, model_name: str = "qwen2.5:3b") -> Dict[str, Any]:
        """High‑level helper that tries the LLM first and falls back to rule‑based logic on any failure or empty result."""
        extraction_notes = extraction_notes or []
        try:
            result = MedibriefService.generate_json_summary(report_text, requested_language, confidence, extraction_notes, model_name)
            # Simple validation: ensure we got a non‑empty overall_summary_bullets list
            if not result.get("overall_summary_bullets"):
                raise ValueError("Empty AI summary")
            result["is_ai_generated"] = 1
            return result
        except Exception as e:
            # Log the error for debugging (in real app you might use logging)
            print(f"AI summarisation failed ({e}); falling back to rule‑based summariser.")
            fallback = MedibriefService._rule_based_summarizer(report_text)
            fallback["is_ai_generated"] = 0
            # Preserve required top‑level keys so UI can still consume it
            fallback.update({
                "meta": {
                    "requested_language": requested_language,
                    "language_name": lang_name(requested_language),
                    "confidence": confidence,
                    "extraction_notes": extraction_notes,
                    "model_used": "fallback-rule_based"
                },
                "summary": {"patient_overview": None, "key_findings": []},
                "vitals": {"blood_pressure": None, "heart_rate": None, "temperature": None, "spO2": None, "weight": None, "bmi": None},
                "diagnosis": [], "symptoms": [], "medications": [], "abnormal_values": [], "medical_terms": [],
                "impression_in_simple_words": [], "next_steps": [], "urgent_warning_signs": [], "report_date": None,
                "disclaimer": ["This is a rule‑based summary. It may omit details."]
            })
            return fallback

    @staticmethod
    def answer_question(summary_json: dict, question: str, model_name: str = "qwen2.5:3b") -> str:
        prompt = f"""You are a specialized medical report assistant.
Answer the user's question using ONLY the provided summary JSON below.

STRICT RULES:
- You are a specialized medical assistant.
- If the QUESTION is completely unrelated to healthcare, medicine, or the provided report, you MUST reply with exactly: "I am a medical assistant. Please ask questions related to your health or the provided medical report." - do not provide an answer.
- Answer ONLY from the data in SUMMARY_JSON. Do NOT invent values, diagnoses, or medications.
- If the answer is not present in the JSON, say: "Not found in the summary."
- Be concise and direct.
- Use bullet points when listing multiple items.

SUMMARY_JSON:
{json.dumps(summary_json, ensure_ascii=False)}

QUESTION:
{question}
"""
        try:
            url = "http://localhost:11434/api/generate"
            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.0, "seed": 42}
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get("response", "No answer generated.").strip()
        except urllib.error.URLError:
            return "Error: Could not reach Ollama server. Make sure it is running on localhost:11434."
        except Exception as e:
            return f"Error: {str(e)}"

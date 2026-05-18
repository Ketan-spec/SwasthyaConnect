import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, List

def lang_name(code: str) -> str:
    return {"en": "English", "hi": "Hindi", "mr": "Marathi"}.get(code, "English")

class MedibriefService:
    @staticmethod
    def generate_json_summary(report_text: str, requested_language: str, confidence: str, extraction_notes: List[str], model_name: str = "mistral") -> Dict[str, Any]:
        """
        Uses local Ollama API to generate structured medical summaries using strict extraction rules.
        No hallucination. No inference. Only explicit values from the report text.
        """
        prompt = f"""========================
STRICT RULES (CRITICAL)
========================

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
  "meta": {{}},
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
        try:
            url = "http://localhost:11434/api/generate"
            payload = {
                "model": model_name,
                "prompt": prompt,
                "format": "json",
                "stream": False
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=1200) as response:
                result = json.loads(response.read().decode('utf-8'))
                response_text = result.get("response", "{}").strip()
                
                # Strip any accidental markdown fences
                if response_text.startswith("```"):
                    response_text = response_text.split("\n", 1)[-1]
                if response_text.endswith("```"):
                    response_text = response_text.rsplit("\n", 1)[0]
                    
                obj = json.loads(response_text)
                
                # Add meta
                obj.setdefault("meta", {})
                obj["meta"]["requested_language"] = requested_language
                obj["meta"]["language_name"] = lang_name(requested_language)
                obj["meta"]["confidence"] = confidence
                obj["meta"]["extraction_notes"] = extraction_notes
                obj["meta"]["model_used"] = f"ollama-{model_name}"
                
                # ---- Bridge new schema -> legacy keys so existing UI code works ----
                
                # key_findings (from new summary.key_findings)
                obj.setdefault("key_findings", obj.get("summary", {}).get("key_findings", []))
                
                # vital_signs as string list (for heatmap / dashboard)
                vitals = obj.get("vitals", {})
                obj.setdefault("vital_signs", [v for v in [
                    f"Blood Pressure: {vitals.get('blood_pressure')}" if vitals.get("blood_pressure") else None,
                    f"Heart Rate: {vitals.get('heart_rate')}" if vitals.get("heart_rate") else None,
                    f"Temperature: {vitals.get('temperature')}" if vitals.get("temperature") else None,
                    f"SpO2: {vitals.get('spO2')}" if vitals.get("spO2") else None,
                    f"Weight: {vitals.get('weight')}" if vitals.get("weight") else None,
                    f"BMI: {vitals.get('bmi')}" if vitals.get("bmi") else None,
                ] if v])
                
                # abnormal_values_explained from new abnormal_values
                obj.setdefault("abnormal_values_explained", obj.get("abnormal_values", []))
                
                # glossary from medical_terms
                obj.setdefault("glossary", [
                    {"term": t, "meaning_simple": ""} if isinstance(t, str) else t
                    for t in obj.get("medical_terms", [])
                ])
                
                # medications readable list
                obj.setdefault("medications_or_treatments_mentioned", [
                    " ".join(filter(None, [m.get("name"), m.get("dosage"), m.get("frequency"), m.get("duration")])).strip()
                    for m in obj.get("medications", []) if m.get("name")
                ])
                
                # impression_in_simple_words from diagnosis
                obj.setdefault("impression_in_simple_words", obj.get("diagnosis", []))
                
                return obj
        except urllib.error.URLError as e:
            raise ValueError(f"Could not connect to local Ollama. Ensure Ollama is running and '{model_name}' is installed. Error: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to parse Ollama JSON response: {str(e)}")

    @staticmethod
    def answer_question(summary_json: dict, question: str, model_name: str = "mistral") -> str:
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
                "stream": False
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get("response", "No answer generated.").strip()
        except urllib.error.URLError:
            return "Error: Could not reach Ollama server. Make sure it is running on localhost:11434."
        except Exception as e:
            return f"Error: {str(e)}"

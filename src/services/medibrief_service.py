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
        Uses local Ollama API to generate structured medical summaries in strictly formatted JSON.
        """
        prompt = f"""
You are an expert medical AI. Analyze the following medical report and extract the details in strict JSON format.
Language: {lang_name(requested_language)}

The output MUST be a valid JSON object matching exactly this schema:
{{
  "meta": {{}},
  "overall_summary_bullets": ["bullet 1", "bullet 2"],
  "key_findings": ["finding 1"],
  "abnormal_values_explained": [
    {{"test": "Heart Rate", "value": "110", "unit": "bpm", "reference_range": "60-100", "flag": "High", "meaning_simple": "Your heart is beating faster than normal."}}
  ],
  "normal_highlights": ["Blood pressure is normal"],
  "impression_in_simple_words": ["The report shows..."],
  "medications_or_treatments_mentioned": ["Paracetamol 500mg"],
  "questions_for_doctor": ["Why is my heart rate high?"],
  "next_steps": ["Consult doctor"],
  "urgent_warning_signs": ["Chest pain"],
  "glossary": [
    {{"term": "Tachycardia", "meaning_simple": "Fast heart rate"}}
  ],
  "technical_lines_simplified": [],
  "disclaimer": ["This is an AI summary and not medical advice."]
}}

If a section has no data, return an empty list []. Do not use markdown blocks like ```json.
If extracting test results, strictly follow the keys: "test", "value", "unit", "reference_range", "flag", "meaning_simple".

Medical Report Text:
{report_text}
"""
        try:
            url = "http://localhost:11434/api/generate"
            data = {
                "model": model_name,
                "prompt": prompt,
                "format": "json",
                "stream": False
            }
            req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=1200) as response:
                result = json.loads(response.read().decode('utf-8'))
                response_text = result.get("response", "{}")
                
                if response_text.startswith("```json"):
                    response_text = response_text.replace("```json\n", "")
                if response_text.endswith("```"):
                    response_text = response_text.replace("\n```", "")
                    
                obj = json.loads(response_text)
                
                obj.setdefault("meta", {})
                obj["meta"]["requested_language"] = requested_language
                obj["meta"]["language_name"] = lang_name(requested_language)
                obj["meta"]["confidence"] = confidence
                obj["meta"]["extraction_notes"] = extraction_notes
                obj["meta"]["model_used"] = f"ollama-{model_name}"
                return obj
        except urllib.error.URLError as e:
            raise ValueError(f"Could not connect to local Ollama. Ensure Ollama is running and '{model_name}' is installed. HTTP Error: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to parse Ollama JSON response: {str(e)}")

    @staticmethod
    def answer_question(summary_json: dict, question: str, model_name: str = "mistral") -> str:
        prompt = f"""
You are a medical report assistant.
Answer the user's question using ONLY the provided summary JSON.
If the answer is not present, say: "Not found in the summary."

SUMMARY_JSON:
{json.dumps(summary_json, ensure_ascii=False)}

QUESTION:
{question}

Rules:
- Be concise.
- Use bullet points when helpful.
- Do not invent lab values or diagnoses.
- No extra commentary outside the answer.
"""
        try:
            url = "http://localhost:11434/api/generate"
            data = {
                "model": model_name,
                "prompt": prompt,
                "stream": False
            }
            req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get("response", "No answer generated.").strip()
        except urllib.error.URLError:
            return "Error: Could not reach Ollama server. Make sure it is running on localhost:11434."
        except Exception as e:
            return f"Error: {str(e)}"

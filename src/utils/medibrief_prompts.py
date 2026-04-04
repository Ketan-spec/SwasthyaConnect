SYSTEM_PROMPT = """
You are “MediBrief”, a careful medical report explainer.

Your job:
Convert medical report text into a structured, user-friendly explanation with glossary.

LANGUAGE RULE (MANDATORY)
Output language must be exactly the one requested in meta.requested_language:
- en = English
- hi = Hindi (Devanagari script)
- mr = Marathi (Devanagari script, Marathi phrasing)

Important:
- Keep medical test names (Hemoglobin, TSH, MRI, CT Scan etc.) in English.
- Explain everything else in the requested language.
- Do NOT mix languages.

SAFETY RULES (MANDATORY)
- Do NOT provide a final diagnosis.
- Use phrases like: “may suggest”, “could be related to”.
- Do NOT give dosage instructions.
- Do NOT tell the user to start/stop medicines.
- If serious red flags appear, include urgent warning signs and suggest immediate medical care.

OUTPUT RULES (STRICT)
- Output ONLY valid JSON.
- No markdown.
- No extra text.
- No trailing commas.
- If something is unknown, use [] or "not provided".
- Keep explanations simple (8th grade level).
- Glossary terms: keep term in English; explain in requested language.
"""

SCHEMA_JSON = """
{
  "meta": {
    "doc_type": "string",
    "requested_language": "en|hi|mr",
    "language_name": "English|Hindi|Marathi",
    "confidence": "high|medium|low",
    "extraction_notes": ["string"]
  },
  "overall_summary_bullets": ["string"],
  "key_findings": ["string"],
  "abnormal_values_explained": [
    {
      "test": "string",
      "value": "string",
      "unit": "string",
      "reference_range": "string",
      "flag": "high|low|critical|borderline|unknown",
      "meaning_simple": "string"
    }
  ],
  "normal_highlights": ["string"],
  "impression_in_simple_words": ["string"],
  "medications_or_treatments_mentioned": ["string"],
  "questions_for_doctor": ["string"],
  "next_steps": ["string"],
  "urgent_warning_signs": ["string"],
  "glossary": [
    { "term": "string", "meaning_simple": "string", "context_from_report": "string" }
  ],
  "technical_lines_simplified": [
    { "original": "string", "simple": "string" }
  ],
  "disclaimer": "string"
}
"""

def build_user_prompt(report_text: str, requested_language: str) -> str:
    return f"""
requested_language: {requested_language}

Extracted medical document text:
\"\"\"
{report_text}
\"\"\"

Output ONLY JSON in this exact schema:
{SCHEMA_JSON}

All user-facing text must be in the requested language.
""".strip()

def build_retry_prompt(report_text: str, requested_language: str) -> str:
    return f"""
Your previous response was invalid JSON or did not match the schema.

Rules:
- Output ONLY valid JSON
- No markdown, no extra text
- Must match schema exactly

requested_language: {requested_language}

Document text:
\"\"\"
{report_text}
\"\"\"

Schema:
{SCHEMA_JSON}
""".strip()

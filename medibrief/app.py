# =========================
# MediBrief — FULL app.py (EN / HI / MR) + OCR + Gemini + Devanagari PDF + History + Q&A + Save Uploaded PDFs
# =========================
# ✅ Features
# 1) Upload PDF (scanned or text) → extract text (PyMuPDF) + OCR fallback (Tesseract)
# 2) Generate summary JSON using Gemini (robust model picker)
# 3) Export Hospital-style PDF (proper Hindi/Marathi using Noto Sans Devanagari TTF)
# 4) Save every uploaded PDF to disk (storage/uploads + storage/index.json)
# 5) Save summary history (storage/summaries/*.json + index)
# 6) Ask multiple questions based on current summary (chat-style)
#
# ✅ Required folder structure
#   medibrief/
#     app.py
#     prompts.py
#     fonts/
#       NotoSansDevanagari-Regular.ttf   (REQUIRED, real .ttf)
#       NotoSansDevanagari-Bold.ttf      (OPTIONAL, real .ttf)
#     storage/ (auto-created)
#
# ✅ Environment variable
#   GEMINI_API_KEY=your_key
#
# ✅ Install deps
#   pip install streamlit pymupdf pillow pytesseract google-generativeai reportlab
#
# Run:
#   streamlit run app.py
# =========================

from __future__ import annotations

import os
import json
import hashlib
from pathlib import Path
from io import BytesIO
from datetime import datetime
from typing import Any, Dict, List, Optional

import streamlit as st
import fitz  # PyMuPDF
from PIL import Image
import pytesseract

import google.generativeai as genai

# PDF export (ReportLab)
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, ListFlowable, ListItem, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from prompts import SYSTEM_PROMPT, build_user_prompt, build_retry_prompt


# =========================
# Page config
# =========================
st.set_page_config(page_title="MediBrief", layout="wide")


# =========================
# OCR setup (Windows)
# =========================
TESS_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
TESS_OK = os.path.exists(TESS_PATH)
if TESS_OK:
    pytesseract.pytesseract.tesseract_cmd = TESS_PATH


# =========================
# Storage (uploads + summaries)
# =========================
STORAGE_DIR = Path("storage")
UPLOADS_DIR = STORAGE_DIR / "uploads"
SUMMARIES_DIR = STORAGE_DIR / "summaries"
UPLOAD_INDEX_FILE = STORAGE_DIR / "uploads_index.json"
SUMMARY_INDEX_FILE = STORAGE_DIR / "summaries_index.json"

UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
SUMMARIES_DIR.mkdir(parents=True, exist_ok=True)
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _load_json_list(path: Path) -> list:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []


def _save_json_list(path: Path, rows: list) -> None:
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def save_uploaded_pdf(file_name: str, pdf_bytes: bytes) -> dict:
    file_hash = _sha256(pdf_bytes)
    safe_name = "".join(c for c in file_name if c.isalnum() or c in ("-", "_", ".", " ")).strip()
    if not safe_name:
        safe_name = "report.pdf"

    stored_name = f"{file_hash[:12]}__{safe_name}"
    path = UPLOADS_DIR / stored_name

    if not path.exists():
        path.write_bytes(pdf_bytes)

    record = {
        "id": file_hash[:12],
        "hash": file_hash,
        "original_name": file_name,
        "stored_name": stored_name,
        "path": str(path.as_posix()),
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    index = _load_json_list(UPLOAD_INDEX_FILE)
    for r in index:
        if r.get("hash") == file_hash:
            return r

    index.insert(0, record)
    _save_json_list(UPLOAD_INDEX_FILE, index)
    return record


def list_saved_reports() -> list:
    return _load_json_list(UPLOAD_INDEX_FILE)


def load_report_bytes(path_str: str) -> bytes:
    return Path(path_str).read_bytes()


def save_summary_record(
    summary_json: dict,
    upload_record: Optional[dict],
    patient_meta: dict,
) -> dict:
    """
    Save summary JSON to storage/summaries/<id>.json
    """
    summary_id = _sha256(json.dumps(summary_json, ensure_ascii=False).encode("utf-8"))[:12]
    out_path = SUMMARIES_DIR / f"{summary_id}.json"

    record = {
        "summary_id": summary_id,
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "upload": upload_record or {},
        "patient_meta": patient_meta or {},
        "path": str(out_path.as_posix()),
        "language": summary_json.get("meta", {}).get("requested_language", ""),
        "model_used": summary_json.get("meta", {}).get("model_used", ""),
    }

    if not out_path.exists():
        out_path.write_text(json.dumps(summary_json, ensure_ascii=False, indent=2), encoding="utf-8")

    idx = _load_json_list(SUMMARY_INDEX_FILE)
    for r in idx:
        if r.get("summary_id") == summary_id:
            return r

    idx.insert(0, record)
    _save_json_list(SUMMARY_INDEX_FILE, idx)
    return record


def list_saved_summaries() -> list:
    return _load_json_list(SUMMARY_INDEX_FILE)


def load_summary_json(path_str: str) -> dict:
    return json.loads(Path(path_str).read_text(encoding="utf-8"))


# =========================
# Language helpers
# =========================
def lang_name(code: str) -> str:
    return {"en": "English", "hi": "Hindi", "mr": "Marathi"}.get(code, "English")


def translate_labels(lang: str) -> dict:
    # Labels used in PDF table/header (keep simple + stable)
    if lang == "hi":
        return {
            "patient_name": "रोगी का नाम",
            "report_id": "रिपोर्ट आईडी",
            "age": "आयु",
            "sex": "लिंग",
            "generated_at": "तैयार किया गया",
            "output_language": "आउटपुट भाषा",
            "confidence": "विश्वास स्तर",
            "model_used": "मॉडल उपयोग किया",
            "overall": "Overall Summary",
            "findings": "Key Findings",
            "abnormal": "Abnormal Values Explained",
            "next": "Next Steps",
            "urgent": "Urgent Warning Signs",
            "glossary": "Glossary (Difficult Terms)",
            "disclaimer": "Disclaimer",
        }
    if lang == "mr":
        return {
            "patient_name": "रुग्णाचे नाव",
            "report_id": "रिपोर्ट आयडी",
            "age": "वय",
            "sex": "लिंग",
            "generated_at": "तयार केले",
            "output_language": "आउटपुट भाषा",
            "confidence": "विश्वास स्तर",
            "model_used": "मॉडेल वापरले",
            "overall": "Overall Summary",
            "findings": "Key Findings",
            "abnormal": "Abnormal Values Explained",
            "next": "Next Steps",
            "urgent": "Urgent Warning Signs",
            "glossary": "Glossary (Difficult Terms)",
            "disclaimer": "Disclaimer",
        }
    return {
        "patient_name": "Patient Name",
        "report_id": "Report ID",
        "age": "Age",
        "sex": "Sex",
        "generated_at": "Generated At",
        "output_language": "Output Language",
        "confidence": "Confidence",
        "model_used": "Model Used",
        "overall": "Overall Summary",
        "findings": "Key Findings",
        "abnormal": "Abnormal Values Explained",
        "next": "Next Steps",
        "urgent": "Urgent Warning Signs",
        "glossary": "Glossary (Difficult Terms)",
        "disclaimer": "Disclaimer",
    }


# =========================
# Helpers: PDF extraction + OCR
# =========================
def extract_text_pymupdf(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages_text = []
    for page in doc:
        pages_text.append(page.get_text("text"))
    return "\n".join(pages_text).strip()


def ocr_pdf_pages(pdf_bytes: bytes, max_pages: int = 3) -> str:
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    out = []
    pages = min(len(doc), max_pages)

    for i in range(pages):
        pix = doc[i].get_pixmap(dpi=220)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        out.append(pytesseract.image_to_string(img))

    return "\n".join(out).strip()


def clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln]
    return "\n".join(lines)


# =========================
# JSON validation
# =========================
REQUIRED_TOP_KEYS = {
    "meta",
    "overall_summary_bullets",
    "key_findings",
    "abnormal_values_explained",
    "normal_highlights",
    "impression_in_simple_words",
    "medications_or_treatments_mentioned",
    "questions_for_doctor",
    "next_steps",
    "urgent_warning_signs",
    "glossary",
    "technical_lines_simplified",
    "disclaimer",
}


def validate_output_schema(obj: Dict[str, Any]) -> None:
    if not isinstance(obj, dict):
        raise ValueError("Output is not a JSON object.")
    missing = REQUIRED_TOP_KEYS - set(obj.keys())
    if missing:
        raise ValueError(f"Missing keys in JSON: {sorted(list(missing))}")
    if not isinstance(obj.get("meta"), dict):
        raise ValueError("meta must be an object.")


# =========================
# Gemini model picker
# =========================
def pick_model_from_list() -> str:
    models = list(genai.list_models())
    preferred: List[str] = []
    fallback: List[str] = []

    for m in models:
        name = getattr(m, "name", "")
        methods = getattr(m, "supported_generation_methods", []) or []
        if "generateContent" in methods:
            if "gemini" in name:
                preferred.append(name)
            else:
                fallback.append(name)

    if preferred:
        return preferred[0]
    if fallback:
        return fallback[0]
    raise RuntimeError("No available models support generateContent for your API key/project.")


# =========================
# Gemini call with retry
# =========================
def gemini_generate_json(
    report_text: str,
    requested_language: str,
    confidence: str,
    extraction_notes: List[str]
) -> Dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not set.\n\n"
            "Fix (Windows PowerShell):\n"
            "  setx GEMINI_API_KEY \"YOUR_KEY\"\n"
            "Then close & reopen VS Code / terminal."
        )

    genai.configure(api_key=api_key)

    model_name = pick_model_from_list()
    model = genai.GenerativeModel(model_name)

    normal_prompt = build_user_prompt(report_text, requested_language)
    retry_prompt = build_retry_prompt(report_text, requested_language)

    meta_hint = f"""
EXTRA META (must include in JSON meta):
- meta.requested_language = "{requested_language}"
- meta.language_name = "{lang_name(requested_language)}"
- meta.confidence = "{confidence}"
- meta.extraction_notes = {json.dumps(extraction_notes, ensure_ascii=False)}
IMPORTANT: Output ONLY JSON. No markdown. No extra text.
"""

    for attempt in range(2):
        user_prompt = normal_prompt if attempt == 0 else retry_prompt
        response = model.generate_content(SYSTEM_PROMPT + "\n\n" + meta_hint + "\n\n" + user_prompt)
        text_out = (response.text or "").strip()

        try:
            obj = json.loads(text_out)
            validate_output_schema(obj)

            obj["meta"]["requested_language"] = requested_language
            obj["meta"]["language_name"] = lang_name(requested_language)
            obj["meta"]["confidence"] = confidence
            obj["meta"]["extraction_notes"] = extraction_notes
            obj["meta"]["model_used"] = model_name
            return obj
        except Exception:
            if attempt == 1:
                raise ValueError(
                    "Gemini did not return valid JSON after retry.\n\n"
                    f"Model used: {model_name}\n\n"
                    f"Model output (first 2000 chars):\n{text_out[:2000]}"
                )

    raise RuntimeError("Unexpected failure.")


# =========================
# Q&A: answer ONLY from summary JSON (multi-question chat)
# =========================
def gemini_answer_question(summary_json: dict, question: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set.")

    genai.configure(api_key=api_key)
    model_name = pick_model_from_list()
    model = genai.GenerativeModel(model_name)

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
    resp = model.generate_content(prompt)
    return (resp.text or "").strip()


# =========================
# PDF fonts (Hindi/Marathi)
# =========================
def register_devanagari_fonts():
    regular = os.path.join("fonts", "NotoSansDevanagari-Regular.ttf")
    bold = os.path.join("fonts", "NotoSansDevanagari-Bold.ttf")

    if not os.path.exists(regular):
        raise FileNotFoundError("Missing font: fonts/NotoSansDevanagari-Regular.ttf")

    if "NotoDeva" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("NotoDeva", regular))

    if os.path.exists(bold) and "NotoDeva-Bold" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("NotoDeva-Bold", bold))


# =========================
# PDF: header/footer
# =========================
def _pdf_header_footer(canvas, doc, footer_text: str, font_name="Helvetica", font_bold="Helvetica-Bold"):
    canvas.saveState()
    width, height = A4

    canvas.setFont(font_bold, 11)
    canvas.drawString(40, height - 40, "MediBrief — Patient-Friendly Medical Summary")

    canvas.setFont(font_name, 9)
    canvas.drawString(40, height - 55, "Generated by AI (for informational use only)")

    canvas.setStrokeColorRGB(0.7, 0.7, 0.7)
    canvas.line(40, height - 62, width - 40, height - 62)

    canvas.setStrokeColorRGB(0.7, 0.7, 0.7)
    canvas.line(40, 45, width - 40, 45)

    canvas.setFont(font_name, 8)
    canvas.drawString(40, 30, footer_text[:120])
    canvas.drawRightString(width - 40, 30, f"Page {canvas.getPageNumber()}")

    canvas.restoreState()


# =========================
# PDF generator (hospital style)
# Fix for "incomplete table data" in hi/mr:
# - Use Devanagari font for the table
# - Use Paragraphs inside table cells (NOT raw strings)
# =========================
def build_summary_pdf_bytes(
    result: dict,
    patient_name: str,
    patient_age: str,
    patient_sex: str,
    report_id: str,
) -> bytes:
    buffer = BytesIO()
    meta = result.get("meta", {})
    req_lang = meta.get("requested_language", "en")

    # Choose fonts
    if req_lang in ["hi", "mr"]:
        register_devanagari_fonts()
        FONT = "NotoDeva"
        FONT_BOLD = "NotoDeva-Bold" if "NotoDeva-Bold" in pdfmetrics.getRegisteredFontNames() else "NotoDeva"
    else:
        FONT = "Helvetica"
        FONT_BOLD = "Helvetica-Bold"

    labels = translate_labels(req_lang)

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Cell", fontSize=9, leading=11, fontName=FONT))
    styles.add(ParagraphStyle(name="CellBold", fontSize=9, leading=11, fontName=FONT_BOLD))
    styles.add(ParagraphStyle(name="Small", fontSize=9, leading=11, fontName=FONT))
    styles.add(ParagraphStyle(name="Section", fontSize=12, leading=14, spaceAfter=6, spaceBefore=10, fontName=FONT_BOLD))

    generated_at = datetime.now().strftime("%d %b %Y, %I:%M %p")
    footer_text = "Not medical advice. For emergencies, seek urgent medical care."

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=40,
        rightMargin=40,
        topMargin=80,
        bottomMargin=70,
        title="MediBrief Summary",
    )

    story: List[Any] = []

    lang_line = f"{meta.get('language_name', 'not provided')} ({meta.get('requested_language', '')})"
    conf_line = meta.get("confidence", "not provided")
    model_used = meta.get("model_used", "not provided")

    p_name = patient_name.strip() if patient_name.strip() else "Not provided"
    p_age = patient_age.strip() if patient_age.strip() else "Not provided"
    p_sex = patient_sex.strip() if patient_sex.strip() else "Not provided"
    r_id = report_id.strip() if report_id.strip() else "Not provided"

    # Build table with Paragraphs (fixes missing/garbled text in hi/mr)
    info_data = [
        [Paragraph(labels["patient_name"], styles["CellBold"]), Paragraph(p_name, styles["Cell"]),
         Paragraph(labels["report_id"], styles["CellBold"]), Paragraph(r_id, styles["Cell"])],

        [Paragraph(labels["age"], styles["CellBold"]), Paragraph(p_age, styles["Cell"]),
         Paragraph(labels["sex"], styles["CellBold"]), Paragraph(p_sex, styles["Cell"])],

        [Paragraph(labels["generated_at"], styles["CellBold"]), Paragraph(generated_at, styles["Cell"]),
         Paragraph(labels["output_language"], styles["CellBold"]), Paragraph(lang_line, styles["Cell"])],

        [Paragraph(labels["confidence"], styles["CellBold"]), Paragraph(conf_line, styles["Cell"]),
         Paragraph(labels["model_used"], styles["CellBold"]), Paragraph(model_used, styles["Cell"])],
    ]

    table = Table(info_data, colWidths=[95, 165, 85, 135])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.3, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))

    story.append(table)
    story.append(Spacer(1, 10))

    def add_bullets(title: str, items: list):
        story.append(Paragraph(title, styles["Section"]))
        if items:
            story.append(ListFlowable(
                [ListItem(Paragraph(str(x), styles["Small"])) for x in items],
                bulletType="bullet",
                leftIndent=18
            ))
        else:
            story.append(Paragraph("Not provided.", styles["Small"]))
        story.append(Spacer(1, 8))

    add_bullets(labels["overall"], result.get("overall_summary_bullets", []))
    add_bullets(labels["findings"], result.get("key_findings", []))

    story.append(Paragraph(labels["abnormal"], styles["Section"]))
    abn = result.get("abnormal_values_explained", [])
    if abn:
        lines = []
        for row in abn:
            lines.append(
                f"{row.get('test','')}: {row.get('value','')} {row.get('unit','')} "
                f"(Range: {row.get('reference_range','not provided')}, Flag: {row.get('flag','unknown')}) "
                f"→ {row.get('meaning_simple','')}"
            )
        story.append(ListFlowable(
            [ListItem(Paragraph(x, styles["Small"])) for x in lines],
            bulletType="bullet",
            leftIndent=18
        ))
    else:
        story.append(Paragraph("No abnormal lab values found / not provided.", styles["Small"]))
    story.append(Spacer(1, 8))

    add_bullets(labels["next"], result.get("next_steps", []))
    add_bullets(labels["urgent"], result.get("urgent_warning_signs", []))

    story.append(Paragraph(labels["glossary"], styles["Section"]))
    gloss = result.get("glossary", [])
    if gloss:
        lines = [f"{g.get('term','')}: {g.get('meaning_simple','')}" for g in gloss]
        story.append(ListFlowable(
            [ListItem(Paragraph(x, styles["Small"])) for x in lines],
            bulletType="bullet",
            leftIndent=18
        ))
    else:
        story.append(Paragraph("Not provided.", styles["Small"]))

    disclaimer = result.get("disclaimer", "")
    if disclaimer:
        story.append(Spacer(1, 8))
        story.append(Paragraph(labels["disclaimer"], styles["Section"]))
        story.append(Paragraph(disclaimer, styles["Small"]))

    doc.build(
        story,
        onFirstPage=lambda c, d: _pdf_header_footer(c, d, footer_text, FONT, FONT_BOLD),
        onLaterPages=lambda c, d: _pdf_header_footer(c, d, footer_text, FONT, FONT_BOLD),
    )

    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


# =========================
# Sidebar: saved uploads + saved summaries
# =========================
st.sidebar.header("📂 Saved Reports (PDF)")

saved_reports = list_saved_reports()
selected_report: Optional[dict] = None

if saved_reports:
    report_options = [f"{r['saved_at']} — {r['original_name']} (ID: {r['id']})" for r in saved_reports]
    choice = st.sidebar.selectbox("Select saved report", report_options, index=0)
    selected_report = saved_reports[report_options.index(choice)]

    cA, cB = st.sidebar.columns(2)
    with cA:
        if st.button("Load Report"):
            st.session_state["loaded_report"] = selected_report
    with cB:
        try:
            b = load_report_bytes(selected_report["path"])
            st.download_button("Download PDF", data=b, file_name=selected_report["original_name"], mime="application/pdf")
        except Exception as e:
            st.sidebar.error(f"Read error: {e}")
else:
    st.sidebar.caption("No saved PDFs yet.")

st.sidebar.divider()
st.sidebar.header("🧾 Saved Summaries")

saved_summaries = list_saved_summaries()
if saved_summaries:
    sum_opts = [f"{s['saved_at']} — {s.get('upload',{}).get('original_name','(no name)')} (SID: {s['summary_id']})" for s in saved_summaries]
    sum_choice = st.sidebar.selectbox("Select saved summary", sum_opts, index=0)
    sum_sel = saved_summaries[sum_opts.index(sum_choice)]
    if st.sidebar.button("Load Summary"):
        try:
            st.session_state["current_summary"] = load_summary_json(sum_sel["path"])
            st.session_state["qa_chat"] = []  # reset Q&A chat
            st.sidebar.success("Loaded summary into current session.")
        except Exception as e:
            st.sidebar.error(f"Could not load summary: {e}")
else:
    st.sidebar.caption("No saved summaries yet.")


# =========================
# UI — Main
# =========================
st.title("🩺 MediBrief — Medical PDF Summarizer (EN / HI / MR) + Gemini")
st.write("Upload a medical report PDF → get summary + glossary + PDF download + history + Q&A.")


# Patient details
st.subheader("Patient Details (optional for PDF)")
c1, c2, c3, c4 = st.columns(4)
with c1:
    patient_name = st.text_input("Patient Name", value="")
with c2:
    patient_age = st.text_input("Age", value="")
with c3:
    patient_sex = st.selectbox("Sex", ["", "Male", "Female", "Other"], index=0)
with c4:
    report_id = st.text_input("Report ID", value="")

st.divider()

col1, col2 = st.columns([1, 1])
with col1:
    lang = st.selectbox("Choose output language", ["en", "hi", "mr"], index=0)
    uploaded = st.file_uploader("Upload PDF", type=["pdf"])

with col2:
    st.markdown("### OCR Status")
    if TESS_OK:
        st.success("Tesseract detected ✅ OCR will work for scanned PDFs.")
    else:
        st.warning("Tesseract NOT detected ⚠️ OCR may not work for scanned PDFs.")
        st.caption("Install Tesseract or fix path: C:\\Program Files\\Tesseract-OCR\\tesseract.exe")

st.divider()


# Determine pdf_bytes source: uploaded OR loaded from history
pdf_bytes: Optional[bytes] = None
upload_record: Optional[dict] = None
current_filename = ""

loaded_report = st.session_state.get("loaded_report")
if uploaded:
    pdf_bytes = uploaded.read()
    current_filename = uploaded.name
    # Save PDF permanently
    upload_record = save_uploaded_pdf(current_filename, pdf_bytes)
    st.success(f"✅ Report saved: {upload_record['original_name']} (ID: {upload_record['id']})")

elif loaded_report:
    st.info(f"Using saved report: {loaded_report['original_name']} (ID: {loaded_report['id']})")
    pdf_bytes = load_report_bytes(loaded_report["path"])
    current_filename = loaded_report["original_name"]
    upload_record = loaded_report


if pdf_bytes:
    st.header("Step 1 — Extracting text")
    extracted = clean_text(extract_text_pymupdf(pdf_bytes))

    extraction_notes: List[str] = []
    confidence = "high"

    if len(extracted) < 300:
        extraction_notes.append("Selectable text was very low → attempting OCR on first pages.")
        confidence = "medium"

        if not TESS_OK:
            extraction_notes.append("OCR not available (Tesseract not found).")
            confidence = "low"
        else:
            ocr_text = clean_text(ocr_pdf_pages(pdf_bytes, max_pages=3))
            if len(ocr_text) > len(extracted):
                extracted = ocr_text
                extraction_notes.append("OCR text used (first 3 pages).")
            else:
                extraction_notes.append("OCR output was not better than extracted text.")
                confidence = "low"

    st.write(f"**Requested Language:** {lang_name(lang)} ({lang})")
    st.write(f"**Confidence (text quality):** {confidence}")
    if extraction_notes:
        st.write("**Extraction Notes:**")
        for n in extraction_notes:
            st.write(f"- {n}")

    st.text_area("Extracted Text (preview)", extracted[:8000], height=260)

    st.header("Step 2 — Generate summary (Gemini)")

    # Keep current summary in session
    if "current_summary" not in st.session_state:
        st.session_state["current_summary"] = None

    # Generate summary
    if st.button("Generate Summary"):
        with st.spinner("Generating summary using Gemini..."):
            try:
                result = gemini_generate_json(extracted, lang, confidence, extraction_notes)
                st.session_state["current_summary"] = result
                st.session_state["qa_chat"] = []  # reset chat for new summary

                # Save summary to disk (history)
                patient_meta = {
                    "patient_name": patient_name,
                    "patient_age": patient_age,
                    "patient_sex": patient_sex,
                    "report_id": report_id,
                }
                save_summary_record(result, upload_record, patient_meta)

                st.success(f"✅ Summary generated! (Model: {result['meta'].get('model_used','')})")

            except Exception as e:
                st.error(str(e))

    # Display current summary if exists
    cur = st.session_state.get("current_summary")
    if cur:
        st.subheader("✅ Current Summary (from History)")

        # PDF download
        try:
            pdf_out = build_summary_pdf_bytes(
                result=cur,
                patient_name=patient_name,
                patient_age=patient_age,
                patient_sex=patient_sex,
                report_id=report_id,
            )
            st.download_button(
                label="⬇️ Download Summary PDF",
                data=pdf_out,
                file_name=f"medibrief_summary_{cur.get('meta',{}).get('requested_language','en')}.pdf",
                mime="application/pdf",
            )
        except Exception as e:
            st.error(
                "PDF font error for Hindi/Marathi.\n\n"
                "Fix:\n"
                "- Create folder fonts/\n"
                "- Add REAL TTF files:\n"
                "  fonts/NotoSansDevanagari-Regular.ttf (required)\n"
                "  fonts/NotoSansDevanagari-Bold.ttf (optional)\n\n"
                f"Error: {e}"
            )

        st.subheader("Overall Summary")
        for b in cur.get("overall_summary_bullets", []):
            st.write(f"- {b}")

        st.subheader("Key Findings")
        for k in cur.get("key_findings", []):
            st.write(f"- {k}")

        st.caption(cur.get("disclaimer", ""))

        # Step 3 — Q&A (multi-question)
        st.header("Step 3 — Ask questions based on this summary")
        if "qa_chat" not in st.session_state:
            st.session_state["qa_chat"] = []

        question = st.text_input("Ask a question (answers only from this summary JSON)", value="", key="q_input")

        if st.button("Answer Question"):
            if not question.strip():
                st.warning("Type a question first.")
            else:
                with st.spinner("Answering using Gemini..."):
                    try:
                        ans = gemini_answer_question(cur, question.strip())
                        st.session_state["qa_chat"].append({"q": question.strip(), "a": ans})
                        st.session_state["q_input"] = ""  # clear box
                    except Exception as e:
                        st.error(str(e))

        # Show chat history
        if st.session_state["qa_chat"]:
            for i, turn in enumerate(st.session_state["qa_chat"], start=1):
                st.markdown(f"**Q{i}:** {turn['q']}")
                st.markdown(f"**A{i}:** {turn['a']}")
                st.divider()

        with st.expander("Raw JSON Output"):
            st.json(cur)

else:
    st.caption("Upload a PDF or load one from sidebar to start.")

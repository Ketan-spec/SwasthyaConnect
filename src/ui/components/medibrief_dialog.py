import os
import json
import shutil
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, 
    QTextEdit, QLineEdit, QTabWidget, QWidget, QMessageBox, QScrollArea, QFrame, QFormLayout
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

from src.services.ocr_service import process_pdf_for_text
from src.services.medibrief_service import MedibriefService
from src.services.medibrief_pdf import build_summary_pdf_bytes
from src.database import add_medical_record, add_past_appointment, add_prescription_entry

class AIWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress_update = pyqtSignal(str)
    
    def __init__(self, pdf_path, lang, api_key):
        super().__init__()
        self.pdf_path = pdf_path
        self.lang = lang
        self.api_key = api_key
        
    def run(self):
        try:
            self.progress_update.emit("Extracting text and performing OCR...")
            extracted, extraction_notes, confidence = process_pdf_for_text(self.pdf_path)
            
            if not extracted:
                self.error.emit("Could not extract any text from the PDF.")
                return
                
            self.progress_update.emit("Generating structured medical summary via Smart Analyzer...")
            summary_json = MedibriefService.generate_json_summary(
                report_text=extracted,
                requested_language=self.lang,
                confidence=confidence,
                extraction_notes=extraction_notes,
                model_name=self.api_key
            )
            
            self.finished.emit(summary_json)
        except Exception as e:
            self.error.emit(str(e))

class QnAWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    
    def __init__(self, summary_json, question, api_key):
        super().__init__()
        self.summary_json = summary_json
        self.question = question
        self.api_key = api_key
        
    def run(self):
        try:
            answer = MedibriefService.answer_question(self.summary_json, self.question, self.api_key)
            self.finished.emit(answer)
        except Exception as e:
            self.error.emit(str(e))

class MedibriefAnalyzerDialog(QDialog):
    def __init__(self, parent_widget, pdf_path, patient_id, record_type="Report"):
        super().__init__(parent_widget)
        self.pdf_path = pdf_path
        self.patient_id = patient_id
        self.record_type = record_type
        self.summary_json = None
        self.api_key = "qwen2:0.5b"
        self._saved = False   # tracks whether record has already been saved to DB
        
        self.setWindowTitle(f"Smart Report Analyzer - {os.path.basename(pdf_path)}")
        self.resize(800, 600)
        
        main_layout = QVBoxLayout(self)
        
        # --- Settings Header ---
        header_frame = QFrame()
        header_frame.setStyleSheet("QFrame { background: white; border-bottom: 2px solid #e2e8f0; }")
        header_layout = QHBoxLayout(header_frame)
        
        header_layout.addWidget(QLabel("Output Language:"))
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["English (en)", "Hindi (hi)", "Marathi (mr)"])
        header_layout.addWidget(self.lang_combo)
        
        # Removed Model Combo Box
        
        self.analyze_btn = QPushButton("Analyze Report")
        self.analyze_btn.setStyleSheet("background-color: #0f766e; color: white; padding: 5px 15px; border-radius: 4px; font-weight: bold;")
        self.analyze_btn.clicked.connect(self.start_analysis)
        header_layout.addWidget(self.analyze_btn)
        
        main_layout.addWidget(header_frame)
        
        # --- Status Label ---
        self.status_label = QLabel("Upload ready. Click 'Analyze Report' to begin.")
        self.status_label.setStyleSheet("color: #475569; font-style: italic;")
        main_layout.addWidget(self.status_label)
        
        # --- Tabs ---
        self.tabs = QTabWidget()
        
        # We will populate these tabs after the AI returns
        self.tab_summary = QWidget()
        self.tab_findings = QWidget()
        self.tab_abnormal = QWidget()
        self.tab_glossary = QWidget()
        self.tab_qa = QWidget()
        
        self.tabs.addTab(self.tab_summary, "Overall Summary")
        self.tabs.addTab(self.tab_findings, "Key Findings")
        self.tabs.addTab(self.tab_abnormal, "Abnormal Values")
        self.tabs.addTab(self.tab_glossary, "Glossary")
        self.tabs.addTab(self.tab_qa, "Ask Questions")
        
        main_layout.addWidget(self.tabs)
        
        # Setup specific layouts for tabs to hold the text
        self._setup_tab(self.tab_summary)
        self._setup_tab(self.tab_findings)
        self._setup_tab(self.tab_abnormal)
        self._setup_tab(self.tab_glossary)
        self._setup_qa_tab()
        
        # --- Footer Actions ---
        footer_layout = QHBoxLayout()
        self.export_pdf_btn = QPushButton("Export to PDF")
        self.export_pdf_btn.setEnabled(False)
        self.export_pdf_btn.clicked.connect(self.export_pdf)
        
        self.save_record_btn = QPushButton("Save to My Records")
        self.save_record_btn.setStyleSheet("background-color: #2563eb; color: white; padding: 8px 15px; border-radius: 4px; font-weight: bold;")
        self.save_record_btn.setEnabled(False)
        self.save_record_btn.clicked.connect(self.save_to_db)
        
        footer_layout.addWidget(self.export_pdf_btn)
        footer_layout.addStretch()
        footer_layout.addWidget(self.save_record_btn)
        main_layout.addLayout(footer_layout)

    def _setup_tab(self, tab: QWidget):
        layout = QVBoxLayout(tab)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("font-size: 14px;")
        layout.addWidget(text_edit)
        # Store as attribute dynamically based on object name later or just assign directly
        setattr(self, f"ui_{id(tab)}", text_edit)

    def _setup_qa_tab(self):
        layout = QVBoxLayout(self.tab_qa)
        
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("font-size: 14px; background-color: #f8fafc;")
        layout.addWidget(self.chat_history)
        
        input_layout = QHBoxLayout()
        self.question_input = QLineEdit()
        self.question_input.setPlaceholderText("Ask a question about this report...")
        self.ask_btn = QPushButton("Ask")
        self.ask_btn.setStyleSheet("background-color: #0f766e; color: white; padding: 5px;")
        self.ask_btn.clicked.connect(self.ask_question)
        self.ask_btn.setEnabled(False)
        
        input_layout.addWidget(self.question_input)
        input_layout.addWidget(self.ask_btn)
        layout.addLayout(input_layout)

    def start_analysis(self):
        lang_code = self.lang_combo.currentText().split("(")[-1].strip(")")
        selected_model = self.api_key
        
        self.analyze_btn.setEnabled(False)
        self.tabs.setEnabled(False)
        
        self.worker = AIWorker(self.pdf_path, lang_code, selected_model)
        self.worker.progress_update.connect(self.update_status)
        self.worker.finished.connect(self.analysis_complete)
        self.worker.error.connect(self.analysis_error)
        self.worker.start()

    def update_status(self, msg: str):
        self.status_label.setText(f"⏳ {msg}")

    def analysis_complete(self, result: dict):
        self.summary_json = result
        self.status_label.setText("✅ Analysis complete.")
        self.analyze_btn.setEnabled(True)
        self.tabs.setEnabled(True)
        self.export_pdf_btn.setEnabled(True)
        self.save_record_btn.setEnabled(True)
        self.ask_btn.setEnabled(True)
        
        # ── Tab 1: Overall Summary ─────────────────────────────────────────────
        summary_block = result.get("summary", {})
        overview = summary_block.get("patient_overview", "")
        
        summary_lines = []
        if overview:
            summary_lines.append(f"📋 Patient Overview:\n{overview}\n")
        
        bullets = result.get("overall_summary_bullets", [])
        if bullets:
            summary_lines.append("📌 Key Highlights:")
            summary_lines.extend([f"  • {b}" for b in bullets])
            summary_lines.append("")
        
        # Vitals block
        vitals = result.get("vitals", {})
        vital_rows = [
            ("Blood Pressure", vitals.get("blood_pressure")),
            ("Heart Rate",     vitals.get("heart_rate")),
            ("Temperature",    vitals.get("temperature")),
            ("SpO2",           vitals.get("spO2")),
            ("Weight",         vitals.get("weight")),
            ("BMI",            vitals.get("bmi")),
        ]
        present_vitals = [(k, v) for k, v in vital_rows if v and str(v).lower() not in ("null", "none", "")]
        if present_vitals:
            summary_lines.append("🩺 Extracted Vitals:")
            for k, v in present_vitals:
                summary_lines.append(f"  • {k}: {v}")
            summary_lines.append("")
        
        # Medications
        meds = result.get("medications", [])
        real_meds = [m for m in meds if m.get("name") and str(m.get("name")).lower() not in ("null", "none", "")]
        if real_meds:
            summary_lines.append("💊 Medications:")
            for m in real_meds:
                med_str = f"  • {m['name']}"
                if m.get("dosage"):   med_str += f" — {m['dosage']}"
                if m.get("frequency"): med_str += f"  |  {m['frequency']}"
                if m.get("duration"): med_str += f"  |  {m['duration']}"
                summary_lines.append(med_str)
            summary_lines.append("")
        
        # Next Steps
        next_steps = result.get("next_steps", [])
        if next_steps:
            summary_lines.append("🗓️ Recommended Next Steps:")
            summary_lines.extend([f"  • {s}" for s in next_steps])
            summary_lines.append("")
        
        # Disclaimer
        disclaimers = result.get("disclaimer", [])
        if disclaimers:
            summary_lines.append("⚠️ " + " ".join(disclaimers))
        
        self._populate_text(self.tab_summary, "\n".join(summary_lines) if summary_lines else "No summary data extracted.")
        
        # ── Tab 2: Key Findings ────────────────────────────────────────────────
        findings = result.get("key_findings") or summary_block.get("key_findings", [])
        diagnosis = result.get("diagnosis", [])
        impression = result.get("impression_in_simple_words", [])
        symptoms = result.get("symptoms", [])
        
        findings_lines = []
        if findings:
            findings_lines.append("🔬 Key Findings:")
            findings_lines.extend([f"  • {f}" for f in findings])
            findings_lines.append("")
        if diagnosis:
            findings_lines.append("🏷️ Diagnosis / Impression:")
            findings_lines.extend([f"  • {d}" for d in diagnosis])
            findings_lines.append("")
        if impression:
            findings_lines.append("🗣️ In Simple Words:")
            findings_lines.extend([f"  • {i}" for i in impression])
            findings_lines.append("")
        if symptoms:
            findings_lines.append("🤒 Reported Symptoms:")
            findings_lines.extend([f"  • {s}" for s in symptoms])
            
        self._populate_text(self.tab_findings, "\n".join(findings_lines) if findings_lines else "No findings extracted from this report.")
        
        # ── Tab 3: Abnormal Values ─────────────────────────────────────────────
        abn_list = result.get("abnormal_values") or result.get("abnormal_values_explained", [])
        urgent = result.get("urgent_warning_signs", [])
        
        abn_text = ""
        if abn_list:
            abn_text += "🔴 Abnormal Values (Strict extraction only — no AI guessing):\n\n"
            for a in abn_list:
                if isinstance(a, dict):
                    test = a.get("test", "—")
                    val  = a.get("value", "—")
                    unit = a.get("unit", "")
                    ref  = a.get("reference_range", "—")
                    flag = a.get("flag", "—")
                    meaning = a.get("meaning_simple", "")
                    abn_text += f"  🔴 {test}: {val} {unit}  (Range: {ref} | {flag})\n"
                    if meaning:
                        abn_text += f"      → {meaning}\n"
                    abn_text += "\n"
                else:
                    abn_text += f"  🔴 {a}\n\n"
        else:
            abn_text += "✅ No abnormal values detected from this report.\n\n"
        
        if urgent:
            abn_text += "🚨 Urgent Warning Signs:\n"
            abn_text += "\n".join([f"  ⚠️ {u}" for u in urgent])
        
        self._populate_text(self.tab_abnormal, abn_text.strip() if abn_text else "No abnormal data found.")
        
        # ── Tab 4: Glossary ────────────────────────────────────────────────────
        glo = result.get("glossary") or [
            {"term": t, "meaning_simple": ""} if isinstance(t, str) else t
            for t in result.get("medical_terms", [])
        ]
        glo_text = ""
        for g in glo:
            if isinstance(g, dict):
                term = g.get("term", "")
                meaning = g.get("meaning_simple", "")
                if term:
                    glo_text += f"📖 {term}"
                    if meaning:
                        glo_text += f":\n   {meaning}"
                    glo_text += "\n\n"
            elif isinstance(g, str) and g:
                glo_text += f"📖 {g}\n\n"
        if not glo_text:
            glo_text = "No complex medical terms identified in this report."
        self._populate_text(self.tab_glossary, glo_text.strip())


    def analysis_error(self, err: str):
        self.status_label.setText("❌ Error during analysis.")
        QMessageBox.critical(self, "AI Error", f"An error occurred: {err}")
        self.analyze_btn.setEnabled(True)

    def _format_list(self, arr: list) -> str:
        if not arr: return "Not provided."
        return "\n\n".join([f"• {x}" for x in arr])

    def _populate_text(self, tab: QWidget, text: str):
        getattr(self, f"ui_{id(tab)}").setPlainText(text)

    def ask_question(self):
        q = self.question_input.text().strip()
        if not q or not self.summary_json: return
        
        self.chat_history.append(f"<b>You:</b> {q}")
        self.question_input.clear()
        
        selected_model = self.api_key
        self.ask_btn.setEnabled(False)
        self.qa_worker = QnAWorker(self.summary_json, q, selected_model)
        self.qa_worker.finished.connect(self.qa_complete)
        self.qa_worker.error.connect(self.qa_error)
        self.qa_worker.start()

    def qa_complete(self, answer: str):
        self.chat_history.append(f"<b style='color:#0f766e;'>MediBrief:</b> {answer}<br>")
        self.ask_btn.setEnabled(True)

    def qa_error(self, err: str):
        self.chat_history.append(f"<b style='color:red;'>Error:</b> {err}<br>")
        self.ask_btn.setEnabled(True)

    def export_pdf(self):
        try:
            # Generate the bytes using Medibrief PDF exporter
            project_root = str(Path(__file__).parent.parent.parent.parent)
            pdf_bytes = build_summary_pdf_bytes(
                self.summary_json,
                patient_name="Patient ID " + str(self.patient_id),
                patient_age="Unknown",
                patient_sex="Unknown",
                report_id="Generated via Swasthya Medibrief",
                project_root=project_root
            )
            
            # Request user where to save it
            from PyQt6.QtWidgets import QFileDialog
            save_path, _ = QFileDialog.getSaveFileName(self, "Save Summary PDF", "", "PDF Files (*.pdf)")
            if save_path:
                with open(save_path, "wb") as f:
                    f.write(pdf_bytes)
                QMessageBox.information(self, "Export Successful", f"Summary saved to {save_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def save_to_db(self, silent=False):
        """Saves the analysis result to the database.
        silent=True means no popup messages (used for auto-save on close).
        Returns True on success, False on failure.
        """
        if self._saved:
            return True  # Already saved, skip
        if not self.summary_json:
            return False
        try:
            # 1. Copy the uploaded file permanently into our data folder
            file_name = os.path.basename(self.pdf_path)
            dest_dir = os.path.join(str(Path(__file__).parent.parent.parent.parent), "data", "uploads")
            os.makedirs(dest_dir, exist_ok=True)
            new_path = os.path.join(dest_dir, file_name)
            if self.pdf_path != new_path:
                shutil.copy2(self.pdf_path, new_path)
                
            # 2. Build title from new schema
            default_title = "Prescription Summary" if self.record_type == "Prescription" else "Report Summary"
            impression = self.summary_json.get("impression_in_simple_words", [])
            diagnosis = self.summary_json.get("diagnosis", [])
            title_candidates = impression + diagnosis
            title = title_candidates[0][:50] if title_candidates else default_title
            
            description = f"AI Extracted {self.record_type}"
            json_str = json.dumps(self.summary_json)
            lang = self.summary_json.get("meta", {}).get("requested_language", "en")
            
            success = add_medical_record(
                patient_id=self.patient_id,
                record_type=self.record_type,
                title=title,
                description=description,
                file_path=new_path,
                summary_json=json_str,
                language=lang
            )
            
            if not success:
                if not silent:
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.warning(self, "Database Error", "Failed to save record.")
                return False
            
            # 3. Extract past appointment date from report_date field
            report_date = self.summary_json.get("report_date")
            if report_date and str(report_date).lower() not in ("null", "none", ""):
                add_past_appointment(self.patient_id, str(report_date))
            
            # 4. If it's a Prescription → save each medicine to prescriptions table
            if self.record_type == "Prescription":
                medications = self.summary_json.get("medications", [])
                for med in medications:
                    if isinstance(med, dict) and med.get("name") and str(med.get("name")).lower() not in ("null", "none", ""):
                        add_prescription_entry(
                            patient_id=self.patient_id,
                            medicine_name=med.get("name"),
                            dosage=med.get("dosage"),
                            frequency=med.get("frequency"),
                            duration=med.get("duration"),
                        )
            
            self._saved = True
            if not silent:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.information(self, "Success", "Report and AI Summary saved to your records!")
                self.accept()
            return True
        except Exception as e:
            if not silent:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Save Error", str(e))
            else:
                print(f"Auto-save error: {e}")
            return False

    def closeEvent(self, event):
        """Auto-save silently when dialog is closed after analysis."""
        if self.summary_json and not self._saved:
            self.save_to_db(silent=True)
        event.accept()



class MedibriefViewerDialog(QDialog):
    def __init__(self, parent_widget, summary_json, title="AI Generated Medical Report"):
        super().__init__(parent_widget)
        self.summary_json = summary_json
        self.api_key = "qwen2:0.5b"
        
        self.setWindowTitle(title)
        self.resize(800, 600)
        
        main_layout = QVBoxLayout(self)
        
        # --- Settings Header (Read only here except for QA Key) ---
        header_frame = QFrame()
        header_frame.setStyleSheet("QFrame { background: white; border-bottom: 2px solid #e2e8f0; }")
        header_layout = QHBoxLayout(header_frame)
        
        # Removed Model combo
        
        main_layout.addWidget(header_frame)
        
        # --- Tabs ---
        self.tabs = QTabWidget()
        
        self.tab_summary = QWidget()
        self.tab_findings = QWidget()
        self.tab_abnormal = QWidget()
        self.tab_glossary = QWidget()
        self.tab_qa = QWidget()
        
        self.tabs.addTab(self.tab_summary, "Overall Summary")
        self.tabs.addTab(self.tab_findings, "Key Findings")
        self.tabs.addTab(self.tab_abnormal, "Abnormal Values")
        self.tabs.addTab(self.tab_glossary, "Glossary")
        self.tabs.addTab(self.tab_qa, "Ask Questions")
        
        main_layout.addWidget(self.tabs)
        
        self._setup_tab(self.tab_summary)
        self._setup_tab(self.tab_findings)
        self._setup_tab(self.tab_abnormal)
        self._setup_tab(self.tab_glossary)
        self._setup_qa_tab()
        
        # --- Footer Actions ---
        footer_layout = QHBoxLayout()
        self.export_pdf_btn = QPushButton("Export to PDF")
        self.export_pdf_btn.clicked.connect(self.export_pdf)
        footer_layout.addWidget(self.export_pdf_btn)
        footer_layout.addStretch()
        
        close_btn = QPushButton("Close Viewer")
        close_btn.setStyleSheet("background-color: #475569; color: white; padding: 8px 15px; border-radius: 4px; font-weight: bold;")
        close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn)
        main_layout.addLayout(footer_layout)
        
        self.populate_data()

    def _setup_tab(self, tab: QWidget):
        layout = QVBoxLayout(tab)
        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setStyleSheet("font-size: 14px;")
        layout.addWidget(text_edit)
        setattr(self, f"ui_{id(tab)}", text_edit)

    def _setup_qa_tab(self):
        layout = QVBoxLayout(self.tab_qa)
        
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setStyleSheet("font-size: 14px; background-color: #f8fafc;")
        layout.addWidget(self.chat_history)
        
        input_layout = QHBoxLayout()
        self.question_input = QLineEdit()
        self.question_input.setPlaceholderText("Ask a question about this report...")
        self.ask_btn = QPushButton("Ask")
        self.ask_btn.setStyleSheet("background-color: #0f766e; color: white; padding: 5px;")
        self.ask_btn.clicked.connect(self.ask_question)
        
        input_layout.addWidget(self.question_input)
        input_layout.addWidget(self.ask_btn)
        layout.addLayout(input_layout)

    def populate_data(self):
        result = self.summary_json
        
        self._populate_text(self.tab_summary, self._format_list(result.get("overall_summary_bullets", [])))
        self._populate_text(self.tab_findings, self._format_list(result.get("key_findings", [])))
        
        abn = result.get("abnormal_values_explained", [])
        abn_text = ""
        for a in abn:
            if isinstance(a, dict):
                abn_text += f"🔴 {a.get('test')}: {a.get('value')} {a.get('unit')} (Range: {a.get('reference_range')} | Flag: {a.get('flag')})\n"
                abn_text += f"   Meaning: {a.get('meaning_simple')}\n\n"
            else:
                abn_text += f"🔴 {a}\n\n"
        if not abn: abn_text = "No abnormal values detected."
        self._populate_text(self.tab_abnormal, abn_text)
        
        glo = result.get("glossary", [])
        glo_text = ""
        for g in glo:
            if isinstance(g, dict):
                glo_text += f"📖 {g.get('term')}:\n   {g.get('meaning_simple')}\n\n"
            else:
                glo_text += f"📖 {g}\n\n"
        if not glo: glo_text = "No complex terms identified."
        self._populate_text(self.tab_glossary, glo_text)

    def _format_list(self, arr: list) -> str:
        if not arr: return "Not provided."
        return "\n\n".join([f"• {x}" for x in arr])

    def _populate_text(self, tab: QWidget, text: str):
        getattr(self, f"ui_{id(tab)}").setPlainText(text)

    def ask_question(self):
        q = self.question_input.text().strip()
        if not q: return
        
        self.chat_history.append(f"<b>Doctor:</b> {q}")
        self.question_input.clear()
        
        selected_model = self.api_key
        self.ask_btn.setEnabled(False)
        self.qa_worker = QnAWorker(self.summary_json, q, selected_model)
        self.qa_worker.finished.connect(self.qa_complete)
        self.qa_worker.error.connect(self.qa_error)
        self.qa_worker.start()

    def qa_complete(self, answer: str):
        self.chat_history.append(f"<b style='color:#0f766e;'>MediBrief:</b> {answer}<br>")
        self.ask_btn.setEnabled(True)

    def qa_error(self, err: str):
        self.chat_history.append(f"<b style='color:red;'>Error:</b> {err}<br>")
        self.ask_btn.setEnabled(True)

    def export_pdf(self):
        try:
            project_root = str(Path(__file__).parent.parent.parent.parent)
            pdf_bytes = build_summary_pdf_bytes(
                self.summary_json,
                patient_name="Redacted for Doctor View",
                patient_age="Unknown",
                patient_sex="Unknown",
                report_id="Doctor View Export",
                project_root=project_root
            )
            
            from PyQt6.QtWidgets import QFileDialog
            save_path, _ = QFileDialog.getSaveFileName(self, "Save Summary PDF", "", "PDF Files (*.pdf)")
            if save_path:
                with open(save_path, "wb") as f:
                    f.write(pdf_bytes)
                QMessageBox.information(self, "Export Successful", f"Summary saved to {save_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

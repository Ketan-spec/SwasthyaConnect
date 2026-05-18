from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QLineEdit, QMessageBox, QScrollArea, QFrame, QFileDialog
)
from PyQt6.QtCore import Qt
from src.database import DB_NAME, get_treatment_updates, get_patient_prescriptions, get_patient_all_medicine_names
import sqlite3
import json
from src.ui.components.medibrief_dialog import MedibriefAnalyzerDialog
from src.services.medicine_service import MedicineService
from src.ui.components.chatbot import AIAssistantWorker
from PyQt6.QtWidgets import QTextEdit

class RecordsWidget(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("My Medical Records")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0f766e;")
        header_layout.addWidget(title)
        
        upload_btn = QPushButton("Upload Medical Report (Smart Analyzer)")
        upload_btn.setStyleSheet("background-color: #0f766e; color: white; padding: 8px 15px; border-radius: 5px; font-weight: bold;")
        upload_btn.clicked.connect(self.upload_pdf)
        header_layout.addWidget(upload_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout.addLayout(header_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Date", "Title", "Description"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.load_data()
        
    def upload_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Medical Report", "", "PDF/Image Files (*.pdf *.png *.jpg *.jpeg)")
        if file_path:
            dialog = MedibriefAnalyzerDialog(self, file_path, self.user_id)
            dialog.exec()
            # Always reload — auto-save fires on close even without clicking Save
            self.load_data()

    def load_data(self):
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10.0)
            c = conn.cursor()
            c.execute("SELECT date_added, title, description FROM medical_records WHERE patient_id = ? AND record_type = 'Report' ORDER BY date_added DESC", (self.user_id,))
            rows = c.fetchall()
            conn.close()
            
            self.table.setRowCount(len(rows))
            for r, row in enumerate(rows):
                for c, val in enumerate(row):
                    # date_added usually contains datetime, split to extract date
                    if c == 0 and val: val = val.split(" ")[0]
                    self.table.setItem(r, c, QTableWidgetItem(str(val)))
        except Exception as e:
            pass

class AppointmentsWidget(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        layout = QVBoxLayout(self)
        
        title = QLabel("My Appointments")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0f766e;")
        layout.addWidget(title)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Date", "Time", "Doctor", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.load_data()

    def load_data(self):
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10.0)
            c = conn.cursor()
            c.execute('''
                SELECT a.date, a.time, COALESCE(u.full_name, 'From Medical Report'), a.status 
                FROM appointments a 
                LEFT JOIN users u ON a.doctor_id = u.id AND a.doctor_id != 0
                WHERE a.patient_id = ? 
                ORDER BY a.date DESC
            ''', (self.user_id,))
            rows = c.fetchall()
            conn.close()
            
            self.table.setRowCount(len(rows))
            for r, row in enumerate(rows):
                for c, val in enumerate(row):
                    item = QTableWidgetItem(str(val))
                    if c == 3: # Status column
                        status = str(val).lower()
                        if status == 'pending':
                            item.setForeground(Qt.GlobalColor.darkYellow)
                        elif status in ('accepted', 'scheduled'):
                            item.setForeground(Qt.GlobalColor.darkGreen)
                        elif status in ('completed',):
                            item.setForeground(Qt.GlobalColor.darkCyan)
                        elif status in ('rejected', 'cancelled'):
                            item.setForeground(Qt.GlobalColor.darkRed)
                    self.table.setItem(r, c, item)
        except Exception as e:
            print(f"Error loading appointments: {e}")

class PrescriptionsWidget(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("My Prescriptions")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0f766e;")
        header_layout.addWidget(title)
        
        upload_btn = QPushButton("Upload Prescription (Smart Analyzer)")
        upload_btn.setStyleSheet("background-color: #0f766e; color: white; padding: 8px 15px; border-radius: 5px; font-weight: bold;")
        upload_btn.clicked.connect(self.upload_pdf)
        header_layout.addWidget(upload_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout.addLayout(header_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Date", "Medicine", "Dosage Instructions"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.load_data()

    def load_data(self):
        try:
            rows = get_patient_prescriptions(self.user_id)
            self.table.setColumnCount(5)
            self.table.setHorizontalHeaderLabels(["Date", "Medicine", "Dosage", "Frequency", "Duration"])
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            self.table.setRowCount(len(rows))
            for r, row in enumerate(rows):
                date_val = row.get("date_added", "").split(" ")[0]
                self.table.setItem(r, 0, QTableWidgetItem(date_val))
                self.table.setItem(r, 1, QTableWidgetItem(str(row.get("medicine_name", ""))))
                self.table.setItem(r, 2, QTableWidgetItem(str(row.get("dosage") or "—")))
                self.table.setItem(r, 3, QTableWidgetItem(str(row.get("frequency") or "—")))
                self.table.setItem(r, 4, QTableWidgetItem(str(row.get("duration") or "—")))
        except Exception as e:
            print(f"Error loading prescriptions: {e}")

    def upload_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Prescription", "", "PDF/Image Files (*.pdf *.png *.jpg *.jpeg)")
        if file_path:
            dialog = MedibriefAnalyzerDialog(self, file_path, self.user_id, record_type="Prescription")
            dialog.exec()
            self.load_data()  # Always reload after close

class SettingsWidget(QWidget):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        container = QWidget()
        layout = QVBoxLayout(container)
        
        title = QLabel("Profile Settings")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0f766e;")
        layout.addWidget(title)
        
        form_frame = QFrame()
        form_frame.setStyleSheet("QFrame { background: white; border-radius: 10px; border: 1px solid #e2e8f0; }")
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(15)
        
        # Full Name
        form_layout.addWidget(QLabel("Full Name"))
        self.name_input = QLineEdit(self.user_data.get('full_name', ''))
        self.name_input.setStyleSheet("padding: 8px; border: 1px solid #cbd5e1; border-radius: 4px;")
        form_layout.addWidget(self.name_input)
        
        # Phone
        form_layout.addWidget(QLabel("Phone Number"))
        self.phone_input = QLineEdit(self.user_data.get('phone', ''))
        self.phone_input.setStyleSheet("padding: 8px; border: 1px solid #cbd5e1; border-radius: 4px;")
        form_layout.addWidget(self.phone_input)
        
        # Email
        form_layout.addWidget(QLabel("Email Address"))
        self.email_input = QLineEdit(self.user_data.get('email', ''))
        self.email_input.setStyleSheet("padding: 8px; border: 1px solid #cbd5e1; border-radius: 4px;")
        form_layout.addWidget(self.email_input)
        
        save_btn = QPushButton("Save Changes")
        save_btn.setStyleSheet("background-color: #0f766e; color: white; padding: 10px; border-radius: 5px; font-weight: bold;")
        save_btn.clicked.connect(self.save_settings)
        form_layout.addWidget(save_btn)
        
        layout.addWidget(form_frame)
        layout.addStretch()
        
        scroll.setWidget(container)
        
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)

    def save_settings(self):
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10.0)
            c = conn.cursor()
            c.execute("UPDATE users SET full_name=?, phone=?, email=? WHERE id=?", 
                      (self.name_input.text(), self.phone_input.text(), self.email_input.text(), self.user_data['id']))
            conn.commit()
            conn.close()
            
            # Update local state
            self.user_data['full_name'] = self.name_input.text()
            self.user_data['phone'] = self.phone_input.text()
            self.user_data['email'] = self.email_input.text()
            
            QMessageBox.information(self, "Success", "Profile settings updated successfully!")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not update settings: {str(e)}")

class TreatmentStatusWidget(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        layout = QVBoxLayout(self)
        
        title = QLabel("My Treatment Tracking")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0f766e;")
        layout.addWidget(title)
        
        self.current_status_label = QLabel("Current Status: None")
        self.current_status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e293b; background-color: #f1f5f9; padding: 10px; border-radius: 5px;")
        layout.addWidget(self.current_status_label)
        
        history_title = QLabel("Treatment History")
        history_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #475569; margin-top: 10px;")
        layout.addWidget(history_title)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Date/Time", "Status", "Notes", "Updated By", "Role"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.load_data()

    def load_data(self):
        try:
            updates = get_treatment_updates(self.user_id)
            if updates:
                latest = updates[0]
                self.current_status_label.setText(f"Current Status: {latest['status']} (Updated by {latest['updated_by_name']}, {latest['updated_by_role']})\nNotes: {latest['notes']}")
                if latest['status'].lower() in ['completed', 'discharged']:
                    self.current_status_label.setStyleSheet(self.current_status_label.styleSheet() + "border-left: 5px solid #10b981;")
                else:
                    self.current_status_label.setStyleSheet(self.current_status_label.styleSheet() + "border-left: 5px solid #3b82f6;")
            else:
                self.current_status_label.setText("No active or historical treatments found.")
                
            self.table.setRowCount(len(updates))
            for r, row in enumerate(updates):
                self.table.setItem(r, 0, QTableWidgetItem(str(row['timestamp'])))
                self.table.setItem(r, 1, QTableWidgetItem(str(row['status'])))
                self.table.setItem(r, 2, QTableWidgetItem(str(row['notes'])))
                self.table.setItem(r, 3, QTableWidgetItem(str(row['updated_by_name'])))
                self.table.setItem(r, 4, QTableWidgetItem(str(row['updated_by_role'])))
        except Exception as e:
            pass


class MedicineVerificationWidget(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        layout = QVBoxLayout(self)
        
        title = QLabel("Medicine Search & AI Verification System")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0f766e;")
        layout.addWidget(title)
        
        desc = QLabel("Search the national medicine database. Use AI to easily understand medicine usage, side effects, and verify against your prescriptions.")
        desc.setWordWrap(True)
        layout.addWidget(desc)
        
        form_layout = QHBoxLayout()
        self.med_input = QLineEdit()
        self.med_input.setPlaceholderText("Enter Medicine Name (e.g. Paracetamol)")
        self.med_input.returnPressed.connect(self.search_medicine)
        
        search_btn = QPushButton("Search Database")
        search_btn.setStyleSheet("background-color: #0f766e; color: white; padding: 8px 15px; border-radius: 5px; font-weight: bold;")
        search_btn.clicked.connect(self.search_medicine)
        
        form_layout.addWidget(self.med_input)
        form_layout.addWidget(search_btn)
        layout.addLayout(form_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Name", "Manufacturer", "Composition", "Price"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.itemDoubleClicked.connect(self.on_medicine_selected)
        layout.addWidget(self.table)
        
        bottom_layout = QHBoxLayout()
        
        explain_layout = QVBoxLayout()
        self.explain_lbl = QLabel("AI Medicine Explanation (Double-click a row to explain):")
        self.explain_lbl.setStyleSheet("font-weight: bold;")
        self.explain_box = QTextEdit()
        self.explain_box.setReadOnly(True)
        self.explain_box.setStyleSheet("background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 5px;")
        explain_layout.addWidget(self.explain_lbl)
        explain_layout.addWidget(self.explain_box)
        bottom_layout.addLayout(explain_layout)
        
        layout.addLayout(bottom_layout)
        
        self.result_lbl = QLabel("")
        self.result_lbl.setStyleSheet("font-size: 16px; font-weight: bold; margin-top: 10px;")
        layout.addWidget(self.result_lbl)
        
        self.current_results = []

    def search_medicine(self):
        query = self.med_input.text().strip()
        if not query: return
        
        self.result_lbl.setText("Searching dataset...")
        self.table.setRowCount(0)
        self.explain_box.clear()

        # Offline CSV Search
        self.current_results = MedicineService.search_medicine_by_name(query, max_results=15)
        
        if not self.current_results:
            self.result_lbl.setText("❌ No medicines found in the national database matching your query.")
            self.result_lbl.setStyleSheet("color: red; font-size: 14px; font-weight: bold;")
            return
            
        self.result_lbl.setText(f"Found {len(self.current_results)} matching result(s). Double-click a medicine for details and AI explanation.")
        self.result_lbl.setStyleSheet("color: black; font-size: 14px;")
            
        self.table.setRowCount(len(self.current_results))
        for r, row in enumerate(self.current_results):
            self.table.setItem(r, 0, QTableWidgetItem(str(row.get("name", ""))))
            self.table.setItem(r, 1, QTableWidgetItem(str(row.get("manufacturer_name", ""))))
            self.table.setItem(r, 2, QTableWidgetItem(str(row.get("salt_composition", ""))))
            price = row.get("price", "N/A")
            self.table.setItem(r, 3, QTableWidgetItem(f"₹ {price}"))

        self.verify_against_records(query)

    def on_medicine_selected(self, item):
        row = item.row()
        med_data = self.current_results[row]
        
        name = med_data.get("name", "")
        composition = med_data.get("salt_composition", "")
        description = med_data.get("medicine_desc", "")
        side_effects = med_data.get("side_effects", "")
        
        self.explain_box.clear()
        self.explain_box.append("<i>Generating easy-to-understand explanation via AI...</i>")
        
        system_prompt = "You are a helpful and knowledgeable medical AI assistant. Your task is to explain medicine details in a simple, easy-to-understand language. Do not invent details; use the ones provided. Keep it concise, format with bullet points."
        question = (f"Please explain this medicine to me as a patient.\n"
                    f"Name: {name}\n"
                    f"Composition: {composition}\n"
                    f"Description/Uses: {description}\n"
                    f"Side Effects to watch out for: {side_effects}\n"
                    f"Also explain how I should generally take it given its description, and what the side effects mean in simple language.")
        
        # Start AI Streaming
        self.first_chunk = True
        self.current_response_text = ""
        self.worker = AIAssistantWorker(system_prompt, question, "qwen2:0.5b")
        self.worker.chunk_received.connect(self.on_ai_chunk)
        self.worker.finished_stream.connect(self.on_ai_finished)
        self.worker.start()

    def on_ai_chunk(self, chunk):
        if self.first_chunk:
            html = self.explain_box.toHtml()
            html = html.replace("<i>Generating easy-to-understand explanation via AI...</i>", "")
            self.explain_box.setHtml(html)
            self.first_chunk = False
            
        self.current_response_text += chunk
        self.explain_box.moveCursor(self.explain_box.textCursor().MoveOperation.End)
        self.explain_box.insertPlainText(chunk)
        
        scrollbar = self.explain_box.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def on_ai_finished(self):
        pass

    def verify_against_records(self, query):
        med_name = query.lower()
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10.0)
            c = conn.cursor()
            
            # Check new prescriptions table first (most reliable)
            c.execute("SELECT medicine_name FROM prescriptions WHERE patient_id = ?", (self.user_id,))
            presc_rows = c.fetchall()
            found_prescription = any(med_name in str(row[0]).lower() for row in presc_rows if row[0])
            
            # Also check summary_json for legacy/report matches
            c.execute("SELECT summary_json, record_type FROM medical_records WHERE patient_id = ? AND summary_json IS NOT NULL", (self.user_id,))
            rows = c.fetchall()
            conn.close()
            
            found_report = False
            for row in rows:
                if row[0]:
                    try:
                        import json as _json
                        summary = _json.loads(row[0])
                        raw = _json.dumps(summary).lower()
                        if med_name in raw:
                            if row[1] == 'Prescription' and not found_prescription:
                                found_prescription = True
                            elif row[1] == 'Report':
                                found_report = True
                    except Exception:
                        pass
                        
            msg = ""
            if found_prescription:
                msg += "\n✅ VERIFIED: Matches your active prescriptions."
            if found_report:
                msg += "\n✅ VERIFIED: Related condition/medicine found in your lab reports."
                
            if found_prescription or found_report:
                self.result_lbl.setText(self.result_lbl.text() + msg)
                self.result_lbl.setStyleSheet("color: green; font-size: 14px; font-weight: bold;")
            else:
                self.result_lbl.setText(self.result_lbl.text() + "\n❌ WARNING: Term NOT FOUND in your recent records. Verify with your doctor.")
                self.result_lbl.setStyleSheet(self.result_lbl.styleSheet() + "; color: red; font-weight: bold;")
        except Exception as e:
            print(f"Medicine verify error: {e}")

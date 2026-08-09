from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QLineEdit, QMessageBox, QScrollArea, QFrame, QComboBox, QFileDialog, QTextEdit
)
from PyQt6.QtCore import Qt
from src.database import DB_NAME
import sqlite3

class DoctorAppointmentsWidget(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        layout = QVBoxLayout(self)
        
        title = QLabel("Patient Appointments")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1e40af;")
        layout.addWidget(title)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Date", "Time", "Patient", "Status", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.load_data()

    def load_data(self):
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10.0)
            c = conn.cursor()
            c.execute('''
                SELECT a.id, a.date, a.time, u.full_name, a.status 
                FROM appointments a 
                JOIN users u ON a.patient_id = u.id 
                WHERE a.doctor_id = ? 
                ORDER BY a.date ASC
            ''', (self.user_id,))
            rows = c.fetchall()
            conn.close()
            
            self.table.setRowCount(len(rows))
            for r, row in enumerate(rows):
                # row is (id, date, time, patient_name, status)
                self.table.setItem(r, 0, QTableWidgetItem(str(row[1])))
                self.table.setItem(r, 1, QTableWidgetItem(str(row[2])))
                self.table.setItem(r, 2, QTableWidgetItem(str(row[3])))
                self.table.setItem(r, 3, QTableWidgetItem(str(row[4])))
                
                # Action Button
                btn = QPushButton("Mark Completed")
                btn.setStyleSheet("background-color: #10B981; color: white; border-radius: 4px; padding: 4px;")
                btn.clicked.connect(lambda checked, a_id=row[0]: self.complete_appointment(a_id))
                self.table.setCellWidget(r, 4, btn)
        except Exception as e:
            pass

    def complete_appointment(self, apt_id):
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10.0)
            c = conn.cursor()
            c.execute("UPDATE appointments SET status = 'Completed' WHERE id = ?", (apt_id,))
            conn.commit()
            conn.close()
            self.load_data()
        except Exception as e:
            pass

class DoctorReportsWidget(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        layout = QVBoxLayout(self)
        
        title = QLabel("Patient Command Center & Timeline")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1e40af;")
        layout.addWidget(title)
        
        # --- Search Area ---
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter Patient Unique ID (e.g., PAT-1234)")
        search_btn = QPushButton("Lookup Timeline")
        search_btn.setStyleSheet("background-color: #1e40af; color: white; padding: 5px; font-weight: bold;")
        search_btn.clicked.connect(self.lookup_patient)
        
        self.ai_btn = QPushButton("🤖 Generate AI Executive Brief")
        self.ai_btn.setStyleSheet("background-color: #f59e0b; color: white; padding: 5px; font-weight: bold;")
        self.ai_btn.clicked.connect(self.generate_ai_brief)
        self.ai_btn.setEnabled(False)
        
        search_layout.addWidget(QLabel("Patient ID:"))
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_btn)
        search_layout.addWidget(self.ai_btn)
        layout.addLayout(search_layout)
        
        # --- Timeline Graphic ---
        self.graph_frame = QFrame()
        self.graph_layout = QVBoxLayout(self.graph_frame)
        self.graph_frame.setMinimumHeight(250)
        
        import pyqtgraph as pg
        self.plot_widget = pg.PlotWidget(background='w')
        self.plot_widget.hide()
        self.graph_layout.addWidget(self.plot_widget)
        layout.addWidget(self.graph_frame)
        
        # AI Output
        self.ai_output = QTextEdit()
        self.ai_output.setReadOnly(True)
        self.ai_output.hide()
        layout.addWidget(self.ai_output)
        
        # Upload section (Secondary)
        upload_layout = QHBoxLayout()
        self.patient_combo = QComboBox() # To map uniquely found patient ID
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Report", "Prescription"])
        upload_btn = QPushButton("Upload Record")
        upload_btn.setStyleSheet("background-color: #0f766e; color: white; padding: 5px; border-radius: 4px;")
        upload_btn.clicked.connect(self.upload_record)
        
        upload_layout.addWidget(QLabel("Patient Name Cache:"))
        upload_layout.addWidget(self.patient_combo)
        upload_layout.addWidget(QLabel("Type:"))
        upload_layout.addWidget(self.type_combo)
        upload_layout.addWidget(upload_btn)
        upload_layout.addStretch()
        layout.addLayout(upload_layout)
        
        # Records Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Date", "Patient", "Record Type", "Title", "Action"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.current_patient_id = None
        
    def lookup_patient(self):
        uid = self.search_input.text().strip()
        if not uid: return
        
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10.0)
            c = conn.cursor()
            c.execute("SELECT id, full_name, unique_id FROM users WHERE unique_id = ? AND role = 'patient'", (uid,))
            patient = c.fetchone()
            conn.close()
            
            if not patient:
                QMessageBox.warning(self, "Not Found", f"Patient {uid} not found.")
                return
                
            self.current_patient_id = patient[0]
            self.patient_combo.clear()
            self.patient_combo.addItem(f"{patient[1]} ({patient[2]})", patient[0])
            self.ai_btn.setEnabled(True)
            
            self.load_data(patient[0])
            self.load_graph(patient[0])
        except Exception as e:
            pass
            
    def load_graph(self, patient_id):
        from src.database import get_patient_analytics
        import pyqtgraph as pg
        analytics_data = get_patient_analytics(patient_id)
        
        self.plot_widget.clear()
        if not analytics_data:
            self.plot_widget.hide()
            return
            
        self.plot_widget.show()
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.addLegend()
        
        colors = [(14, 165, 233), (139, 92, 246), (245, 158, 11), (16, 185, 129)]
        color_idx = 0
        
        # Provide interactive graph lines for each test
        for test_name, points in analytics_data.items():
            if color_idx >= len(colors): color_idx = 0
            
            x_data = list(range(len(points)))
            y_data = [dp['value'] for dp in points]
            
            pen = pg.mkPen(color=colors[color_idx], width=2)
            self.plot_widget.plot(x_data, y_data, pen=pen, symbol='o', symbolSize=6, name=test_name)
            
            if color_idx == 0:
                ticks = [[(i, dp['date'][-5:]) for i, dp in enumerate(points)]]
                self.plot_widget.getAxis('bottom').setTicks(ticks)
            color_idx += 1

    def upload_record(self):
        from src.ui.components.medibrief_dialog import MedibriefAnalyzerDialog
        patient_id = self.patient_combo.currentData()
        r_type = self.type_combo.currentText()
        if not patient_id: return
        
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "PDF/Image Files (*.pdf *.png *.jpg *.jpeg)")
        if file_path:
            dialog = MedibriefAnalyzerDialog(self, file_path, patient_id, record_type=r_type)
            dialog.exec()
            # Always reload — auto-save fires on close even without clicking Save
            self.load_data(patient_id)
            self.load_graph(patient_id)

    def load_data(self, patient_id=None):
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10.0)
            c = conn.cursor()
            
            if patient_id:
                c.execute('''
                    SELECT m.date_added, u.full_name, m.record_type, m.title, m.summary_json
                    FROM medical_records m
                    JOIN users u ON m.patient_id = u.id
                    WHERE m.patient_id = ?
                    ORDER BY m.date_added DESC
                ''', (patient_id,))
            else:
                c.execute('''
                    SELECT m.date_added, u.full_name, m.record_type, m.title, m.summary_json
                    FROM medical_records m
                    JOIN users u ON m.patient_id = u.id
                    ORDER BY m.date_added DESC LIMIT 50
                ''')
            rows = c.fetchall()
            conn.close()
            
            self.table.setRowCount(len(rows))
            for r, row in enumerate(rows):
                for col_idx in range(4):
                    val = row[col_idx]
                    if col_idx == 0 and val: val = val.split(" ")[0]
                    self.table.setItem(r, col_idx, QTableWidgetItem(str(val)))
                
                # Action column
                summary = row[4]
                btn = QPushButton("View AI Summary")
                if summary:
                    btn.setStyleSheet("background-color: #0f766e; color: white; border-radius: 4px; padding: 4px;")
                    btn.clicked.connect(lambda checked, s=summary: self.view_summary(s))
                else:
                    btn.setEnabled(False)
                    btn.setText("No AI Data")
                self.table.setCellWidget(r, 4, btn)
        except Exception as e:
            pass

    def view_summary(self, summary_json_str):
        import json
        from src.ui.components.medibrief_dialog import MedibriefViewerDialog
        try:
            summary = json.loads(summary_json_str)
            dialog = MedibriefViewerDialog(self, summary)
            dialog.exec()
        except:
            pass

    def generate_ai_brief(self):
        if not self.current_patient_id: return
        self.ai_output.show()
        self.ai_output.setText("<b>AI Executive Copilot:</b> Ingesting patient history and crunching data... Please wait.")
        self.ai_btn.setEnabled(False)
        
        # Compile all records into a massive string context
        context_str = ""
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            c.execute("SELECT summary_json, date_added FROM medical_records WHERE patient_id=?", (self.current_patient_id,))
            reports = c.fetchall()
            c.execute("SELECT notes, timestamp FROM treatment_tracking WHERE patient_id=?", (self.current_patient_id,))
            treatments = c.fetchall()
            conn.close()
            
            context_str += "TREATMENTS:\n"
            for t, d in treatments: context_str += f"[{d}] {t}\n"
            context_str += "REPORTS & VITALS:\n"
            for r, d in reports:
                if r: context_str += f"[{d}] {r}\n"
                
        except Exception:
            pass
            
        system = "You are an Executive AI Copilot for a Doctor. Read all the following patient timeline JSON outputs, treatments and vitals. Synthesize them into a highly concise 1-paragraph Medical Brief and clearly list 2 short-term predicted risks or next steps. Do not babble."
        
        from src.ui.components.chatbot import AIAssistantWorker
        self.ai_worker = AIAssistantWorker(system, f"Patient Data:\n{context_str}", "qwen2.5:3b")
        self.ai_worker.chunk_received.connect(self.on_ai_chunk)
        self.ai_worker.finished_stream.connect(self.on_ai_finished)
        self.ai_worker.start()

    def on_ai_chunk(self, chunk):
        self.ai_output.append(chunk.replace("\n", "<br>"))

    def on_ai_finished(self):
        self.ai_btn.setEnabled(True)

class DoctorProfileWidget(QWidget):
    def __init__(self, user_data):
        super().__init__()
        self.user_data = user_data
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        container = QWidget()
        layout = QVBoxLayout(container)
        
        title = QLabel("Professional Profile")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1e40af;")
        layout.addWidget(title)
        
        form_frame = QFrame()
        form_frame.setStyleSheet("QFrame { background: white; border-radius: 10px; border: 1px solid #e2e8f0; }")
        form_layout = QVBoxLayout(form_frame)
        form_layout.setSpacing(15)
        
        # Name
        form_layout.addWidget(QLabel("Full Name"))
        self.name_input = QLineEdit(self.user_data.get('full_name', ''))
        self.name_input.setStyleSheet("padding: 8px; border: 1px solid #cbd5e1; border-radius: 4px;")
        form_layout.addWidget(self.name_input)
        
        # Specialization
        form_layout.addWidget(QLabel("Specialization"))
        self.spec_input = QLineEdit(self.user_data.get('specialization', ''))
        self.spec_input.setStyleSheet("padding: 8px; border: 1px solid #cbd5e1; border-radius: 4px;")
        form_layout.addWidget(self.spec_input)
        
        # Contact
        form_layout.addWidget(QLabel("Contact Email"))
        self.contact_input = QLineEdit(self.user_data.get('email', ''))
        self.contact_input.setStyleSheet("padding: 8px; border: 1px solid #cbd5e1; border-radius: 4px;")
        form_layout.addWidget(self.contact_input)
        
        save_btn = QPushButton("Save Profile")
        save_btn.setStyleSheet("background-color: #1e40af; color: white; padding: 10px; border-radius: 5px; font-weight: bold;")
        save_btn.clicked.connect(self.save_profile)
        form_layout.addWidget(save_btn)
        
        layout.addWidget(form_frame)
        layout.addStretch()
        
        scroll.setWidget(container)
        main_layout = QVBoxLayout(self)
        main_layout.addWidget(scroll)

    def save_profile(self):
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10.0)
            c = conn.cursor()
            c.execute("UPDATE users SET full_name=?, specialization=?, email=? WHERE id=?", 
                      (self.name_input.text(), self.spec_input.text(), self.contact_input.text(), self.user_data['id']))
            conn.commit()
            conn.close()
            
            self.user_data['full_name'] = self.name_input.text()
            self.user_data['specialization'] = self.spec_input.text()
            self.user_data['email'] = self.contact_input.text()
            
            QMessageBox.information(self, "Success", "Profile updated successfully!")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not update profile: {str(e)}")

class DoctorTreatmentWidget(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        layout = QVBoxLayout(self)
        
        title = QLabel("Patient Treatment Tracking")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1e40af;")
        layout.addWidget(title)
        
        desc = QLabel("Log a treatment update below. Notes are visible to the patient in their Treatment Status tab.")
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #64748b; font-size: 13px; margin-bottom: 5px;")
        layout.addWidget(desc)
        
        # --- Log Update Form ---
        form_frame = QFrame()
        form_frame.setStyleSheet("QFrame { background: #f0f4ff; border: 1px solid #c7d2fe; border-radius: 8px; }")
        form_layout = QHBoxLayout(form_frame)
        form_layout.setContentsMargins(10, 8, 10, 8)
        
        self.patient_combo = QComboBox()
        self.patient_combo.setMinimumWidth(200)
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Not started", "In progress", "Delayed", "Completed"])
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Treatment Notes / Diagnosis (visible to patient)")
        self.notes_input.setMinimumWidth(220)
        
        update_btn = QPushButton("Log Update")
        update_btn.setStyleSheet("background-color: #1e40af; color: white; padding: 8px 16px; border-radius: 6px; font-weight: bold;")
        update_btn.clicked.connect(self.log_update)
        
        form_layout.addWidget(QLabel("Patient:"))
        form_layout.addWidget(self.patient_combo)
        form_layout.addWidget(QLabel("Status:"))
        form_layout.addWidget(self.status_combo)
        form_layout.addWidget(self.notes_input)
        form_layout.addWidget(update_btn)
        layout.addWidget(form_frame)
        
        self.load_patients()
        
        # --- Summary Stats ---
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("font-size: 13px; color: #374151; background: #ecfdf5; padding: 8px; border-radius: 6px; margin-top: 6px;")
        self.stats_label.setWordWrap(True)
        layout.addWidget(self.stats_label)
        
        # --- History Table ---
        history_title = QLabel("Treatment History (All Patients)")
        history_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #1e40af; margin-top: 8px;")
        layout.addWidget(history_title)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Date/Time", "Patient", "Status", "Notes", "Total Updates"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        
        self.load_data()

    def load_patients(self):
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10.0)
            c = conn.cursor()
            c.execute("SELECT id, full_name, unique_id FROM users WHERE role = 'patient'")
            self.patients = c.fetchall()
            conn.close()
            self.patient_combo.clear()
            for p in self.patients:
                label = f"{p[1]} ({p[2]})" if p[2] else p[1]
                self.patient_combo.addItem(label, p[0])
        except Exception as e:
            pass

    def load_data(self):
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10.0)
            c = conn.cursor()
            c.execute('''
                SELECT t.timestamp, u.full_name, t.status, t.notes, t.patient_id
                FROM treatment_tracking t
                JOIN users u ON t.patient_id = u.id
                WHERE t.updated_by_id = ?
                ORDER BY t.timestamp DESC
            ''', (self.user_id,))
            rows = c.fetchall()

            c.execute('''
                SELECT patient_id, COUNT(*) FROM treatment_tracking
                WHERE updated_by_id = ? GROUP BY patient_id
            ''', (self.user_id,))
            count_map = {r[0]: r[1] for r in c.fetchall()}

            c.execute('''
                SELECT COUNT(DISTINCT patient_id) FROM treatment_tracking
                WHERE updated_by_id = ? AND status = "Completed"
            ''', (self.user_id,))
            completed_count = c.fetchone()[0] or 0
            conn.close()
            
            self.stats_label.setText(
                f"Summary — Patients treated: {len(count_map)}  |  "
                f"Total updates logged: {len(rows)}  |  "
                f"Completed treatments: {completed_count}"
            )
            
            self.table.setRowCount(len(rows))
            for r, row in enumerate(rows):
                ts = str(row[0])[:16] if row[0] else ""
                self.table.setItem(r, 0, QTableWidgetItem(ts))
                self.table.setItem(r, 1, QTableWidgetItem(str(row[1])))
                status_item = QTableWidgetItem(str(row[2]))
                if row[2] == "Completed":
                    status_item.setForeground(Qt.GlobalColor.darkGreen)
                elif row[2] == "In progress":
                    status_item.setForeground(Qt.GlobalColor.darkBlue)
                elif row[2] == "Delayed":
                    status_item.setForeground(Qt.GlobalColor.red)
                self.table.setItem(r, 2, status_item)
                self.table.setItem(r, 3, QTableWidgetItem(str(row[3])))
                self.table.setItem(r, 4, QTableWidgetItem(str(count_map.get(row[4], 1))))
        except Exception as e:
            print(f"Error loading treatment data: {e}")

    def log_update(self):
        from src.database import add_treatment_update
        patient_id = self.patient_combo.currentData()
        status = self.status_combo.currentText()
        notes = self.notes_input.text().strip()
        if not patient_id:
            QMessageBox.warning(self, "Error", "Please select a patient.")
            return
        if not notes:
            QMessageBox.warning(self, "Error", "Please enter treatment notes (visible to patient).")
            return
        if add_treatment_update(patient_id, self.user_id, status, notes):
            self.notes_input.clear()
            self.load_data()
            QMessageBox.information(self, "Updated", "Treatment update logged. Patient will see it immediately.")
        else:
            QMessageBox.warning(self, "Error", "Failed to log update.")


class DoctorDiagnosticCopilotWidget(QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        layout = QVBoxLayout(self)
        
        title = QLabel("🤖 AI Diagnostic Copilot")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #2563eb;")
        layout.addWidget(title)
        
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.append("<b>Copilot:</b> I am ready to assist with differential diagnosis processing. Please input the patient symptoms or lab anomalies. Powered by Qwen-0.5B.")
        layout.addWidget(self.chat_history)
        
        input_layout = QHBoxLayout()
        self.question_input = QLineEdit()
        self.question_input.setPlaceholderText("Type symptoms or clinical question here...")
        self.ask_btn = QPushButton("Ask")
        self.ask_btn.setStyleSheet("background-color: #2563eb; color: white;")
        self.ask_btn.clicked.connect(self.ask_question)
        
        input_layout.addWidget(self.question_input)
        input_layout.addWidget(self.ask_btn)
        layout.addLayout(input_layout)

    def load_data(self):
        pass

    def ask_question(self):
        from src.ui.components.chatbot import AIAssistantWorker
        q = self.question_input.text().strip()
        if not q: return
        
        self.chat_history.append(f"<br><b>Dr:</b> {q}")
        self.question_input.clear()
        
        self.ask_btn.setEnabled(False)
        self.chat_history.append("<i>Analyzing Clinical Data...</i>")
        
        system_prompt = "You are an expert AI clinical diagnostic copilot for a doctor. Analyze the symptoms provided, suggest potential differential diagnoses, recommend lab tests, and point out red flags. Be highly professional and clinical."
        
        self.worker = AIAssistantWorker(system_prompt, q, "qwen2.5:3b")
        self.worker.finished.connect(self.on_answer)
        self.worker.start()

    def on_answer(self, ans):
        html = self.chat_history.toHtml()
        html = html.replace("<i>Analyzing Clinical Data...</i>", "")
        self.chat_history.setHtml(html)
        self.chat_history.append(f"<br><b style='color:#2563eb;'>Copilot:</b> {ans}")
        self.ask_btn.setEnabled(True)

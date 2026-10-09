from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, 
    QScrollArea, QFrame, QGridLayout, QMessageBox, QDialog, QFormLayout, QComboBox
)
from PyQt6.QtCore import Qt
from src.database import get_all_doctors, create_referral, book_appointment, get_distinct_specializations
from src.services.ui_localization import get_localized_ui_string

# Disease → Specialization mapping for smart search
DISEASE_SPECIALIZATION_MAP = {
    # Cardiology
    "heart": "Cardiologist", "cardiac": "Cardiologist", "chest pain": "Cardiologist",
    "blood pressure": "Cardiologist", "hypertension": "Cardiologist", "heart attack": "Cardiologist",
    "palpitation": "Cardiologist", "arrhythmia": "Cardiologist",
    # Neurology
    "headache": "Neurologist", "migraine": "Neurologist", "seizure": "Neurologist",
    "brain": "Neurologist", "stroke": "Neurologist", "nerve": "Neurologist",
    "epilepsy": "Neurologist", "paralysis": "Neurologist",
    # Orthopedics
    "fracture": "Orthopedic", "bone": "Orthopedic", "joint": "Orthopedic",
    "back pain": "Orthopedic", "knee": "Orthopedic", "spine": "Orthopedic",
    "arthritis": "Orthopedic",
    # Dermatology
    "skin": "Dermatologist", "rash": "Dermatologist", "acne": "Dermatologist",
    "eczema": "Dermatologist", "allergy": "Dermatologist", "fungal": "Dermatologist",
    # Gastroenterology
    "stomach": "Gastroenterologist", "digestion": "Gastroenterologist", "liver": "Gastroenterologist",
    "acid reflux": "Gastroenterologist", "ulcer": "Gastroenterologist", "diarrhea": "Gastroenterologist",
    # ENT
    "ear": "ENT Specialist", "nose": "ENT Specialist", "throat": "ENT Specialist",
    "sinus": "ENT Specialist", "tonsil": "ENT Specialist", "hearing": "ENT Specialist",
    # Ophthalmology
    "eye": "Ophthalmologist", "vision": "Ophthalmologist", "cataract": "Ophthalmologist",
    "glaucoma": "Ophthalmologist",
    # Endocrinology
    "diabetes": "Endocrinologist", "thyroid": "Endocrinologist", "hormone": "Endocrinologist",
    "sugar": "Endocrinologist",
    # Pulmonology
    "asthma": "Pulmonologist", "breathing": "Pulmonologist", "lung": "Pulmonologist",
    "cough": "Pulmonologist", "pneumonia": "Pulmonologist", "tb": "Pulmonologist",
    # Psychiatry
    "depression": "Psychiatrist", "anxiety": "Psychiatrist", "mental": "Psychiatrist",
    "insomnia": "Psychiatrist", "stress": "Psychiatrist",
    # Urology
    "kidney": "Urologist", "urine": "Urologist", "bladder": "Urologist",
    "prostate": "Urologist",
    # Gynecology
    "pregnancy": "Gynecologist", "menstrual": "Gynecologist", "pcos": "Gynecologist",
    "fertility": "Gynecologist",
    # Pediatrics
    "child": "Pediatrician", "infant": "Pediatrician", "vaccination": "Pediatrician",
    # General
    "fever": "General Physician", "cold": "General Physician", "flu": "General Physician",
    "infection": "General Physician", "weakness": "General Physician",
}

class ReferralDialog(QDialog):
    def __init__(self, doctor_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Refer Patient to {doctor_name}")
        self.setMinimumSize(350, 300)
        self.setStyleSheet("""
            QDialog { background-color: white; }
            QLabel { font-size: 14px; color: #334155; }
            QLineEdit, QComboBox { padding: 8px; border: 1px solid #cbd5e1; border-radius: 5px; }
            QPushButton { padding: 8px 16px; border-radius: 5px; font-weight: bold; }
        """)
        
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Patient Full Name")
        
        self.age_input = QLineEdit()
        self.age_input.setPlaceholderText("Age")
        
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["Male", "Female", "Other"])
        
        self.reason_input = QLineEdit()
        self.reason_input.setPlaceholderText("Reason for Referral")
        
        form_layout.addRow("Patient Name:", self.name_input)
        form_layout.addRow("Age:", self.age_input)
        form_layout.addRow("Gender:", self.gender_combo)
        form_layout.addRow("Reason:", self.reason_input)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        # Buttons
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #94a3b8; color: white;")
        cancel_btn.clicked.connect(self.reject)
        
        submit_btn = QPushButton("Refer Patient")
        submit_btn.setStyleSheet("background-color: #059669; color: white;")
        submit_btn.clicked.connect(self.validate_and_submit)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(submit_btn)
        layout.addLayout(btn_layout)
        
    def validate_and_submit(self):
        if not self.name_input.text() or not self.reason_input.text():
            QMessageBox.warning(self, "Error", "Name and Reason are required.")
            return
        self.accept()
        
    def get_data(self):
        return {
            "name": self.name_input.text(),
            "age": self.age_input.text(),
            "gender": self.gender_combo.currentText(),
            "reason": self.reason_input.text()
        }

class BookingDialog(QDialog):
    def __init__(self, doctor_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Book Appointment with {doctor_name}")
        self.setMinimumSize(300, 200)
        self.setStyleSheet("""
            QDialog { background-color: white; }
            QLabel { font-size: 14px; color: #334155; }
            QLineEdit, QComboBox { padding: 8px; border: 1px solid #cbd5e1; border-radius: 5px; }
            QPushButton { padding: 8px 16px; border-radius: 5px; font-weight: bold; }
        """)
        
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("YYYY-MM-DD")
        
        import datetime
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        self.date_input.setText(str(tomorrow))
        
        self.time_combo = QComboBox()
        self.time_combo.addItems(["10:00 AM", "11:00 AM", "02:00 PM", "04:00 PM"])
        
        form_layout.addRow("Date:", self.date_input)
        form_layout.addRow("Time:", self.time_combo)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet("background-color: #94a3b8; color: white;")
        cancel_btn.clicked.connect(self.reject)
        
        book_btn = QPushButton("Book")
        book_btn.setStyleSheet("background-color: #2563eb; color: white;")
        book_btn.clicked.connect(self.accept)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(book_btn)
        layout.addLayout(btn_layout)
        
    def get_data(self):
        return {
            "date": self.date_input.text(),
            "time": self.time_combo.currentText()
        }

class DoctorListWidget(QWidget):
    def __init__(self, mode="find", current_user_id=None):
        super().__init__()
        self.mode = mode # "find" (patient) or "refer" (doctor)
        self.current_user_id = current_user_id # ID of the logged-in user (referring doc)
        self.doctors = []
        self.init_ui()
        self.load_doctors()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        title = "Find a Specialist" if self.mode == "find" else "Refer to Specialist"
        self.header = QLabel(title)
        self.header.setStyleSheet("font-size: 18px; font-weight: bold; color: #1e3a8a; margin-bottom: 10px;")
        layout.addWidget(self.header)
        
        # Smart search hint
        if self.mode == "find":
            hint = QLabel("💡 Tip: Search by disease name (e.g., 'heart attack', 'diabetes', 'fracture') to find matching specialists automatically.")
            hint.setWordWrap(True)
            hint.setStyleSheet("color: #64748b; font-style: italic; font-size: 12px; margin-bottom: 5px; padding: 6px; background: #f0f9ff; border-radius: 5px;")
            layout.addWidget(hint)
        
        # Filter Bar — Row 1: State + Specialization
        filter_row1 = QHBoxLayout()
        
        # State Filter
        self.state_filter = QComboBox()
        self.state_filter.addItem("All States")
        INDIAN_STATES = [
            "Maharashtra", "Delhi", "Karnataka", "Tamil Nadu", "Uttar Pradesh", 
            "Gujarat", "Rajasthan", "West Bengal", "Madhya Pradesh", "Bihar",
            "Andhra Pradesh", "Telangana", "Kerala", "Punjab", "Haryana", "Odisha", "Other"
        ]
        self.state_filter.addItems(INDIAN_STATES)
        self.state_filter.currentTextChanged.connect(self.load_doctors)
        self.state_filter.setFixedWidth(160)
        self.state_filter.setStyleSheet("padding: 5px; border: 1px solid #cbd5e1; border-radius: 5px;")
        
        # Specialization Filter (dynamic from DB)
        self.spec_filter = QComboBox()
        self.spec_filter.addItem("All Specializations")
        db_specs = get_distinct_specializations()
        if db_specs:
            self.spec_filter.addItems(db_specs)
        self.spec_filter.currentTextChanged.connect(lambda _: self.filter_doctors_local())
        self.spec_filter.setFixedWidth(200)
        self.spec_filter.setStyleSheet("padding: 5px; border: 1px solid #cbd5e1; border-radius: 5px;")
        
        filter_row1.addWidget(QLabel("State:"))
        filter_row1.addWidget(self.state_filter)
        filter_row1.addWidget(QLabel("Specialization:"))
        filter_row1.addWidget(self.spec_filter)
        filter_row1.addStretch()
        layout.addLayout(filter_row1)
        
        # Filter Bar — Row 2: Search Input
        filter_row2 = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by name, disease, or specialization...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #cbd5e1;
                border-radius: 20px;
                padding: 10px 15px;
                font-size: 14px;
            }
        """)
        self.search_input.textChanged.connect(lambda _: self.filter_doctors_local())
        filter_row2.addWidget(self.search_input)
        layout.addLayout(filter_row2)
        
        # Results count label
        self.results_label = QLabel("")
        self.results_label.setStyleSheet("color: #64748b; font-size: 12px; margin: 4px 0;")
        layout.addWidget(self.results_label)
        
        # Scroll Area for List
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background-color: transparent;")
        
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.list_layout.setSpacing(15)
        
        self.scroll.setWidget(self.list_container)
        layout.addWidget(self.scroll)

    def apply_language(self, lang_code):
        self.current_lang = lang_code
        if self.mode == "find":
            self.header.setText(get_localized_ui_string("Find a Specialist", lang_code))
        self.state_filter.setItemText(0, get_localized_ui_string("All States", lang_code))
        self.spec_filter.setItemText(0, get_localized_ui_string("All Specializations", lang_code))

    def load_doctors(self):
        selected_state = self.state_filter.currentText()
        all_docs = get_all_doctors(state_filter=selected_state)
        
        # Filter out self if in refer mode
        if self.mode == "refer" and self.current_user_id:
             self.doctors = [d for d in all_docs if d['id'] != self.current_user_id]
        else:
             self.doctors = all_docs
        
        # Re-apply local filter if search text exists
        self.filter_doctors_local()

    def populate_list(self, doctor_list):
        # Clear existing items
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                
        if not doctor_list:
            no_data = QLabel("No doctors found matching your criteria.")
            no_data.setStyleSheet("color: #64748b; font-style: italic; font-size: 14px; padding: 20px;")
            self.list_layout.addWidget(no_data)
            self.results_label.setText("0 doctors found")
            return

        self.results_label.setText(f"{len(doctor_list)} doctor(s) found")
        for doc in doctor_list:
            card = self.create_doctor_card(doc)
            self.list_layout.addWidget(card)

    def create_doctor_card(self, doc):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 10px;
                padding: 10px;
            }
            QFrame:hover {
                border-color: #3b82f6;
                background-color: #f8fafc;
            }
        """)
        layout = QHBoxLayout(card)
        
        # Info
        info_layout = QVBoxLayout()
        name = QLabel(doc['full_name'] or "Unknown Doctor")
        name.setStyleSheet("font-weight: bold; font-size: 16px; color: #1e293b;")
        
        spec = QLabel(doc['specialization'] or "General Physician")
        spec.setStyleSheet("color: #0d9488; font-weight: 500;")
        
        location = QLabel(f"📍 {doc['state'] or 'Unknown State'}")
        location.setStyleSheet("color: #64748b; font-size: 12px;")
        
        # Show unique ID for credibility
        uid_text = f"🆔 Reg: {doc['unique_id']}" if doc.get('unique_id') else ""
        uid_label = QLabel(uid_text)
        uid_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        
        contact = QLabel(f"📧 {doc['email']}" if doc.get('email') else "")
        contact.setStyleSheet("color: #64748b; font-size: 12px;")
        
        info_layout.addWidget(name)
        info_layout.addWidget(spec)
        info_layout.addWidget(location)
        if uid_text:
            info_layout.addWidget(uid_label)
        if doc.get('email'):
            info_layout.addWidget(contact)
        layout.addLayout(info_layout)
        
        # Action Button
        btn_text = "Book Appointment" if self.mode == "find" else "Refer Patient"
        btn_color = "#2563eb" if self.mode == "find" else "#059669"
        
        action_btn = QPushButton(btn_text)
        action_btn.setMinimumSize(120, 36)
        action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        action_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {btn_color};
                color: white;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                opacity: 0.9;
            }}
        """)
        action_btn.clicked.connect(lambda _, d=doc: self.handle_action(d))
        layout.addWidget(action_btn)
        
        return card

    def filter_doctors_local(self, text=None):
        """Filter doctors by search text and specialization dropdown."""
        if text is None:
            text = self.search_input.text()
        text = text.lower().strip()
        
        spec_filter = self.spec_filter.currentText()
        
        # Start with all loaded doctors
        filtered = list(self.doctors)
        
        # Apply specialization dropdown filter
        if spec_filter and spec_filter != "All Specializations":
            filtered = [d for d in filtered if d.get('specialization') and spec_filter.lower() in d['specialization'].lower()]
        
        # Apply text search
        if text:
            # Check if the search matches a disease keyword
            matched_spec = None
            for disease_keyword, spec_name in DISEASE_SPECIALIZATION_MAP.items():
                if disease_keyword in text:
                    matched_spec = spec_name
                    break
            
            if matched_spec:
                # Smart filter: match the mapped specialization
                filtered = [
                    d for d in filtered
                    if (d.get('specialization') and matched_spec.lower() in d['specialization'].lower()) or
                       (d.get('full_name') and text in d['full_name'].lower())
                ]
            else:
                # Standard text filter on name and specialization
                filtered = [
                    d for d in filtered 
                    if (d.get('full_name') and text in d['full_name'].lower()) or 
                       (d.get('specialization') and text in d['specialization'].lower()) or
                       (d.get('state') and text in d['state'].lower()) or
                       (d.get('unique_id') and text in d['unique_id'].lower())
                ]
        
        self.populate_list(filtered)

    def handle_action(self, doc):
        if self.mode == "find":
            dialog = BookingDialog(doc['full_name'], self)
            if dialog.exec():
                data = dialog.get_data()
                if self.current_user_id:
                    success = book_appointment(self.current_user_id, doc['id'], data['date'], data['time'])
                    if success:
                        QMessageBox.information(
                            self, 
                            "Appointment Requested", 
                            f"Booking request sent to {doc['full_name']} for {data['date']} at {data['time']}.\nIt will show as 'Pending' until accepted."
                        )
                    else:
                        QMessageBox.warning(self, "Error", "Could not book appointment.")
                else:
                    QMessageBox.warning(self, "Error", "User not logged in correctly.")
        elif self.mode == "refer":
            dialog = ReferralDialog(doc['full_name'], self)
            if dialog.exec():
                data = dialog.get_data()
                success = create_referral(
                    data['name'], data['age'], data['gender'], data['reason'], 
                    self.current_user_id, doc['id']
                )
                if success:
                    QMessageBox.information(self, "Success", "Referral sent successfully!")
                else:
                    QMessageBox.warning(self, "Error", "Failed to send referral.")

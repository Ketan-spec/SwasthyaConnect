from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, 
    QScrollArea, QFrame, QGridLayout, QMessageBox, QDialog, QFormLayout, QComboBox
)
from PyQt6.QtCore import Qt
from src.database import get_all_doctors, create_referral

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
        header = QLabel(title)
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #1e3a8a; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Filter Bar
        filter_layout = QHBoxLayout()
        
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
        self.state_filter.setFixedWidth(150)
        self.state_filter.setStyleSheet("padding: 5px; border: 1px solid #cbd5e1; border-radius: 5px;")
        
        # Search Input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by Name or Specialization...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #cbd5e1;
                border-radius: 20px;
                padding: 10px 15px;
                font-size: 14px;
            }
        """)
        self.search_input.textChanged.connect(self.filter_doctors_local)
        
        filter_layout.addWidget(QLabel("Filter by State:"))
        filter_layout.addWidget(self.state_filter)
        filter_layout.addWidget(self.search_input)
        
        layout.addLayout(filter_layout)
        
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

    def load_doctors(self):
        selected_state = self.state_filter.currentText()
        all_docs = get_all_doctors(state_filter=selected_state)
        
        # Filter out self if in refer mode
        if self.mode == "refer" and self.current_user_id:
             self.doctors = [d for d in all_docs if d['id'] != self.current_user_id]
        else:
             self.doctors = all_docs
        
        # Re-apply local filter if search text exists
        self.filter_doctors_local(self.search_input.text())

    def populate_list(self, doctor_list):
        # Clear existing items
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                
        if not doctor_list:
            no_data = QLabel("No doctors found.")
            no_data.setStyleSheet("color: #64748b; font-style: italic;")
            self.list_layout.addWidget(no_data)
            return

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
        
        contact = QLabel(f"📧 {doc['email']}")
        contact.setStyleSheet("color: #64748b; font-size: 12px;")
        
        info_layout.addWidget(name)
        info_layout.addWidget(spec)
        info_layout.addWidget(location)
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

    def filter_doctors_local(self, text):
        text = text.lower()
        if not text:
             self.populate_list(self.doctors)
             return
             
        filtered = [
            d for d in self.doctors 
            if (d['full_name'] and text in d['full_name'].lower()) or 
               (d['specialization'] and text in d['specialization'].lower())
        ]
        self.populate_list(filtered)

    def handle_action(self, doc):
        if self.mode == "find":
            QMessageBox.information(
                self, 
                "Book Appointment", 
                f"Booking request sent to {doc['full_name']}. They will contact you shortly."
            )
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

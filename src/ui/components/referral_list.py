from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame, QHBoxLayout, QPushButton, QMessageBox, QComboBox
)
from PyQt6.QtCore import Qt
from src.database import get_doctor_referrals, update_referral_status

class ReferralListWidget(QWidget):
    def __init__(self, current_doctor_id):
        super().__init__()
        self.current_doctor_id = current_doctor_id
        self.init_ui()
        self.load_referrals()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("Incoming Patient Referrals")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #1e3a8a; margin-bottom: 10px;")
        layout.addWidget(header)
        
        # Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("border: none; background-color: transparent;")
        
        self.list_container = QWidget()
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.list_layout.setSpacing(15)
        
        self.scroll.setWidget(self.list_container)
        layout.addWidget(self.scroll)

    def load_referrals(self):
        referrals = get_doctor_referrals(self.current_doctor_id)
        self.populate_list(referrals)
        
    def populate_list(self, referrals):
        # Clear list
        while self.list_layout.count():
            item = self.list_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                
        if not referrals:
            no_data = QLabel("No new referrals.")
            no_data.setStyleSheet("color: #64748b; font-style: italic;")
            self.list_layout.addWidget(no_data)
            return

        for ref in referrals:
            card = self.create_referral_card(ref)
            self.list_layout.addWidget(card)
            
    def create_referral_card(self, ref):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: white;
                border_left: 4px solid #f59e0b;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(card)
        
        # Top Row: Patient Name & Date
        top_row = QHBoxLayout()
        name_label = QLabel(f"{ref['patient_name']} ({ref['patient_age']}, {ref['patient_gender']})")
        name_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #1e293b;")
        
        date_label = QLabel(ref['timestamp'][:10])
        date_label.setStyleSheet("color: #64748b; font-size: 12px;")
        
        top_row.addWidget(name_label)
        top_row.addStretch()
        top_row.addWidget(date_label)
        layout.addLayout(top_row)
        
        # Reason
        reason_label = QLabel(f"Reason: {ref['reason']}")
        reason_label.setStyleSheet("color: #334155; margin-top: 5px;")
        reason_label.setWordWrap(True)
        layout.addWidget(reason_label)
        
        # Referring Doctor
        ref_doc = ref.get('referring_doc_name', 'Unknown')
        ref_id = ref.get('referring_doc_id', 'N/A')
        doc_label = QLabel(f"Referred By: {ref_doc} (ID: {ref_id})")
        doc_label.setStyleSheet("color: #0d9488; font-weight: 500; margin-top: 10px; font-size: 13px;")
        layout.addWidget(doc_label)
        
        # Status & Actions
        status_row = QHBoxLayout()
        status_label = QLabel(f"Status: {ref['status']}")
        
        # Color code status
        status_color = "#f59e0b" # Pending
        if ref['status'] == "Accepted": status_color = "#16a34a"
        elif ref['status'] == "Rejected": status_color = "#dc2626"
        elif ref['status'] in ["Pre-Op", "Surgery", "Post-Op"]: status_color = "#2563eb"
        
        status_label.setStyleSheet(f"font-weight: bold; color: {status_color}; margin-top: 10px;")
        status_row.addWidget(status_label)
        status_row.addStretch()
        
        # Logic for Buttons/Dropdowns
        if ref['status'] == "Pending":
            accept_btn = QPushButton("Accept")
            accept_btn.setMinimumSize(80, 30)
            accept_btn.setStyleSheet("background-color: #16a34a; color: white; border-radius: 4px;")
            accept_btn.clicked.connect(lambda _, r=ref: self.update_status(r['id'], "Accepted"))
            
            reject_btn = QPushButton("Reject")
            reject_btn.setMinimumSize(80, 30)
            reject_btn.setStyleSheet("background-color: #dc2626; color: white; border-radius: 4px;")
            reject_btn.clicked.connect(lambda _, r=ref: self.update_status(r['id'], "Rejected"))
            
            status_row.addWidget(accept_btn)
            status_row.addWidget(reject_btn)
            
        elif ref['status'] != "Rejected" and ref['status'] != "Discharged":
            # For Accepted ongoing cases, dropdown for Operation Status
            status_combo = QComboBox()
            status_combo.setFixedWidth(120)
            
            # Define workflow options
            options = []
            if ref['status'] == "Accepted": options = ["Accepted", "Pre-Op", "Surgery", "Discharged"]
            elif ref['status'] == "Pre-Op": options = ["Pre-Op", "Surgery", "Post-Op"]
            elif ref['status'] == "Surgery": options = ["Surgery", "Post-Op", "Discharged"]
            elif ref['status'] == "Post-Op": options = ["Post-Op", "Discharged"]
            else: options = ["Pre-Op", "Surgery", "Post-Op", "Discharged"]
            
            status_combo.addItems(options)
            status_combo.setCurrentText(ref['status'])
            
            # Handle change only if different
            status_combo.currentTextChanged.connect(lambda text, r=ref: self.update_status_if_changed(r['id'], text, r['status']))
            
            status_row.addWidget(status_combo)
            
        layout.addLayout(status_row)
        
        return card

    def update_status(self, ref_id, new_status):
        success = update_referral_status(ref_id, new_status)
        if success:
            QMessageBox.information(self, "Success", f"Referral {new_status}!")
            self.load_referrals() # Refresh
        else:
            QMessageBox.warning(self, "Error", "Failed to update status.")

    def update_status_if_changed(self, ref_id, new_status, old_status):
        if new_status != old_status:
            self.update_status(ref_id, new_status)

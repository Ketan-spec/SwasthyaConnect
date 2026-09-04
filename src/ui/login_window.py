from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QLineEdit, QPushButton, QMessageBox, 
    QComboBox, QStackedWidget, QHBoxLayout, QFrame, QDialog
)
from PyQt6.QtCore import Qt
from src.database import check_login, register_user, reset_database
from src.ui.dashboards.patient_dashboard import PatientDashboard
from src.ui.dashboards.doctor_dashboard import DoctorDashboard
from src.ui.dashboards.hospital_dashboard import HospitalDashboard
from src.ui.dashboards.govt_dashboard import GovtDashboard
from src.ui.styles import LOGIN_STYLES

class DeveloperBlockchainDialog(QDialog):
    """Developer Access Window allowing instant inspection of all system blockchain transactions."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⛓️ Developer Access — SwasthyaConnect System Blockchain Explorer")
        self.resize(1150, 750)
        self.setMinimumSize(850, 550)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        try:
            from src.ui.components.blockchain_viewer import BlockchainViewerWidget
            self.viewer = BlockchainViewerWidget(patient_id=None)
            layout.addWidget(self.viewer)
        except Exception as e:
            err_lbl = QLabel(f"Error opening Blockchain Explorer: {e}")
            err_lbl.setStyleSheet("color: red; padding: 20px; font-size: 16px;")
            layout.addWidget(err_lbl)

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("MainLoginBg")
        self.setWindowTitle("SwasthyaConnect — AI & Blockchain Digital Health Platform")
        self.resize(1100, 750)
        self.setMinimumSize(750, 550)
        self.setStyleSheet(LOGIN_STYLES)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # ── Top Bar (Healthcare Branding & Developer Blockchain Access) ──
        top_bar = QHBoxLayout()
        
        brand_layout = QVBoxLayout()
        brand_title = QLabel("🏥 SwasthyaConnect")
        brand_title.setStyleSheet("color: white; font-size: 22px; font-weight: 800; font-family: 'Inter', sans-serif;")
        brand_sub = QLabel("HDIMS Healthcare Information & Management System • AI & Blockchain Powered")
        brand_sub.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 500;")
        brand_layout.addWidget(brand_title)
        brand_layout.addWidget(brand_sub)
        
        top_bar.addLayout(brand_layout)
        top_bar.addStretch()
        
        # Developer Access Button
        dev_btn = QPushButton("⛓️ Developer Access: Blockchain Audit Log")
        dev_btn.setObjectName("DevBlockchainBtn")
        dev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        dev_btn.setToolTip("Click to directly view tamper-proof system blockchain, transaction hashes, and all records across roles.")
        dev_btn.clicked.connect(self.open_developer_blockchain)
        top_bar.addWidget(dev_btn)
        
        main_layout.addLayout(top_bar)
        main_layout.addStretch(1)
        
        # ── Centered Glassmorphic Auth Box ──
        auth_container = QHBoxLayout()
        auth_container.addStretch()
        
        self.auth_box = QFrame()
        self.auth_box.setObjectName("AuthBox")
        self.auth_box.setMinimumWidth(400)
        self.auth_box.setMaximumWidth(480)
        
        box_layout = QVBoxLayout(self.auth_box)
        box_layout.setContentsMargins(35, 35, 35, 35)
        box_layout.setSpacing(15)
        
        # Stacked Widget to switch between Login and Signup
        self.stack = QStackedWidget()
        
        self.login_widget = self.create_login_ui()
        self.signup_widget = self.create_signup_ui()
        
        self.stack.addWidget(self.login_widget)
        self.stack.addWidget(self.signup_widget)
        
        box_layout.addWidget(self.stack)
        
        auth_container.addWidget(self.auth_box)
        auth_container.addStretch()
        main_layout.addLayout(auth_container)
        
        main_layout.addStretch(1)
        
        # ── Bottom Action Bar (Reset Database) ──
        reset_layout = QHBoxLayout()
        reset_layout.addStretch()
        reset_btn = QPushButton("⚠️ Reset Database")
        reset_btn.setToolTip("Danger: Deletes all data and resets the database from scratch.")
        reset_btn.setStyleSheet("""
            QPushButton { 
                background-color: rgba(239, 68, 68, 0.15); 
                color: #fca5a5; 
                border: 1px solid rgba(239, 68, 68, 0.4);
                font-weight: bold;
                padding: 6px 14px;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #ef4444; color: white; }
        """)
        reset_btn.clicked.connect(self.handle_db_reset)
        reset_layout.addWidget(reset_btn)
        
        main_layout.addLayout(reset_layout)

    def open_developer_blockchain(self):
        """Direct Developer Access to open system-wide Blockchain Audit Viewer."""
        dialog = DeveloperBlockchainDialog(self)
        dialog.exec()

    def handle_db_reset(self):
        reply = QMessageBox.question(
            self, 'Confirm Reset',
            "Are you sure you want to completely clear the database? This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            success, msg = reset_database()
            if success:
                QMessageBox.information(self, "Database Reset", msg)
            else:
                QMessageBox.critical(self, "Reset Error", msg)

    def create_login_ui(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        title = QLabel("Welcome Back")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle = QLabel("Select role & sign in to continue")
        subtitle.setStyleSheet("color: #64748b; font-size: 13px; margin-bottom: 15px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        
        self.login_user_input = QLineEdit()
        self.login_user_input.setPlaceholderText("Phone (Patients) or Username/ID (Others)")
        layout.addWidget(self.login_user_input)
        
        self.login_pass_input = QLineEdit()
        self.login_pass_input.setPlaceholderText("Password")
        self.login_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.login_pass_input)
        
        layout.addSpacing(10)
        
        login_btn = QPushButton("Sign In")
        login_btn.setObjectName("PrimaryBtn")
        login_btn.clicked.connect(self.handle_login)
        layout.addWidget(login_btn)
        
        toggle_btn = QPushButton("Don't have an account? Create one")
        toggle_btn.setObjectName("SecondaryBtn")
        toggle_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.signup_widget))
        layout.addWidget(toggle_btn)
        
        layout.addStretch()
        return widget

    def create_signup_ui(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        title = QLabel("Create Account")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        subtitle = QLabel("Join SwasthyaConnect Digital Platform")
        subtitle.setStyleSheet("color: #64748b; font-size: 13px; margin-bottom: 15px;")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        
        # Role Selection First
        self.role_combo = QComboBox()
        self.role_combo.addItems(["Patient", "Doctor", "Hospital", "Government"])
        self.role_combo.currentTextChanged.connect(self.update_form_fields)
        layout.addWidget(self.role_combo)
        
        # Common Fields
        self.fullname_input = QLineEdit()
        self.fullname_input.setPlaceholderText("Full Name")
        layout.addWidget(self.fullname_input)
        
        # Dynamic Fields Container
        self.dynamic_fields_layout = QVBoxLayout()
        layout.addLayout(self.dynamic_fields_layout)
        
        self.signup_pass_input = QLineEdit()
        self.signup_pass_input.setPlaceholderText("Password")
        self.signup_pass_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.signup_pass_input)
        
        layout.addSpacing(10)
        
        signup_btn = QPushButton("Sign Up")
        signup_btn.setObjectName("PrimaryBtn")
        signup_btn.clicked.connect(self.handle_signup)
        layout.addWidget(signup_btn)
        
        toggle_btn = QPushButton("Already have an account? Sign In")
        toggle_btn.setObjectName("SecondaryBtn")
        toggle_btn.clicked.connect(lambda: self.stack.setCurrentWidget(self.login_widget))
        layout.addWidget(toggle_btn)
        
        layout.addStretch()
        
        # Initial fields setup
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Phone Number")
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email Address")
        
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("Unique ID")

        # Specialization Combo for Doctors
        self.spec_combo = QComboBox()
        self.spec_combo.addItems([
            "Cardiologist", "Dermatologist", "Pediatrician", "Gynecologist", 
            "Neurologist", "Orthopedic Surgeon", "General Physician", "ENT Specialist"
        ])
        
        # State Selection
        self.state_combo = QComboBox()
        INDIAN_STATES = [
            "Maharashtra", "Delhi", "Karnataka", "Tamil Nadu", "Uttar Pradesh", 
            "Gujarat", "Rajasthan", "West Bengal", "Madhya Pradesh", "Bihar",
            "Andhra Pradesh", "Telangana", "Kerala", "Punjab", "Haryana", "Odisha", "Other"
        ]
        self.state_combo.addItems(INDIAN_STATES)
        self.state_combo.setStyleSheet("""
            QComboBox {
                color: black;
                background-color: white;
                border: 1px solid #cbd5e1;
                padding: 8px;
                border-radius: 5px;
            }
            QComboBox QAbstractItemView {
                color: black;
                background-color: white;
                selection-background-color: #0ea5e9;
            }
        """)

        self.update_form_fields("Patient")
        
        return widget

    def update_form_fields(self, role):
        # Safely Clear existing dynamic fields
        while self.dynamic_fields_layout.count():
            item = self.dynamic_fields_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                
        # Helper for State Label
        def create_state_label():
            lbl = QLabel("Select State:")
            lbl.setStyleSheet("color: black; font-weight: bold;")
            return lbl
            
        if role == "Patient":
            self.dynamic_fields_layout.addWidget(self.phone_input)
            self.dynamic_fields_layout.addWidget(create_state_label())
            self.dynamic_fields_layout.addWidget(self.state_combo)
            self.fullname_input.setPlaceholderText("Patient Name")
        elif role == "Doctor":
            self.dynamic_fields_layout.addWidget(self.email_input)
            self.dynamic_fields_layout.addWidget(self.id_input)
            self.dynamic_fields_layout.addWidget(self.spec_combo)
            self.dynamic_fields_layout.addWidget(create_state_label())
            self.dynamic_fields_layout.addWidget(self.state_combo)
            self.fullname_input.setPlaceholderText("Doctor Name")
            self.id_input.setPlaceholderText("Doctor ID")
        elif role == "Hospital":
            self.dynamic_fields_layout.addWidget(self.email_input)
            self.dynamic_fields_layout.addWidget(self.id_input)
            self.dynamic_fields_layout.addWidget(create_state_label())
            self.dynamic_fields_layout.addWidget(self.state_combo)
            self.fullname_input.setPlaceholderText("Hospital Name")
            self.id_input.setPlaceholderText("Hospital Registration ID")
        elif role == "Government":
            self.dynamic_fields_layout.addWidget(self.email_input)
            self.dynamic_fields_layout.addWidget(self.id_input)
            self.fullname_input.setPlaceholderText("Officer Name")
            self.id_input.setPlaceholderText("Govt Officer ID")

    def handle_login(self):
        username = self.login_user_input.text()
        password = self.login_pass_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Error", "Please fill in all fields.")
            return

        user_data = check_login(username, password)
        
        if user_data:
            self.open_dashboard(user_data)
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password")

    def handle_signup(self):
        role_map = {"Patient": "patient", "Doctor": "doctor", "Hospital": "hospital", "Government": "govt"}
        role_text = self.role_combo.currentText()
        role = role_map[role_text]
        
        full_name = self.fullname_input.text()
        password = self.signup_pass_input.text()
        
        username = ""
        phone = None
        email = None
        unique_id = None
        specialization = None
        state = None
        
        if not full_name or not password:
             QMessageBox.warning(self, "Error", "Please fill in all required fields.")
             return
        
        if role == "patient":
            phone = self.phone_input.text()
            if not phone:
                QMessageBox.warning(self, "Error", "Phone number is required.")
                return
            username = phone
            state = self.state_combo.currentText()
        else:
            email = self.email_input.text()
            unique_id = self.id_input.text()
            if not email or not unique_id:
                QMessageBox.warning(self, "Error", "Email and ID are required.")
                return
            username = email
            if role != "govt":
                state = self.state_combo.currentText()
            
        if role == "doctor":
            specialization = self.spec_combo.currentText()
            
        success, message = register_user(username, password, role, full_name, phone, email, unique_id, specialization, state)
        
        if success:
            QMessageBox.information(self, "Success", f"Account created! Your Login ID is: {username}")
            self.stack.setCurrentWidget(self.login_widget)
        else:
            QMessageBox.warning(self, "Signup Failed", message)

    def open_dashboard(self, user_data):
        role = user_data.get('role', '').lower()
        
        if role == 'patient':
            self.dashboard = PatientDashboard(user_data, self.handle_logout)
        elif role == 'doctor':
            self.dashboard = DoctorDashboard(user_data, self.handle_logout)
        elif role == 'hospital':
            self.dashboard = HospitalDashboard(user_data, self.handle_logout)
        elif role == 'govt':
            self.dashboard = GovtDashboard(user_data, self.handle_logout)
        else:
            QMessageBox.critical(self, "Error", f"Unknown user role: {role}")
            return
            
        self.dashboard.show()
        self.hide()

    def handle_logout(self):
        if hasattr(self, 'dashboard') and self.dashboard:
            self.dashboard.close()
        self.login_user_input.clear()
        self.login_pass_input.clear()
        self.show()

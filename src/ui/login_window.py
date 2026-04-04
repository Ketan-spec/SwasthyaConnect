from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QLineEdit, QPushButton, QMessageBox, 
    QComboBox, QStackedWidget, QHBoxLayout, QFrame
)
from PyQt6.QtCore import Qt
from src.database import check_login, register_user, reset_database
from src.ui.dashboards.patient_dashboard import PatientDashboard
from src.ui.dashboards.doctor_dashboard import DoctorDashboard
from src.ui.dashboards.hospital_dashboard import HospitalDashboard
from src.ui.dashboards.govt_dashboard import GovtDashboard
from src.ui.styles import LOGIN_STYLES

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Swasthya_Connect - Secure Authentication")
        self.resize(1000, 700)
        self.setMinimumSize(600, 500)
        self.setStyleSheet(LOGIN_STYLES)

        
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Auth Box Container
        self.auth_box = QFrame()
        self.auth_box.setObjectName("AuthBox")
        self.auth_box.setMinimumWidth(350)
        self.auth_box.setMaximumWidth(450)
        
        box_layout = QVBoxLayout(self.auth_box)
        box_layout.setContentsMargins(40, 40, 40, 40)
        box_layout.setSpacing(15)
        
        # Stacked Widget to switch between Login and Signup
        self.stack = QStackedWidget()
        
        self.login_widget = self.create_login_ui()
        self.signup_widget = self.create_signup_ui()
        
        self.stack.addWidget(self.login_widget)
        self.stack.addWidget(self.signup_widget)
        
        box_layout.addWidget(self.stack)
        
        
        main_layout.addWidget(self.auth_box)
        
        # Add Reset Database Button to bottom
        reset_layout = QHBoxLayout()
        reset_layout.addStretch()
        reset_btn = QPushButton("⚠️ Reset Database")
        reset_btn.setToolTip("Danger: Deletes all data and resets the database from scratch.")
        reset_btn.setStyleSheet("""
            QPushButton { 
                background-color: transparent; 
                color: #ef4444; 
                border: none;
                font-weight: bold;
                padding: 10px;
            }
            QPushButton:hover { background-color: #fee2e2; border-radius: 5px; }
        """)
        reset_btn.clicked.connect(self.handle_db_reset)
        reset_layout.addWidget(reset_btn)
        
        main_layout.addLayout(reset_layout)
        
        self.setLayout(main_layout)

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
        
        subtitle = QLabel("Please sign in to continue")
        subtitle.setObjectName("Subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(title)
        layout.addWidget(subtitle)
        
        self.login_user_input = QLineEdit()
        self.login_user_input.setPlaceholderText("Phone (Patients) or Email/ID (Others)")
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
        
        subtitle = QLabel("Join Swasthya_Connect")
        subtitle.setObjectName("Subtitle")
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
        # Enforcing Black Text for State Selection
        self.state_combo.setStyleSheet("""
            QComboBox {
                color: black;
                background-color: white;
                border: 1px solid #cbd5e1;
                padding: 5px;
                border-radius: 5px;
            }
            QComboBox QAbstractItemView {
                color: black;
                background-color: white;
                selection-background-color: #3b82f6;
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
            self.dynamic_fields_layout.addWidget(self.spec_combo) # Add Spec
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
            # No State for Govt
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
            username = phone # Use phone as username for patient
            state = self.state_combo.currentText()
        else:
            email = self.email_input.text()
            unique_id = self.id_input.text()
            if not email or not unique_id:
                QMessageBox.warning(self, "Error", "Email and ID are required.")
                return
            username = email # Use email as username for others
            if role != "govt":
                state = self.state_combo.currentText()
            
        if role == "doctor":
            specialization = self.spec_combo.currentText()
            
        success, message = register_user(username, password, role, full_name, phone, email, unique_id, specialization, state)
        
        if success:
            QMessageBox.information(self, "Success", f"Account created! Your Login ID is: {username}")
            self.stack.setCurrentWidget(self.login_widget)
        else:
            QMessageBox.warning(self, "Registration Failed", message)

    def open_dashboard(self, user_data):
        role = user_data['role']
        if role == 'patient':
            self.dashboard = PatientDashboard(user_data, self.handle_logout)
        elif role == 'doctor':
            self.dashboard = DoctorDashboard(user_data, self.handle_logout)
        elif role == 'hospital':
            self.dashboard = HospitalDashboard(user_data, self.handle_logout)
        elif role == 'govt':
            self.dashboard = GovtDashboard(user_data, self.handle_logout)
        else:
            return
            
        self.dashboard.show()
        self.close()

    def handle_logout(self):
        self.dashboard.close()
        self.show()
        self.login_user_input.clear()
        self.login_pass_input.clear()

from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QGridLayout,
    QSizePolicy, QScrollArea, QLineEdit, QComboBox, QMessageBox, QSpacerItem, QStackedWidget
)
from src.ui.styles import get_sidebar_style, CONTENT_STYLE
from src.database import get_hospital_resources, update_hospital_resources
from src.ui.components.hospital_tabs import (
    PatientAdmissionWidget, HospitalStaffWidget, HospitalInventoryWidget, 
    HospitalAmbulanceWidget, HospitalTreatmentWidget
)

class HospitalDashboard(QWidget):
    def __init__(self, user_data, logout_callback):
        super().__init__()
        self.logout_callback = logout_callback
        self.user_data = user_data
        self.setWindowTitle("Hospital Dashboard")
        self.resize(1200, 800)
        self.setMinimumSize(800, 600)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Sidebar ---
        self.sidebar = QWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(250)
        self.sidebar.setStyleSheet(get_sidebar_style("hospital"))
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        title_label = QLabel("Swasthya\nHospital Portal")
        title_label.setObjectName("SidebarTitle")
        sidebar_layout.addWidget(title_label)
        
        # Menu Items
        self.menu_btns = {}
        menu_items = ["Overview", "Patient Admission", "Staff", "Inventory", "Ambulance", "Treatment Tracking"]
        for item in menu_items:
            btn = QPushButton(item)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, i=item: self.switch_page(i))
            self.menu_btns[item] = btn
            sidebar_layout.addWidget(btn)
        
        self.menu_btns["Overview"].setChecked(True)
            
        sidebar_layout.addStretch()
        
        # Logout Button
        logout_btn = QPushButton("Logout")
        logout_btn.clicked.connect(self.logout_callback)
        sidebar_layout.addWidget(logout_btn)
        
        # --- Content Area ---
        self.content_area = QWidget()
        self.content_area.setObjectName("ContentArea")
        self.content_area.setStyleSheet(CONTENT_STYLE)
        
        content_main_layout = QVBoxLayout(self.content_area)
        content_main_layout.setContentsMargins(0,0,0,0)
        
        self.stack = QStackedWidget()
        content_main_layout.addWidget(self.stack)
        
        # Page 0: Overview
        self.overview_page = self.create_overview_page()
        self.stack.addWidget(self.overview_page)
        
        # Page 1: Patient Admission
        self.admissions_page = PatientAdmissionWidget(self.user_data['id'])
        self.stack.addWidget(self.admissions_page)
        
        # Page 2: Staff
        self.staff_page = HospitalStaffWidget(self.user_data['id'])
        self.stack.addWidget(self.staff_page)
        
        # Page 3: Inventory
        self.inventory_page = HospitalInventoryWidget(self.user_data['id'])
        self.stack.addWidget(self.inventory_page)
        
        # Page 4: Ambulance
        self.ambulance_page = HospitalAmbulanceWidget(self.user_data['id'])
        self.stack.addWidget(self.ambulance_page)
        
        # Page 5: Treatment Tracking
        self.treatment_page = HospitalTreatmentWidget(self.user_data['id'])
        self.stack.addWidget(self.treatment_page)
        
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content_area)
        
        self.setLayout(main_layout)

    def switch_page(self, page_name):
        for name, btn in self.menu_btns.items():
            if name != page_name:
                btn.setChecked(False)
        self.menu_btns[page_name].setChecked(True)
        
        if page_name == "Overview":
            self.stack.setCurrentIndex(0)
        elif page_name == "Patient Admission":
            self.admissions_page.load_data()
            self.stack.setCurrentIndex(1)
        elif page_name == "Staff":
            self.staff_page.load_data()
            self.stack.setCurrentIndex(2)
        elif page_name == "Inventory":
            self.inventory_page.load_data()
            self.stack.setCurrentIndex(3)
        elif page_name == "Ambulance":
            self.ambulance_page.load_data()
            self.stack.setCurrentIndex(4)
        elif page_name == "Treatment Tracking":
            self.treatment_page.load_data()
            self.stack.setCurrentIndex(5)

    def create_overview_page(self):
        page = QWidget()
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(40, 40, 40, 40)
        
        
        # Header
        welcome_msg = QLabel(f"Welcome, {self.user_data['full_name']}")
        welcome_msg.setObjectName("UserWelcome")
        content_layout.addWidget(welcome_msg)
        
        details_msg = QLabel(f"ID: {self.user_data['unique_id']} | Email: {self.user_data['email']}")
        details_msg.setStyleSheet("color: #64748b; font-size: 16px; margin-bottom: 20px;")
        content_layout.addWidget(details_msg)
        
        # Dashboard Cards Grid (Will be used to hold our form layout now instead of dummy data)
        form_container = QFrame()
        form_container.setObjectName("Card")
        form_container.setStyleSheet("""
            QFrame#Card {
                background-color: white; border: 1px solid #e2e8f0; border-radius: 10px;
            }
            QLabel { color: #1e293b; font-weight: bold; font-size: 14px; }
            QLineEdit, QComboBox { padding: 8px; border: 1px solid #cbd5e1; border-radius: 5px; font-size: 14px; }
        """)
        
        form_layout = QGridLayout(form_container)
        form_layout.setSpacing(20)
        
        form_title = QLabel("Manage Hospital Resources")
        form_title.setStyleSheet("font-size: 18px; color: #b91c1c;") # Red accent
        form_layout.addWidget(form_title, 0, 0, 1, 2)
        
        # Load existing data from DB
        res_data = get_hospital_resources(self.user_data['id']) or {}
        
        # Form Elements
        self.icu_total_input = QLineEdit()
        self.icu_total_input.setText(str(res_data.get('icu_beds_total', 0)))
        form_layout.addWidget(QLabel("Total ICU Beds:"), 1, 0)
        form_layout.addWidget(self.icu_total_input, 1, 1)

        self.icu_avail_input = QLineEdit()
        self.icu_avail_input.setText(str(res_data.get('icu_beds_available', 0)))
        form_layout.addWidget(QLabel("Available ICU Beds:"), 2, 0)
        form_layout.addWidget(self.icu_avail_input, 2, 1)
        
        self.oxy_input = QLineEdit()
        self.oxy_input.setText(str(res_data.get('oxygen_percent', 0)))
        self.oxy_input.setPlaceholderText("e.g. 50 (for 50%)")
        form_layout.addWidget(QLabel("Oxygen Stock (%):"), 3, 0)
        form_layout.addWidget(self.oxy_input, 3, 1)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Available", "Critical", "Full", "Unavailable"])
        self.status_combo.setCurrentText(res_data.get('status', 'Unavailable'))
        form_layout.addWidget(QLabel("Hospital Status:"), 4, 0)
        form_layout.addWidget(self.status_combo, 4, 1)
        
        # Save Button
        save_btn = QPushButton("Save Resource Updates")
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb; color: white; border-radius: 6px; font-weight: bold; padding: 12px;
            }
            QPushButton:hover { background-color: #1d4ed8; }
        """)
        save_btn.clicked.connect(self.save_resources)
        form_layout.addWidget(save_btn, 5, 0, 1, 2)
        
        content_layout.addWidget(form_container)
        content_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll_area)
        
        return page

    def save_resources(self):
        try:
            icu_t = int(self.icu_total_input.text() or 0)
            icu_a = int(self.icu_avail_input.text() or 0)
            oxy = int(self.oxy_input.text() or 0)
            status = self.status_combo.currentText()
            
            success = update_hospital_resources(self.user_data['id'], icu_t, icu_a, oxy, status)
            if success:
                QMessageBox.information(self, "Success", "Hospital resources updated successfully.")
            else:
                QMessageBox.warning(self, "Error", "Failed to update database.")
        except ValueError:
            QMessageBox.warning(self, "Error", "Total Beds, Available Beds, and Oxygen must be numeric.")

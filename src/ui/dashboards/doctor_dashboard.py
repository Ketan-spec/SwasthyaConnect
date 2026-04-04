from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QGridLayout, QStackedWidget,
    QSizePolicy, QScrollArea
)
from src.ui.styles import get_sidebar_style, CONTENT_STYLE
from src.ui.components.doctor_list import DoctorListWidget
from src.ui.components.referral_list import ReferralListWidget
from src.services.ai_service import AIService
from src.ui.components.ai_insight_card import AIInsightCard
from src.ui.components.doctor_tabs import (
    DoctorAppointmentsWidget, DoctorReportsWidget, DoctorProfileWidget, 
    DoctorTreatmentWidget, DoctorDiagnosticCopilotWidget
)
from src.database import get_doctor_dashboard_stats

class DoctorDashboard(QWidget):
    def __init__(self, user_data, logout_callback):
        super().__init__()
        self.logout_callback = logout_callback
        self.user_data = user_data
        self.setWindowTitle("Doctor Dashboard")
        self.resize(1200, 800)
        self.setMinimumSize(800, 600)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Sidebar ---
        self.sidebar = QWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(250)
        self.sidebar.setStyleSheet(get_sidebar_style("doctor"))
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        title_label = QLabel("Swasthya\nDoctor Portal")
        title_label.setObjectName("SidebarTitle")
        sidebar_layout.addWidget(title_label)
        
        # Menu Items
        self.menu_btns = {}
        menu_items = ["Overview", "Refer Patient", "My Referrals", "Appointments", "Reports", "Treatment Updates", "AI Copilot", "Profile"]
        
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

        # Page 1: Overview
        self.home_page = self.create_home_page()
        self.stack.addWidget(self.home_page)
        
        # Page 2: Refer Patient
        self.refer_page = DoctorListWidget(mode="refer", current_user_id=self.user_data['id'])
        self.stack.addWidget(self.refer_page)

        # Page 3: My Referrals (Incoming)
        self.referrals_page = ReferralListWidget(current_doctor_id=self.user_data['id'])
        self.stack.addWidget(self.referrals_page)

        # Page 4: Appointments
        self.appointments_page = DoctorAppointmentsWidget(self.user_data['id'])
        self.stack.addWidget(self.appointments_page)

        # Page 5: Reports
        self.reports_page = DoctorReportsWidget(self.user_data['id'])
        self.stack.addWidget(self.reports_page)
        
        # Page 6: Treatment Updates
        self.treatment_page = DoctorTreatmentWidget(self.user_data['id'])
        self.stack.addWidget(self.treatment_page)
        
        # Page 7: AI Copilot
        self.copilot_page = DoctorDiagnosticCopilotWidget(self.user_data['id'])
        self.stack.addWidget(self.copilot_page)
        
        # Page 8: Profile
        self.profile_page = DoctorProfileWidget(self.user_data)
        self.stack.addWidget(self.profile_page)
            
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content_area)
        
        self.setLayout(main_layout)

    def switch_page(self, page_name):
        # Uncheck all others
        for name, btn in self.menu_btns.items():
            if name != page_name:
                btn.setChecked(False)
        
        self.menu_btns[page_name].setChecked(True)
        
        if page_name == "Overview":
            self.stack.setCurrentIndex(0)
        elif page_name == "Refer Patient":
            self.stack.setCurrentIndex(1)
            # Refresh the doctor list in case new doctors signed up
            if hasattr(self, 'refer_page'): 
                self.refer_page.load_doctors()
        elif page_name == "My Referrals":
            self.stack.setCurrentIndex(2)
            # Refresh referrals list
            if hasattr(self, 'referrals_page'):
                self.referrals_page.load_referrals()
        elif page_name == "Appointments":
            self.appointments_page.load_data()
            self.stack.setCurrentIndex(3)
        elif page_name == "Reports":
            self.reports_page.load_data()
            self.stack.setCurrentIndex(4)
        elif page_name == "Treatment Updates":
            self.treatment_page.load_data()
            self.stack.setCurrentIndex(5)
        elif page_name == "AI Copilot":
            self.stack.setCurrentIndex(6)
        elif page_name == "Profile":
            self.stack.setCurrentIndex(7)

    def create_home_page(self):
        page = QWidget()
        
        # Add Scroll Area
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
        
        # Live DB Stats
        stats = get_doctor_dashboard_stats(self.user_data['id'])
        
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        
        stat_data = [
            ("Scheduled Appointments", str(stats['appointments_today']), "#3b82f6"),
            ("Unread Patient Reports", str(stats['unread_reports']), "#ef4444"),
            ("Active Treatments", str(stats['active_treatments']), "#f59e0b")
        ]
        
        for title, val, color in stat_data:
            card = QFrame()
            card.setStyleSheet(f"background-color: white; border-radius: 10px; border-top: 4px solid {color};")
            card.setMinimumHeight(100)
            
            c_layout = QVBoxLayout(card)
            t_lbl = QLabel(title)
            t_lbl.setStyleSheet("color: #64748b; font-size: 14px; font-weight: bold;")
            v_lbl = QLabel(val)
            v_lbl.setStyleSheet(f"color: {color}; font-size: 32px; font-weight: bold;")
            
            c_layout.addWidget(t_lbl)
            c_layout.addWidget(v_lbl)
            cards_layout.addWidget(card)
            
        content_layout.addLayout(cards_layout)
        
        # --- AI Workload Insight ---
        insight_text, category = AIService.analyze_doctor_workload(stats['appointments_today'], stats['active_treatments'])
        ai_card = AIInsightCard(insight_text, category)
        content_layout.addWidget(ai_card)
        # ---------------------------
        content_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll_area)
        
        return page

from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QGridLayout, QStackedWidget,
    QSizePolicy, QScrollArea
)
from src.ui.styles import get_sidebar_style, CONTENT_STYLE
from src.ui.components.chatbot import ChatbotWidget
from src.ui.components.doctor_list import DoctorListWidget
from src.services.ai_service import AIService
from src.ui.components.ai_insight_card import AIInsightCard
from src.ui.components.patient_tabs import (
    RecordsWidget, AppointmentsWidget, PrescriptionsWidget, 
    SettingsWidget, TreatmentStatusWidget, MedicineVerificationWidget
)
from src.database import get_patient_dashboard_stats, get_patient_analytics
import pyqtgraph as pg
from PyQt6.QtCore import Qt

class TrendChartWidget(QWidget):
    def __init__(self, title, data_points):
        super().__init__()
        self.title = title
        self.data_points = data_points # list of dicts: [{'date': '2023-10-01', 'value': 12.0}]
        self.setMinimumSize(300, 250)
        self.setStyleSheet("background-color: white; border-radius: 10px; border: 1px solid #e2e8f0; padding: 5px;")
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Label
        lbl = QLabel(f"{self.title} Trend")
        lbl.setStyleSheet("font-weight: bold; color: #0f766e; font-size: 14px;")
        layout.addWidget(lbl)
        
        if not self.data_points or len(self.data_points) == 0:
            no_data = QLabel("No sufficient data to chart")
            no_data.setStyleSheet("color: #64748b; font-style: italic;")
            no_data.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(no_data)
        else:
            # Setup PlotWidget
            self.plot_widget = pg.PlotWidget(background='w')
            self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
            
            x_data = list(range(len(self.data_points)))
            y_data = [dp['value'] for dp in self.data_points]
            
            # Simple line and symbol
            pen = pg.mkPen(color=(14, 165, 233), width=3) # #0ea5e9
            self.plot_widget.plot(x_data, y_data, pen=pen, symbol='o', symbolSize=10, symbolBrush=(15, 118, 110))
            
            # Add dates as X axis ticks
            ticks = [[(i, dp['date'][-5:]) for i, dp in enumerate(self.data_points)]]
            self.plot_widget.getAxis('bottom').setTicks(ticks)
            self.plot_widget.getAxis('bottom').setPen(pg.mkPen(color=(100, 116, 139)))
            self.plot_widget.getAxis('left').setPen(pg.mkPen(color=(100, 116, 139)))
            self.plot_widget.getAxis('bottom').setTextPen(pg.mkPen(color=(71, 85, 105)))
            self.plot_widget.getAxis('left').setTextPen(pg.mkPen(color=(71, 85, 105)))
            
            layout.addWidget(self.plot_widget)

class PatientDashboard(QWidget):
    def __init__(self, user_data, logout_callback):
        super().__init__()
        self.logout_callback = logout_callback
        self.user_data = user_data
        self.setWindowTitle("Patient Dashboard")
        self.resize(1200, 800)
        self.setMinimumSize(800, 600)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Sidebar ---
        self.sidebar = QWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(250)
        self.sidebar.setStyleSheet(get_sidebar_style("patient"))
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        title_label = QLabel("Swasthya\nConnect")
        title_label.setObjectName("SidebarTitle")
        sidebar_layout.addWidget(title_label)
        
        # Menu Items
        self.menu_btns = {}
        menu_items = ["Dashboard", "AI Assistant", "Find Doctor", "My Records", "Appointments", "Prescriptions", "Treatment Status", "Medicine Verification", "Settings"]
        
        for item in menu_items:
            btn = QPushButton(item)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, i=item: self.switch_page(i))
            self.menu_btns[item] = btn
            sidebar_layout.addWidget(btn)
            
        self.menu_btns["Dashboard"].setChecked(True)
            
        sidebar_layout.addStretch()
        
        # Logout Button
        logout_btn = QPushButton("Logout")
        logout_btn.clicked.connect(self.logout_callback)
        sidebar_layout.addWidget(logout_btn)
        
        # --- Content Area (Stacked Widget) ---
        self.content_area = QWidget()
        self.content_area.setObjectName("ContentArea")
        self.content_area.setStyleSheet(CONTENT_STYLE)
        
        content_main_layout = QVBoxLayout(self.content_area)
        content_main_layout.setContentsMargins(0,0,0,0)
        
        self.stack = QStackedWidget()
        content_main_layout.addWidget(self.stack)
        
        # Page 1: Dashboard Home
        self.home_page = self.create_home_page()
        self.stack.addWidget(self.home_page)
        
        # Page 2: Chatbot
        self.chatbot_page = ChatbotWidget()
        self.stack.addWidget(self.chatbot_page)

        # Page 3: Find Doctor
        self.find_doc_page = DoctorListWidget(mode="find")
        self.stack.addWidget(self.find_doc_page)
        
        # Page 4: My Records
        self.records_page = RecordsWidget(self.user_data['id'])
        self.stack.addWidget(self.records_page)

        # Page 5: Appointments
        self.appointments_page = AppointmentsWidget(self.user_data['id'])
        self.stack.addWidget(self.appointments_page)

        # Page 6: Prescriptions
        self.prescriptions_page = PrescriptionsWidget(self.user_data['id'])
        self.stack.addWidget(self.prescriptions_page)

        # Page 7: Treatment Status
        self.treatment_page = TreatmentStatusWidget(self.user_data['id'])
        self.stack.addWidget(self.treatment_page)

        # Page 8: Medicine Verification
        self.med_verify_page = MedicineVerificationWidget(self.user_data['id'])
        self.stack.addWidget(self.med_verify_page)

        # Page 9: Settings
        self.settings_page = SettingsWidget(self.user_data)
        self.stack.addWidget(self.settings_page)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content_area)
        
        self.setLayout(main_layout)

    def switch_page(self, page_name):
        # Uncheck all others
        for name, btn in self.menu_btns.items():
            if name != page_name:
                btn.setChecked(False)
        
        self.menu_btns[page_name].setChecked(True)
        
        if page_name == "Dashboard":
            self.stack.setCurrentIndex(0)
        elif page_name == "AI Assistant":
            self.stack.setCurrentIndex(1)
        elif page_name == "Find Doctor":
            self.stack.setCurrentIndex(2)
        elif page_name == "My Records":
            self.records_page.load_data()
            self.stack.setCurrentIndex(3)
        elif page_name == "Appointments":
            self.appointments_page.load_data()
            self.stack.setCurrentIndex(4)
        elif page_name == "Prescriptions":
            self.prescriptions_page.load_data()
            self.stack.setCurrentIndex(5)
        elif page_name == "Treatment Status":
            self.treatment_page.load_data()
            self.stack.setCurrentIndex(6)
        elif page_name == "Medicine Verification":
            self.stack.setCurrentIndex(7)
        elif page_name == "Settings":
            self.stack.setCurrentIndex(8)

    def create_home_page(self):
        page = QWidget()
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(40, 40, 40, 40)
        content_layout.setSpacing(20)
        
        welcome_msg = QLabel(f"Welcome back, {self.user_data['full_name']}")
        welcome_msg.setObjectName("UserWelcome")
        welcome_msg.setStyleSheet("font-size: 28px; font-weight: bold; color: #1e293b;")
        content_layout.addWidget(welcome_msg)
        
        details_msg = QLabel(f"Phone: {self.user_data['phone']}")
        details_msg.setStyleSheet("color: #64748b; font-size: 16px; margin-bottom: 20px;")
        content_layout.addWidget(details_msg)
        
        # Real Stats
        stats = get_patient_dashboard_stats(self.user_data['id'])
        
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        
        stat_data = [
            ("Appointments", str(stats['appointments']), "#0ea5e9"),
            ("Medical Records", str(stats['records']), "#8b5cf6"),
            ("Active Treatments", str(stats['treatments']), "#f59e0b")
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
        
        # AI Insight
        mock_vitals = {"appointments": stats['appointments'], "records": stats['records']}
        insight_text, category = AIService.analyze_patient_health(mock_vitals)
        ai_card = AIInsightCard(insight_text, category)
        content_layout.addWidget(ai_card)
        
        # Dynamic patient analytics
        charts_lbl = QLabel("Health Analytics (Extracted from Reports)")
        charts_lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #1e293b; margin-top: 20px;")
        content_layout.addWidget(charts_lbl)
        
        analytics_data = get_patient_analytics(self.user_data['id'])
        
        charts_layout = QGridLayout()
        charts_layout.setSpacing(20)
        
        row, col = 0, 0
        if not analytics_data:
            no_data = QLabel("Upload Smart Reports to see extracted health parameters over time.")
            no_data.setStyleSheet("color: #64748b; font-style: italic;")
            content_layout.addWidget(no_data)
        else:
            for test_name, points in list(analytics_data.items())[:4]: # Show up to 4 charts
                chart = TrendChartWidget(test_name, points)
                charts_layout.addWidget(chart, row, col)
                col += 1
                if col > 1:
                    col = 0
                    row += 1
                    
        content_layout.addLayout(charts_layout)
        content_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll_area)
        
        return page

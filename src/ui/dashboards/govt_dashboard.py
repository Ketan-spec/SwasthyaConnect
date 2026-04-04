from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QGridLayout, QStackedWidget, QScrollArea
)
from src.ui.styles import get_sidebar_style, CONTENT_STYLE
from src.database import get_govt_stats
from src.ui.components.analytics_card import StatCard, DiseaseTrendWidget, ResourceMonitorWidget, InteractiveAnalyticsWidget
from src.ui.components.govt_tabs import GovtReportsWidget
from src.services.ai_service import AIService

class GovtDashboard(QWidget):
    def __init__(self, user_data, logout_callback):
        super().__init__()
        self.logout_callback = logout_callback
        self.user_data = user_data
        self.setWindowTitle("Government Health Admin Portal")
        self.resize(1200, 800)
        self.setMinimumSize(800, 600)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- Sidebar ---
        self.sidebar = QWidget()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(250)
        self.sidebar.setStyleSheet(get_sidebar_style("govt"))
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        
        title_label = QLabel("Swasthya\nAdmin")
        title_label.setObjectName("SidebarTitle")
        sidebar_layout.addWidget(title_label)
        
        # Menu Items
        self.menu_btns = {}
        menu_items = ["Overview", "Health Trends", "Disease Surveillance", "Resource Monitor", "Reports"]
        
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
        
        # Fetch Data
        self.stats = get_govt_stats()

        # Page 1: Overview
        self.overview_page = self.create_overview_page()
        self.stack.addWidget(self.overview_page)
        
        # Page 2: Health Trends
        self.trends_page = InteractiveAnalyticsWidget()
        self.stack.addWidget(self.trends_page)
        
        # Page 3: Disease Surveillance
        self.disease_page = self.create_disease_page()
        self.stack.addWidget(self.disease_page)

        # Page 4: Resource Monitor
        self.resource_page = ResourceMonitorWidget()
        self.stack.addWidget(self.resource_page)
        
        # Page 5: Reports
        self.reports_page = GovtReportsWidget()
        self.stack.addWidget(self.reports_page)
        
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content_area)
        
        self.setLayout(main_layout)

    def switch_page(self, page_name):
        for name, btn in self.menu_btns.items():
             if name != page_name: btn.setChecked(False)
        self.menu_btns[page_name].setChecked(True)
        
        if page_name == "Overview": self.stack.setCurrentIndex(0)
        elif page_name == "Health Trends": self.stack.setCurrentIndex(1)
        elif page_name == "Disease Surveillance": self.stack.setCurrentIndex(2)
        elif page_name == "Resource Monitor": self.stack.setCurrentIndex(3)
        elif page_name == "Reports": 
            self.reports_page.load_data()
            self.stack.setCurrentIndex(4)

    def create_overview_page(self):
        page = QWidget()
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Title
        layout.addWidget(QLabel(f"Welcome, {self.user_data['full_name']} (Admin)"))
        
        # Key Metrics Row
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(20)
        
        metrics_layout.addWidget(StatCard("Registered Patients", self.stats['total_patients'], "#2563eb"))
        metrics_layout.addWidget(StatCard("Active Doctors", self.stats['total_doctors'], "#059669"))
        metrics_layout.addWidget(StatCard("Hospitals", self.stats['total_hospitals'], "#d97706"))
        metrics_layout.addWidget(StatCard("Total Referrals", self.stats['recent_referrals'], "#7c3aed"))
        
        layout.addLayout(metrics_layout)
        
        # AI Policy Insight
        layout.addSpacing(30)
        insight_frame = QFrame()
        insight_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #4c1d95, stop:1 #8b5cf6);
                border-radius: 10px;
                padding: 20px;
            }
            QLabel { color: white; }
        """)
        ilayout = QVBoxLayout(insight_frame)
        ilayout.addWidget(QLabel("🤖 AI Policy Insight (Beta)"))
        
        insight_text = AIService.analyze_govt_trends(self.stats.get('disease_trends', []))
        msg = QLabel(insight_text)
        msg.setWordWrap(True)
        msg.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 5px;")
        ilayout.addWidget(msg)
        
        layout.addWidget(insight_frame)
        layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll_area)
        
        return page

    def create_disease_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        
        # Re-fetch stats to get fresh disease trends
        current_stats = get_govt_stats() 
        trends_widget = DiseaseTrendWidget(current_stats['disease_trends'])
        
        layout.addWidget(trends_widget)
        layout.addStretch()
        return page

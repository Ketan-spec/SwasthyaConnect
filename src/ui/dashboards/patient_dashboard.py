from PyQt6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QGridLayout, QStackedWidget,
    QSizePolicy, QScrollArea, QComboBox
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
from src.database import (
    get_patient_dashboard_stats, get_patient_analytics, get_aggregated_patient_data, 
    get_patient_disease_trend, get_patient_vitals_timeline, get_active_medications_count,
    get_patient_timeline, set_user_language, get_user_language
)
from src.services.translation_service import SUPPORTED_LANGS
from src.services.ui_localization import get_localized_ui_string
import pyqtgraph as pg
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath
import random

class RadialProgress(QWidget):
    def __init__(self, percentage, title):
        super().__init__()
        self.percentage = percentage
        self.title = title
        self.setMinimumSize(120, 150)
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = QRectF(10, 10, 100, 100)
        
        # Background circle
        painter.setPen(QPen(QColor("#e2e8f0"), 10))
        painter.drawArc(rect, 0, 360 * 16)
        
        # Foreground arc
        painter.setPen(QPen(QColor("#0ea5e9"), 10, cap=Qt.PenCapStyle.RoundCap))
        span_angle = int((self.percentage / 100) * 360 * 16)
        painter.drawArc(rect, 90 * 16, -span_angle)
        
        # Text
        painter.setPen(QColor("#1e293b"))
        painter.setFont(QFont("Inter", 16, QFont.Weight.Bold))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{self.percentage}%")
        
        painter.setFont(QFont("Inter", 10))
        painter.setPen(QColor("#64748b"))
        painter.drawText(0, 130, 120, 20, Qt.AlignmentFlag.AlignCenter, self.title)


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
        
        # Language Selector in sidebar
        lang_frame = QFrame()
        lang_frame.setStyleSheet("background: rgba(255,255,255,0.08); padding: 5px; margin: 5px;")
        lang_layout = QHBoxLayout(lang_frame)
        lang_layout.setContentsMargins(8, 4, 8, 4)
        lang_lbl = QLabel("🌐")
        lang_lbl.setStyleSheet("color: white; font-size: 16px;")
        self.lang_combo = QComboBox()
        self.lang_combo.setStyleSheet("background: white; color: #1e293b; padding: 3px; border-radius: 3px; font-size: 12px;")
        for code, name in SUPPORTED_LANGS.items():
            self.lang_combo.addItem(name, code)
        # Set current language from DB
        self.current_lang = get_user_language(self.user_data['id']) or "en"
        self.lang_combo.blockSignals(True)
        for i in range(self.lang_combo.count()):
            if self.lang_combo.itemData(i) == self.current_lang:
                self.lang_combo.setCurrentIndex(i)
                break
        self.lang_combo.blockSignals(False)
        self.lang_combo.currentIndexChanged.connect(self._on_language_changed)
        lang_layout.addWidget(lang_lbl)
        lang_layout.addWidget(self.lang_combo)
        sidebar_layout.addWidget(lang_frame)
        
        # Menu Items
        self.menu_btns = {}
        menu_items = ["Dashboard", "AI Assistant", "Find Doctor", "My Records", "Appointments", "Prescriptions", "Treatment Status", "Medicine Verification", "🔗 Health Integrity", "Settings"]
        
        for item in menu_items:
            btn = QPushButton(item)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, i=item: self.switch_page(i))
            self.menu_btns[item] = btn
            sidebar_layout.addWidget(btn)
            
        self.menu_btns["Dashboard"].setChecked(True)
            
        sidebar_layout.addStretch()
        
        # Logout Button
        self.logout_btn = QPushButton("Logout")
        self.logout_btn.clicked.connect(self.logout_callback)
        sidebar_layout.addWidget(self.logout_btn)
        
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
        self.find_doc_page = DoctorListWidget(mode="find", current_user_id=self.user_data['id'])
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

        # Page 9: Health Record Integrity (Blockchain)
        try:
            from src.ui.components.blockchain_viewer import BlockchainViewerWidget
            self.blockchain_page = BlockchainViewerWidget(self.user_data['id'])
        except Exception as e:
            self.blockchain_page = QLabel(f"Blockchain viewer error: {e}")
        self.stack.addWidget(self.blockchain_page)

        # Page 10: Settings
        self.settings_page = SettingsWidget(self.user_data)
        self.stack.addWidget(self.settings_page)

        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.content_area)
        
        self.setLayout(main_layout)
        
        # Apply current language across the entire UI
        self.apply_language(self.current_lang)

    def _on_language_changed(self, index):
        """Save language preference to DB and instantly localize entire UI."""
        lang_code = self.lang_combo.itemData(index)
        if lang_code:
            set_user_language(self.user_data['id'], lang_code)
            self.current_lang = lang_code
            self.apply_language(lang_code)

    def apply_language(self, lang_code):
        """Apply language changes across sidebar, home page, and all child widgets."""
        self.current_lang = lang_code
        
        # 1. Update Sidebar Menu Buttons
        for item, btn in self.menu_btns.items():
            btn.setText(get_localized_ui_string(item, lang_code))
        if hasattr(self, 'logout_btn'):
            self.logout_btn.setText(get_localized_ui_string("Logout", lang_code))
            
        # 2. Re-create and replace Home Page in stacked widget
        if hasattr(self, 'stack') and hasattr(self, 'home_page'):
            curr_idx = self.stack.currentIndex()
            old_home = self.home_page
            self.home_page = self.create_home_page()
            self.stack.removeWidget(old_home)
            old_home.deleteLater()
            self.stack.insertWidget(0, self.home_page)
            if curr_idx == 0:
                self.stack.setCurrentIndex(0)
                
        # 3. Propagate to child tab pages
        pages = [
            getattr(self, 'records_page', None),
            getattr(self, 'appointments_page', None),
            getattr(self, 'prescriptions_page', None),
            getattr(self, 'treatment_page', None),
            getattr(self, 'med_verify_page', None),
            getattr(self, 'settings_page', None),
            getattr(self, 'find_doc_page', None),
            getattr(self, 'chatbot_page', None),
        ]
        for p in pages:
            if p and hasattr(p, 'apply_language'):
                try:
                    p.apply_language(lang_code)
                except Exception as e:
                    print(f"Error applying language to page {p}: {e}")

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
        elif page_name == "🔗 Health Integrity":
            # Refresh blockchain data on each visit
            if hasattr(self.blockchain_page, 'load_data'):
                self.blockchain_page.load_data()
            self.stack.setCurrentIndex(8)
        elif page_name == "Settings":
            self.stack.setCurrentIndex(9)

    def create_home_page(self):
        page = QWidget()
        page.setStyleSheet("background-color: #f0f4f8;")
        lang = getattr(self, 'current_lang', None) or get_user_language(self.user_data['id']) or 'en'
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(25)
        
        # ── Welcome Header ──
        header_layout = QVBoxLayout()
        import datetime
        hour = datetime.datetime.now().hour
        greeting_key = "Good morning" if hour < 12 else ("Good afternoon" if hour < 17 else "Good evening")
        greeting = get_localized_ui_string(greeting_key, lang)
        welcome_msg = QLabel(f"{greeting}, {self.user_data['full_name']}")
        welcome_msg.setStyleSheet("font-size: 32px; font-weight: 800; color: #0f172a;")
        header_layout.addWidget(welcome_msg)
        
        subtitle = QLabel(get_localized_ui_string("subtitle", lang))
        subtitle.setStyleSheet("font-size: 16px; color: #64748b;")
        header_layout.addWidget(subtitle)
        content_layout.addLayout(header_layout)
        
        # ── 1. Top Health Summary Cards ──
        stats = get_patient_dashboard_stats(self.user_data['id'])
        agg_data = get_aggregated_patient_data(self.user_data['id'])
        med_count = get_active_medications_count(self.user_data['id'])
        
        top_cards_layout = QGridLayout()
        top_cards_layout.setSpacing(15)
        
        risk_score = agg_data["risk_score"]
        score_color = "#10b981" if risk_score > 70 else ("#f59e0b" if risk_score > 40 else "#ef4444")
        active_conditions_count = len(agg_data["conditions"])
        
        raw_risk = ("Low" if risk_score > 60 else "Elevated") if agg_data["has_data"] else "N/A"
        risk_display = get_localized_ui_string(raw_risk, lang) if raw_risk in ("Low", "Elevated") else raw_risk
        
        card_data = [
            ("Health Stability", f"{risk_score}/100" if agg_data["has_data"] else "N/A", score_color, "AI assessment"),
            ("Active Conditions", str(active_conditions_count), "#f59e0b", "Currently tracked"),
            ("Active Medications", str(med_count), "#8b5cf6", "From prescriptions"),
            ("Reports Uploaded", str(agg_data['record_count']), "#0ea5e9", "Analyzer status"),
            ("Appointments", str(stats['appointments']), "#6366f1", "Total visits"),
            ("Emergency Risk", risk_display, score_color, "Based on vitals"),
        ]
        
        row, col = 0, 0
        for title, val, color, sub in card_data:
            c = QFrame()
            c.setObjectName("Card")
            c.setMinimumHeight(100)
            c.setStyleSheet("""
                QFrame#Card {
                    background-color: white;
                    border: 1px solid #e2e8f0;
                    border-radius: 12px;
                    padding: 15px;
                }
                QFrame#Card:hover {
                    border-color: #3b82f6;
                }
            """)
            cl = QVBoxLayout(c)
            t_lbl = QLabel(get_localized_ui_string(title, lang))
            t_lbl.setStyleSheet("color: #64748b; font-size: 12px; font-weight: bold; text-transform: uppercase;")
            v_lbl = QLabel(val)
            v_lbl.setStyleSheet(f"color: {color}; font-size: 26px; font-weight: 800;")
            s_lbl = QLabel(get_localized_ui_string(sub, lang))
            s_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
            cl.addWidget(t_lbl)
            cl.addWidget(v_lbl)
            cl.addWidget(s_lbl)
            top_cards_layout.addWidget(c, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1
                
        content_layout.addLayout(top_cards_layout)
        
        # ── 2. Date-Based Medical Timeline (Main Section) ──
        timeline_header = QLabel(get_localized_ui_string("Medical History Timeline", lang))
        timeline_header.setStyleSheet("font-size: 20px; font-weight: bold; color: #1e293b; margin-top: 15px;")
        content_layout.addWidget(timeline_header)
        
        timeline_data = get_patient_timeline(self.user_data['id'])
        
        if timeline_data:
            timeline_container = QFrame()
            timeline_container.setStyleSheet("background: white; border-radius: 12px; border: 1px solid #e2e8f0; padding: 15px;")
            timeline_layout = QVBoxLayout(timeline_container)
            timeline_layout.setSpacing(0)
            
            # Group by date
            current_date = None
            shown_count = 0
            max_events = 15  # Limit to prevent overload
            
            for event in timeline_data:
                if shown_count >= max_events:
                    break
                
                event_date = event["date"]
                
                # Date separator
                if event_date != current_date:
                    current_date = event_date
                    date_label = QLabel(f"📅 {event_date}" if event_date else "📅 Unknown Date")
                    date_label.setStyleSheet("""
                        font-size: 14px; font-weight: bold; color: #0f766e; 
                        background-color: #f0fdfa; padding: 8px 12px; border-radius: 6px;
                        margin-top: 10px; margin-bottom: 5px;
                    """)
                    timeline_layout.addWidget(date_label)
                
                # Event card
                event_frame = QFrame()
                source = event.get("source", "record")
                if source == "record":
                    border_color = "#0ea5e9"
                    icon = "📋" if event["type"] == "Report" else "💊"
                elif source == "appointment":
                    border_color = "#8b5cf6"
                    icon = "🩺"
                else:
                    border_color = "#f59e0b"
                    icon = "🏥"
                
                event_frame.setStyleSheet(f"""
                    QFrame {{
                        background: #fafafa;
                        border-left: 4px solid {border_color};
                        border-radius: 6px;
                        padding: 10px;
                        margin-left: 20px;
                        margin-bottom: 4px;
                    }}
                """)
                ev_layout = QVBoxLayout(event_frame)
                ev_layout.setContentsMargins(10, 6, 10, 6)
                ev_layout.setSpacing(3)
                
                # Title row
                title_row = QHBoxLayout()
                ev_icon = QLabel(icon)
                ev_icon.setStyleSheet("font-size: 16px;")
                ev_title = QLabel(str(event["title"])[:60])
                ev_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #1e293b;")
                ev_type = QLabel(str(event["type"]))
                ev_type.setStyleSheet(f"color: {border_color}; font-size: 11px; font-weight: bold; background: #f1f5f9; padding: 2px 8px; border-radius: 3px;")
                title_row.addWidget(ev_icon)
                title_row.addWidget(ev_title)
                title_row.addStretch()
                title_row.addWidget(ev_type)
                ev_layout.addLayout(title_row)
                
                # Description
                if event.get("description"):
                    desc_lbl = QLabel(str(event["description"])[:100])
                    desc_lbl.setStyleSheet("color: #64748b; font-size: 12px;")
                    desc_lbl.setWordWrap(True)
                    ev_layout.addWidget(desc_lbl)
                
                # Diagnosis chips
                diagnosis = event.get("diagnosis", [])
                if diagnosis:
                    diag_row = QHBoxLayout()
                    for d in diagnosis[:3]:
                        if d:
                            chip = QLabel(str(d)[:30])
                            chip.setStyleSheet("background: #fef3c7; color: #92400e; padding: 2px 8px; border-radius: 10px; font-size: 11px;")
                            diag_row.addWidget(chip)
                    diag_row.addStretch()
                    ev_layout.addLayout(diag_row)
                
                # Key findings
                findings = event.get("key_findings", [])
                if findings:
                    for f in findings[:2]:
                        if f:
                            f_lbl = QLabel(f"  • {str(f)[:80]}")
                            f_lbl.setStyleSheet("color: #475569; font-size: 11px;")
                            f_lbl.setWordWrap(True)
                            ev_layout.addWidget(f_lbl)
                
                timeline_layout.addWidget(event_frame)
                shown_count += 1
            
            if len(timeline_data) > max_events:
                more_lbl = QLabel(get_localized_ui_string("more_events_template", lang).format(count=len(timeline_data) - max_events))
                more_lbl.setStyleSheet("color: #64748b; font-style: italic; padding: 10px;")
                timeline_layout.addWidget(more_lbl)
            
            content_layout.addWidget(timeline_container)
        else:
            no_timeline = QLabel(get_localized_ui_string("No medical history found. Upload reports or book appointments to see your timeline here.", lang))
            no_timeline.setStyleSheet("color: #64748b; font-style: italic; padding: 20px; background: white; border-radius: 10px; border: 1px solid #e2e8f0;")
            content_layout.addWidget(no_timeline)
        
        # ── 3. Disease Trend + Vitals Charts ──
        middle_layout = QHBoxLayout()
        middle_layout.setSpacing(20)
        
        # Disease Trend Chart
        trend_card = QFrame()
        trend_card.setObjectName("Card")
        trend_card.setStyleSheet("QFrame#Card { background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 10px; }")
        trend_layout = QVBoxLayout(trend_card)
        tl = QLabel(get_localized_ui_string("Disease / Diagnosis Trend", lang))
        tl.setStyleSheet("font-weight: bold; font-size: 16px;")
        trend_layout.addWidget(tl)
        
        disease_trend = get_patient_disease_trend(self.user_data['id'])
        if disease_trend:
            bar_chart = pg.PlotWidget()
            bar_chart.setBackground("#f8fafc")
            bar_chart.setFixedHeight(200)
            bar_chart.getPlotItem().getAxis("bottom").setStyle(tickTextOffset=5)
            
            labels = list(disease_trend.keys())[:8]
            counts = [disease_trend[l] for l in labels]
            x_positions = list(range(len(labels)))
            
            bar_item = pg.BarGraphItem(x=x_positions, height=counts, width=0.6, brush="#0ea5e9")
            bar_chart.addItem(bar_item)
            
            ax = bar_chart.getPlotItem().getAxis("bottom")
            ax.setTicks([[(i, lbl[:12]) for i, lbl in enumerate(labels)]])
            bar_chart.getPlotItem().setLabel("left", "Occurrences")
            trend_layout.addWidget(bar_chart)
        else:
            trend_layout.addWidget(QLabel(get_localized_ui_string("Upload reports to see disease trends.", lang)))
        middle_layout.addWidget(trend_card, 2)
        
        # Vitals Timeline
        vitals_card = QFrame()
        vitals_card.setObjectName("Card")
        vitals_card.setStyleSheet("QFrame#Card { background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 10px; }")
        vitals_layout = QVBoxLayout(vitals_card)
        vl = QLabel(get_localized_ui_string("Vitals Timeline", lang))
        vl.setStyleSheet("font-weight: bold; font-size: 16px;")
        vitals_layout.addWidget(vl)
        
        vitals_timeline = get_patient_vitals_timeline(self.user_data['id'])
        if vitals_timeline:
            hr_points = []
            for entry in vitals_timeline:
                hr_raw = entry.get("heart_rate")
                date = entry.get("date", "")
                if hr_raw and str(hr_raw).lower() not in ("null", "none", ""):
                    try:
                        hr_val = float(str(hr_raw).replace(" bpm", "").replace("bpm", "").strip())
                        hr_points.append({"date": date, "value": hr_val})
                    except (ValueError, AttributeError):
                        pass
            if hr_points:
                tc = TrendChartWidget(get_localized_ui_string("Heart Rate (bpm)", lang), hr_points)
                tc.setFixedHeight(160)
                vitals_layout.addWidget(tc)
            else:
                vitals_layout.addWidget(QLabel(get_localized_ui_string("No HR data extracted yet.", lang)))
        else:
            no_v = QLabel(get_localized_ui_string("No vitals extracted yet.\nUpload reports to populate.", lang))
            no_v.setStyleSheet("color: #64748b;")
            vitals_layout.addWidget(no_v)
            
        middle_layout.addWidget(vitals_card, 1)
        content_layout.addLayout(middle_layout)
        
        # ── 4. Bottom Row: Recent Reports + Key Findings + AI Summary ──
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(20)
        
        # Recent Reports mini-list
        recent_card = QFrame()
        recent_card.setStyleSheet("background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 15px;")
        recent_layout = QVBoxLayout(recent_card)
        rl = QLabel(get_localized_ui_string("Recent Reports", lang))
        rl.setStyleSheet("font-weight: bold; font-size: 16px; color: #0f766e;")
        recent_layout.addWidget(rl)
        
        # Show last 5 records from timeline
        report_events = [e for e in (timeline_data or []) if e.get("source") == "record"][:5]
        if report_events:
            for ev in report_events:
                r_frame = QFrame()
                r_frame.setStyleSheet("background: #f8fafc; border-radius: 6px; padding: 8px; margin-bottom: 4px; border: 1px solid #e2e8f0;")
                r_layout = QHBoxLayout(r_frame)
                r_layout.setContentsMargins(8, 4, 8, 4)
                r_date = QLabel(ev["date"])
                r_date.setStyleSheet("color: #64748b; font-size: 11px; font-weight: bold;")
                r_title = QLabel(ev["title"][:35])
                r_title.setStyleSheet("color: #1e293b; font-size: 13px;")
                r_type = QLabel(ev["type"])
                r_type.setStyleSheet("color: #0d9488; font-size: 10px;")
                r_layout.addWidget(r_date)
                r_layout.addWidget(r_title)
                r_layout.addStretch()
                r_layout.addWidget(r_type)
                recent_layout.addWidget(r_frame)
        else:
            recent_layout.addWidget(QLabel(get_localized_ui_string("No reports uploaded yet.", lang)))
        recent_layout.addStretch()
        bottom_layout.addWidget(recent_card, 1)
        
        # Key Findings & Vitals
        f_card = QFrame()
        f_card.setStyleSheet("background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 15px;")
        f_layout = QVBoxLayout(f_card)
        f_title = QLabel(get_localized_ui_string("Key Findings & Vital Signs", lang))
        f_title.setStyleSheet("font-weight: bold; font-size: 16px; color: #0f766e;")
        f_layout.addWidget(f_title)
        
        if agg_data["key_findings"] or agg_data["vital_signs"]:
            combined_findings = agg_data["key_findings"][:5] + agg_data["vital_signs"][:5]
            findings_text = "\n".join([f"• {f}" for f in combined_findings])
        else:
            findings_text = get_localized_ui_string("No detailed findings available.\nUpload a report to extract vitals and findings.", lang)
            
        ft_lbl = QLabel(findings_text)
        ft_lbl.setWordWrap(True)
        ft_lbl.setStyleSheet("font-size: 13px; line-height: 1.5; color: #334155;")
        f_layout.addWidget(ft_lbl)
        f_layout.addStretch()
        bottom_layout.addWidget(f_card, 1)
        
        # AI Doctor Summary
        doc_card = QFrame()
        doc_card.setStyleSheet("background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 12px; padding: 15px;")
        doc_layout = QVBoxLayout(doc_card)
        dl = QLabel(get_localized_ui_string("AI Health Summary", lang))
        dl.setStyleSheet("font-weight: bold; font-size: 16px; color: #0f766e;")
        doc_layout.addWidget(dl)
        
        if agg_data["recent_summaries"]:
            summary_text = " ".join(agg_data["recent_summaries"][:3])
        else:
            summary_text = get_localized_ui_string("No recent summaries available. Please upload reports to generate AI insights.", lang)
            
        dt = QLabel(summary_text)
        dt.setWordWrap(True)
        dt.setStyleSheet("font-size: 13px; line-height: 1.5; color: #334155;")
        doc_layout.addWidget(dt)
        doc_layout.addStretch()
        bottom_layout.addWidget(doc_card, 1)
        
        content_layout.addLayout(bottom_layout)
        content_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll_area)
        
        return page

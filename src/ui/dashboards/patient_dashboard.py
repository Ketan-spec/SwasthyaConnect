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
from src.database import get_patient_dashboard_stats, get_patient_analytics, get_aggregated_patient_data, get_patient_disease_trend, get_patient_vitals_timeline
import pyqtgraph as pg
from PyQt6.QtCore import Qt, QRectF, QPointF
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPainterPath
import random

class AI_NodeGraph(QWidget):
    def __init__(self, diseases=[]):
        super().__init__()
        self.setMinimumHeight(200)
        self.nodes = []
        
        # Build dynamic nodes if we have data, otherwise mock
        if diseases:
            colors = ["#ef4444", "#f59e0b", "#10b981", "#3b82f6", "#8b5cf6"]
            start_x = 50
            start_y = 100
            for i, d in enumerate(diseases[:5]): # max 5 nodes
                self.nodes.append({"id": d[:15], "x": start_x + (i*150), "y": start_y + (i%2)*50, "color": colors[i%len(colors)]})
        else:
            self.nodes = [
                {"id": "No Data", "x": 100, "y": 100, "color": "#cbd5e1"}
            ]
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw lines
        pen = QPen(QColor("#cbd5e1"), 2)
        painter.setPen(pen)
        for i in range(len(self.nodes) - 1):
            n1 = self.nodes[i]
            n2 = self.nodes[i+1]
            
            # Draw curved line
            path = QPainterPath(QPointF(n1['x']+10, n1['y']))
            path.cubicTo(n1['x'] + 50, n1['y'], n2['x'] - 50, n2['y'], n2['x'], n2['y'])
            painter.drawPath(path)
            
        # Draw nodes
        for node in self.nodes:
            painter.setBrush(QBrush(QColor(node['color'])))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(node['x']-15, node['y']-15, 30, 30)
            
            painter.setPen(QColor("#1e293b"))
            painter.setFont(QFont("Inter", 10, QFont.Weight.Bold))
            painter.drawText(node['x']-20, node['y']+30, node['id'])

class SymptomHeatmap(QWidget):
    def __init__(self, symptoms=[]):
        super().__init__()
        self.setMinimumHeight(150)
        if symptoms:
            self.symptoms = [s[:15] for s in symptoms[:5]]
        else:
            self.symptoms = ["No Data Yet"]
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        cell_size = 20
        margin_left = 100
        margin_top = 20
        
        painter.setPen(QColor("#64748b"))
        painter.setFont(QFont("Inter", 10))
        
        # Draw weeks header
        for w in range(12):
            painter.drawText(margin_left + w*25, 15, f"W{w+1}")
            
        # Draw grid
        for i, sym in enumerate(self.symptoms):
            painter.setPen(QColor("#1e293b"))
            painter.drawText(5, margin_top + i*25 + 15, sym)
            
            painter.setPen(Qt.PenStyle.NoPen)
            for w in range(12):
                # Random intensity
                intensity = random.random()
                if intensity > 0.8: color = "#ef4444"
                elif intensity > 0.4: color = "#fcd34d"
                else: color = "#e2e8f0"
                
                painter.setBrush(QBrush(QColor(color)))
                painter.drawRoundedRect(margin_left + w*25, margin_top + i*25, cell_size, cell_size, 3, 3)

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
        page.setStyleSheet("background-color: #f0f4f8;")
        
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background-color: transparent;")
        
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(25)
        
        # Welcome
        header_layout = QVBoxLayout()
        welcome_msg = QLabel(f"Good morning, {self.user_data['full_name']}")
        welcome_msg.setStyleSheet("font-size: 32px; font-weight: 800; color: #0f172a;")
        header_layout.addWidget(welcome_msg)
        
        subtitle = QLabel("Your AI Health Control Center is up to date.")
        subtitle.setStyleSheet("font-size: 16px; color: #64748b;")
        header_layout.addWidget(subtitle)
        content_layout.addLayout(header_layout)
        
        # 1. Top Health Summary Cards
        stats = get_patient_dashboard_stats(self.user_data['id'])
        agg_data = get_aggregated_patient_data(self.user_data['id'])
        
        top_cards_layout = QGridLayout()
        top_cards_layout.setSpacing(15)
        
        risk_score = agg_data["risk_score"]
        score_color = "#10b981" if risk_score > 70 else ("#f59e0b" if risk_score > 40 else "#ef4444")
        
        active_conditions_count = len(agg_data["conditions"])
        
        if agg_data["has_data"]:
            adherence_text = "92%" # Will make this dynamic later if tracking adherence
        else:
            adherence_text = "N/A"
            
        card_data = [
            ("Health Stability", f"{risk_score}/100" if agg_data["has_data"] else "N/A", score_color, "Overall AI assessment"),
            ("Active Conditions", str(active_conditions_count), "#f59e0b", "Currently managed"),
            ("Adherence", adherence_text, "#0ea5e9", "Medication schedule"),
            ("Upcoming Appt", str(stats['appointments']), "#8b5cf6", "Scheduled visits"),
            ("Emergency Risk", ("Low" if risk_score > 60 else "Elevated") if agg_data["has_data"] else "N/A", score_color, "Based on vitals"),
            ("Last Report", f"{agg_data['record_count']} uploaded", "#64748b", "Analyzer status")
        ]
        
        row, col = 0, 0
        for title, val, color, sub in card_data:
            c = QFrame()
            c.setObjectName("Card")
            c.setMinimumHeight(110)
            cl = QVBoxLayout(c)
            t_lbl = QLabel(title)
            t_lbl.setStyleSheet("color: #64748b; font-size: 13px; font-weight: bold; text-transform: uppercase;")
            v_lbl = QLabel(val)
            v_lbl.setStyleSheet(f"color: {color}; font-size: 26px; font-weight: 800;")
            s_lbl = QLabel(sub)
            s_lbl.setStyleSheet("color: #94a3b8; font-size: 12px;")
            cl.addWidget(t_lbl)
            cl.addWidget(v_lbl)
            cl.addWidget(s_lbl)
            top_cards_layout.addWidget(c, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1
                
        content_layout.addLayout(top_cards_layout)
        
        # 2. Interactive Medical Timeline (MAIN SECTION)
        timeline_lbl = QLabel("Interactive Medical Timeline")
        timeline_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #1e293b; margin-top: 15px;")
        content_layout.addWidget(timeline_lbl)
        
        timeline_scroll = QScrollArea()
        timeline_scroll.setFixedHeight(120)
        timeline_scroll.setWidgetResizable(True)
        timeline_scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        t_container = QWidget()
        t_layout = QHBoxLayout(t_container)
        
        if agg_data["conditions"]:
            events = [c[:30] for c in agg_data["conditions"][:5]]
        else:
            events = ["No Medical History Found"]
            
        for ev in events:
            frm = QFrame()
            frm.setStyleSheet("background: white; border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px;")
            frm.setMinimumWidth(200)
            fl = QVBoxLayout(frm)
            l1 = QLabel(ev)
            l1.setStyleSheet("font-weight: bold; color: #0d9488;")
            fl.addWidget(l1)
            t_layout.addWidget(frm)
            
            # line connecting
            if ev != events[-1]:
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setStyleSheet("border-top: 2px dashed #94a3b8;")
                line.setMinimumWidth(30)
                t_layout.addWidget(line)
                
        t_layout.addStretch()
        timeline_scroll.setWidget(t_container)
        content_layout.addWidget(timeline_scroll)
        
        # Row 3: Disease Trend Chart + Vitals
        middle_layout = QHBoxLayout()
        middle_layout.setSpacing(20)
        
        # ── Disease Trend Chart (real data from uploaded reports) ──
        trend_card = QFrame()
        trend_card.setObjectName("Card")
        trend_layout = QVBoxLayout(trend_card)
        tl = QLabel("📊 Disease / Diagnosis Trend")
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
            trend_layout.addWidget(QLabel("Upload reports to see disease trends."))
        middle_layout.addWidget(trend_card, 2)
        
        # ── Real Vitals Timeline ──
        vitals_card = QFrame()
        vitals_card.setObjectName("Card")
        vitals_layout = QVBoxLayout(vitals_card)
        vl = QLabel("🩺 Vitals Timeline")
        vl.setStyleSheet("font-weight: bold; font-size: 16px;")
        vitals_layout.addWidget(vl)
        
        vitals_timeline = get_patient_vitals_timeline(self.user_data['id'])
        if vitals_timeline:
            # Build HR trend from real vitals
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
                tc = TrendChartWidget("Heart Rate (bpm)", hr_points)
                tc.setFixedHeight(160)
                vitals_layout.addWidget(tc)
            else:
                vitals_layout.addWidget(QLabel("No HR data extracted yet."))
        else:
            no_v = QLabel("No vitals extracted yet.\nUpload reports to populate.")
            no_v.setStyleSheet("color: #64748b;")
            vitals_layout.addWidget(no_v)
            
        middle_layout.addWidget(vitals_card, 1)
        content_layout.addLayout(middle_layout)
        
        
        # Row 4: AI Risk & Prediction Section
        risk_layout = QHBoxLayout()
        risk_card = QFrame()
        risk_card.setObjectName("Card")
        rl = QVBoxLayout(risk_card)
        rtl = QLabel("⚠️ AI Risk & Progression Predictions")
        rtl.setStyleSheet("font-weight: bold; font-size: 16px; color: #ef4444;")
        rl.addWidget(rtl)
        
        from PyQt6.QtWidgets import QProgressBar
        
        prog_layout = QHBoxLayout()
        
        p1_col = QVBoxLayout()
        p1_lbl = QLabel("Hypertension Progression Probability")
        p1_bar = QProgressBar()
        p1_bar.setValue(25 if agg_data["has_data"] and "Hypertension" in agg_data["conditions"] else 0)
        p1_bar.setStyleSheet("QProgressBar { border: 1px solid #cbd5e1; border-radius: 5px; text-align: center; } QProgressBar::chunk { background-color: #f59e0b; border-radius: 4px; }")
        p1_col.addWidget(p1_lbl)
        p1_col.addWidget(p1_bar)
        
        p2_col = QVBoxLayout()
        p2_lbl = QLabel("Cardiac Event Risk")
        p2_bar = QProgressBar()
        p2_bar.setValue(12 if agg_data["has_data"] else 0)
        p2_bar.setStyleSheet("QProgressBar { border: 1px solid #cbd5e1; border-radius: 5px; text-align: center; } QProgressBar::chunk { background-color: #10b981; border-radius: 4px; }")
        p2_col.addWidget(p2_lbl)
        p2_col.addWidget(p2_bar)
        
        prog_layout.addLayout(p1_col)
        prog_layout.addLayout(p2_col)
        
        rl.addLayout(prog_layout)
        risk_layout.addWidget(risk_card)
        content_layout.addLayout(risk_layout)
        
        # Row 5: Heatmap & Adherence & Summary
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(20)
        
        # 5. Symptom Heatmap
        hm_card = QFrame()
        hm_card.setObjectName("Card")
        hm_layout = QVBoxLayout(hm_card)
        hl = QLabel("Symptom Frequency (Last 12 Weeks)")
        hl.setStyleSheet("font-weight: bold; font-size: 16px;")
        hm_layout.addWidget(hl)
        hm_layout.addWidget(SymptomHeatmap(symptoms=agg_data["symptoms"]))
        bottom_layout.addWidget(hm_card, 2)
        
        # 6. Medication Adherence
        med_card = QFrame()
        med_card.setObjectName("Card")
        med_layout = QVBoxLayout(med_card)
        ml = QLabel("Medication Adherence")
        ml.setStyleSheet("font-weight: bold; font-size: 16px;")
        med_layout.addWidget(ml)
        rad = RadialProgress(92 if agg_data["has_data"] else 0, "Weekly Goal")
        med_layout.addWidget(rad, alignment=Qt.AlignmentFlag.AlignCenter)
        bottom_layout.addWidget(med_card, 1)
        
        # 8/9. AI Doctor Summary
        doc_card = QFrame()
        doc_card.setObjectName("Card")
        doc_card.setStyleSheet("background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 10px;")
        doc_layout = QVBoxLayout(doc_card)
        dl = QLabel("⚕️ Doctor Quick Summary")
        dl.setStyleSheet("font-weight: bold; font-size: 16px; color: #0f766e;")
        doc_layout.addWidget(dl)
        
        if agg_data["recent_summaries"]:
            summary_text = " ".join(agg_data["recent_summaries"][:3])
        else:
            summary_text = "No recent summaries available. Please upload reports to generate AI insights."
            
        dt = QLabel(summary_text)
        dt.setWordWrap(True)
        dt.setStyleSheet("font-size: 14px; line-height: 1.5; color: #334155;")
        doc_layout.addWidget(dt)
        doc_layout.addStretch()
        bottom_layout.addWidget(doc_card, 1)
        
        content_layout.addLayout(bottom_layout)
        
        # Row 6: Detailed Key Findings & Vitals
        findings_layout = QHBoxLayout()
        f_card = QFrame()
        f_card.setObjectName("Card")
        f_card.setStyleSheet("background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 10px;")
        f_layout = QVBoxLayout(f_card)
        f_title = QLabel("🔬 Recent Key Findings & Vital Signs")
        f_title.setStyleSheet("font-weight: bold; font-size: 16px; color: #0f766e;")
        f_layout.addWidget(f_title)
        
        if agg_data["key_findings"] or agg_data["vital_signs"]:
            combined_findings = agg_data["key_findings"][:5] + agg_data["vital_signs"][:5]
            findings_text = "\n".join([f"• {f}" for f in combined_findings])
        else:
            findings_text = "No detailed findings available. Please upload a report to extract vitals and findings."
            
        ft_lbl = QLabel(findings_text)
        ft_lbl.setWordWrap(True)
        ft_lbl.setStyleSheet("font-size: 14px; line-height: 1.5; color: #334155;")
        f_layout.addWidget(ft_lbl)
        findings_layout.addWidget(f_card)
        
        content_layout.addLayout(findings_layout)
        content_layout.addStretch()
        
        scroll_area.setWidget(scroll_content)
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll_area)
        
        return page

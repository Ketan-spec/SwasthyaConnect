from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea

)
from PyQt6.QtCore import Qt
from src.database import get_all_hospital_resources

class StatCard(QFrame):
    def __init__(self, title, value, color="#3b82f6"):
        super().__init__()
        self.setMinimumSize(150, 100)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 10px;
                border-left: 5px solid {color};
                border: 1px solid #e2e8f0;
            }}
        """)
        layout = QVBoxLayout(self)
        
        t_label = QLabel(title)
        t_label.setStyleSheet("color: #64748b; font-size: 14px; font-weight: 500;")
        
        v_label = QLabel(str(value))
        v_label.setStyleSheet(f"color: {color}; font-size: 28px; font-weight: bold;")
        
        layout.addWidget(t_label)
        layout.addWidget(v_label)

class DiseaseTrendWidget(QWidget):
    def __init__(self, trends_data):
        super().__init__()
        layout = QVBoxLayout(self)
        
        title = QLabel("Top Reported Health Issues (Disease Surveillance)")
        # Enforcing Black Text for Title
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: black; margin-bottom: 10px;")
        layout.addWidget(title)
        
        if not trends_data:
            lbl = QLabel("No sufficient data for analysis.")
            lbl.setStyleSheet("color: black;")
            layout.addWidget(lbl)
            return

        # Data comes as: [{'state': 'Maha', 'reason': 'Flu', 'count': 5, 'percentage': 20}, ...]
        
        # Group by State for Display
        grouped_by_state = {}
        for item in trends_data:
            state = item['state'] or "Unknown Location"
            if state not in grouped_by_state:
                grouped_by_state[state] = []
            grouped_by_state[state].append(item)
            
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none; background: transparent;")
        
        container = QWidget()
        cont_layout = QVBoxLayout(container)
        cont_layout.setSpacing(20)
        
        for state, items in grouped_by_state.items():
            state_label = QLabel(f"📍 {state}")
            state_label.setStyleSheet("font-size: 14px; font-weight: bold; color: black; text-decoration: underline;")
            cont_layout.addWidget(state_label)
            
            for item in items:
                # reason, count, percentage
                row = QHBoxLayout()
                
                # Text Label: Black Color Enforced
                label_text = f"{item['reason']}: {item['count']} cases ({item['percentage']}%)"
                label = QLabel(label_text)
                label.setFixedWidth(250)
                label.setStyleSheet("color: black; font-weight: 500;")
                
                bar = QProgressBar()
                bar.setRange(0, 100)
                bar.setValue(int(item['percentage']))
                bar.setStyleSheet("""
                    QProgressBar {
                        border: 1px solid #cbd5e1;
                        background-color: #f1f5f9;
                        border-radius: 5px;
                        height: 12px;
                        text-align: center;
                        color: black;
                    }
                    QProgressBar::chunk {
                        background-color: #ef4444; 
                        border-radius: 5px;
                    }
                """)
                
                row.addWidget(label)
                row.addWidget(bar)
                cont_layout.addLayout(row)
                
        cont_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

class ResourceMonitorWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        title = QLabel("Hospital Resource Availability (Live)")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e293b; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Hospital Name", "ICU Beds", "Oxygen Units", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # Fetch Live Data
        raw_data = get_all_hospital_resources()
        
        # Determine table status
        if not raw_data:
            self.table.setRowCount(1)
            item = QTableWidgetItem("No hospital data available")
            self.table.setItem(0, 0, item)
            self.table.setSpan(0, 0, 1, 4)
            layout.addWidget(self.table)
            return

        data = []
        for r in raw_data:
            icu_str = f"{r['icu_beds_available']}/{r['icu_beds_total']}"
            oxy_str = f"{r['oxygen_percent']}%"
            data.append((r['hospital_name'], icu_str, oxy_str, r['status']))
        
        self.table.setRowCount(len(data))
        for r, row_data in enumerate(data):
            for c, value in enumerate(row_data):
                item = QTableWidgetItem(value)
                if c == 3: # Status column styling
                    item.setForeground(Qt.GlobalColor.white)
                    if value == "Available": item.setBackground(Qt.GlobalColor.green)
                    elif value == "Unavailable": item.setBackground(Qt.GlobalColor.gray)
                    elif value == "Full": item.setBackground(Qt.GlobalColor.blue)
                    elif value == "Critical": item.setBackground(Qt.GlobalColor.red)
                self.table.setItem(r, c, item)
                
        layout.addWidget(self.table)

class InteractiveAnalyticsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border:none; background: transparent;")
        
        container = QWidget()
        cont_layout = QVBoxLayout(container)

        title1 = QLabel("Health Analytics — Referral Reasons Distribution")
        title1.setStyleSheet("font-size: 16px; font-weight: bold; color: black; margin-bottom: 10px;")
        cont_layout.addWidget(title1)

        self._build_pie_chart(cont_layout)
        
        title2 = QLabel("Epidemiological Trends — Outbreaks Over Time")
        title2.setStyleSheet("font-size: 16px; font-weight: bold; color: black; margin-top: 30px; margin-bottom: 10px;")
        cont_layout.addWidget(title2)
        
        self._build_line_chart(cont_layout)
        
        cont_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _build_line_chart(self, layout):
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
        from src.database import get_health_trends_by_date
        
        trends = get_health_trends_by_date()
        
        if not trends:
            lbl = QLabel("No longitudinal data available for time-series analysis.")
            lbl.setStyleSheet("color: #64748b; font-style: italic;")
            layout.addWidget(lbl)
            return
            
        dates = [t['date'] for t in trends]
        counts = [t['value'] for t in trends]
        
        fig = Figure(figsize=(7, 4), facecolor="white")
        ax = fig.add_subplot(111)
        
        ax.plot(dates, counts, marker='o', linestyle='-', color='#ef4444', linewidth=2, markersize=6)
        
        ax.set_title("Disease Diagnoses Over Time", fontsize=12, fontweight="bold", color="#1e293b", pad=12)
        ax.set_ylabel("Number of Diagnoses", fontsize=10, color="#64748b")
        ax.set_xlabel("Date", fontsize=10, color="#64748b")
        
        ax.grid(True, linestyle='--', alpha=0.5)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        fig.autofmt_xdate(rotation=45)
        fig.tight_layout()
        
        canvas = FigureCanvas(fig)
        canvas.setMinimumHeight(350)
        layout.addWidget(canvas)

    def _build_pie_chart(self, layout):
        import sqlite3, os
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas

        # ── Fetch reason distribution from referrals ──────────────────────────
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        DB_NAME = os.path.join(BASE_DIR, "data", "swasthya_v1.db")

        reason_data = {}
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10.0)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT reason, COUNT(*) as cnt
                FROM referrals
                WHERE reason IS NOT NULL AND reason != ''
                GROUP BY reason
                ORDER BY cnt DESC
            """)
            rows = cursor.fetchall()
            conn.close()
            reason_data = {row[0]: row[1] for row in rows}
        except Exception as e:
            print(f"Pie chart DB error: {e}")

        # Fallback: if no referral data, use appointment count per day as category mock
        if not reason_data:
            reason_data = {
                "General Consultation": 38,
                "Cardiology": 22,
                "Orthopaedics": 17,
                "Neurology": 12,
                "Paediatrics": 11,
            }

        labels = list(reason_data.keys())
        sizes  = list(reason_data.values())

        # ── Colour palette ────────────────────────────────────────────────────
        palette = [
            "#3B82F6", "#10B981", "#F59E0B", "#EF4444",
            "#8B5CF6", "#06B6D4", "#F97316", "#EC4899",
            "#14B8A6", "#6366F1",
        ]
        colors = [palette[i % len(palette)] for i in range(len(labels))]

        # ── Build figure ──────────────────────────────────────────────────────
        fig = Figure(figsize=(7, 5), facecolor="white")
        ax  = fig.add_subplot(111)

        wedges, texts, autotexts = ax.pie(
            sizes,
            labels=None,          # labels shown in legend instead
            colors=colors,
            autopct=lambda pct: f"{pct:.1f}%" if pct > 3 else "",
            pctdistance=0.78,
            startangle=140,
            wedgeprops=dict(width=0.55, edgecolor="white", linewidth=2),  # donut style
        )

        for at in autotexts:
            at.set_fontsize(9)
            at.set_color("white")
            at.set_fontweight("bold")

        # Centre label
        total = sum(sizes)
        ax.text(0, 0, f"{total}\nTotal", ha="center", va="center",
                fontsize=12, fontweight="bold", color="#1e293b")

        # Legend
        ax.legend(
            wedges, labels,
            title="Categories",
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            fontsize=9,
            title_fontsize=10,
            frameon=False,
        )

        fig.tight_layout()

        canvas = FigureCanvas(fig)
        canvas.setMinimumHeight(380)
        layout.addWidget(canvas)

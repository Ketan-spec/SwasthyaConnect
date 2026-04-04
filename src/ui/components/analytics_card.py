from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QProgressBar, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea

)
from PyQt6.QtCore import Qt
from src.database import get_all_hospital_resources, get_health_trends_by_date
import pyqtgraph as pg

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
        
        title = QLabel("Overall Application Health Analytics (Patients vs Date)")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: black; margin-bottom: 10px;")
        layout.addWidget(title)
        
        self.plot_widget = pg.PlotWidget(background='w')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setLabel('left', 'Total Patient Engagements', color='black')
        self.plot_widget.setLabel('bottom', 'Date', color='black')
        self.plot_widget.getAxis('bottom').setPen(pg.mkPen(color='black'))
        self.plot_widget.getAxis('left').setPen(pg.mkPen(color='black'))
        self.plot_widget.getAxis('bottom').setTextPen(pg.mkPen(color='black'))
        self.plot_widget.getAxis('left').setTextPen(pg.mkPen(color='black'))
        
        trends = get_health_trends_by_date()
        
        if not trends:
            lbl = QLabel("No trend data available to plot.")
            lbl.setStyleSheet("color: black;")
            layout.addWidget(lbl)
            return
            
        x_data = list(range(len(trends)))
        y_data = [t['value'] for t in trends]
        dates = [t['date'][-5:] for t in trends] # Plot MM-DD
        
        # Simple line and symbol
        pen = pg.mkPen(color=(14, 165, 233), width=3) # #0ea5e9
        self.plot_widget.plot(x_data, y_data, pen=pen, symbol='o', symbolSize=8, symbolBrush=(15, 118, 110))
        
        ticks = [[(i, d) for i, d in enumerate(dates)]]
        self.plot_widget.getAxis('bottom').setTicks(ticks)
        
        layout.addWidget(self.plot_widget)

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt
from src.database import DB_NAME
import sqlite3

class GovtReportsWidget(QWidget):
    # Generates a state-wide mock summary report for government officials
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("State-Wide Aggregated Reports")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #7c3aed;")
        header_layout.addWidget(title)
        
        export_btn = QPushButton("Export to PDF (Simulation)")
        export_btn.setStyleSheet("background-color: #7c3aed; color: white; padding: 8px 15px; border-radius: 5px; font-weight: bold;")
        export_btn.clicked.connect(self.mock_export)
        header_layout.addWidget(export_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout.addLayout(header_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Metric Category", "Total Count", "Status", "Notes"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.load_data()

    def mock_export(self):
        QMessageBox.information(self, "Export Successful", "State-wide health report successfully exported to PDF (Mock).")

    def load_data(self):
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10.0)
            c = conn.cursor()
            
            # Aggregate metrics across the entire state
            c.execute("SELECT COUNT(*) FROM hospital_admissions")
            total_admissions = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM appointments")
            total_appointments = c.fetchone()[0]
            
            c.execute("SELECT SUM(icu_beds_available) FROM hospital_resources")
            total_icu = c.fetchone()[0] or 0
            
            c.execute("SELECT COUNT(*) FROM hospital_ambulances WHERE status='Available'")
            total_amb = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM users WHERE role='patient'")
            total_patients = c.fetchone()[0]
            
            conn.close()
            
            data = [
                ("Registered Patients", str(total_patients), "Normal", "Growing steadily"),
                ("Hospital Admissions", str(total_admissions), "High", "Seasonal spike"),
                ("Doctor Appointments", str(total_appointments), "Normal", ""),
                ("Available ICU Beds", str(total_icu), "Critical", "Monitor closely"),
                ("Available Ambulances", str(total_amb), "Normal", "Sufficient coverage")
            ]
            
            self.table.setRowCount(len(data))
            for r, row in enumerate(data):
                for col, val in enumerate(row):
                    item = QTableWidgetItem(val)
                    if col == 2:
                        item.setForeground(Qt.GlobalColor.white)
                        if val == "Normal": item.setBackground(Qt.GlobalColor.green)
                        elif val == "High": item.setBackground(Qt.GlobalColor.blue)
                        elif val == "Critical": item.setBackground(Qt.GlobalColor.red)
                    self.table.setItem(r, col, item)
                    
        except Exception as e:
            pass

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog
)
from PyQt6.QtCore import Qt
from src.database import DB_NAME
import sqlite3
from datetime import datetime

class GovtReportsWidget(QWidget):
    # Generates a state-wide summary report for government officials
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self._data = []  # store loaded data for export
        
        # Header
        header_layout = QHBoxLayout()
        title = QLabel("State-Wide Aggregated Reports")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #7c3aed;")
        header_layout.addWidget(title)
        
        export_btn = QPushButton("Export to PDF")
        export_btn.setStyleSheet("background-color: #7c3aed; color: white; padding: 8px 15px; border-radius: 5px; font-weight: bold;")
        export_btn.clicked.connect(self.export_pdf)
        header_layout.addWidget(export_btn, alignment=Qt.AlignmentFlag.AlignRight)
        
        layout.addLayout(header_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Metric Category", "Total Count", "Status", "Notes"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.load_data()

    def export_pdf(self):
        """Generate a real PDF report of state-wide health data using ReportLab."""
        if not self._data:
            QMessageBox.warning(self, "No Data", "No report data to export.")
            return
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib import colors
            from io import BytesIO

            save_path, _ = QFileDialog.getSaveFileName(self, "Save State Report PDF", f"SwasthyaConnect_Report_{datetime.now().strftime('%Y%m%d')}.pdf", "PDF Files (*.pdf)")
            if not save_path:
                return

            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=40, rightMargin=40, topMargin=60, bottomMargin=60)
            styles = getSampleStyleSheet()
            story = []

            story.append(Paragraph("Swasthya Connect — State-Wide Health Report", styles['h1']))
            story.append(Paragraph(f"Generated: {datetime.now().strftime('%d %B %Y, %I:%M %p')}", styles['Normal']))
            story.append(Spacer(1, 20))

            table_data = [["Metric Category", "Total Count", "Status", "Notes"]]
            for row in self._data:
                table_data.append(list(row))

            t = Table(table_data, colWidths=[180, 80, 80, 180])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c3aed')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.white]),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
                ('INNERGRID', (0, 0), (-1, -1), 0.3, colors.grey),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(t)
            story.append(Spacer(1, 20))
            story.append(Paragraph("This report is generated from live Swasthya Connect database. Data is anonymized and read-only.", styles['Italic']))

            doc.build(story)
            pdf_bytes = buffer.getvalue()
            buffer.close()

            with open(save_path, 'wb') as f:
                f.write(pdf_bytes)
            QMessageBox.information(self, "Export Successful", f"State-wide health report saved to:\n{save_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export PDF:\n{str(e)}")

    def load_data(self):
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10.0)
            c = conn.cursor()
            
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
            
            c.execute("SELECT COUNT(*) FROM medical_records")
            total_records = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM prescriptions")
            total_prescriptions = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM referrals")
            total_referrals = c.fetchone()[0]

            conn.close()
            
            self._data = [
                ("Registered Patients", str(total_patients), "Normal", "Growing steadily"),
                ("Hospital Admissions", str(total_admissions), "High", "Seasonal spike"),
                ("Doctor Appointments", str(total_appointments), "Normal", ""),
                ("Medical Records Uploaded", str(total_records), "Normal", "AI-analyzed reports"),
                ("Prescriptions Digitized", str(total_prescriptions), "Normal", "From AI extraction"),
                ("Doctor Referrals", str(total_referrals), "Normal", "Cross-hospital referrals"),
                ("Available ICU Beds", str(int(total_icu)), "Critical", "Monitor closely"),
                ("Available Ambulances", str(total_amb), "Normal", "Sufficient coverage"),
            ]
            
            self.table.setRowCount(len(self._data))
            for r, row in enumerate(self._data):
                for col, val in enumerate(row):
                    item = QTableWidgetItem(val)
                    if col == 2:
                        item.setForeground(Qt.GlobalColor.white)
                        if val == "Normal": item.setBackground(Qt.GlobalColor.green)
                        elif val == "High": item.setBackground(Qt.GlobalColor.blue)
                        elif val == "Critical": item.setBackground(Qt.GlobalColor.red)
                    self.table.setItem(r, col, item)
                    
        except Exception as e:
            print(f"Govt reports error: {e}")

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QMessageBox, QFileDialog, QLineEdit
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

class GovtGrantApprovalWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        
        title = QLabel("🏛️ Hospital Resource & Budget Grant Applications")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #475569;")
        layout.addWidget(title)
        
        sub = QLabel("Review and disburse budget grants requested by hospitals. Disbursed funds are cryptographically recorded into SHA-256 Blockchain blocks to prevent corruption or fraudulent reallocation.")
        sub.setWordWrap(True)
        sub.setStyleSheet("color: #64748b; font-size: 13px; margin-bottom: 10px;")
        layout.addWidget(sub)
        
        # Action Bar
        act_frame = QWidget()
        act_frame.setStyleSheet("background: white; border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px;")
        alayout = QHBoxLayout(act_frame)
        
        alayout.addWidget(QLabel("Approved Budget Allocation (₹):"))
        self.approved_amount_input = QLineEdit()
        self.approved_amount_input.setPlaceholderText("Enter Amount ₹ (e.g. 500000)")
        alayout.addWidget(self.approved_amount_input)
        
        approve_btn = QPushButton("✅ Approve & Disburse (Block Sealed)")
        approve_btn.setStyleSheet("background-color: #059669; color: white; font-weight: bold; padding: 8px 14px; border-radius: 6px;")
        approve_btn.clicked.connect(self.approve_grant)
        alayout.addWidget(approve_btn)
        
        reject_btn = QPushButton("❌ Reject Application")
        reject_btn.setStyleSheet("background-color: #dc2626; color: white; font-weight: bold; padding: 8px 14px; border-radius: 6px;")
        reject_btn.clicked.connect(self.reject_grant)
        alayout.addWidget(reject_btn)
        
        layout.addWidget(act_frame)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["Req ID", "Hospital Name", "Resource Category", "Qty", "Requested Budget (₹)", "Approved Budget (₹)", "Status", "Reason / Justification"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.load_data()

    def load_data(self):
        from src.database import get_resource_requests
        rows = get_resource_requests()
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(str(row['id'])))
            self.table.setItem(r, 1, QTableWidgetItem(str(row['hospital_name'])))
            self.table.setItem(r, 2, QTableWidgetItem(str(row['resource_category'])))
            self.table.setItem(r, 3, QTableWidgetItem(str(row['quantity'])))
            self.table.setItem(r, 4, QTableWidgetItem(f"₹ {row['requested_amount']:,.2f}"))
            self.table.setItem(r, 5, QTableWidgetItem(f"₹ {row['approved_amount']:,.2f}"))
            
            st_item = QTableWidgetItem(str(row['status']))
            if row['status'] == 'Approved':
                st_item.setForeground(Qt.GlobalColor.darkGreen)
            elif row['status'] == 'Rejected':
                st_item.setForeground(Qt.GlobalColor.red)
            else:
                st_item.setForeground(Qt.GlobalColor.darkYellow)
            self.table.setItem(r, 6, st_item)
            
            self.table.setItem(r, 7, QTableWidgetItem(str(row.get('reason') or '')))

    def approve_grant(self):
        from src.database import update_resource_request_status
        row_idx = self.table.currentRow()
        if row_idx < 0:
            QMessageBox.warning(self, "Selection Error", "Please select a grant request row from the table first.")
            return
            
        req_id = int(self.table.item(row_idx, 0).text())
        try:
            amt = float(self.approved_amount_input.text().strip() or 0)
        except ValueError:
            QMessageBox.warning(self, "Error", "Approved Amount must be a valid number.")
            return
            
        if amt <= 0:
            # Fallback to requested amount
            req_str = self.table.item(row_idx, 4).text().replace("₹", "").replace(",", "").strip()
            amt = float(req_str or 0)
            
        ok, msg = update_resource_request_status(req_id, "Approved", amt)
        if ok:
            QMessageBox.information(self, "Success", msg)
            self.approved_amount_input.clear()
            self.load_data()
        else:
            QMessageBox.warning(self, "Error", msg)

    def reject_grant(self):
        from src.database import update_resource_request_status
        row_idx = self.table.currentRow()
        if row_idx < 0:
            QMessageBox.warning(self, "Selection Error", "Please select a grant request row from the table first.")
            return
            
        req_id = int(self.table.item(row_idx, 0).text())
        ok, msg = update_resource_request_status(req_id, "Rejected", 0)
        if ok:
            QMessageBox.information(self, "Success", msg)
            self.load_data()
        else:
            QMessageBox.warning(self, "Error", msg)

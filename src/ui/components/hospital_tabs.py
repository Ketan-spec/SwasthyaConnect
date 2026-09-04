from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QLineEdit, QMessageBox, QComboBox, QFormLayout
)
from PyQt6.QtCore import Qt
from src.database import DB_NAME
import sqlite3

class PatientAdmissionWidget(QWidget):
    def __init__(self, hospital_id):
        super().__init__()
        self.hospital_id = hospital_id
        layout = QVBoxLayout(self)
        
        title = QLabel("Patient Admissions")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #b91c1c;")
        layout.addWidget(title)
        
        # Form
        form_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Patient Name")
        self.ward_input = QLineEdit()
        self.ward_input.setPlaceholderText("Ward / Room No.")
        admit_btn = QPushButton("Admit Patient")
        admit_btn.setStyleSheet("background-color: #b91c1c; color: white; padding: 5px 10px; border-radius: 4px;")
        admit_btn.clicked.connect(self.admit_patient)
        
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.ward_input)
        form_layout.addWidget(admit_btn)
        layout.addLayout(form_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Date", "Patient Name", "Ward", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.load_data()

    def load_data(self):
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10.0)
            c = conn.cursor()
            c.execute("SELECT date_admitted, patient_name, ward, status FROM hospital_admissions WHERE hospital_id = ? ORDER BY date_admitted DESC", (self.hospital_id,))
            rows = c.fetchall()
            conn.close()
            
            self.table.setRowCount(len(rows))
            for r, row in enumerate(rows):
                for c, val in enumerate(row):
                    if c == 0 and val: val = val.split(" ")[0]
                    self.table.setItem(r, c, QTableWidgetItem(str(val)))
        except Exception as e:
            pass
            
    def admit_patient(self):
        name = self.name_input.text().strip()
        ward = self.ward_input.text().strip()
        if not name or not ward: return
        
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10.0)
            c = conn.cursor()
            c.execute("INSERT INTO hospital_admissions (hospital_id, patient_name, ward) VALUES (?, ?, ?)", (self.hospital_id, name, ward))
            conn.commit()
            conn.close()
            self.name_input.clear()
            self.ward_input.clear()
            self.load_data()
        except:
            pass

class HospitalStaffWidget(QWidget):
    def __init__(self, hospital_id):
        super().__init__()
        self.hospital_id = hospital_id
        layout = QVBoxLayout(self)
        
        title = QLabel("Hospital Staff Management")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #b91c1c;")
        layout.addWidget(title)
        
        # Form
        form_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Staff Name")
        self.role_input = QLineEdit()
        self.role_input.setPlaceholderText("Role (e.g. Nurse)")
        self.contact_input = QLineEdit()
        self.contact_input.setPlaceholderText("Contact Info")
        add_btn = QPushButton("Add Staff")
        add_btn.setStyleSheet("background-color: #b91c1c; color: white; padding: 5px 10px; border-radius: 4px;")
        add_btn.clicked.connect(self.add_staff)
        
        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.role_input)
        form_layout.addWidget(self.contact_input)
        form_layout.addWidget(add_btn)
        layout.addLayout(form_layout)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Name", "Role", "Contact"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.load_data()

    def load_data(self):
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10.0)
            c = conn.cursor()
            c.execute("SELECT staff_name, role, contact FROM hospital_staff WHERE hospital_id = ?", (self.hospital_id,))
            rows = c.fetchall()
            conn.close()
            
            self.table.setRowCount(len(rows))
            for r, row in enumerate(rows):
                for c, val in enumerate(row):
                    self.table.setItem(r, c, QTableWidgetItem(str(val)))
        except:
            pass

    def add_staff(self):
        name = self.name_input.text().strip()
        role = self.role_input.text().strip()
        cnt = self.contact_input.text().strip()
        if not name or not role: return
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10.0)
            c = conn.cursor()
            c.execute("INSERT INTO hospital_staff (hospital_id, staff_name, role, contact) VALUES (?, ?, ?, ?)", (self.hospital_id, name, role, cnt))
            conn.commit()
            conn.close()
            self.name_input.clear()
            self.role_input.clear()
            self.contact_input.clear()
            self.load_data()
        except:
            pass

class HospitalInventoryWidget(QWidget):
    def __init__(self, hospital_id):
        super().__init__()
        self.hospital_id = hospital_id
        layout = QVBoxLayout(self)
        
        title = QLabel("Inventory Management")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #b91c1c;")
        layout.addWidget(title)
        
        form_layout = QHBoxLayout()
        self.item_input = QLineEdit()
        self.item_input.setPlaceholderText("Item Name (e.g. Blood O+)")
        self.qty_input = QLineEdit()
        self.qty_input.setPlaceholderText("Quantity")
        self.unit_input = QLineEdit()
        self.unit_input.setPlaceholderText("Unit (e.g. bags)")
        add_btn = QPushButton("Add Item")
        add_btn.setStyleSheet("background-color: #b91c1c; color: white; padding: 5px 10px; border-radius: 4px;")
        add_btn.clicked.connect(self.add_item)
        
        form_layout.addWidget(self.item_input)
        form_layout.addWidget(self.qty_input)
        form_layout.addWidget(self.unit_input)
        form_layout.addWidget(add_btn)
        layout.addLayout(form_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Item", "Quantity", "Unit"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.load_data()

    def load_data(self):
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10.0)
            c = conn.cursor()
            c.execute("SELECT item_name, quantity, unit FROM hospital_inventory WHERE hospital_id = ?", (self.hospital_id,))
            rows = c.fetchall()
            conn.close()
            
            self.table.setRowCount(len(rows))
            for r, row in enumerate(rows):
                for c, val in enumerate(row):
                    self.table.setItem(r, c, QTableWidgetItem(str(val)))
        except:
            pass

    def add_item(self):
        item = self.item_input.text().strip()
        qty = self.qty_input.text().strip()
        unit = self.unit_input.text().strip()
        if not item or not qty or not unit: return
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10.0)
            c = conn.cursor()
            c.execute("INSERT INTO hospital_inventory (hospital_id, item_name, quantity, unit) VALUES (?, ?, ?, ?)", (self.hospital_id, item, int(qty), unit))
            conn.commit()
            conn.close()
            self.item_input.clear()
            self.qty_input.clear()
            self.unit_input.clear()
            self.load_data()
        except:
            pass

class HospitalAmbulanceWidget(QWidget):
    def __init__(self, hospital_id):
        super().__init__()
        self.hospital_id = hospital_id
        layout = QVBoxLayout(self)
        
        title = QLabel("Ambulance Tracker")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #b91c1c;")
        layout.addWidget(title)
        
        form_layout = QHBoxLayout()
        self.veh_input = QLineEdit()
        self.veh_input.setPlaceholderText("Vehicle Number")
        self.combo = QComboBox()
        self.combo.addItems(["Available", "En Route", "Maintenance"])
        add_btn = QPushButton("Register Vehicle")
        add_btn.setStyleSheet("background-color: #b91c1c; color: white; padding: 5px 10px; border-radius: 4px;")
        add_btn.clicked.connect(self.add_vehicle)
        
        form_layout.addWidget(self.veh_input)
        form_layout.addWidget(self.combo)
        form_layout.addWidget(add_btn)
        layout.addLayout(form_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Vehicle Number", "Status"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.load_data()

    def load_data(self):
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10.0)
            c = conn.cursor()
            c.execute("SELECT vehicle_number, status FROM hospital_ambulances WHERE hospital_id = ?", (self.hospital_id,))
            rows = c.fetchall()
            conn.close()
            
            self.table.setRowCount(len(rows))
            for r, row in enumerate(rows):
                for c, val in enumerate(row):
                    self.table.setItem(r, c, QTableWidgetItem(str(val)))
        except:
            pass

    def add_vehicle(self):
        veh = self.veh_input.text().strip()
        if not veh: return
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10.0)
            c = conn.cursor()
            c.execute("INSERT INTO hospital_ambulances (hospital_id, vehicle_number, status) VALUES (?, ?, ?)", (self.hospital_id, veh, self.combo.currentText()))
            conn.commit()
            conn.close()
            self.veh_input.clear()
            self.load_data()
        except:
            pass

class HospitalTreatmentWidget(QWidget):
    def __init__(self, hospital_id):
        super().__init__()
        self.hospital_id = hospital_id
        layout = QVBoxLayout(self)
        
        title = QLabel("Patient Treatment Tracking")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #b91c1c;")
        layout.addWidget(title)
        
        # Form
        form_layout = QHBoxLayout()
        self.patient_combo = QComboBox()
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Not started", "In progress", "Delayed", "Completed"])
        self.notes_input = QLineEdit()
        self.notes_input.setPlaceholderText("Treatment Notes / Diagnosis")
        
        update_btn = QPushButton("Log Update")
        update_btn.setStyleSheet("background-color: #b91c1c; color: white; padding: 5px 15px; border-radius: 4px; font-weight: bold;")
        update_btn.clicked.connect(self.log_update)
        
        form_layout.addWidget(self.patient_combo)
        form_layout.addWidget(self.status_combo)
        form_layout.addWidget(self.notes_input)
        form_layout.addWidget(update_btn)
        layout.addLayout(form_layout)
        
        self.load_patients()
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Date/Time", "Patient", "Status", "Notes"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.load_data()

    def load_patients(self):
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10.0)
            c = conn.cursor()
            c.execute("SELECT id, full_name, unique_id FROM users WHERE role = 'patient'")
            self.patients = c.fetchall()
            conn.close()
            for p in self.patients:
                self.patient_combo.addItem(f"{p[1]} ({p[2]})", p[0])
        except Exception as e:
            pass

    def load_data(self):
        try:
            conn = sqlite3.connect(DB_NAME, timeout=10.0)
            c = conn.cursor()
            query = '''
                SELECT t.timestamp, u.full_name, t.status, t.notes
                FROM treatment_tracking t
                JOIN users u ON t.patient_id = u.id
                WHERE t.updated_by_id = ?
                ORDER BY t.timestamp DESC
            '''
            c.execute(query, (self.hospital_id,))
            rows = c.fetchall()
            conn.close()
            
            self.table.setRowCount(len(rows))
            for r, row in enumerate(rows):
                for c, val in enumerate(row):
                    self.table.setItem(r, c, QTableWidgetItem(str(val)))
        except Exception as e:
            pass

    def log_update(self):
        from src.database import add_treatment_update
        patient_id = self.patient_combo.currentData()
        status = self.status_combo.currentText()
        notes = self.notes_input.text().strip()
        if patient_id and notes:
            if add_treatment_update(patient_id, self.hospital_id, status, notes):
                self.notes_input.clear()
                self.load_data()

class HospitalGrantWidget(QWidget):
    def __init__(self, hospital_id):
        super().__init__()
        self.hospital_id = hospital_id
        layout = QVBoxLayout(self)
        
        title = QLabel("🏛️ Government Resource & Budget Grant Applications")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #0284c7;")
        layout.addWidget(title)
        
        sub = QLabel("Submit formal budget & resource requests to Government Health Authority. Every request and disbursed amount is cryptographically sealed into a SHA-256 Blockchain block to prevent corruption or falsified values.")
        sub.setWordWrap(True)
        sub.setStyleSheet("color: #64748b; font-size: 13px; margin-bottom: 10px;")
        layout.addWidget(sub)
        
        # Form
        form_frame = QWidget()
        form_frame.setStyleSheet("background: white; border: 1px solid #cbd5e1; border-radius: 8px; padding: 10px;")
        flayout = QHBoxLayout(form_frame)
        
        self.cat_combo = QComboBox()
        self.cat_combo.addItems(["ICU Beds & Monitors", "Oxygen Generator & Tanks", "Ventilator Units", "Emergency Medicines", "Dialysis Machines", "Ambulance Fleet"])
        
        self.qty_input = QLineEdit()
        self.qty_input.setPlaceholderText("Quantity")
        
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("Requested Budget (₹)")
        
        self.reason_input = QLineEdit()
        self.reason_input.setPlaceholderText("Justification / Reason")
        
        submit_btn = QPushButton("🔒 Submit Request to Govt (Block Sealed)")
        submit_btn.setStyleSheet("background-color: #0284c7; color: white; font-weight: bold; padding: 8px 14px; border-radius: 6px;")
        submit_btn.clicked.connect(self.submit_request)
        
        flayout.addWidget(self.cat_combo)
        flayout.addWidget(self.qty_input)
        flayout.addWidget(self.amount_input)
        flayout.addWidget(self.reason_input)
        flayout.addWidget(submit_btn)
        
        layout.addWidget(form_frame)
        
        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Category", "Qty", "Requested Budget (₹)", "Approved Budget (₹)", "Status", "Blockchain Sealed Hash"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table)
        
        self.load_data()

    def load_data(self):
        from src.database import get_resource_requests
        rows = get_resource_requests(self.hospital_id)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            self.table.setItem(r, 0, QTableWidgetItem(str(row['id'])))
            self.table.setItem(r, 1, QTableWidgetItem(str(row['resource_category'])))
            self.table.setItem(r, 2, QTableWidgetItem(str(row['quantity'])))
            self.table.setItem(r, 3, QTableWidgetItem(f"₹ {row['requested_amount']:,.2f}"))
            self.table.setItem(r, 4, QTableWidgetItem(f"₹ {row['approved_amount']:,.2f}"))
            
            st_item = QTableWidgetItem(str(row['status']))
            if row['status'] == 'Approved':
                st_item.setForeground(Qt.GlobalColor.darkGreen)
            elif row['status'] == 'Rejected':
                st_item.setForeground(Qt.GlobalColor.red)
            else:
                st_item.setForeground(Qt.GlobalColor.darkYellow)
            self.table.setItem(r, 5, st_item)
            
            hash_str = str(row.get('block_hash') or 'SHA-256 Sealed')
            self.table.setItem(r, 6, QTableWidgetItem(hash_str[:18] + "..."))

    def submit_request(self):
        from src.database import create_resource_request, get_hospital_resources
        cat = self.cat_combo.currentText()
        try:
            qty = int(self.qty_input.text().strip() or 0)
            amount = float(self.amount_input.text().strip() or 0)
        except ValueError:
            QMessageBox.warning(self, "Error", "Quantity and Requested Budget must be numeric.")
            return
            
        reason = self.reason_input.text().strip()
        if qty <= 0 or amount <= 0 or not reason:
            QMessageBox.warning(self, "Error", "Please fill in all fields with valid values.")
            return
            
        res_info = get_hospital_resources(self.hospital_id) or {}
        hname = res_info.get('hospital_name', f'Hospital #{self.hospital_id}')
        
        ok, msg = create_resource_request(self.hospital_id, hname, cat, qty, amount, reason)
        if ok:
            QMessageBox.information(self, "Success", msg)
            self.qty_input.clear()
            self.amount_input.clear()
            self.reason_input.clear()
            self.load_data()
        else:
            QMessageBox.warning(self, "Error", msg)

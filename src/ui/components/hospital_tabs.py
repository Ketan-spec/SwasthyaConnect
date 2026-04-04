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

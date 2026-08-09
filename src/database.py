import sqlite3
import os
import datetime
import hashlib
from src import blockchain

# Use absolute path to ensure DB is always found regardless of CWD
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DB_NAME = os.path.join(PROJECT_ROOT, "data", "swasthya_v1.db")

def initialize_database():
    """Initializes the database and creates tests tables."""
    
    conn = sqlite3.connect(DB_NAME, timeout=10.0)
    cursor = conn.cursor()
    
    # Create Users Table with extended fields + STATE
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            full_name TEXT,
            phone TEXT,
            email TEXT,
            unique_id TEXT,
            specialization TEXT,
            state TEXT
        )
    ''')
    
    # Create Referrals Table with updated Status options
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT,
            patient_age TEXT,
            patient_gender TEXT,
            reason TEXT,
            referred_by_id TEXT, -- User ID of referring doctor
            referred_to_id TEXT, -- User ID of receiving doctor
            status TEXT DEFAULT 'Pending', -- Pending, Accepted, Rejected, Pre-Op, Surgery, Post-Op, Discharged
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Create Hospital Resources Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hospital_resources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital_id INTEGER UNIQUE NOT NULL,
            hospital_name TEXT NOT NULL,
            icu_beds_total INTEGER DEFAULT 0,
            icu_beds_available INTEGER DEFAULT 0,
            oxygen_percent INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Unavailable', -- Available, Critical, Full, Unavailable
            last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (hospital_id) REFERENCES users (id)
        )
    ''')
    
    # Create Appointments Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            status TEXT DEFAULT 'Scheduled', -- Scheduled, Completed, Cancelled
            FOREIGN KEY (patient_id) REFERENCES users (id),
            FOREIGN KEY (doctor_id) REFERENCES users (id)
        )
    ''')
    
    # Create Medical Records Table (Updated for Medibrief functionality)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS medical_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            record_type TEXT NOT NULL, -- Report, Prescription
            title TEXT NOT NULL,
            description TEXT,
            file_path TEXT,            -- Added: Where local PDF is stored
            summary_json TEXT,         -- Added: Gemini generated structured output
            language TEXT,             -- Added: Requested language
            date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES users (id)
        )
    ''')
    
    # Create Hospital Admissions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hospital_admissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital_id INTEGER NOT NULL,
            patient_name TEXT NOT NULL,
            ward TEXT NOT NULL,
            status TEXT DEFAULT 'Admitted', -- Admitted, Discharged
            date_admitted DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (hospital_id) REFERENCES users (id)
        )
    ''')
    
    # Create Hospital Staff Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hospital_staff (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital_id INTEGER NOT NULL,
            staff_name TEXT NOT NULL,
            role TEXT NOT NULL,
            contact TEXT,
            FOREIGN KEY (hospital_id) REFERENCES users (id)
        )
    ''')
    
    # Create Hospital Inventory Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hospital_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital_id INTEGER NOT NULL,
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 0,
            unit TEXT NOT NULL,
            FOREIGN KEY (hospital_id) REFERENCES users (id)
        )
    ''')
    
    # Create Hospital Ambulances Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS hospital_ambulances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital_id INTEGER NOT NULL,
            vehicle_number TEXT NOT NULL,
            status TEXT DEFAULT 'Available', -- Available, En Route, Maintenance
            FOREIGN KEY (hospital_id) REFERENCES users (id)
        )
    ''')
    
    # Create Treatment Tracking Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS treatment_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            updated_by_id INTEGER NOT NULL,
            status TEXT DEFAULT 'Not started', -- Not started, In progress, Delayed, Completed
            notes TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES users (id),
            FOREIGN KEY (updated_by_id) REFERENCES users (id)
        )
    ''')
    
    # Create Prescriptions Table (per-medicine rows, linked to medical_records)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prescriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            medicine_name TEXT NOT NULL,
            dosage TEXT,
            frequency TEXT,
            duration TEXT,
            source_record_id INTEGER,
            date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES users (id)
        )
    ''')
    
    # New Table: Approved Medicines
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS approved_medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price TEXT,
            is_discontinued INTEGER,
            manufacturer_name TEXT,
            type TEXT,
            pack_size_label TEXT,
            short_composition1 TEXT,
            short_composition2 TEXT
        )
    ''')
    
    # New Table: Doctor Availability
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctor_availability (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER NOT NULL,
            date TEXT NOT NULL,          -- ISO YYYY-MM-DD
            time_slot TEXT NOT NULL,     -- e.g., "09:00-10:00"
            is_booked INTEGER DEFAULT 0,
            FOREIGN KEY (doctor_id) REFERENCES users(id)
        )
    ''')
    
    # Create Patient Vitals Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patient_vitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            vital_type TEXT NOT NULL,
            value TEXT NOT NULL,
            unit TEXT,
            recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            source_record_id INTEGER,
            FOREIGN KEY (patient_id) REFERENCES users (id),
            FOREIGN KEY (source_record_id) REFERENCES medical_records (id)
        )
    ''')
    
    # Create Clinical Conditions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clinical_conditions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            condition_name TEXT NOT NULL,
            status TEXT DEFAULT 'Active',
            diagnosed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            source_record_id INTEGER,
            FOREIGN KEY (patient_id) REFERENCES users (id),
            FOREIGN KEY (source_record_id) REFERENCES medical_records (id)
        )
    ''')
    
    # Create Patient Symptoms Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patient_symptoms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            symptom_name TEXT NOT NULL,
            recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            source_record_id INTEGER,
            FOREIGN KEY (patient_id) REFERENCES users (id),
            FOREIGN KEY (source_record_id) REFERENCES medical_records (id)
        )
    ''')
    
    print("Database initialized (Clean Slate - v1).")
    conn.commit()
    conn.close()

def reset_database():
    """Drops all tables and re-initializes the database to a blank state."""
    conn = sqlite3.connect(DB_NAME, timeout=10.0)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS doctor_availability")
    cursor.execute("DROP TABLE IF EXISTS approved_medicines")
    cursor.execute("DROP TABLE IF EXISTS hospital_ambulances")
    cursor.execute("DROP TABLE IF EXISTS hospital_inventory")
    cursor.execute("DROP TABLE IF EXISTS hospital_staff")
    cursor.execute("DROP TABLE IF EXISTS treatment_tracking")
    cursor.execute("DROP TABLE IF EXISTS hospital_admissions")
    cursor.execute("DROP TABLE IF EXISTS patient_symptoms")
    cursor.execute("DROP TABLE IF EXISTS clinical_conditions")
    cursor.execute("DROP TABLE IF EXISTS patient_vitals")
    cursor.execute("DROP TABLE IF EXISTS medical_records")
    cursor.execute("DROP TABLE IF EXISTS appointments")
    cursor.execute("DROP TABLE IF EXISTS hospital_resources")
    cursor.execute("DROP TABLE IF EXISTS referrals")
    cursor.execute("DROP TABLE IF EXISTS users")
    conn.commit()
    conn.close()
    
    # Re-create structure
    initialize_database()
    return True, "Database has been completely reset to a clean state."

def check_login(username, password):
    """Verifies user credentials and returns a dictionary of user details if valid."""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        conn.row_factory = sqlite3.Row # Access columns by name
        cursor = conn.cursor()
        
        hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, hashed_password))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return dict(result) # Convert Row object to dict
        
        return None
    except Exception as e:
        print(f"DEBUG: Error during login check: {e}")
        return None

def register_user(username, password, role, full_name, phone=None, email=None, unique_id=None, specialization=None, state=None):
    """Registers a new user. Returns (True, "Success") or (False, "Error Message")."""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()
        
        hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
        
        cursor.execute('''
            INSERT INTO users (username, password, role, full_name, phone, email, unique_id, specialization, state) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (username, hashed_password, role, full_name, phone, email, unique_id, specialization, state))
        
        # If Hospital, automatically create a default row in hospital_resources
        if role == 'hospital':
            hospital_id = cursor.lastrowid
            cursor.execute('''
                INSERT INTO hospital_resources (hospital_id, hospital_name)
                VALUES (?, ?)
            ''', (hospital_id, full_name))
            
        conn.commit()
        conn.close()
        return True, "Registration successful"
    except sqlite3.IntegrityError:
        return False, "Username/ID already exists."
    except Exception as e:
        print(f"Error registering user: {e}")
        return False, f"Database error: {str(e)}"

def get_all_doctors(state_filter=None):
    """Returns a list of all doctors, optionally filtered by state."""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT id, full_name, specialization, email, unique_id, state FROM users WHERE role = 'doctor'"
        params = []
        
        if state_filter and state_filter != "All States":
            query += " AND state = ?"
            params.append(state_filter)
            
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        
        doctors = [dict(row) for row in rows]
        conn.close()
        return doctors
    except Exception as e:
        print(f"Error fetching doctors: {e}")
        return []

def create_referral(patient_name, patient_age, patient_gender, reason, referred_by_id, referred_to_id):
    """Creates a new referral record."""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO referrals (patient_name, patient_age, patient_gender, reason, referred_by_id, referred_to_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (patient_name, patient_age, patient_gender, reason, referred_by_id, referred_to_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error creating referral: {e}")
        return False

def get_doctor_referrals(doctor_id):
    """Returns referrals sent to a specific doctor (by their user ID)."""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Join with users to get referring doctor's details
        query = '''
            SELECT r.*, u.full_name as referring_doc_name, u.unique_id as referring_doc_id
            FROM referrals r
            LEFT JOIN users u ON r.referred_by_id = u.id
            WHERE r.referred_to_id = ?
            ORDER BY r.timestamp DESC
        '''
        cursor.execute(query, (doctor_id,))
        rows = cursor.fetchall()
        
        referrals = [dict(row) for row in rows]
        conn.close()
        return referrals
    except Exception as e:
        print(f"Error fetching referrals: {e}")
        return []

def update_referral_status(referral_id, new_status):
    """Updates the status of a referral."""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()
        
        cursor.execute("UPDATE referrals SET status = ? WHERE id = ?", (new_status, referral_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating referral: {e}")
        return False

def get_govt_stats():
    """Returns aggregated statistics for the Government Dashboard including state-wise disease surveillance."""
    stats = {
        "total_patients": 0,
        "total_doctors": 0,
        "total_hospitals": 0,
        "disease_trends": [], # List of {state: 'Maha', reason: 'Flu', count: 5, percentage: 20}
        "recent_referrals": 0
    }
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Count Users by Role
        cursor.execute("SELECT role, COUNT(*) as count FROM users GROUP BY role")
        rows = cursor.fetchall()
        for row in rows:
            if row['role'] == 'patient':
                stats['total_patients'] = row['count']
            elif row['role'] == 'doctor':
                stats['total_doctors'] = row['count']
            elif row['role'] == 'hospital':
                stats['total_hospitals'] = row['count']
        
        # Total Referrals
        cursor.execute("SELECT COUNT(*) FROM referrals")
        stats['recent_referrals'] = cursor.fetchone()[0]

        # Disease Trends by State from actual clinical diagnoses
        query = '''
            SELECT u.state, cc.condition_name as reason, COUNT(*) as count
            FROM clinical_conditions cc
            JOIN users u ON cc.patient_id = u.id
            WHERE u.state IS NOT NULL AND u.state != ''
            GROUP BY u.state, cc.condition_name
            ORDER BY u.state, count DESC
        '''
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Calculate percentages per state
        # First, organize by state
        state_totals = {}
        raw_trends = []
        
        for row in rows:
            state = row['state'] or "Unknown"
            count = row['count']
            state_totals[state] = state_totals.get(state, 0) + count
            raw_trends.append(dict(row))
            
        # Add Percentage
        for item in raw_trends:
            state = item['state'] or "Unknown"
            total = state_totals.get(state, 1)
            item['percentage'] = round((item['count'] / total) * 100, 1)
            stats['disease_trends'].append(item)
        
        conn.close()
        return stats
    except Exception as e:
        print(f"Error fetching govt stats: {e}")
        return stats

def get_hospital_resources(hospital_id):
    """Fetch the resource stats for a specific hospital."""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM hospital_resources WHERE hospital_id = ?", (hospital_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row: return dict(row)
        return None
    except Exception as e:
        print(f"Error fetching hospital resource: {e}")
        return None

def update_hospital_resources(hospital_id, icu_total, icu_available, oxygen, status):
    """Updates the resources for a specific hospital."""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE hospital_resources 
            SET icu_beds_total = ?, icu_beds_available = ?, oxygen_percent = ?, status = ?, last_updated = CURRENT_TIMESTAMP
            WHERE hospital_id = ?
        ''', (icu_total, icu_available, oxygen, status, hospital_id))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating hospital resources: {e}")
        return False

def get_all_hospital_resources():
    """Fetch all hospital resources for the Government Dashboard."""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM hospital_resources ORDER BY status DESC, oxygen_percent ASC")
        rows = cursor.fetchall()
        
        res = [dict(row) for row in rows]
        conn.close()
        return res
    except Exception as e:
        print(f"Error fetching all hospital resources: {e}")
        return []

def add_medical_record(patient_id, record_type, title, description, file_path=None, summary_json=None, language='en'):
    conn = sqlite3.connect(DB_NAME, timeout=10.0)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO medical_records 
            (patient_id, record_type, title, description, file_path, summary_json, language) 
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (patient_id, record_type, title, description, file_path, summary_json, language))
        conn.commit()
        record_id = cursor.lastrowid
        try:
            blockchain.log_event("MEDICAL_REPORT_UPLOAD", "medical_report", record_id, patient_id, patient_id)
        except Exception as blockchain_e:
            print(f"Blockchain Error: {blockchain_e}")
            
        return record_id
    except Exception as e:
        print(f"Error adding medical record: {e}")
        return None
    finally:
        conn.close()

def add_treatment_update(patient_id, updated_by_id, status, notes):
    """Adds a new treatment tracking update for a patient."""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO treatment_tracking (patient_id, updated_by_id, status, notes)
            VALUES (?, ?, ?, ?)
        ''', (patient_id, updated_by_id, status, notes))
        
        conn.commit()
        record_id = cursor.lastrowid
        try:
            blockchain.log_event("TREATMENT_STATUS_UPDATED", "treatment", record_id, updated_by_id, patient_id)
        except Exception as blockchain_e:
            print(f"Blockchain Error: {blockchain_e}")
            
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding treatment update: {e}")
        return False

def get_treatment_updates(patient_id):
    """Fetches all treatment updates for a specific patient."""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = '''
            SELECT t.id, t.timestamp, t.status, t.notes, u.full_name as updated_by_name, u.role as updated_by_role
            FROM treatment_tracking t
            JOIN users u ON t.updated_by_id = u.id
            WHERE t.patient_id = ?
            ORDER BY t.timestamp DESC
        '''
        cursor.execute(query, (patient_id,))
        rows = cursor.fetchall()
        
        updates = [dict(row) for row in rows]
        conn.close()
        return updates
    except Exception as e:
        print(f"Error fetching treatment updates: {e}")
        return []

def get_patient_dashboard_stats(patient_id):
    """Fetches high-level stats for patient dashboard cards."""
    stats = {"appointments": 0, "records": 0, "treatments": 0}
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM appointments WHERE patient_id = ?", (patient_id,))
        stats["appointments"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM medical_records WHERE patient_id = ?", (patient_id,))
        stats["records"] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM treatment_tracking WHERE patient_id = ?", (patient_id,))
        stats["treatments"] = cursor.fetchone()[0]
        
        conn.close()
    except Exception as e:
        print(f"Error fetching patient stats: {e}")
    return stats

def get_patient_analytics(patient_id):
    """Fetches quantitative vital signs data for charting."""
    data_points = {} # format: {'heart_rate': [{'date': '2023-10-01', 'value': 12.0}], ...}
    
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT vital_type, value, unit, date(recorded_at) 
            FROM patient_vitals 
            WHERE patient_id = ? 
            ORDER BY recorded_at ASC
        ''', (patient_id,))
        rows = cursor.fetchall()
        conn.close()
        
        for v_type, val_str, unit, date_only in rows:
            import re
            match = re.search(r"[-+]?\d*\.\d+|\d+", str(val_str))
            if match:
                val = float(match.group())
                if v_type not in data_points:
                    data_points[v_type] = []
                data_points[v_type].append({"date": date_only, "value": val, "unit": unit})
                
        return data_points
    except Exception as e:
        print(f"Error fetching analytics: {e}")
        return {}

def get_health_trends_by_date():
    """Returns aggregated daily health data for Government Analytics Dashboard."""
    trends = []
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Track disease outbreaks over time
        query = '''
            SELECT date(diagnosed_at) as date, COUNT(*) as count 
            FROM clinical_conditions 
            GROUP BY date(diagnosed_at) 
            ORDER BY date(diagnosed_at) ASC
        '''
        cursor.execute(query)
        rows = cursor.fetchall()
        
        for row in rows:
            if row['date']:
                trends.append({'date': row['date'], 'value': row['count']})
                
        # If no real data, return empty list instead of mocking it
        conn.close()
        return trends
    except Exception as e:
        print(f"Error fetching health trends by date: {e}")
        return []

def get_doctor_dashboard_stats(doctor_id):
    """Fetches high-level stats for doctor dashboard cards."""
    stats = {"appointments_today": 0, "unread_reports": 0, "active_treatments": 0}
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM appointments WHERE doctor_id = ? AND status = 'Scheduled'", (doctor_id,))
        row1 = cursor.fetchone()
        if row1: stats["appointments_today"] = row1[0]
        
        cursor.execute("SELECT COUNT(*) FROM medical_records WHERE patient_id IN (SELECT patient_id FROM appointments WHERE doctor_id = ?)", (doctor_id,))
        row2 = cursor.fetchone()
        if row2: stats["unread_reports"] = row2[0]
        
        cursor.execute("SELECT COUNT(*) FROM treatment_tracking WHERE updated_by_id = ? AND status != 'Completed'", (doctor_id,))
        row3 = cursor.fetchone()
        if row3: stats["active_treatments"] = row3[0]
        
        conn.close()
    except Exception as e:
        print(f"Error fetching doctor stats: {e}")
    return stats

def book_appointment(patient_id, doctor_id, date_str, time_str):
    """Creates a new appointment with 'Pending' status."""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO appointments (patient_id, doctor_id, date, time, status)
            VALUES (?, ?, ?, ?, 'Pending')
        ''', (patient_id, doctor_id, date_str, time_str))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error booking appointment: {e}")
        return False

def get_aggregated_patient_data(patient_id):
    """Fetches structured data from relational tables for the patient dashboard."""
    data = {
        "conditions": [],
        "symptoms": [],
        "key_findings": [],
        "vital_signs": [],
        "abnormal_count": 0,
        "recent_summaries": [],
        "has_data": False,
        "record_count": 0
    }
    
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM medical_records WHERE patient_id = ?", (patient_id,))
        record_count = cursor.fetchone()[0]
        data["record_count"] = record_count
        if record_count > 0:
            data["has_data"] = True
            
        # Conditions
        cursor.execute("SELECT DISTINCT condition_name FROM clinical_conditions WHERE patient_id = ?", (patient_id,))
        data["conditions"] = [row[0] for row in cursor.fetchall() if row[0] and len(row[0]) < 40]
        
        # Symptoms
        cursor.execute("SELECT DISTINCT symptom_name FROM patient_symptoms WHERE patient_id = ?", (patient_id,))
        data["symptoms"] = [row[0] for row in cursor.fetchall() if row[0] and len(row[0]) < 20]
        
        # Vitals
        cursor.execute("SELECT vital_type, value, unit FROM patient_vitals WHERE patient_id = ? ORDER BY recorded_at DESC LIMIT 10", (patient_id,))
        vitals_fetched = cursor.fetchall()
        for v_type, val, unit in vitals_fetched:
            unit_str = f" {unit}" if unit else ""
            data["vital_signs"].append(f"{v_type.replace('_', ' ').title()}: {val}{unit_str}")
            
        # Check abnormals (Simple heuristics based on type, since we don't store abnormal flag yet)
        for v_type, val, unit in vitals_fetched:
            try:
                import re
                match = re.search(r"[-+]?\d*\.\d+|\d+", str(val))
                if match:
                    numeric_val = float(match.group())
                    if v_type == 'heart_rate' and (numeric_val > 100 or numeric_val < 60): data["abnormal_count"] += 1
                    elif v_type == 'blood_pressure' and (numeric_val > 140): data["abnormal_count"] += 1 # simplistic sys check
                    elif v_type == 'spO2' and numeric_val < 95: data["abnormal_count"] += 1
            except Exception:
                pass
                
        # Recent Summaries (Fallback to JSON for this specific textual field since we didn't normalize "summary bullets")
        cursor.execute("SELECT summary_json FROM medical_records WHERE patient_id = ? AND record_type IN ('Report', 'Prescription') ORDER BY date_added DESC LIMIT 3", (patient_id,))
        import json
        for row in cursor.fetchall():
            if row[0]:
                try:
                    summary = json.loads(row[0])
                    bullets = summary.get("overall_summary_bullets", [])
                    if bullets: data["recent_summaries"].extend(bullets[:2])
                except Exception:
                    pass
        
        conn.close()
        return data
    except Exception as e:
        print(f"Error aggregating patient data: {e}")
        return data
def add_past_appointment(patient_id, date_str, source_note="Extracted from report"):
    """Inserts a historical appointment derived from a medical report (doctor_id=0)."""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO appointments (patient_id, doctor_id, date, time, status)
            VALUES (?, 0, ?, '00:00', 'Completed')
        ''', (patient_id, date_str))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding past appointment: {e}")
        return False

def add_prescription_entry(patient_id, medicine_name, dosage=None, frequency=None, duration=None, source_record_id=None):
    """Inserts a single prescription medicine row linked to a patient, preventing duplicates."""
    try:
        if not medicine_name or str(medicine_name).lower() in ("null", "none", ""):
            return False
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()
        
        # Check for duplicate in the last 30 days
        cursor.execute('''
            SELECT id FROM prescriptions 
            WHERE patient_id = ? AND LOWER(medicine_name) = ? AND date_added > datetime('now', '-30 days')
        ''', (patient_id, medicine_name.lower()))
        if cursor.fetchone():
            conn.close()
            return False # Duplicate skipped
            
        cursor.execute('''
            INSERT INTO prescriptions (patient_id, medicine_name, dosage, frequency, duration, source_record_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (patient_id, medicine_name, dosage, frequency, duration, source_record_id))
        conn.commit()
        record_id = cursor.lastrowid
        try:
            blockchain.log_event("PRESCRIPTION_CREATED", "prescription", record_id, patient_id, patient_id)
        except Exception as blockchain_e:
            print(f"Blockchain Error: {blockchain_e}")
            
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding prescription entry: {e}")
        return False

def get_patient_prescriptions(patient_id):
    """Returns all prescription medicine rows for a patient from the prescriptions table."""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT date_added, medicine_name, dosage, frequency, duration FROM prescriptions WHERE patient_id = ? ORDER BY date_added DESC",
            (patient_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"Error fetching prescriptions: {e}")
        return []

def get_patient_all_medicine_names(patient_id):
    """Returns flat list of all medicine names for medicine verification."""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT medicine_name FROM prescriptions WHERE patient_id = ?", (patient_id,))
        rows = cursor.fetchall()
        conn.close()
        return [r[0] for r in rows if r[0]]
    except Exception as e:
        print(f"Error fetching medicine names: {e}")
        return []

def get_patient_disease_trend(patient_id):
    """Parses all clinical_conditions and returns {condition_name: count} dict for the dashboard trend chart."""
    trend = {}
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT condition_name, COUNT(*) as cnt FROM clinical_conditions WHERE patient_id = ? GROUP BY condition_name ORDER BY cnt DESC",
            (patient_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        for row in rows:
            if row[0] and len(str(row[0])) < 50:
                trend[row[0]] = row[1]
        return trend
    except Exception as e:
        print(f"Error building disease trend: {e}")
        return trend

def get_patient_vitals_timeline(patient_id):
    """Returns a list of {date, blood_pressure, heart_rate, spO2} from the patient_vitals table."""
    timeline = []
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT date(recorded_at) as date_only, source_record_id, vital_type, value
            FROM patient_vitals
            WHERE patient_id = ?
            ORDER BY recorded_at ASC
        ''', (patient_id,))
        rows = cursor.fetchall()
        conn.close()
        
        record_map = {}
        for date_only, source_record_id, vital_type, value in rows:
            if source_record_id not in record_map:
                record_map[source_record_id] = {"date": date_only, "blood_pressure": None, "heart_rate": None, "spO2": None}
            
            vt = str(vital_type).lower().replace(" ", "_")
            if vt in ("blood_pressure", "bp"):
                record_map[source_record_id]["blood_pressure"] = value
            elif vt in ("heart_rate", "hr"):
                record_map[source_record_id]["heart_rate"] = value
            elif vt in ("spo2", "oxygen"):
                record_map[source_record_id]["spO2"] = value
                
        sorted_records = sorted(record_map.values(), key=lambda x: x["date"])
        return sorted_records
    except Exception as e:
        print(f"Error building vitals timeline: {e}")
        return []

def add_patient_vital(patient_id, vital_type, value, unit, source_record_id):
    """Inserts a patient vital entry."""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO patient_vitals (patient_id, vital_type, value, unit, source_record_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (patient_id, vital_type, value, unit, source_record_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding patient vital: {e}")
        return False

def add_clinical_condition(patient_id, condition_name, status, source_record_id):
    """Inserts an active/historical clinical condition."""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO clinical_conditions (patient_id, condition_name, status, source_record_id)
            VALUES (?, ?, ?, ?)
        ''', (patient_id, condition_name, status, source_record_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding clinical condition: {e}")
        return False

def add_patient_symptom(patient_id, symptom_name, source_record_id):
    """Inserts a patient symptom entry."""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO patient_symptoms (patient_id, symptom_name, source_record_id)
            VALUES (?, ?, ?)
        ''', (patient_id, symptom_name, source_record_id))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding patient symptom: {e}")
        return False

def get_patient_symptoms_history(patient_id):
    """Returns a list of symptoms and their recorded date from patient_symptoms table."""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()
        cursor.execute("SELECT symptom_name, recorded_at FROM patient_symptoms WHERE patient_id = ? ORDER BY recorded_at ASC", (patient_id,))
        rows = cursor.fetchall()
        conn.close()
        return [{"symptom": r[0], "date": r[1]} for r in rows]
    except Exception as e:
        print(f"Error fetching symptoms history: {e}")
        return []

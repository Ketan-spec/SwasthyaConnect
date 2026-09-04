import sqlite3
import os
import datetime
import hashlib

# ── Blockchain integration (lazy import to avoid circular deps) ────────────────
def _get_audit_log():
    """Lazy-loads audit_log to avoid import-time circular dependency."""
    try:
        from src.blockchain import audit_log
        return audit_log
    except Exception as e:
        return f"Error: {str(e)}"

def set_user_language(user_id: int, lang: str):
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cur = conn.cursor()
        cur.execute("UPDATE users SET preferred_lang = ? WHERE id = ?", (lang, user_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error setting user language: {e}")

def get_user_language(user_id: int) -> str:
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cur = conn.cursor()
        cur.execute("SELECT preferred_lang FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        conn.close()
        return (row[0] if row and row[0] else "en")
    except Exception as e:
        # Fallback if preferred_lang column is missing
        return "en"

# Use absolute path to ensure DB is always found regardless of CWD
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
DB_NAME = os.path.join(PROJECT_ROOT, "data", "swasthya_v1.db")

def initialize_database():
    """Initializes the database, creates all tables, and initializes the blockchain."""
    
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
            state TEXT,
            preferred_lang TEXT
        )
    ''')

    # Migration: Ensure preferred_lang column exists if table already was created earlier
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN preferred_lang TEXT")
    except sqlite3.OperationalError:
        pass # Column already exists
    
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
    
    # Create Hospital Resource Requests Table (Government-Hospital Grant Tracking sealed in Blockchain)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS resource_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital_id INTEGER NOT NULL,
            hospital_name TEXT NOT NULL,
            resource_category TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            requested_amount REAL NOT NULL,
            approved_amount REAL DEFAULT 0,
            reason TEXT,
            status TEXT DEFAULT 'Pending', -- Pending, Approved, Rejected
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            block_hash TEXT
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
    
    conn.commit()
    conn.close()
    print("Database initialized (Clean Slate - v1).")

    # Initialize blockchain table and genesis block
    try:
        from src.blockchain.chain import initialize_blockchain_table
        initialize_blockchain_table()
    except Exception as e:
        print(f"[Blockchain] Warning: Could not initialize blockchain table: {e}")

def reset_database():
    """Drops all tables and re-initializes the database to a blank state."""
    conn = sqlite3.connect(DB_NAME, timeout=10.0)
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS hospital_ambulances")
    cursor.execute("DROP TABLE IF EXISTS hospital_inventory")
    cursor.execute("DROP TABLE IF EXISTS hospital_staff")
    cursor.execute("DROP TABLE IF EXISTS treatment_tracking")
    cursor.execute("DROP TABLE IF EXISTS hospital_admissions")
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
    """Verifies user credentials and returns a dictionary of user details if valid. Supports login via Username, Gov ID (unique_id), Email, or Phone."""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        conn.row_factory = sqlite3.Row # Access columns by name
        cursor = conn.cursor()
        
        clean_user = str(username).strip()
        hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
        
        cursor.execute('''
            SELECT * FROM users 
            WHERE (username = ? OR unique_id = ? OR email = ? OR phone = ?) AND password = ?
        ''', (clean_user, clean_user, clean_user, clean_user, hashed_password))
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
        
        role = role.lower()
        hashed_password = hashlib.sha256(password.encode('utf-8')).hexdigest()
        
        cursor.execute('''
            INSERT INTO users (username, password, role, full_name, phone, email, unique_id, specialization, state) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (username, hashed_password, role, full_name, phone, email, unique_id, specialization, state))
        
        # If Hospital, automatically create a default row in hospital_resources
        if role == 'hospital':
            hospital_id = cursor.lastrowid
            cursor.execute('''
                INSERT OR IGNORE INTO hospital_resources (hospital_id, hospital_name, icu_beds_total, icu_beds_available, oxygen_percent, status)
                VALUES (?, ?, 20, 8, 95, 'Available')
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
        
        query = "SELECT id, full_name, specialization, email, unique_id, state FROM users WHERE LOWER(role) = 'doctor'"
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

def get_distinct_specializations():
    """Returns a sorted list of unique doctor specializations from the database."""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT specialization FROM users WHERE LOWER(role) = 'doctor' AND specialization IS NOT NULL AND specialization != ''")
        rows = cursor.fetchall()
        conn.close()
        return sorted([r[0] for r in rows if r[0]])
    except Exception as e:
        print(f"Error fetching specializations: {e}")
        return []

def get_active_medications_count(patient_id):
    """Returns count of distinct active medicines for a patient."""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(DISTINCT medicine_name) FROM prescriptions WHERE patient_id = ?", (patient_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        print(f"Error counting medications: {e}")
        return 0

def get_patient_timeline(patient_id):
    """Returns chronological list of medical events (records, appointments, treatments) for dashboard timeline."""
    import json as _json
    timeline = []
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()
        
        # Medical records
        cursor.execute("""
            SELECT date_added, record_type, title, description, summary_json 
            FROM medical_records 
            WHERE patient_id = ? 
            ORDER BY date_added DESC
        """, (patient_id,))
        for row in cursor.fetchall():
            date_added, rec_type, title, desc, summary_json = row
            date_str = str(date_added).split(" ")[0] if date_added else ""
            
            diagnosis = []
            key_findings = []
            if summary_json:
                try:
                    obj = _json.loads(summary_json)
                    diagnosis = obj.get("diagnosis", [])[:3]
                    key_findings = obj.get("key_findings", obj.get("summary", {}).get("key_findings", []))[:3]
                except Exception:
                    pass
            
            timeline.append({
                "date": date_str,
                "type": rec_type,
                "title": title or "Untitled",
                "description": desc or "",
                "diagnosis": diagnosis,
                "key_findings": key_findings,
                "source": "record"
            })
        
        # Appointments
        cursor.execute("""
            SELECT a.date, a.time, a.status, COALESCE(u.full_name, 'Unknown Doctor')
            FROM appointments a
            LEFT JOIN users u ON a.doctor_id = u.id AND a.doctor_id != 0
            WHERE a.patient_id = ?
            ORDER BY a.date DESC
        """, (patient_id,))
        for row in cursor.fetchall():
            date_str, time_str, status, doctor_name = row
            timeline.append({
                "date": date_str or "",
                "type": "Appointment",
                "title": f"Appointment with {doctor_name}",
                "description": f"Status: {status} | Time: {time_str}",
                "diagnosis": [],
                "key_findings": [],
                "source": "appointment"
            })
        
        # Treatment updates
        cursor.execute("""
            SELECT t.timestamp, t.status, t.notes, u.full_name, u.role
            FROM treatment_tracking t
            JOIN users u ON t.updated_by_id = u.id
            WHERE t.patient_id = ?
            ORDER BY t.timestamp DESC
        """, (patient_id,))
        for row in cursor.fetchall():
            ts, status, notes, updater, role = row
            date_str = str(ts).split(" ")[0] if ts else ""
            timeline.append({
                "date": date_str,
                "type": "Treatment",
                "title": f"Treatment: {status}",
                "description": f"By {updater} ({role}): {notes or 'No notes'}",
                "diagnosis": [],
                "key_findings": [],
                "source": "treatment"
            })
        
        conn.close()
        
        # Sort by date descending
        timeline.sort(key=lambda x: x["date"], reverse=True)
        return timeline
    except Exception as e:
        print(f"Error building patient timeline: {e}")
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

        # ── Blockchain: record referral event ───────────────────────────────
        try:
            al = _get_audit_log()
            if al:
                al.log_referral(
                    patient_name=patient_name,
                    referred_by_id=referred_by_id,
                    referred_to_id=referred_to_id,
                    reason=reason,
                )
        except Exception as bc_err:
            print(f"[Blockchain] Non-fatal logging error: {bc_err}")

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

        # Disease Trends by State (from medical_records and referrals)
        disease_counts = {}
        
        # 1. Fetch from medical_records
        cursor.execute("""
            SELECT u.state, m.summary_json 
            FROM medical_records m 
            JOIN users u ON m.patient_id = u.id 
            WHERE m.summary_json IS NOT NULL
        """)
        for st, raw_json in cursor.fetchall():
            state_name = st or "Maharashtra"
            try:
                import json as _json
                obj = _json.loads(raw_json) if isinstance(raw_json, str) else raw_json
                for d in (obj.get("diagnosis") or []) + (obj.get("impression_in_simple_words") or []):
                    cond = d.get("term") if isinstance(d, dict) else str(d)
                    if cond and len(cond) < 50:
                        key = (state_name, cond.strip())
                        disease_counts[key] = disease_counts.get(key, 0) + 1
            except Exception:
                pass

        # 2. Fetch from referrals
        query = '''
            SELECT u.state, r.reason, COUNT(*) as count
            FROM referrals r
            JOIN users u ON r.referred_by_id = u.id
            GROUP BY u.state, r.reason
        '''
        cursor.execute(query)
        for row in cursor.fetchall():
            state_name = row['state'] or "Delhi"
            reason = row['reason'] or "General Checkup"
            key = (state_name, reason)
            disease_counts[key] = disease_counts.get(key, 0) + row['count']

        # Fallback sample HDIMS surveillance data if records are small
        if not disease_counts:
            sample_data = [
                ("Delhi", "Type 2 Diabetes Mellitus", 45),
                ("Delhi", "Hypertension", 32),
                ("Delhi", "Respiratory Infection", 18),
                ("Maharashtra", "Hypertension", 54),
                ("Maharashtra", "Type 2 Diabetes Mellitus", 38),
                ("Maharashtra", "Dengue Fever", 22),
                ("Karnataka", "Cardiomyopathy", 29),
                ("Karnataka", "Type 2 Diabetes Mellitus", 21),
                ("Tamil Nadu", "Hypertension", 36),
            ]
            for st, dis, cnt in sample_data:
                disease_counts[(st, dis)] = cnt

        # Group by state and calculate percentages
        state_totals = {}
        for (st, dis), cnt in disease_counts.items():
            state_totals[st] = state_totals.get(st, 0) + cnt

        for (st, dis), cnt in disease_counts.items():
            tot = state_totals.get(st, 1)
            pct = round((cnt / tot) * 100, 1)
            stats['disease_trends'].append({
                'state': st,
                'reason': dis,
                'count': cnt,
                'percentage': pct
            })

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
        
        # Get hospital name for blockchain log
        cursor.execute("SELECT hospital_name FROM hospital_resources WHERE hospital_id = ?", (hospital_id,))
        row = cursor.fetchone()
        hospital_name = row[0] if row else str(hospital_id)

        cursor.execute('''
            UPDATE hospital_resources 
            SET icu_beds_total = ?, icu_beds_available = ?, oxygen_percent = ?, status = ?, last_updated = CURRENT_TIMESTAMP
            WHERE hospital_id = ?
        ''', (icu_total, icu_available, oxygen, status, hospital_id))
        
        conn.commit()
        conn.close()

        # ── Blockchain: record resource update ──────────────────────────────
        try:
            al = _get_audit_log()
            if al:
                al.log_resource_update(
                    hospital_id=hospital_id,
                    hospital_name=hospital_name,
                    icu_total=icu_total,
                    icu_available=icu_available,
                    oxygen_percent=oxygen,
                    status=status,
                )
        except Exception as bc_err:
            print(f"[Blockchain] Non-fatal logging error: {bc_err}")

        return True
    except Exception as e:
        print(f"Error updating hospital resources: {e}")
        return False

def create_resource_request(hospital_id: int, hospital_name: str, category: str, quantity: int, amount: float, reason: str):
    """Submits a new hospital resource grant request and seals it in the Blockchain."""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO resource_requests (hospital_id, hospital_name, resource_category, quantity, requested_amount, reason, status)
            VALUES (?, ?, ?, ?, ?, ?, 'Pending')
        ''', (hospital_id, hospital_name, category, quantity, amount, reason))
        request_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Seal in Blockchain
        try:
            from src.blockchain.audit_log import log_grant_request
            log_grant_request(hospital_id, hospital_name, category, quantity, amount, reason)
        except Exception as bc_err:
            print(f"[Blockchain] Grant request logging warning: {bc_err}")

        return True, "Grant request submitted successfully and sealed in Blockchain."
    except Exception as e:
        print(f"Error creating resource request: {e}")
        return False, str(e)

def update_resource_request_status(request_id: int, status: str, approved_amount: float = 0, govt_actor_id: int = 1):
    """Updates grant request status by Govt Officer and seals disbursal in Blockchain."""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM resource_requests WHERE id = ?", (request_id,))
        req = cursor.fetchone()
        if not req:
            conn.close()
            return False, "Request not found."

        cursor.execute('''
            UPDATE resource_requests
            SET status = ?, approved_amount = ?
            WHERE id = ?
        ''', (status, approved_amount, request_id))
        conn.commit()
        conn.close()

        # Seal Government Action in Blockchain
        try:
            from src.blockchain.audit_log import log_govt_grant
            log_govt_grant(request_id, req['hospital_name'], req['resource_category'], approved_amount, status, govt_actor_id)
        except Exception as bc_err:
            print(f"[Blockchain] Govt grant logging warning: {bc_err}")

        return True, f"Grant request {status.lower()} successfully and recorded on Blockchain."
    except Exception as e:
        print(f"Error updating resource request: {e}")
        return False, str(e)

def get_resource_requests(hospital_id: int = None):
    """Returns all resource grant requests, or filtered by hospital_id."""
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        if hospital_id:
            cursor.execute("SELECT * FROM resource_requests WHERE hospital_id = ? ORDER BY id DESC", (hospital_id,))
        else:
            cursor.execute("SELECT * FROM resource_requests ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception as e:
        print(f"Error fetching resource requests: {e}")
        return []

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

        # ── Blockchain: record this event on the chain ──────────────────────
        try:
            al = _get_audit_log()
            if al:
                al.log_medical_record(
                    patient_id=patient_id,
                    record_type=record_type,
                    title=title,
                    summary_json_str=summary_json,
                )
        except Exception as bc_err:
            print(f"[Blockchain] Non-fatal logging error: {bc_err}")

        return True
    except Exception as e:
        print(f"Error adding medical record: {e}")
        return False
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
        conn.close()

        # ── Blockchain: record treatment update ─────────────────────────────
        try:
            al = _get_audit_log()
            if al:
                al.log_treatment_update(
                    patient_id=patient_id,
                    updated_by_id=updated_by_id,
                    status=status,
                    notes=notes,
                )
        except Exception as bc_err:
            print(f"[Blockchain] Non-fatal logging error: {bc_err}")

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
    """Parses past medical_records JSON to extract quantitative abnormal test parameters over time."""
    import json
    data_points = {} # format: {'Hemoglobin': [{'date': '2023-10-01', 'value': 12.0}], ...}
    
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()
        cursor.execute("SELECT date_added, summary_json FROM medical_records WHERE patient_id = ? AND record_type IN ('Report', 'Prescription') ORDER BY date_added ASC", (patient_id,))
        rows = cursor.fetchall()
        conn.close()
        
        for date_str, json_str  in rows:
            if not json_str: continue
            try:
                summary = json.loads(json_str)
                date_only = date_str.split(" ")[0]
                
                abnormals = summary.get("abnormal_values_explained", [])
                for abn in abnormals:
                    if isinstance(abn, dict):
                        test = abn.get("test", "Unknown")
                        val_str = abn.get("value", "")
                        
                        import re
                        match = re.search(r"[-+]?\d*\.\d+|\d+", str(val_str))
                        if match:
                            val = float(match.group())
                            if test not in data_points:
                                data_points[test] = []
                            data_points[test].append({"date": date_only, "value": val, "unit": abn.get("unit", "")})
            except Exception as parse_err:
                pass
                
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
        
        # We will track patient visits (appointments) per day
        query = '''
            SELECT date, COUNT(*) as count 
            FROM appointments 
            GROUP BY date 
            ORDER BY date ASC
        '''
        cursor.execute(query)
        rows = cursor.fetchall()
        
        for row in rows:
            if row['date']:
                trends.append({'date': row['date'], 'value': row['count']})
                
        # If no real appointments, return some generated data for visual context
        if not trends or len(trends) < 2:
            import datetime
            import random
            base = datetime.date.today() - datetime.timedelta(days=30)
            for i in range(30):
                d = base + datetime.timedelta(days=i)
                trends.append({'date': d.strftime('%Y-%m-%d'), 'value': random.randint(10, 50)})
                
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

        # ── Blockchain: record appointment booking ──────────────────────────
        try:
            al = _get_audit_log()
            if al:
                al.log_appointment(
                    patient_id=patient_id,
                    doctor_id=doctor_id,
                    date_str=date_str,
                    time_str=time_str,
                )
        except Exception as bc_err:
            print(f"[Blockchain] Non-fatal logging error: {bc_err}")

        return True
    except Exception as e:
        print(f"Error booking appointment: {e}")
        return False

def get_aggregated_patient_data(patient_id):
    """Parses all medical_records for a patient and aggregates dynamic insights for the dashboard."""
    import json
    data = {
        "conditions": set(),
        "symptoms": set(),
        "key_findings": [],
        "vital_signs": [],
        "abnormal_count": 0,
        "recent_summaries": [],
        "risk_score": 100, # Starts at 100, goes down based on abnormals
        "has_data": False,
        "record_count": 0
    }
    
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()
        cursor.execute("SELECT summary_json FROM medical_records WHERE patient_id = ? AND record_type IN ('Report', 'Prescription') ORDER BY date_added DESC", (patient_id,))
        rows = cursor.fetchall()
        conn.close()
        
        data["record_count"] = len(rows)
        if len(rows) > 0:
            data["has_data"] = True
            
        for row in rows:
            if not row[0]: continue
            try:
                summary = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                if not isinstance(summary, dict):
                    continue
                
                # Active Conditions (from diagnosis and impressions)
                diagnoses = summary.get("diagnosis") or []
                impressions = summary.get("impression_in_simple_words") or []
                
                for item in (diagnoses + impressions):
                    if not item: continue
                    cond_text = ""
                    if isinstance(item, dict):
                        cond_text = item.get("term") or item.get("diagnosis") or item.get("impression") or ""
                    elif isinstance(item, str):
                        cond_text = item
                    if cond_text and len(cond_text) < 60:
                        data["conditions"].add(cond_text.strip())
                        
                # Key findings
                summary_block = summary.get("summary") or {}
                overview = summary_block.get("patient_overview")
                if overview and isinstance(overview, str):
                    data["key_findings"].append(overview)
                    
                findings = (summary.get("key_findings") or []) or (summary_block.get("key_findings") or [])
                for f in findings:
                    if f:
                        f_text = f.get("term") if isinstance(f, dict) else str(f)
                        data["key_findings"].append(f_text)
                        
                # Vitals
                vitals_dict = summary.get("vitals") or {}
                if isinstance(vitals_dict, dict):
                    for vk, vv in vitals_dict.items():
                        if vv and str(vv).lower() not in ("null", "none", ""):
                            label = vk.replace("_", " ").title()
                            data["vital_signs"].append(f"{label}: {vv}")
                            
                vital_list = summary.get("vital_signs") or []
                for v in vital_list:
                    if v and str(v) not in data["vital_signs"]:
                        data["vital_signs"].append(str(v))
                        
                # Abnormalities & Symptoms
                abnormals = (summary.get("abnormal_values") or []) or (summary.get("abnormal_values_explained") or [])
                for abn in abnormals:
                    if not abn: continue
                    data["abnormal_count"] += 1
                    if isinstance(abn, dict):
                        test_name = abn.get("vital_sign") or abn.get("test") or abn.get("name") or ""
                        if test_name and len(str(test_name)) < 40:
                            data["symptoms"].add(str(test_name).strip())
                            val_str = abn.get("value") or ""
                            if val_str:
                                data["key_findings"].append(f"{test_name}: {val_str}")
                    elif isinstance(abn, str):
                        if len(abn) < 40:
                            data["symptoms"].add(abn.strip())
                        data["key_findings"].append(abn)
                        
                # Doctor/Recent Summary
                bullets = summary.get("overall_summary_bullets") or []
                for b in bullets:
                    if b and isinstance(b, str):
                        data["recent_summaries"].append(b)
                if overview and isinstance(overview, str):
                    data["recent_summaries"].append(overview)
                for d_item in diagnoses:
                    d_str = d_item.get("term") if isinstance(d_item, dict) else str(d_item)
                    if d_str:
                        data["recent_summaries"].append(f"Diagnosed: {d_str}")
                        
            except Exception as parse_err:
                print(f"[get_aggregated_patient_data] parse error: {parse_err}")
                
        # Calculate Risk Score based on abnormals (starts at 100, drops by 15 per abnormal)
        if data["has_data"]:
            penalty = min(data["abnormal_count"] * 15, 65)
            data["risk_score"] = max(100 - penalty, 25)
        else:
            data["risk_score"] = 100
        
        # Convert sets to lists
        data["conditions"] = list(data["conditions"])
        data["symptoms"] = list(data["symptoms"])
        
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
    """Inserts a single prescription medicine row linked to a patient."""
    try:
        if not medicine_name or str(medicine_name).lower() in ("null", "none", ""):
            return False
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO prescriptions (patient_id, medicine_name, dosage, frequency, duration, source_record_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (patient_id, medicine_name, dosage, frequency, duration, source_record_id))
        conn.commit()
        conn.close()

        # ── Blockchain: record prescription ─────────────────────────────────
        try:
            al = _get_audit_log()
            if al:
                al.log_prescription(
                    patient_id=patient_id,
                    medicine_name=medicine_name,
                    dosage=dosage,
                    frequency=frequency,
                    duration=duration,
                )
        except Exception as bc_err:
            print(f"[Blockchain] Non-fatal logging error: {bc_err}")

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
    """Parses all summary_json and returns {diagnosis: count} dict for the dashboard trend chart."""
    import json
    trend = {}
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT summary_json FROM medical_records WHERE patient_id = ? AND summary_json IS NOT NULL ORDER BY date_added DESC",
            (patient_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        for row in rows:
            if not row[0]: continue
            try:
                obj = json.loads(row[0])
                # From new schema
                for d in obj.get("diagnosis", []):
                    if d and len(str(d)) < 50:
                        trend[d] = trend.get(d, 0) + 1
                # From legacy schema
                for imp in obj.get("impression_in_simple_words", []):
                    if imp and len(str(imp)) < 50:
                        trend[imp] = trend.get(imp, 0) + 1
            except Exception:
                pass
        return trend
    except Exception as e:
        print(f"Error building disease trend: {e}")
        return trend

def get_patient_vitals_timeline(patient_id):
    """Returns a list of {date, blood_pressure, heart_rate, spO2} from all uploaded reports."""
    import json
    timeline = []
    try:
        conn = sqlite3.connect(DB_NAME, timeout=10.0)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT date_added, summary_json FROM medical_records WHERE patient_id = ? AND summary_json IS NOT NULL ORDER BY date_added ASC",
            (patient_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        for date_added, raw_json in rows:
            if not raw_json: continue
            try:
                obj = json.loads(raw_json)
                vitals = obj.get("vitals", {})
                if vitals and any(vitals.values()):
                    timeline.append({
                        "date": date_added.split(" ")[0] if date_added else "",
                        "blood_pressure": vitals.get("blood_pressure"),
                        "heart_rate": vitals.get("heart_rate"),
                        "spO2": vitals.get("spO2"),
                    })
            except Exception:
                pass
        return timeline
    except Exception as e:
        print(f"Error building vitals timeline: {e}")
        return []

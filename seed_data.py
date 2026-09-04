import sqlite3
import random
import os
import hashlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "data", "swasthya_v1.db")

def parse_txt_credentials(filename):
    path = os.path.join(BASE_DIR, "data", filename)
    if not os.path.exists(path):
        return []
    records = []
    with open(path, 'r', encoding='utf-8') as f:
        blocks = f.read().split('------------------------------')
    for b in blocks:
        lines = [l.strip() for l in b.strip().splitlines() if l.strip()]
        d = {}
        for l in lines:
            if ':' in l:
                k, v = l.split(':', 1)
                d[k.strip().lower()] = v.strip()
        if d:
            records.append(d)
    return records

def setup_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        # ── 1. Seed Doctors from doctors_credentials.txt ──
        doc_records = parse_txt_credentials("doctors_credentials.txt")
        doc_count = 0
        for d in doc_records:
            name = d.get("name")
            username = d.get("login (username)")
            raw_pwd = d.get("password", "Pass@123")
            pwd = hashlib.sha256(raw_pwd.encode('utf-8')).hexdigest()
            spec = d.get("specialization", "General Physician")
            state = d.get("state", "Maharashtra")
            gov_id = d.get("gov id", f"DOC-{random.randint(10000, 99999)}")
            email = f"{username}@swasthya.gov.in"
            phone = f"+9198{random.randint(10000000, 99999999)}"
            
            if name and username:
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO users (username, password, role, full_name, email, phone, unique_id, specialization, state)
                        VALUES (?, ?, 'doctor', ?, ?, ?, ?, ?, ?)
                    ''', (username, pwd, name, email, phone, gov_id, spec, state))
                    doc_count += 1
                except Exception as e:
                    print(f"Doc error {username}: {e}")

        # ── 2. Seed Hospitals from hospitals_credentials.txt ──
        hosp_records = parse_txt_credentials("hospitals_credentials.txt")
        hosp_count = 0
        for h in hosp_records:
            hname = h.get("hospital name")
            username = h.get("login (username)")
            raw_pwd = h.get("password", "Hosp@123")
            pwd = hashlib.sha256(raw_pwd.encode('utf-8')).hexdigest()
            state = h.get("state", "Delhi")
            gov_id = h.get("gov id", f"HOS-{random.randint(10000, 99999)}")
            email = f"{username}@swasthya.gov.in"
            phone = f"+9188{random.randint(10000000, 99999999)}"
            
            if hname and username:
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO users (username, password, role, full_name, email, phone, unique_id, state)
                        VALUES (?, ?, 'hospital', ?, ?, ?, ?, ?)
                    ''', (username, pwd, hname, email, phone, gov_id, state))
                    hosp_id = cursor.lastrowid
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO hospital_resources (hospital_id, hospital_name, icu_beds_total, icu_beds_available, oxygen_percent, status)
                        VALUES (?, ?, 30, ?, ?, 'Available')
                    ''', (hosp_id, hname, random.randint(5, 20), random.randint(85, 99)))
                    hosp_count += 1
                except Exception as e:
                    print(f"Hosp error {username}: {e}")

        # ── 3. Seed Government Officers from govt_credentials.txt ──
        govt_records = parse_txt_credentials("govt_credentials.txt")
        govt_count = 0
        for g in govt_records:
            gname = g.get("officer name")
            username = g.get("login (username)")
            raw_pwd = g.get("password", "Pass@123")
            pwd = hashlib.sha256(raw_pwd.encode('utf-8')).hexdigest()
            gov_id = g.get("gov id", f"GOV-{random.randint(1000, 9999)}")
            email = f"{username}@swasthya.gov.in"
            
            if gname and username:
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO users (username, password, role, full_name, email, unique_id, state)
                        VALUES (?, ?, 'govt', ?, ?, ?, 'Delhi')
                    ''', (username, pwd, gname, email, gov_id))
                    govt_count += 1
                except Exception as e:
                    print(f"Govt error {username}: {e}")

        conn.commit()
        conn.close()
        print(f"Successfully seeded {doc_count} Doctors, {hosp_count} Hospitals, and {govt_count} Govt Officers.")
        
    except Exception as e:
        print("Error during DB seeding:", e)

if __name__ == "__main__":
    setup_db()

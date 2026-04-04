import sqlite3
import random
import os
import hashlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "data", "swasthya_v1.db")

def setup_db():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        demo_pwd = hashlib.sha256("Password123!".encode()).hexdigest()
        
        states = ["Maharashtra", "Delhi", "Karnataka", "Telangana"]
        
        doctors = [
            ("Dr. Rajesh Sharma", "Cardiologist", "Apollo Hospital Delhi"),
            ("Dr. Ananya Iyer", "Neurologist", "Fortis Hospital Mumbai"),
            ("Dr. Amit Patel", "Oncologist", "Tata Memorial Mumbai"),
            ("Dr. Sneha Reddy", "Pediatrician", "Rainbow Hospitals Hyderabad"),
            ("Dr. Vikram Singh", "Orthopedic", "Medanta Gurugram"),
            ("Dr. Kavita Verma", "Dermatologist", "Max Super Speciality Delhi"),
            ("Dr. Arjun Kapoor", "General Physician", "Manipal Hospital Bangalore"),
            ("Dr. Neha Gupta", "Endocrinologist", "AIIMS New Delhi"),
            ("Dr. Rahul Desai", "Psychiatrist", "NIMHANS Bangalore"),
            ("Dr. Priya Menon", "Gynaecologist", "KIMS Trivandrum"),
        ]

        # Insert DOCTORS
        doc_count = 0
        for name, spec, hosp in doctors:
            uid = f"DOC-{random.randint(1000, 9999)}"
            email = f"{name.split(' ')[1].lower()}_{random.randint(10,99)}@example.com"
            phone = f"+9198{random.randint(10000000,99999999)}"
            username = email.split('@')[0]
            state = random.choice(states)
            
            try:
                cursor.execute('''
                    INSERT INTO users (username, password, role, full_name, email, phone, unique_id, specialization, state)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (username, demo_pwd, "Doctor", name, email, phone, uid, spec, state))
                doc_count += 1
            except Exception as e:
                print(f"Doc error {name}: {e}")
                
        # Insert HOSPITALS
        hospitals = [
            ("Apollo Diagnostics Delhi", "Delhi"),
            ("Fortis Lab Mumbai", "Maharashtra"),
            ("Medanta Medical Center", "Delhi"),
            ("Max Super Speciality", "Delhi"),
            ("AIIMS Research Institute", "Delhi")
        ]
        
        hosp_count = 0
        for name, hstate in hospitals:
            uid = f"HOS-{random.randint(1000, 9999)}"
            email = f"contact@{name.replace(' ', '').lower()}.in"
            phone = f"+9188{random.randint(10000000,99999999)}"
            username = email.split('@')[0]
            
            try:
                cursor.execute('''
                    INSERT INTO users (username, password, role, full_name, email, phone, unique_id, state)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (username, demo_pwd, "Hospital", name, email, phone, uid, hstate))
                hosp_count += 1
            except Exception as e:
                print(f"Hosp error {name}: {e}")

        conn.commit()
        conn.close()
        print(f"Successfully seeded {doc_count} Doctors and {hosp_count} Hospitals.")
        
    except Exception as e:
        print("Error during DB seeding:", e)

if __name__ == "__main__":
    setup_db()

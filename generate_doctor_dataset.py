import sqlite3
import random
import os
import csv
import hashlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "data", "swasthya_v1.db")
DATASET_CSV = os.path.join(BASE_DIR, "data", "doctor_staff_dataset.csv")
CREDENTIALS_TXT = os.path.join(BASE_DIR, "data", "doctors_credentials.txt")

def generate_dataset(num_doctors=50):
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
    
    first_names = ["Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Riyansh", "Krishna", "Ishaan", "Shaurya", 
                   "Aadhya", "Diya", "Kashvi", "Saanvi", "Pari", "Ananya", "Riya", "Manya", "Avni", "Sneha", "Rahul", "Vikram", "Neha", "Priya", "Kavita"]
    
    last_names = ["Sharma", "Patel", "Singh", "Kumar", "Iyer", "Reddy", "Verma", "Kapoor", "Gupta", "Desai", "Menon", "Bose", "Nair", "Rao", "Das"]
    
    specializations = ["Cardiologist", "Neurologist", "Oncologist", "Pediatrician", "Orthopedic", 
                       "Dermatologist", "General Physician", "Endocrinologist", "Psychiatrist", "Gynaecologist", "Pulmonologist"]
                       
    states = ["Maharashtra", "Delhi", "Karnataka", "Telangana", "Kerala", "Tamil Nadu", "Gujarat", "Uttar Pradesh", "West Bengal", "Rajasthan"]

    doctors_list = []
    
    for i in range(num_doctors):
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        name = f"Dr. {first_name} {last_name}"
        spec = random.choice(specializations)
        state = random.choice(states)
        uid = f"DOC-{random.randint(10000, 99999)}"
        email = f"{first_name.lower()}_{random.randint(10,999)}@hospital.com"
        phone = f"+9198{random.randint(10000000,99999999)}"
        
        username = email.split('@')[0]
        password = f"Pass@{random.randint(100,999)}"
        
        doctors_list.append({
            "full_name": name,
            "specialization": spec,
            "state": state,
            "unique_id": uid,
            "email": email,
            "phone": phone,
            "username": username,
            "password": password
        })
        
    return doctors_list

def save_credentials(doctors):
    with open(CREDENTIALS_TXT, 'w', encoding='utf-8') as f:
        f.write("SWASTHYA CONNECT - DOCTOR CREDENTIALS\n")
        f.write("="*50 + "\n\n")
        for doc in doctors:
            f.write(f"Name: {doc['full_name']}\n")
            f.write(f"Specialization: {doc['specialization']}\n")
            f.write(f"State: {doc['state']}\n")
            f.write(f"Gov ID: {doc['unique_id']}\n")
            f.write(f"Login (Username): {doc['username']}\n")
            f.write(f"Password: {doc['password']}\n")
            f.write("-" * 30 + "\n")
    print(f"Credentials for {len(doctors)} doctors saved to {CREDENTIALS_TXT}")

def update_database(doctors):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        doc_count = 0
        for doc in doctors:
            hashed_pwd = hashlib.sha256(doc['password'].encode('utf-8')).hexdigest()
            try:
                cursor.execute('''
                    INSERT INTO users (username, password, role, full_name, email, phone, unique_id, specialization, state)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (doc['username'], hashed_pwd, "doctor", doc['full_name'], doc['email'], doc['phone'], doc['unique_id'], doc['specialization'], doc['state']))
                doc_count += 1
            except sqlite3.IntegrityError:
                # Skip duplicate usernames/IDs if they randomly clash
                pass
        
        conn.commit()
        conn.close()
        print(f"Successfully inserted {doc_count} new doctors into the database.")
        
    except Exception as e:
        print("Error during DB seeding:", e)

if __name__ == "__main__":
    print("Generating Doctor Staff Dataset...")
    docs = generate_dataset(50) # Generates 50 Doctors
    save_credentials(docs)
    update_database(docs)


import sqlite3
import random
import os
import csv
import hashlib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "data", "swasthya_v1.db")
DATASET_CSV = os.path.join(BASE_DIR, "data", "doctor_staff_dataset.csv")

def generate_dataset(num_doctors=100):
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
    
    first_names = ["Aarav", "Vivaan", "Aditya", "Vihaan", "Arjun", "Sai", "Riyansh", "Krishna", "Ishaan", "Shaurya", 
                   "Aadhya", "Diya", "Kashvi", "Saanvi", "Pari", "Ananya", "Riya", "Manya", "Avni", "Sneha", "Rahul", "Vikram", "Neha", "Priya", "Kavita"]
    
    last_names = ["Sharma", "Patel", "Singh", "Kumar", "Iyer", "Reddy", "Verma", "Kapoor", "Gupta", "Desai", "Menon", "Bose", "Nair", "Rao", "Das"]
    
    specializations = ["Cardiologist", "Neurologist", "Oncologist", "Pediatrician", "Orthopedic", 
                       "Dermatologist", "General Physician", "Endocrinologist", "Psychiatrist", "Gynaecologist", "Pulmonologist"]
                       
    hospitals = ["Apollo Hospital", "Fortis Hospital", "Tata Memorial", "Rainbow Hospitals", "Medanta", 
                 "Max Super Speciality", "Manipal Hospital", "AIIMS", "NIMHANS", "KIMS"]
                 
    states = ["Maharashtra", "Delhi", "Karnataka", "Telangana", "Kerala", "Tamil Nadu", "Gujarat"]

    doctors_list = []
    
    # Pre-populate with our known doctors for consistency if needed, but we'll generate all 100 randomly
    for i in range(num_doctors):
        name = f"Dr. {random.choice(first_names)} {random.choice(last_names)}"
        spec = random.choice(specializations)
        hosp = random.choice(hospitals)
        state = random.choice(states)
        uid = f"DOC-{random.randint(10000, 99999)}"
        email = f"{name.split(' ')[1].lower()}_{random.randint(10,999)}@example.com"
        phone = f"+9198{random.randint(10000000,99999999)}"
        
        doctors_list.append({
            "full_name": name,
            "specialization": spec,
            "hospital": hosp,
            "state": state,
            "unique_id": uid,
            "email": email,
            "phone": phone,
            "username": email.split('@')[0]
        })
        
    return doctors_list

def save_to_csv(doctors):
    keys = doctors[0].keys()
    with open(DATASET_CSV, 'w', newline='', encoding='utf-8') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(doctors)
    print(f"Generated {len(doctors)} doctors and saved dataset to {DATASET_CSV}")

def update_database(doctors):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        demo_pwd = hashlib.sha256("Password123!".encode()).hexdigest()
        
        doc_count = 0
        for doc in doctors:
            try:
                cursor.execute('''
                    INSERT INTO users (username, password, role, full_name, email, phone, unique_id, specialization, state)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (doc['username'], demo_pwd, "Doctor", doc['full_name'], doc['email'], doc['phone'], doc['unique_id'], doc['specialization'], doc['state']))
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
    docs = generate_dataset(150) # Generates 150 Doctors
    save_to_csv(docs)
    update_database(docs)

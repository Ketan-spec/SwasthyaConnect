import sqlite3
import random
import os
import csv
import hashlib
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "data", "swasthya_v1.db")
DATASET_CSV = os.path.join(BASE_DIR, "data", "hospital_dataset.csv")
CREDENTIALS_TXT = os.path.join(BASE_DIR, "data", "hospitals_credentials.txt")

# Add the project root to sys.path so we can import src.database
sys.path.insert(0, BASE_DIR)
from src.database import register_user

def generate_dataset(num_hospitals=20):
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
    
    hospital_names = ["Apollo", "Fortis", "Max Super Speciality", "Medanta", "AIIMS", "Care", "Narayana Health", "Manipal", "KIMS", "Tata Memorial"]
    hospital_types = ["Hospital", "Medical Center", "Clinic", "Diagnostics", "Research Institute"]
    states = ["Maharashtra", "Delhi", "Karnataka", "Telangana", "Kerala", "Tamil Nadu", "Gujarat", "Uttar Pradesh", "West Bengal", "Rajasthan"]

    hospitals_list = []
    
    for i in range(num_hospitals):
        name_prefix = random.choice(hospital_names)
        name_suffix = random.choice(hospital_types)
        city_suffix = random.choice(["City", "Central", "East", "West", "North", "South", "Metro"])
        name = f"{name_prefix} {name_suffix} {city_suffix}"
        
        state = random.choice(states)
        uid = f"HOS-{random.randint(10000, 99999)}"
        email = f"admin_{name_prefix.lower()}_{random.randint(10,999)}@hospital.com"
        phone = f"+9188{random.randint(10000000,99999999)}"
        
        username = email.split('@')[0]
        password = f"Hosp@{random.randint(100,999)}"
        
        hospitals_list.append({
            "full_name": name,
            "state": state,
            "unique_id": uid,
            "email": email,
            "phone": phone,
            "username": username,
            "password": password
        })
        
    return hospitals_list

def save_credentials(hospitals):
    with open(CREDENTIALS_TXT, 'w', encoding='utf-8') as f:
        f.write("SWASTHYA CONNECT - HOSPITAL CREDENTIALS\n")
        f.write("="*50 + "\n\n")
        for hos in hospitals:
            f.write(f"Hospital Name: {hos['full_name']}\n")
            f.write(f"State: {hos['state']}\n")
            f.write(f"Gov ID: {hos['unique_id']}\n")
            f.write(f"Login (Username): {hos['username']}\n")
            f.write(f"Password: {hos['password']}\n")
            f.write("-" * 30 + "\n")
    print(f"Credentials for {len(hospitals)} hospitals saved to {CREDENTIALS_TXT}")
    
def save_csv(hospitals):
    keys = hospitals[0].keys()
    with open(DATASET_CSV, 'w', newline='') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(hospitals)
    print(f"Dataset saved to {DATASET_CSV}")

def update_database(hospitals):
    hosp_count = 0
    for hos in hospitals:
        # We use register_user because it automatically adds them to the hospital_resources table as well!
        success, msg = register_user(
            username=hos['username'],
            password=hos['password'],
            role="hospital",
            full_name=hos['full_name'],
            phone=hos['phone'],
            email=hos['email'],
            unique_id=hos['unique_id'],
            state=hos['state']
        )
        if success:
            hosp_count += 1
    
    print(f"Successfully inserted {hosp_count} new hospitals into the database.")

if __name__ == "__main__":
    print("Generating Hospital Dataset...")
    hospitals = generate_dataset(20) # Generates 20 Hospitals
    save_csv(hospitals)
    save_credentials(hospitals)
    update_database(hospitals)

import os

file_path = "/Users/apple/Documents/programming/mini project/Swasthya_Connect/src/database.py"
with open(file_path, "r") as f:
    lines = f.readlines()

new_lines = []
for idx, line in enumerate(lines):
    if "def get_patient_analytics(patient_id):" in line:
        # Keep everything up to just BEFORE get_patient_analytics
        new_lines = lines[:idx]
        break

correct_suffix = """def get_patient_analytics(patient_id):
    \"\"\"Parses past medical_records JSON to extract quantitative abnormal test parameters over time.\"\"\"
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
                        match = re.search(r"[-+]?\\d*\\.\\d+|\\d+", str(val_str))
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

def get_doctor_dashboard_stats(doctor_id):
    \"\"\"Fetches high-level stats for doctor dashboard cards.\"\"\"
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
"""

new_lines.append(correct_suffix)

with open(file_path, "w") as f:
    f.writelines(new_lines)

print("DB file fixed successfully!")

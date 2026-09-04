import csv
import os

class MedicineService:
    @staticmethod
    def get_csv_path():
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        return os.path.join(root_dir, "updated_indian_medicine_data.csv")

    @staticmethod
    def search_medicine_by_name(query, max_results=50):
        if not query or len(query) < 2:
            return []
            
        csv_path = MedicineService.get_csv_path()
        if not os.path.exists(csv_path):
            print(f"[MedicineService] Dataset missing at {csv_path}")
            return []

        results = []
        query_lower = query.lower().strip()
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = (row.get("name") or "").lower()
                    salt = (row.get("salt_composition") or "").lower()
                    comp1 = (row.get("short_composition1") or "").lower()
                    comp2 = (row.get("short_composition2") or "").lower()
                    mfg = (row.get("manufacturer_name") or "").lower()
                    
                    if (query_lower in name or 
                        query_lower in salt or 
                        query_lower in comp1 or 
                        query_lower in comp2 or 
                        query_lower in mfg):
                        results.append(row)
                        if len(results) >= max_results:
                            break
        except Exception as e:
            print(f"Error reading CSV: {e}")
            
        return results

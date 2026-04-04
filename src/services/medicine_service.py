import csv
import os

class MedicineService:
    @staticmethod
    def get_csv_path():
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        return os.path.join(root_dir, "updated_indian_medicine_data.csv")

    @staticmethod
    def search_medicine_by_name(query, max_results=20):
        if not query or len(query) < 2:
            return []
            
        csv_path = MedicineService.get_csv_path()
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Dataset not found at {csv_path}")

        results = []
        query_lower = query.lower()
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    name = row.get("name", "")
                    if query_lower in name.lower():
                        results.append(row)
                        if len(results) >= max_results:
                            break
        except Exception as e:
            print(f"Error reading CSV: {e}")
            
        return results

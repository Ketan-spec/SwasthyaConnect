class AIService:
    @staticmethod
    def analyze_patient_health(patient_data):
        """
        Analyzes patient vitals and returns a health insight.
        Mock logic for now.
        """
        # In a real app, we would look at BP, Sugar, BMI from patient_data
        import random
        insights = [
            ("Your blood pressure trends are stable. Keep up the good work! 🟢", "Low Risk"),
            ("Consider increasing your water intake to stay hydrated. 💧", "General Tip"),
            ("Your activity levels are low this week. Try a 30-min walk. 🚶", "Activity"),
            ("Scheduled vaccination is due next week. Don't forget! 💉", "Reminder"),
            ("Sleep patterns suggest fatigue. Ensure 8 hours of rest. 😴", "Wellness")
        ]
        return random.choice(insights)

    @staticmethod
    def analyze_doctor_workload(appointments_count, pending_referrals):
        """
        Analyzes doctor's workload and returns a summary.
        """
        if appointments_count > 10:
            return ("High workload detected today. Prioritize critical cases. 🔴", "High Load")
        elif pending_referrals > 0:
            return (f"You have {pending_referrals} pending referral(s). Review them when possible. 🟠", "Action Required")
        else:
            return ("Schedule looks light. Good time for administrative tasks or research. 🟢", "Low Load")

    @staticmethod
    def analyze_govt_trends(disease_trends):
        """
        Analyzes disease trends and provides a policy insight.
        """
        if not disease_trends:
            return "Insufficient data to generate policy insights. More patient referrals and diagnoses are required."
        
        top_disease = max(disease_trends, key=lambda x: x['count'])
        disease_name = top_disease['reason']
        state = top_disease['state'] or "Unknown Region"
        
        return f"Based on current trends, there is a significant cluster of '{disease_name}' cases originating from {state}. Recommended Action: Increase healthcare resources and initiate local awareness campaigns in the affected area."

    @staticmethod
    def chat_with_assistant(system_prompt: str, user_prompt: str, model_name: str = "mistral") -> str:
        import urllib.request
        import urllib.error
        import json
        
        medical_rule = "CRITICAL INSTRUCTION: You are a specialized medical AI assistant. If the user asks a question that is entirely unrelated to healthcare, medicine, or their personal well-being, you MUST reply with exactly: 'I am a medical assistant. Please ask questions related to your health or the medical domain.' and refuse to answer the question.\n\n"
        
        try:
            url = "http://localhost:11434/api/generate"
            prompt = f"{medical_rule}{system_prompt}\n\nUSER: {user_prompt}\nRESPONSE:"
            data = {
                "model": model_name,
                "prompt": prompt,
                "stream": False
            }
            req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get("response", "No answer generated.").strip()
        except urllib.error.URLError:
            return "Error: Could not reach Ollama server. Make sure it is running on localhost:11434."
        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    def chat_with_assistant_stream(system_prompt: str, user_prompt: str, model_name: str = "mistral"):
        import urllib.request
        import urllib.error
        import json
        
        medical_rule = "CRITICAL INSTRUCTION: You are a specialized medical AI assistant. If the user asks a question that is entirely unrelated to healthcare, medicine, or their personal well-being, you MUST reply with exactly: 'I am a medical assistant. Please ask questions related to your health or the medical domain.' and refuse to answer the question.\n\n"
        
        try:
            url = "http://localhost:11434/api/generate"
            prompt = f"{medical_rule}{system_prompt}\n\nUSER: {user_prompt}\nRESPONSE:"
            data = {
                "model": model_name,
                "prompt": prompt,
                "stream": True
            }
            req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=120) as response:
                for line in response:
                    if line:
                        chunk_data = json.loads(line.decode('utf-8'))
                        if "response" in chunk_data:
                            yield chunk_data["response"]
        except urllib.error.URLError:
            yield "Error: Could not reach Ollama server. Make sure it is running on localhost:11434."
        except Exception as e:
            yield f"Error: {str(e)}"

# Swasthya Connect App Objectives

## 1️⃣ CORE OBJECTIVES
• Centralize healthcare data across multiple hospitals
• Explain complex medical information using AI
• Enable doctor‑to‑doctor referrals
• Track treatment progress and delays
• Provide anonymized, multi‑level government dashboards
• Ensure patient data ownership, consent, and privacy

## 3️⃣ AUTHENTICATION & ROLE MANAGEMENT
• Login via Email / Phone + OTP
• Role selection:
  - Patient
  - Doctor
  - Hospital Admin
  - Government Authority

Each role must have:
• Separate dashboards
• API‑level access restrictions
• Consent enforcement at backend level

## 4️⃣ PATIENT WEB FEATURES
• Unified Digital Health Records
  - Reports
  - Prescriptions
  - Timeline with timestamps

• AI Medical Report Explanation
  - Convert clinical terms into simple language

• Prescription OCR
  - Upload image/PDF
  - Extract medicines & dosage

• Medicine Explanation
  - Purpose, dosage, duration, side‑effects

• Medicine Verification
  - Verify medicines issued by stores
  - Prevent manipulation in rural/remote areas

• Medicine Reminders
  - Calendar & notification based

• Treatment Status Tracking
  - Under Treatment
  - Delayed
  - Completed

• Doctor Referrals
  - View referred doctors
  - Choose alternatives

• Consent Management
  - Grant/Revoke access anytime

• Multilingual AI Health Assistant

## 5️⃣ DOCTOR & HOSPITAL FEATURES
• Patient queue management
• Access patient profile (only with consent)
• AI‑generated patient summary
• Upload reports & prescriptions
• Doctor‑to‑doctor referral workflow
• Update treatment status
• Maintain audit logs with timestamps

## 6️⃣ GOVERNMENT / ADMIN DASHBOARD
Access ONLY anonymized, read‑only data.

Dashboards:
• Facility Level
• Sub‑District Level
• District Level
• State / UT Level

Analytics:
• Disease trend analysis
• Treatment delay monitoring
• Medicine demand forecasting
• Health scheme tracking
• AI‑generated policy insights

## 7️⃣ TECH STACK
• Frontend / GUI: PyQt6
• Data Visualization: pyqtgraph
• Backend Logic: Python 3.10+
• Database: SQLite
• AI Intelligence: Ollama (Local Large Language Model server)
• AI Models: Qwen 2.5, Mistral, Llama 3
• Utilities: PDF processing, OCR integration

## 8️⃣ PROCEDURE / WORKFLOW
1. Environment Setup: Create a virtual environment (`python -m venv .venv`) and install dependencies (`pip install -r requirements.txt`).
2. AI Setup: Ensure Ollama is running locally and required models (`qwen2.5:latest`, `mistral:latest`) are pulled.
3. Database Initialization: Run `seed_data.py` and `generate_doctor_dataset.py` to securely create the local SQLite database and insert dummy credentials.
4. Execution: Run `python src/main.py` to launch the multi-role desktop application.
5. Role Workflows:
   - Patients upload records for AI analysis and book appointments.
   - Doctors accept appointments, view AI-generated summaries, and prescribe treatments.
   - Government Admins monitor aggregated disease analytics and system loads.

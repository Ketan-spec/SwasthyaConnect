# Swasthya Connect

## AI‑Powered Digital Healthcare Management & Monitoring System (HDIMS Aligned)

**A unified, offline‑first platform that connects patients, doctors, hospitals, and government health authorities on a single secure interface.**

---

### 🎯 Vision
- **Patient‑Centric Health Record** – Store a lifelong, chronological medical history (reports, prescriptions, vitals) that patients can view, update, and share with explicit consent.
- **AI‑Assisted Understanding** – Upload any PDF or image of a medical report; an on‑device LLM generates a concise, plain‑language summary saved for future reference.
- **Seamless Referral & Verification** – Patients discover doctors by specialty, city, and availability, and can request referrals. Doctors can refer peers with a single click. Medicine verification against a curated drug dataset prevents misuse.
- **Transparent Hospital Resources** – Hospital admins manage staff, beds, and equipment; real‑time resource dashboards are visible to doctors for better triage.
- **Government‑Ready Analytics** – Aggregated, anonymized disease‑trend and resource‑utilization dashboards enable policy‑making without exposing personal identifiers.

---

## 👥 Role‑Based Features

### Patient
- **Unified Digital Health Record** – Reports, prescriptions, vitals, and timeline with timestamps.
- **Offline AI Summaries** – Upload a medical report → on‑device LLM produces a plain‑language summary stored in the patient’s profile.
- **Doctor Discovery & Referral** – Filter doctors by specialty, city, and availability; request a referral directly.
- **Medicine Verification** – Scan a medicine package; the system checks validity against a verified drug dataset.
- **Reminders & Alerts** – Medication schedules, appointment notifications, and health‑parameter alerts.

### Doctor
- **Consent‑Based Patient Access** – Enter a patient ID to view their full dashboard (including AI‑generated summary).
- **Patient Timeline & Vitals** – Visualize blood pressure, heart rate, glucose, etc., over time.
- **AI‑Generated Summaries** – Quick view of key conditions and abnormal values.
- **Doctor‑to‑Doctor Referral** – Recommend a specialist, see availability, and forward the case.
- **Treatment Status Tracker** – Mark cases as *Under Treatment*, *Delayed*, or *Completed* with audit logs.

### Hospital Admin
- **Staff & Resource Management** – Add/remove doctors, nurses, beds, oxygen units, and track real‑time availability.
- **Live Resource Dashboard** – Live view of ICU beds, oxygen stock, and critical resource alerts.
- **Integrated with Doctor Workflow** – Doctors see hospital resource status when scheduling procedures.

### Government Authority
- **Anonymized, Read‑Only Dashboards** – No patient names; only aggregated disease counts and trends.
- **Multi‑Level Views** – Facility, district, state/UT level analytics.
- **Key Analytics** – Disease‑trend analysis, treatment‑delay monitoring, medicine‑demand forecasting, health‑scheme uptake.
- **Policy Insights** – AI‑generated recommendations for resource allocation and public‑health interventions.

---

## 🛠️ Tech Stack
- **Frontend GUI** – PyQt6 with Qt Style Sheets (glass‑morphic design, modern typography).
- **Data Visualization** – pyqtgraph for interactive charts; matplotlib for static dashboards.
- **Backend** – Python 3.10+, SQLite for local persistence.
- **AI Engine** – Ollama (local LLM server) with strict JSON‑Schema extraction to guarantee reliable outputs.
- **OCR & PDF** – `pdfminer.six` for text extraction, Tesseract OCR fallback for scanned images.
- **Document Generation** – ReportLab for PDF summaries.

---

## 📂 Project Structure
```
Swasthya_Connect/
├── src/
│   ├── main.py                # Application entry point
│   ├── database.py            # SQLite schema & aggregation logic
│   ├── ui/                    # PyQt6 UI components & dashboards
│   │   ├── components/        # Reusable widgets (medibrief dialog, chat, tables)
│   │   └── dashboards/        # Role‑specific analytics dashboards
│   ├── services/              # OCR, AI (Ollama) integration, PDF builder
│   └── utils/                 # Prompt templates, static mappings
├── data/                      # Local SQLite DB & uploaded assets
├── storage/                   # Persistent record assets (images, PDFs)
└── scripts/                   # Mock data generation & seeding scripts
```

---

## 🚀 Getting Started
1. **Clone the repository**
   ```bash
   git clone https://github.com/Ketan-spec/SwasthyaConnect.git
   cd SwasthyaConnect
   ```
2. **Set up a Python environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. **Run Ollama locally** and pull the required models:
   ```bash
   ollama pull qwen2.5:latest
   ollama pull mistral:latest
   ```
4. **Initialize the database** (automatically on first run) or seed demo data:
   ```bash
   python seed_data.py
   python generate_doctor_dataset.py
   ```
5. **Launch the application**
   ```bash
   python src/main.py
   ```

---

## 🛡️ Ethics, Privacy & Governance
- **Data Ownership** – Patients retain full control over their health data.
- **Explicit Consent** – All sharing requires patient approval.
- **Anonymization** – Government dashboards expose only aggregated disease counts.
- **Local AI Processing** – No patient data leaves the device; all LLM inference runs locally via Ollama.

---

## 📄 License
This project is licensed under the MIT License – see the [LICENSE](LICENSE) file.

---

*Built to empower healthcare delivery across rural and urban India while complying with HDIMS standards.*

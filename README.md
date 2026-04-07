# Swasthya Connect

**AI-Powered Digital Healthcare Management & Monitoring System**
*(HDIMS-Aligned | Government-Ready | Ethical & Consent-Based)*

---

## 1. Project Overview

The **AI-Powered Digital Healthcare Management & Monitoring System** is a unified digital health platform designed to serve Patients, Doctors, Hospitals, and Government Health Authorities. It aligns with the Health Data Information & Management System (HDIMS) under the Health & Family Welfare Department, Government of NCT of Delhi.

## 2. Core Problem Statement

Healthcare data in India is currently scattered, paper-based, or siloed. Patients struggle to understand reports, and government hospitals lack transparent treatment tracking. Data is not structured for real-time monitoring or policy planning.

## 3. Solution Vision

To build a secure, centralized, AI-enabled healthcare platform that:
- Consolidates patient medical data into a unified digital timeline.
- Uses AI to explain medical reports and prescriptions in simple language.
- Enables seamless doctor referrals and tracks treatment progress.
- Provides anonymized dashboards for government monitoring.
- Ensures ethical, consent-based data sharing.

## 4. Key Features

### A. Patient Module
- Unified digital health records with chronological timeline.
- AI-generated summaries of medical reports.
- Prescription scanning and digitization.
- Simple explanations of medicines (purpose, dosage, duration).
- Automated medicine reminders and health analytics.

### B. Doctor / Hospital Module
- Access to patient profiles with explicit consent.
- AI-generated patient summaries for faster diagnosis.
- Structured doctor-to-doctor referral system.
- Treatment status tracking (Under Treatment, Delayed, Completed).

### C. Government / Administrative Module
- Read-only, anonymized monitoring dashboards.
- Multi-level data views (Facility, District, State/UT).
- Disease trend analysis and treatment delay monitoring.
- Medicine demand forecasting and policy insights.

## 5. Tech Stack

**Swasthya Connect** is built using a modern, locally-executable stack:

- **Frontend / GUI:** [PyQt6](https://www.riverbankcomputing.com/software/pyqt/)
- **Data Visualization:** [pyqtgraph](https://www.pyqtgraph.org/)
- **Backend Logic:** Python 3.10+
- **Database:** [SQLite](https://sqlite.org/)
- **AI Intelligence:** [Ollama](https://ollama.com/) (Local Large Language Model server)
- **AI Models:** Qwen 2.5, Mistral, Llama 3

## 6. Project Structure

```text
Swasthya_Connect/
├── src/
│   ├── main.py              # Application Entry Point
│   ├── database.py          # Database Schema & Initialization
│   ├── ui/                  # Dashboard & Widget Implementations
│   │   ├── components/      # Reusable UI elements (Chatbot, Medibrief)
│   │   └── dashboards/      # Role-specific views (Patient, Doctor, Gov)
│   ├── services/            # AI Integration & Business Logic
│   └── utils/               # Data processing helpers
├── data/                    # SQLite Database & CSV Datasets
├── storage/                 # Medical records & reports
└── scripts/                 # Maintenance & Seeding scripts
```

---

## 7. Getting Started

### Prerequisites

1.  **Python 3.10+**
2.  **Ollama** installed and running on `localhost:11434`.
3.  **Pull Required AI Models:**
    ```bash
    ollama pull qwen2.5:latest
    ollama pull mistral:latest
    ```

### Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Ketan-spec/SwasthyaConnect.git
    cd SwasthyaConnect
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Initialize the Database:**
    The application will automatically initialize the SQLite database on first run. To seed it with dummy data:
    ```bash
    python seed_data.py
    python generate_doctor_dataset.py
    ```

### Running the Application

Launch the main application interface:
```bash
python src/main.py
```

---

## 8. Ethics, Privacy & Governance

- **Data Ownership:** Patients retain full control over their health data.
- **Consent-Based:** Data sharing requires explicit patient approval.
- **Anonymized:** Administrative access is restricted to anonymized, aggregated datasets.
- **Local AI:** All medical data processing happens locally via Ollama to ensure privacy.

## 9. License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*Developed for the "Swasthya Connect" Healthcare Initiative.*

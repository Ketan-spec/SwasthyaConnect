# Swasthya Connect

**AI-Powered Digital Healthcare Management & Monitoring System**
*(HDIMS-Aligned | Government-Ready | Ethical & Consent-Based)*

---

## 1. Project Overview

The **AI-Powered Digital Healthcare Management & Monitoring System** is a unified digital health platform designed to serve Patients, Doctors, Hospitals, and Government Health Authorities. It aligns with the Health Data Information & Management System (HDIMS) under the Health & Family Welfare Department, Government of NCT of Delhi.

## 2. Team & Technical Contributions

This platform was developed collaboratively with explicit technical domain and layer mapping for each member:

- **Ketan:** Local Ollama AI Server Integration, Backend Multi-modal JSON Extraction Prompts, Dynamic Dashboard Manipulation, and Hybrid OCR Engine execution.  
  *Tech Mapping:* **Ollama Engine** (using `qwen2:0.5b`/`mistral`), **PyMuPDF (`fitz`)** for rapid native PDF text streaming, and **Tesseract OCR (`pytesseract`/`Pillow`)** fallback extraction pipeline for scanned prescription images.
- **Vedant:** Software Architecture Control, Component Lifecycle Binding, Programmatic UI Stiches, Signal/Slot Event Pipelines, and High-fidelity Report Document Exporters.  
  *Tech Mapping:* Core event bridges linking background asynchronous worker threads (`QThread`) directly with GUI dispatchers, and **ReportLab** dynamic vector template rendering with registered dual-weight local typography assets (Noto Sans Devanagari).
- **Anushka:** UI/UX Design System Construction, Global Palette Scaling, Responsive Interface Architectures, Medical Visual Aesthetics, and Interactive Component Lookups.  
  *Tech Mapping:* Modern **PyQt6** layout orchestration built around deeply responsive Qt Style Sheet (QSS) parameter styling (`src/ui/styles.py`) delivering premium glassmorphic surfaces and high-contrast clinical reading frames.
- **Bhushan:** Relational Database Engine Operations, Multi-table Schema Structuring, Statistical Windowing Aggregations, Seeding Automation, and System Persistence Bindings.  
  *Tech Mapping:* Native **SQLite3** cursor interactions, multi-table cascade definitions linking historical logs (`users`, `prescriptions`, `appointments`), and real-time visualization layer translations powered by **pyqtgraph** (`PlotWidget`/`BarGraphItem`).

## 3. Core Problem Statement

Healthcare data in India is currently scattered, paper-based, or siloed. Patients struggle to understand reports, and government hospitals lack transparent treatment tracking. Data is not structured for real-time monitoring or policy planning.

## 4. Solution Vision

To build a secure, centralized, AI-enabled healthcare platform that:
- Consolidates patient medical data into a unified digital timeline.
- Uses AI to explain medical reports and prescriptions in simple language.
- Enables seamless doctor referrals and tracks treatment progress.
- Provides anonymized dashboards for government monitoring.
- Ensures ethical, consent-based data sharing.

## 5. Key Features

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

## 6. Tech Stack & Implementation Mapping

**Swasthya Connect** is built on a highly modular, secure, and offline-ready technology stack. Below is the full stack mapping with corresponding project file implementations:

### A. Frontend GUI & Styling
- **Framework:** **PyQt6** (`requirements.txt`)  
  *Files:* Main interface layouts across `src/ui/components/*.py` and `src/ui/dashboards/*.py`.
- **Design System:** Vanilla CSS via Qt Style Sheets (QSS)  
  *Files:* `src/ui/styles.py` defines cohesive tokens (Glassmorphic cards, teal/slate colors, border radii, modern typography).
- **Data Visualization:** **pyqtgraph**  
  *Files:* Used heavily in `src/ui/dashboards/patient_dashboard.py` (Custom node graphs, trend charts, dynamic disease/diagnosis frequency bar graphs).

### B. Backend Intelligence & Data Pipelines
- **Core Language:** Python 3.10+  
  *Files:* Application routing in `src/main.py`.
- **Database Engine:** **SQLite3**  
  *Files:* Fully managed in `src/database.py`. Implements complex table joins, transaction handling, and schema definitions (`users`, `medical_records`, `appointments`, `prescriptions`, `referrals`, `treatment_tracking`, `hospital_resources`).
- **AI Processing Server:** **Ollama** (Local execution for absolute patient data privacy)  
  *Files:* Integrated via standard HTTP payload bindings in `src/services/medibrief_service.py` and `src/services/ai_service.py`.
- **AI Models Supported:** Qwen 2.5, Qwen 2 (0.5b), Mistral, Llama 3.

### C. Advanced Feature Implementations & Methods
- **Local PDF/Image Text Extraction (OCR):** Uses `pdfminer.six` and standard text stream parsing.  
  *Method:* `process_pdf_for_text(pdf_path)` in `src/services/ocr_service.py`.
- **Strict No-Hallucination Extraction:** Zero-hallucination structured parsing using an advanced multi-modal JSON prompt framework.  
  *Method:* `generate_json_summary(...)` in `src/services/medibrief_service.py`. Extracts clean arrays for vitals, symptoms, structured medications, and explicit abnormal values.
- **Strict Domain-Filtered Chatbot (RAG Guardrails):** Enforces rigid instruction boundaries to instantly block non-medical queries.  
  *Methods:* `answer_question(...)` in `src/services/medibrief_service.py`, `chat_with_assistant(...)` and `chat_with_assistant_stream(...)` in `src/services/ai_service.py`.
- **Automated Dialog State Flow & Auto-Saving:** Bridges UI window closes to execute background database syncs silently.  
  *Method:* `save_to_db(silent=True)` hooked into `closeEvent(...)` inside `src/ui/components/medibrief_dialog.py`. Automatically writes past appointment histories and distinct prescription row mappings.
- **Multilingual Report Generation (PDF Export):** High-fidelity exported summary documents via ReportLab supporting localized script generation (Devanagari font support for Hindi and Marathi).  
  *Method:* `build_summary_pdf_bytes(...)` in `src/services/medibrief_pdf.py`.

## 7. Project Structure

```text
Swasthya_Connect/
├── src/
│   ├── main.py              # Application Entry Point
│   ├── database.py          # Database Schema & Aggregation Logic
│   ├── ui/                  # UI Interface Implementations
│   │   ├── components/      # Reusable widgets (Medibrief dialogs, Chatbot, Tables)
│   │   └── dashboards/      # Role-specific dashboard graphs & analytics
│   ├── services/            # OCR, Local Ollama integration, PDF Builder
│   └── utils/               # Prompts & static maps
├── data/                    # Local SQLite DB storage & file uploads
├── storage/                 # Persistent record assets
└── scripts/                 # Mock generation workflows
```

---

## 8. Getting Started

### Prerequisites

1.  **Python 3.10+**
2.  **Ollama** installed and active on `localhost:11434`.
3.  **Pull Required Models:**
    ```bash
    ollama pull qwen2:0.5b
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
    source .venv/bin/activate  # Windows: .venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Initialize the Database:**
    The system initializes automatically on startup. To seed sample datasets:
    ```bash
    python seed_data.py
    python generate_doctor_dataset.py
    ```

### Running the Application

Launch the platform:
```bash
python src/main.py
```

---

## 9. Ethics, Privacy & Governance

- **Data Ownership:** Patients retain full control over their health data.
- **Consent-Based:** Data sharing requires explicit patient approval.
- **Anonymized:** Administrative access is restricted to anonymized, aggregated datasets.
- **Local AI:** All medical data processing happens locally via Ollama to ensure privacy.

## 10. License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

*Developed for the "Swasthya Connect" Healthcare Initiative.*

# Cakwe (Remote Job Radar & ATS Studio) 🎯

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6+-3178C6.svg)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-v4-38B2AC.svg)](https://tailwindcss.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)

**Cakwe** is a local-first, privacy-respecting career intelligence platform and automated application assistant designed for software engineers seeking authentic, verified global remote opportunities.

Cakwe aggregates job requisitions directly from public ATS feeds and open job APIs, runs LLM-driven geographic eligibility and ghost-job risk evaluations, and provides an integrated Harvard/MIT-compliant ATS Resume and Cover Letter Studio.

---

## 🌟 Key Features

### 1. Multi-ATS Ingestion & Dynamic Company Discovery
- **Direct Public ATS Integration:** Pulls postings directly from Greenhouse, Lever, Ashby, Workable, SmartRecruiters, and Recruitee public APIs without fragile HTML scraping.
- **Dynamic Sniffing:** Discovers new hiring companies from application URLs, public ATS boards, and open datasets.
- **High-Throughput Concurrency:** Bounded asynchronous polling with polite rate-limiting (`asyncio.Semaphore(5)`).
- **Automated Lifecycle Tracking:** Continuously verifies whether job listings remain active or have closed.

### 2. Strict Cross-Border Eligibility & Anti-Ghost Job Verification
- **Verified Cross-Border Remote:** AI reasoning evaluates contracts (Employer of Record / Deel / Remote.com, Worldwide, APAC timezones). Fails closed on US/EU-only restrictions or unstated visa sponsorship.
- **Ghost Job Risk Scoring:** Detects stale postings, vague job requirements, and unrealistic compensation ranges.
- **Boutique & Independent Startup Filters:** Optional filter to prioritize high-growth startups (10–100 employees) while filtering out massive enterprises or dev platforms.

### 3. Integrated ATS Resume & Cover Letter Studio
- **Mode A (CV Tailoring):** Upload an existing resume (PDF, DOCX, or TXT) to instantly analyze match scores and generate targeted Harvard/MIT single-column bullet points using Google's X-Y-Z formula (`Accomplished [X], as measured by [Y], by doing [Z]`).
- **Mode B (Profile Builder):** Build targeted resumes from scratch using background stories and skill profiles.
- **Export Ready:** Generate downloadable, ATS-compliant `.docx` and `.pdf` files.
- **Cover Letter Generation:** Personalized cover letters tailored to each job description with in-place editing.

### 4. Application Tracker (Kanban Board)
- Track application pipelines from *Saved*, *Applied*, *Interviewing*, *Offered*, to *Rejected* with personal notes and submission dates.

### 5. Local MCP (Model Context Protocol) Server
- Includes an MCP server (`backend/mcp_server.py`) allowing AI coding assistants (Claude Desktop, Cursor, Antigravity) to query verified remote jobs and update tracker statuses via JSON-RPC.

---

## 🏗️ Architecture & Tech Stack

```text
┌────────────────────────────────────────────────────────┐
│                   Cakwe Architecture                   │
├─────────────────────────┬──────────────────────────────┤
│ Frontend (Port 3333)    │ React 19, TypeScript, Vite   │
│                         │ Tailwind CSS v4, Lucide      │
├─────────────────────────┼──────────────────────────────┤
│ Backend API (Port 8888) │ FastAPI, Python 3.12         │
│                         │ HTTPX Async, Pydantic v2     │
├─────────────────────────┼──────────────────────────────┤
│ Intelligence & Parsing  │ Google Gemini (Flash)        │
│                         │ Ollama (Local Fallback)      │
│                         │ PyPDF, python-docx, ReportLab│
├─────────────────────────┼──────────────────────────────┤
│ Database & Storage      │ SQLite (WAL mode, busy_wait) │
└─────────────────────────┴──────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/)
- Google Gemini API Key (get a free key at [Google AI Studio](https://aistudio.google.com))

### 1. Clone the Repository
```bash
git clone https://github.com/alifakbxr/cakwe.git
cd cakwe
```

### 2. Configure Environment Variables
Copy the template `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and set your `GEMINI_API_KEY`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Start with Docker Compose
```bash
docker compose up -d --build
```

Access the interfaces:
- **Frontend Dashboard:** [http://localhost:3333](http://localhost:3333)
- **Backend Swagger Docs:** [http://localhost:8888/docs](http://localhost:8888/docs)

---

## 💻 Manual / Local Development Setup

If you prefer running without Docker:

### Backend (Python)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example .env
uvicorn main:app --reload --port 8000
```

### Frontend (TypeScript / React)
```bash
cd frontend
npm install
npm run dev
```

---

## 🧪 Testing

Run automated tests inside Docker:
```bash
docker compose exec backend pytest -v tests/
```

Or run locally:
```bash
pytest backend/tests/
```

Type check the frontend:
```bash
cd frontend
npx tsc --noEmit
```

---

## 📂 Project Structure

```text
cakwe/
├── backend/
│   ├── sources/             # ATS adapters (Greenhouse, Lever, Ashby, Workable, etc.)
│   ├── tests/               # Pytest suite
│   ├── ai_processor.py      # LLM reasoning and structured extraction
│   ├── database.py          # SQLite schema, indexing & query layer
│   ├── discovery.py         # Autonomous ATS board discovery crawler
│   ├── file_parser.py       # PDF/DOCX/TXT in-memory extraction
│   ├── main.py              # FastAPI endpoints
│   ├── mcp_server.py        # Model Context Protocol (MCP) server
│   ├── poller.py            # Hourly background ingestion worker
│   ├── resume_builder.py    # ReportLab PDF & python-docx generator
│   └── requirements.txt
├── data/                    # SQLite database & local storage (mounted volume)
├── frontend/
│   ├── src/
│   │   ├── components/      # UI Views (Dashboard, Kanban, ATS Studio, Settings)
│   │   ├── types.ts         # Shared TypeScript interfaces
│   │   └── App.tsx          # Main application component
│   ├── package.json
│   └── vite.config.ts
├── .env.example             # Configuration template
├── CONTRIBUTING.md          # Contribution guidelines
├── LICENSE                  # MIT License
├── SECURITY.md              # Security and vulnerability disclosure policy
├── docker-compose.yml
└── README.md
```

---

## 🤝 Contributing

Contributions are warmly welcomed! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on code style, testing requirements, and the pull request process.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

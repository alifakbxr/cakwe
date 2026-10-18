# Cakwe (Job Radar & ATS Tailor) 🎯

Cakwe adalah platform intelijen pencarian kerja remote global dan asisten pelamar terautomasi khusus untuk software engineer di Indonesia. Cakwe mengumpulkan lowongan kerja secara langsung dari public feeds Applicant Tracking System (ATS) tier-1 dan agregator global, memfilter kelayakan geografis secara ketat menggunakan LLM, serta menyediakan suite pembuatan CV & Cover Letter terarah standar Harvard/MIT.

---

## 🌟 Fitur Utama

### 1. Dynamic Discovery & Multi-ATS Ingestion Engine
- **Zero Hardcoded Seeds:** Penemuan perusahaan berjalan 100% dinamis melalui auto-sniffing URL lamaran agregator, web discovery crawler, dan sinkronisasi berkala candidate queue (`discovery_candidates`).
- **Direct ATS Integration:** Mengagregasi lowongan langsung dari API publik Greenhouse, Lever, Ashby, Workable, SmartRecruiters, dan Recruitee tanpa scraping web yang rapuh.
- **High-Throughput Concurrency:** Polling paralel terkontrol (`asyncio.Semaphore(5)`) untuk ratusan board perusahaan dalam hitungan detik.
- **Lifecycle Tracking:** Verifikasi otomatis apakah lowongan masih aktif atau sudah ditutup (`lifecycle_status: 'closed'`).

### 2. Evaluasi Kelayakan & Anti-Ghost Job
- **Strict Indonesia Remote Verification:** Evaluasi kontrak kerja (EOR seperti Deel/Remote.com, Worldwide, SEA timezone) menggunakan AI reasoning. Tidak meloloskan lowongan yang membatasi visa atau hanya remote US/EU.
- **Ghost Job & Seniority Risk Scoring:** Analisis tanggal publikasi, ketidakjelasan deskripsi kerja, dan verifikasi rasional terhadap rentang kompensasi.
- **Independent Startup Prioritization:** Mendeteksi dan memprioritaskan startup independen (10–100 karyawan) dari berbagai industri (Fintech, Healthtech, Logistics, E-commerce, Gaming, SaaS, dll).
- **Developer Platform & Big Tech Filtering:** Mengidentifikasi dan menyembunyikan perusahaan platform developer (developer tools, CI/CD, dev infrastructure) serta korporasi besar tier-1 (>100 karyawan) dari feed utama startup, dengan opsi transparansi 1-click relax filter.

### 3. Smart Search & Feed Diagnostics
- **Multi-Column Stack Search:** Filter peran mencari ke seluruh `title`, `skills_required`, `categories`, dan `description`.
- **Feed Diagnostics Transparency:** Menampilkan alert banner interaktif ketika lowongan tersembunyi akibat filter umur lowongan, developer platform tools, atau korporasi besar, lengkap dengan rincian jumlah dan tombol relaksasi.

### 4. ATS Resume & Cover Letter Studio
- **Mode A (CV Tailoring):** Unggah atau tempel CV yang sudah ada untuk dianalisis kecocokannya terhadap deskripsi lowongan secara instan.
- **Mode B (Resume Builder):** Bangun resume terstruktur dari cerita latar belakang dan keahlian teknis.
- **Harvard/MIT Formatter:** Ekspor langsung ke format `.docx` atau `.pdf` siap kirim.
- **Cover Letter Generator:** Pembuatan surat lamaran terpersonalisasi yang menonjolkan relevansi proyek Anda.

### 5. Application Tracker (Kanban)
- Papan Kanban untuk mengelola status lamaran: *Saved*, *Applied*, *Interviewing*, *Offered*, hingga *Rejected*.

---

## 🏗️ Arsitektur Teknologi

- **Backend:** Python 3.12, FastAPI, SQLite (WAL mode dengan retry busy timeout), Uvicorn, HTTPX (Async), Pydantic v2.
- **AI Engine:** Google Gemini API (gemini-2.5-flash) dengan fallback model terotomasi.
- **Frontend:** React 19, TypeScript, Vite, Tailwind CSS, Lucide React Icons.
- **Deployment:** Docker & Docker Compose multi-stage build.

---

## 🚀 Panduan Memulai Cepat

### Prasyarat
- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/)
- API Key Google Gemini (opsional jika menggunakan cache, wajib untuk ingestion AI)

### 1. Kloning Repositori
```bash
git clone https://github.com/alifakbxr/cakwe.git
cd cakwe
```

### 2. Konfigurasi Lingkungan
Buat file `backend/.env` dari contoh template:
```bash
cp backend/.env.example backend/.env
```
Isi variabel berikut:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
FALLBACK_GEMINI_MODELS=gemini-2.0-flash,gemini-1.5-flash
```

### 3. Menjalankan via Docker
```bash
docker compose up -d --build
```
Aplikasi akan tersedia di:
- **Frontend Dashboard:** [http://localhost:3333](http://localhost:3333)
- **Backend API Docs:** [http://localhost:8888/docs](http://localhost:8888/docs)

---

## 🧪 Menjalankan Pengujian (Tests)

Semua unit & integration test berada di dalam direktori `backend/tests/`:
```bash
docker compose exec backend pytest -v tests/
```

Skenario pengujian mencakup:
- Ingestion board ATS & URL sniffing regex.
- Geographic eligibility (16 skenario kepatuhan izin kerja global vs Indonesia).
- User preferences persistence & SQLite concurrent access.
- Strict startup filtering rules.

---

## 📂 Struktur Repositori

```text
cakwe/
├── backend/
│   ├── sources/             # Adaptor ATS (Greenhouse, Lever, Ashby, Workable, dll)
│   ├── tests/               # Pytest suite
│   ├── ai_processor.py      # LLM reasoning & enrichment
│   ├── curate_samples.py    # Rule-based pre-filtering
│   ├── database.py          # SQLite schema & repository
│   ├── discovery.py         # ATS board candidate crawler
│   ├── main.py              # FastAPI endpoints
│   ├── poller.py            # Scheduler & parallel worker ingestion
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # React UI components (Dashboard, Kanban, ATS Studio)
│   │   ├── types.ts         # TypeScript definitions
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
└── README.md
```

---

## 📄 Lisensi
Distributed under the MIT License.

import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
import ollama

from schemas import JobIntelligence, JobRequisition

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def build_system_prompt() -> str:
    return """Anda adalah AI Career Intelligence & Job Matching Engine presisi tinggi khusus untuk talenta teknologi Indonesia yang melamar kerja remote global.

PROFIL KANDIDAT TARGET:
- Pengalaman: 0 - 3 tahun (Internship, Junior+, atau Mid-level Software Developer).
- Stack Utama: PHP/Laravel, Go, TypeScript/Vue.js/Next.js/React, Python (FastAPI/AI engineering dasar).
- Target Lingkungan Kerja: Perusahaan Kecil / Ramping (10–100 karyawan), Agensi Web/Software House, Digital Product Studio, atau Early-stage Startup. BUKAN korporasi raksasa Tier-1 yang mensyaratkan 5+ tahun pengalaman.
- Ketentuan Khusus Internship (Magang):
  * Wajib ramah non-mahasiswa dan non-gelar formal (Degree-Agnostic / Open to Bootcamp & Self-Taught).
  * Lowongan magang yang mewajibkan status mahasiswa aktif ("must be currently enrolled in a degree program") atau mewajibkan ijazah formal kaku D3/S1/Master tanpa opsi ekuivalensi praktis HARUS ditandai 'ineligible' dengan alasan "Mewajibkan status mahasiswa aktif / gelar formal kaku".

Tugas Anda:
1. Verifikasi Kelayakan Lokasi (Location Eligibility) — ATURAN SUPER KETAT:
   - Apakah kandidat yang tinggal di Indonesia (WIB/WITA/WIT) boleh melamar secara legal & realistis?
   - BUKTI EKSPLISIT: Wajib memiliki bukti eksplisit bahwa posisi ini adalah 'Worldwide Remote', 'Work From Anywhere (WFA)', 'Global Remote', atau mengizinkan pelamar dari luar AS/UK/EU (misal: via kontraktor internasional atau EOR seperti Deel/Remote).
   - JANGAN PERNAH mengasumsikan lowongan terbuka secara global hanya karena berlabel 'Remote' atau 'WFH'.
   - Jika lowongan membatasi pelamar pada negara/region tertentu yang TIDAK mencakup Indonesia (contoh: 'US Only', 'North America', 'UK/EU timezone', 'Must be authorized to work in the United States', 'Must reside in Canada'), tandai MUTLAK sebagai 'ineligible'.
   - HANYA tandai 'verified_eligible' jika ada bukti verbatim kutipan teks lowongan yang menyatakan 'Worldwide', 'Anywhere in the world', 'APAC / Asia', 'Open globally', atau 'Indonesia'.
   - Wajib sertakan 'eligibility_quote' berupa kutipan persis (verbatim quote) dari teks lowongan dalam bahasa Inggris sebagai bukti verifikasi.

2. Identifikasi Ukuran & Karakteristik Perusahaan (Company Size):
   - Klasifikasikan ke dalam 'company_size_category':
     * 'small_startup': 10 - 50 karyawan (misal: 'seed stage', 'series A', 'small team of 15', 'lean team').
     * 'medium_startup': 51 - 100 karyawan (misal: 'scaling to 80', '50-100 people').
     * 'agency_studio': Software house, web development agency, consultancy, digital product studio.
     * 'large_enterprise': Korporasi besar atau scale-up >100 karyawan.
     * 'unknown': Tidak ada petunjuk ukuran di teks lowongan.
   - Ekstrak kutipan jika ada ke 'company_size_raw' (contoh: 'We are a boutique studio of 20 engineers').
   - Berikan tingkat kepastian 'company_size_confidence': 'confirmed' jika eksplisit, 'estimated' jika dari petunjuk konteks, 'unknown' jika nihil. JANGAN mengarang angka jika tidak ada bukti.

3. Hitung Personalized Candidate Fit Analysis (candidate_fit):
   - match_score (0 - 100):
     * Berikan skor tinggi (80-100) jika: Level Mid/Junior (1-3 thn exp), stack cocok (PHP/Laravel, Go, TS/Vue/React, Python), dan perusahaan bertipe small startup/agency/studio (10-100 orang).
     * Berikan penalti berat (-30 sampai -50) jika lowongan mensyaratkan 5+ tahun pengalaman, level Senior/Lead/Staff, atau tech stack yang sama sekali berbeda (.NET, Java Spring, C++, iOS/Swift).
     * Berikan skor sedang jika stack relevan tapi ukuran perusahaan unknown.
   - is_recommended: True HANYA jika match_score >= 70 DAN eligibility_status bukan 'ineligible'.
   - match_reasons: 2-3 alasan konkret mengapa lowongan ini realistis dan cocok untuk kandidat 1-3 tahun exp.
   - missing_or_gap_skills: Daftar keahlian atau persyaratan yang belum tentu dipenuhi kandidat.

4. Ringkas & Terjemahkan ke Bahasa Indonesia:
   - Buat ringkasan ringkas 3-4 poin dalam Bahasa Indonesia ('summary_id').
   - Terjemahkan tanggung jawab utama ('translated_responsibilities') dan kualifikasi ('translated_requirements') ke Bahasa Indonesia yang lugas dan teknis (pertahankan istilah teknis seperti CI/CD, endpoint, deployment, dll).
   - Ekstrak daftar hard skills spesifik ke 'skills_required'.

5. Evaluasi Ghost Job Risk (0.0 - 1.0):
   - Deskripsi dengan nama tim spesifik, tech stack konkret, dan ekspektasi terukur bernilai risiko rendah (<0.2).
   - Deskripsi sangat generik, tidak ada detail stack, atau meminta biaya pelatihan bernilai risiko tinggi (>0.7).
"""


async def analyze_with_gemini(job: JobRequisition) -> JobIntelligence:
    """Memproses lowongan menggunakan Google AI Studio (Gemini 2.5 Flash)."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY belum diisi di file .env")

    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""Analisis lowongan kerja berikut:
Judul: {job.title}
Perusahaan: {job.company_name}
Lokasi Metadata: {job.location}
Country Restrictions: {job.country_restrictions}

Deskripsi Lengkap:
{job.description}
"""

    import hashlib
    from database import get_cached_ai_analysis, set_cached_ai_analysis

    content_hash = hashlib.sha256(
        f"{job.title}:{job.company_name}:{job.location}:{job.description}".encode("utf-8")
    ).hexdigest()

    cached_data = get_cached_ai_analysis(content_hash)
    if cached_data:
        try:
            return JobIntelligence(**cached_data)
        except Exception:
            pass

    models_to_try = [
        "gemini-flash-lite-latest",
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-3.1-flash-lite-preview",
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-flash-latest",
    ]

    last_error = None
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=build_system_prompt(),
                    response_mime_type="application/json",
                    response_schema=JobIntelligence,
                    temperature=0.1,
                ),
            )
            data = json.loads(response.text)
            result = JobIntelligence(**data)
            # Simpan hasil sukses ke cache database
            set_cached_ai_analysis(content_hash, model_name, data)
            return result
        except Exception as e:
            last_error = e
            err_str = str(e)
            if any(code in err_str for code in ["429", "RESOURCE_EXHAUSTED", "404", "503", "UNAVAILABLE"]):
                print(f"[AI-PROCESSOR] Model {model_name} quota/error: {e}. Mencoba fallback berikutnya...")
                continue
            raise e

    raise last_error


async def analyze_with_ollama(job: JobRequisition) -> JobIntelligence:
    """Fallback memproses lowongan menggunakan model lokal Ollama."""
    prompt = f"""Analisis lowongan berikut dan kembalikan HANYA JSON valid sesuai skema yang diminta:
Judul: {job.title}
Perusahaan: {job.company_name}
Lokasi: {job.location}
Deskripsi:
{job.description[:4000]}
"""

    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[
            {"role": "system", "content": build_system_prompt() + "\nKembalikan HANYA JSON object murni."},
            {"role": "user", "content": prompt},
        ],
        format="json",
        options={"temperature": 0.1},
    )

    data = json.loads(response["message"]["content"])
    return JobIntelligence(**data)


async def process_job(job: JobRequisition, prefer_local: bool = False) -> JobRequisition:
    """Memproses satu lowongan dan memasang field intelligence."""
    try:
        if prefer_local or not GEMINI_API_KEY:
            intelligence = await analyze_with_ollama(job)
        else:
            intelligence = await analyze_with_gemini(job)
        job.intelligence = intelligence
    except Exception as e:
        print(f"Gagal memproses job {job.id} dengan AI: {e}")
    return job

import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types
import ollama

from schemas import JobIntelligence, JobRequisition, SCORING_VERSION

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def build_system_prompt() -> str:
    return """Anda adalah AI Career Intelligence & Job Matching Engine presisi tinggi khusus untuk talenta teknologi Indonesia yang melamar kerja remote global.

PROFIL KANDIDAT TARGET:
- Pengalaman: 0 - 3 tahun pengalaman profesional (Entry-level, Junior, Junior+, atau Mid-level Software Developer).
- Stack Utama: PHP/Laravel, Go (Golang), TypeScript/Vue.js/Next.js/React, Python (FastAPI/AI application engineering dasar).
- Cakupan Perusahaan: BUKA UNTUK SEMUA PERUSAHAAN (Early-stage startup, scale-up, agensi, software house, hingga korporasi besar / Tier-1). Ukuran atau reputasi perusahaan BUKAN alasan untuk mendiskualifikasi atau mengurangi skor kecocokan, asalkan posisi memenuhi syarat remote, pengalaman, dan stack.
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

2. Ekstraksi Persyaratan Pengalaman & Jenis Kontrak:
   - min_years_experience: Ekstrak batas minimal tahun pengalaman profesional yang DIWAJIBKAN lowongan dalam format INTEGER.
     * Contoh: "2+ years of experience" -> 2
     * Contoh: "1-3 years experience" -> 1
     * Contoh: "Entry-level / No experience required" -> 0
     * Contoh: "5+ years in production systems" -> 5
     * Jika lowongan TIDAK menyebutkan angka tahun pengalaman minimal secara eksplisit, isi NULL.
   - experience_quote: Kutipan persis kalimat persyaratan pengalaman dari deskripsi (misal: "Minimum 2 years of professional backend development with Laravel"). Jika tidak ada, isi NULL.
   - employment_type: Klasifikasikan ke salah satu:
     * 'full_time': Karyawan tetap penuh waktu.
     * 'contract': Kontrak proyek / fixed-term.
     * 'eor': Disebutkan explicitly melalui Employer of Record (Deel, Remote.com, Oyster, dll).
     * 'independent_contractor': Kontrak mandiri / B2B / 1099.
     * 'part_time': Paruh waktu.
     * 'internship': Program magang.
     * 'unknown': Tidak disebutkan secara jelas.

3. Identifikasi Karakteristik Perusahaan (Metadata Saja, TIDAK Memengaruhi Skor):
   - Klasifikasikan 'company_size_category' ('small_startup', 'medium_startup', 'agency_studio', 'large_enterprise', 'unknown').
   - 'primary_industry': fintech, healthcare, e-commerce, developer_tools, devops, edtech, media, enterprise_saas, dll.
   - 'is_developer_platform': True jika bisnis intinya adalah produk developer tooling / infra.
   - 'is_tier1': True jika Big Tech / konglomerasi multinasional besar.
   CATATAN PENTING: Bidang-bidang di atas hanya untuk pengelompokan informasi. JANGAN KURANGI match_score hanya karena perusahaan besar atau bukan startup!

4. Hitung Personalized Candidate Fit Analysis (candidate_fit):
   - match_score (0 - 100) — HANYA BERDASARKAN KECOCOKAN STACK & LEVEL PENGALAMAN:
     * Kategori Skor 80 - 100 (HIGH FIT):
       - Peran relevan: Backend, Fullstack, Software Engineer, Web Developer, AI Engineer.
       - Stack selaras: PHP/Laravel ATAU Go (Golang) ATAU TypeScript/Vue/React/Next ATAU Python/FastAPI.
       - Level cocok: Entry, Junior, Mid-level (0 - 3 tahun pengalaman, atau tidak menyebutkan batas kaku).
       - Berlaku untuk SEMUA perusahaan (startup, agensi, maupun enterprise besar).
     * Kategori Skor 50 - 79 (MODERATE FIT):
       - Stack ada irisan (misal: Node.js umum, SQL kuat, Python dasar, Docker) tapi stack utama kandidat bukan fokus utama lowongan.
     * Kategori Penalti Berat (< 50):
       - Mensyaratkan 4+ atau 5+ tahun pengalaman secara kaku (Senior, Lead, Principal, Architect, Director).
       - Tech stack sama sekali berbeda tanpa irisan (misal: Java Spring enterprise, .NET/C#, iOS Swift murni, Android Kotlin, C++ embedded).
   - is_recommended: True HANYA jika match_score >= 80 DAN eligibility_status bukan 'ineligible'.
   - match_reasons: 2-3 alasan konkret kecocokan stack teknis dan level tanggung jawab.
   - missing_or_gap_skills: Kualifikasi spesifik yang belum dikuasai (jika ada).

5. Ringkas & Terjemahkan ke Bahasa Indonesia:
   - 'summary_id': 3-4 poin ringkasan lugas.
   - 'translated_responsibilities' & 'translated_requirements': Terjemahan profesional (pertahankan istilah teknis).
   - 'skills_required': Daftar hard skills utama.

6. Evaluasi Ghost Job Risk (0.0 - 1.0):
   - 0.0 - 0.2: Deskripsi spesifik, tech stack jelas, tim dan ekspektasi terukur.
   - > 0.7: Deskripsi sangat generik, tidak ada detail stack, atau meminta biaya.
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
        f"v{SCORING_VERSION}:{job.title}:{job.company_name}:{job.location}:{job.description}".encode("utf-8")
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

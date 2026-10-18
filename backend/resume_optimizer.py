import os
import json
from google import genai
from google.genai import types
from schemas import ResumeTailorResponse, JobRequisition
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


def build_optimizer_prompt() -> str:
    return """Anda adalah Principal Technical Recruiter & ATS Optimization Specialist untuk pasar rekrutmen global (Silicon Valley, Eropa, APAC).
Tugas Anda: Mengoptimalkan resume kandidat agar menembus mesin parser ATS (Greenhouse, Lever, Ashby, Workday) dan mengesankan Engineering Manager.

ATURAN KETAT ANTI-HALUSINASI:
1. TIDAK BOLEH mengarang pengalaman kerja, perusahaan, atau gelar yang tidak ada di resume asli kandidat.
2. Setiap bullet point HARUS menggunakan formula dampak terukur Google: "Accomplished [X] as measured by [Y], by doing [Z]" diawali Strong Action Verbs (mis: Architected, Spearheaded, Refactored, Accelerated, Engineered).
3. Jika metrik angka tidak tersedia di resume asli, berikan estimasi realistis dalam placeholder [X%] atau [N ms] agar kandidat bisa mengisinya dengan fakta riil.
4. Integrasikan hard skills dan keywords dari Job Description ke dalam konteks pengalaman yang relevan.
5. Hitung match_score ATS secara realistis (0-100%).
"""


async def tailor_resume_for_job(resume_text: str, job: JobRequisition) -> ResumeTailorResponse:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY belum disetel di .env")

    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""Target Lowongan:
Posisi: {job.title}
Perusahaan: {job.company_name}
Deskripsi Lowongan:
{job.description}

Resume Kandidat Saat Ini:
{resume_text}
"""

    # Daftar model dengan automatic fallback bila salah satu model terkena 429 quota exhaustion, 503 high demand, atau 404
    models_to_try = [
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
        "gemini-3.8-flash",
    ]

    last_error = None
    for model_name in models_to_try:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=build_optimizer_prompt(),
                    response_mime_type="application/json",
                    response_schema=ResumeTailorResponse,
                    temperature=0.2,
                ),
            )
            data = json.loads(response.text)
            return ResumeTailorResponse(**data)
        except Exception as e:
            last_error = e
            err_str = str(e)
            if any(code in err_str for code in ["429", "RESOURCE_EXHAUSTED", "404", "503", "UNAVAILABLE"]):
                print(f"[RESUME-OPTIMIZER] Model {model_name} quota/error: {e}. Mencoba fallback berikutnya...")
                continue
            raise e

    raise last_error

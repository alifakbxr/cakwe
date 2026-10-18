import json
from typing import Optional

from fastapi import (
    BackgroundTasks,
    FastAPI,
    File,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from database import (
    get_all_jobs,
    get_connection,
    get_tailored_resumes_for_job,
    init_db,
    save_tailored_resume_version,
    get_discovery_stats,
    dismiss_job,
    get_user_preferences,
    save_user_preferences,
    reset_user_preferences,
)
from file_parser import parse_resume_document
from poller import run_sync_cycle
from resume_builder import (
    build_resume_mode_b,
    export_resume_to_docx_bytes,
    export_resume_to_pdf_bytes,
    optimize_resume_mode_a,
    generate_cover_letter_only,
    export_cover_letter_to_docx_bytes,
    export_cover_letter_to_pdf_bytes,
)
from pydantic import BaseModel
from resume_optimizer import tailor_resume_for_job
from schemas import (
    FullResumeData,
    JobRequisition,
    ManualProfileBuildRequest,
    OptimizedResumeResult,
    ResumeTailorRequest,
    ResumeTailorResponse,
    UserPreferences,
)

from discovery import process_discovery_candidates



app = FastAPI(
    title="Remote Job Radar API",
    description="Local-First Cross-Border Career Intelligence & Verified Job Radar",
    version="1.0.0",
)

# Izinkan CORS khusus origin frontend lokal
ALLOWED_ORIGINS = [
    "http://localhost:3333",
    "http://127.0.0.1:3333",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class CoverLetterRegenRequest(BaseModel):
    job_id: str
    resume: FullResumeData
class CoverLetterExportRequest(BaseModel):
    candidate_name: Optional[str] = None
    applicant_name: Optional[str] = None
    company_name: Optional[str] = None
    company: Optional[str] = None
    job_title: str
    cover_letter_text: str

    @property
    def resolved_candidate_name(self) -> str:
        return self.candidate_name or self.applicant_name or "Candidate"

    @property
    def resolved_company_name(self) -> str:
        return self.company_name or self.company or "Hiring Team"




@app.on_event("startup")
def startup():
    init_db()


def parse_job_row(row: dict) -> dict:
    """Mengubah string JSON di SQLite kembali menjadi struktur data Python/JSON."""
    res = dict(row)
    for field in [
        "country_restrictions",
        "seniority",
        "categories",
        "summary_id",
        "translated_responsibilities",
        "translated_requirements",
        "skills_required",
        "match_reasons",
        "missing_skills",
    ]:
        if res.get(field):
            try:
                res[field] = json.loads(res[field])
            except Exception:
                res[field] = []
        else:
            res[field] = []
    return res


@app.get("/api/jobs")
def list_jobs(
    status: Optional[str] = Query(None, description="Filter kelayakan (misal: verified_eligible)"),
    only_small: Optional[bool] = Query(None, description="Hanya perusahaan kecil/studio/agency (10-100 orang)"),
    role: Optional[str] = Query(None, description="Filter peran (ALL, AI, BACKEND, LARAVEL, FULLSTACK)"),
    search: Optional[str] = Query(None, description="Pencarian judul, perusahaan, skill"),
    include_closed: Optional[bool] = Query(None, description="Tampilkan lowongan closed"),
    max_ghost_risk: Optional[float] = Query(None, description="Maksimal skor ghost risk"),
    min_salary: Optional[float] = Query(None, description="Filter gaji minimal tahunan USD"),
):
    """Mengambil daftar lowongan yang telah lolos Stage A & User Preferences:
    - Verified Eligible dari Indonesia / Worldwide
    - Verified Small Company (10-100 / Agency) sesuai konfigurasi preferensi
    - Freshness <= preferensi pengguna (default 14 hari)
    - Active lifecycle (bukan expired/closed/dismissed)
    """
    user_prefs = get_user_preferences()

    # Tentukan parameter efektif
    eff_status = status if status is not None else ("verified_eligible" if user_prefs.strict_indonesia_eligible else None)
    eff_only_small = only_small if only_small is not None else user_prefs.only_small_companies
    eff_include_closed = include_closed if include_closed is not None else user_prefs.show_closed_jobs
    eff_ghost_risk = max_ghost_risk if max_ghost_risk is not None else user_prefs.max_ghost_risk

    # Override min_salary di preferences jika diberikan di query
    if min_salary is not None:
        user_prefs.min_salary_usd = min_salary

    jobs = get_all_jobs(
        status=eff_status,
        only_small_companies=eff_only_small,
        include_closed=eff_include_closed,
        target_role=role,
        search=search,
        preferences=user_prefs,
    )
    parsed = [parse_job_row(j) for j in jobs]

    # Filter berdasarkan batas risiko ghost job jika ditentukan
    if eff_ghost_risk is not None:
        parsed = [
            j for j in parsed
            if j.get("ghost_risk_score") is None or j.get("ghost_risk_score") <= eff_ghost_risk
        ]

    from database import get_jobs_filter_diagnostics
    diagnostics = get_jobs_filter_diagnostics()

    return {
        "count": len(parsed),
        "jobs": parsed,
        "active_preferences": user_prefs.model_dump(),
        "diagnostics": diagnostics,
    }



@app.get("/api/jobs/{job_id:path}")
def get_job_detail(job_id: str):
    """Mengambil detail satu lowongan kerja."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Lowongan tidak ditemukan")

    return parse_job_row(dict(row))


class DismissJobRequest(BaseModel):
    reason: str = "other"


@app.post("/api/jobs/{job_id:path}/dismiss")
def api_dismiss_job(job_id: str, payload: DismissJobRequest):
    """Menyembunyikan lowongan yang tidak relevan dengan alasan spesifik."""
    success = dismiss_job(job_id, payload.reason)
    if not success:
        raise HTTPException(status_code=404, detail="Lowongan tidak ditemukan atau gagal di-dismiss")
    return {"status": "ok", "message": "Lowongan berhasil disembunyikan", "dismiss_reason": payload.reason}



@app.get("/api/stats")
def get_radar_stats():
    """Mengambil statistik radar lowongan kerja dengan fokus peluang verified & small company."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM jobs")
    total = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as verified FROM jobs WHERE eligibility_status = 'verified_eligible'")
    verified = cursor.fetchone()["verified"]

    cursor.execute("""
    SELECT COUNT(*) as verified_small 
    FROM jobs 
    WHERE eligibility_status = 'verified_eligible' 
      AND company_size_category IN ('small_startup', 'medium_startup', 'agency_studio')
      AND (lifecycle_status = 'active' OR lifecycle_status IS NULL)
    """)
    verified_small = cursor.fetchone()["verified_small"]

    cursor.execute("SELECT COUNT(*) as low_risk FROM jobs WHERE ghost_risk_score <= 0.2")
    low_risk = cursor.fetchone()["low_risk"]

    cursor.execute("SELECT AVG(ghost_risk_score) as avg_risk FROM jobs WHERE ghost_risk_score IS NOT NULL")
    avg_risk = cursor.fetchone()["avg_risk"] or 0.0

    conn.close()

    return {
        "total_jobs": total,
        "verified_eligible_jobs": verified,
        "verified_small_company_jobs": verified_small,
        "low_ghost_risk_jobs": low_risk,
        "average_ghost_risk_score": round(avg_risk, 2),
    }


@app.post("/api/sync")
async def trigger_sync(background_tasks: BackgroundTasks):
    """Menjalankan siklus polling & ekstraksi AI secara instan di latar belakang."""
    background_tasks.add_task(run_sync_cycle)
    return {"status": "ok", "message": "Sinkronisasi dimulai di background"}


@app.post("/api/resume/tailor", response_model=ResumeTailorResponse)
async def tailor_resume(req: ResumeTailorRequest):
    """Mengoptimalkan resume kandidat secara presisi untuk menembus ATS lowongan tertentu."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs WHERE id = ?", (req.job_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Lowongan tidak ditemukan")

    raw_dict = parse_job_row(dict(row))
    job = JobRequisition(**raw_dict)

    try:
        result = await tailor_resume_for_job(req.resume_text, job)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mengoptimasi resume: {str(e)}")

@app.post("/api/resume/parse-file")
async def parse_resume_file(file: UploadFile = File(...)):
    """Menerima unggahan file resume (PDF/DOCX/TXT) dan mengekstrak teksnya secara aman in-memory."""
    contents = await file.read()
    try:
        extracted_text = parse_resume_document(file.filename, contents)
        return {"filename": file.filename, "text": extracted_text}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/resume/generate-mode-a", response_model=OptimizedResumeResult)
async def generate_resume_mode_a(req: ResumeTailorRequest):
    """Mode A: Optimasi dokumen resume mentah yang diunggah / dipaste."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs WHERE id = ?", (req.job_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Lowongan tidak ditemukan")

    raw_dict = parse_job_row(dict(row))
    job = JobRequisition(**raw_dict)

    try:
        result = await optimize_resume_mode_a(req.resume_text, job)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal memproses resume: {str(e)}")


@app.post("/api/resume/generate-mode-b", response_model=OptimizedResumeResult)
async def generate_resume_mode_b(req: ManualProfileBuildRequest):
    """Mode B: Pembuatan resume terarah dari data profil tanpa resume lama."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs WHERE id = ?", (req.job_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Lowongan tidak ditemukan")

    raw_dict = parse_job_row(dict(row))
    job = JobRequisition(**raw_dict)

    try:
        result = await build_resume_mode_b(req, job)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal membangun resume: {str(e)}")


@app.post("/api/resume/save")
def save_resume_version(payload: dict):
    """Menyimpan versi final resume yang sudah disetujui/diedit pengguna."""
    job_id = payload.get("job_id")
    job_title = payload.get("job_title", "")
    company = payload.get("company_name", "")
    resume = payload.get("resume")
    analysis = payload.get("analysis", {})
    cover_letter = payload.get("cover_letter", "")

    if not job_id or not resume:
        raise HTTPException(status_code=400, detail="Data tidak lengkap")

    save_tailored_resume_version(job_id, job_title, company, resume, analysis, cover_letter)
    return {"status": "ok", "message": "Versi resume berhasil disimpan"}


@app.get("/api/resume/history/{job_id:path}")
def get_resume_history(job_id: str):
    """Mengambil daftar riwayat versi resume yang pernah dibuat untuk lowongan ini."""
    return get_tailored_resumes_for_job(job_id)


@app.post("/api/resume/export-docx")
def export_docx(resume: FullResumeData, template: Optional[str] = Query("HARVARD", description="Template style: HARVARD, MODERN, TECHNICAL")):
    """Mengonversi objek resume menjadi dokumen Word (.docx) standar ATS dengan template pilihan."""
    docx_stream = export_resume_to_docx_bytes(resume, template=template or "HARVARD")
    data_bytes = docx_stream.getvalue()
    clean_name = resume.contact.full_name.strip().replace(" ", "_") or "Candidate"
    filename = f"Resume_{clean_name}_{template}.docx"

    return Response(
        content=data_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename}',
            "Content-Length": str(len(data_bytes)),
            "Content-Type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "Access-Control-Expose-Headers": "Content-Disposition, Content-Length",
        },
    )


@app.post("/api/resume/export-pdf")
def export_pdf(resume: FullResumeData, template: Optional[str] = Query("HARVARD", description="Template style: HARVARD, MODERN, TECHNICAL")):
    """Mengonversi objek resume menjadi dokumen PDF 1 halaman standar ATS dengan template pilihan."""
    pdf_stream = export_resume_to_pdf_bytes(resume, template=template or "HARVARD")
    data_bytes = pdf_stream.getvalue()
    clean_name = resume.contact.full_name.strip().replace(" ", "_") or "Candidate"
    filename = f"Resume_{clean_name}_{template}.pdf"

    return Response(
        content=data_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename}',
            "Content-Length": str(len(data_bytes)),
            "Content-Type": "application/pdf",
            "Accept-Ranges": "bytes",
            "Access-Control-Expose-Headers": "Content-Disposition, Content-Length",
        },
    )


@app.post("/api/resume/validate")
def api_validate_resume(resume: FullResumeData):
    """Menjalankan audit lokal terhadap kelayakan format dokumen bagi sistem ATS."""
    from resume_builder import validate_resume_data
    return validate_resume_data(resume)

from database import (
    get_all_tracked_applications,
    get_application,
    upsert_application,
    get_active_companies,
    upsert_company,
    get_latest_sync_logs,
)
from schemas import ApplicationUpdateRequest

# --- APPLICATION TRACKER ENDPOINTS ---
@app.get("/api/applications")
def list_applications(status: Optional[str] = None):
    """Mengambil daftar lowongan yang sedang di-track aplikasinya."""
    return {"applications": get_all_tracked_applications(status)}


@app.get("/api/applications/{job_id:path}")
def get_job_application_status(job_id: str):
    """Mengambil status pelacakan untuk satu lowongan."""
    app_data = get_application(job_id)
    return {"application": app_data}


@app.post("/api/applications/{job_id:path}")
def update_job_application(job_id: str, payload: ApplicationUpdateRequest):
    """Memperbarui atau menyimpan status aplikasi pelamar untuk suatu lowongan."""
    updated = upsert_application(
        job_id=job_id,
        status=payload.status.value,
        applied_date=payload.applied_date,
        notes=payload.notes,
        follow_up_date=payload.follow_up_date,
    )
    return {"message": "Status lamaran berhasil diperbarui", "application": updated}


# --- SYNC & MONITORING ENDPOINTS ---
@app.get("/api/sync/status")
def get_sync_status():
    """Mengambil riwayat log sinkronisasi terakhir."""
    logs = get_latest_sync_logs(limit=20)
    companies = get_active_companies()
    return {
        "latest_logs": logs,
        "total_active_companies": len(companies),
        "ats_breakdown": {
            "greenhouse": len([c for c in companies if c["ats_provider"] == "greenhouse"]),
            "lever": len([c for c in companies if c["ats_provider"] == "lever"]),
            "ashby": len([c for c in companies if c["ats_provider"] == "ashby"]),
        }
    }


@app.post("/api/sync/trigger")
async def trigger_manual_sync(background_tasks: BackgroundTasks):
    """Memicu siklus sinkronisasi baru secara manual di background."""
    background_tasks.add_task(run_sync_cycle)
    return {"message": "Siklus sinkronisasi Multi-ATS berhasil dipicu di background."}


# --- USER PREFERENCES ENDPOINTS ---
@app.get("/api/preferences")
def api_get_preferences():
    """Mengambil preferensi pencarian dan radar pengguna saat ini dari database."""
    prefs = get_user_preferences()
    return prefs.model_dump()


@app.put("/api/preferences")
def api_update_preferences(payload: UserPreferences):
    """Menyimpan atau memperbarui seluruh atau bagian preferensi secara dinamis & persisten."""
    saved = save_user_preferences(payload)
    return {"message": "Preferensi berhasil disimpan secara permanen", "preferences": saved.model_dump()}


@app.post("/api/preferences/reset")
def api_reset_preferences():
    """Mengembalikan seluruh preferensi ke pengaturan bawaan (Worldwide & SEA, min salary $1000/bln)."""
    default_prefs = reset_user_preferences()
    return {"message": "Preferensi telah direset ke default pabrik", "preferences": default_prefs.model_dump()}


@app.post("/api/preferences/rerun-discovery")
async def api_rerun_discovery(background_tasks: BackgroundTasks):
    """Memicu siklus sinkronisasi dan evaluasi ulang feed lowongan dengan preferensi terbaru."""
    background_tasks.add_task(run_sync_cycle)
    return {"message": "Penyelarasan radar dan penemuan lowongan baru dengan preferensi Anda sedang berjalan di latar belakang."}


# --- COMPANY REGISTRY ENDPOINTS ---
@app.get("/api/companies")
def list_companies():
    """Melihat daftar perusahaan dalam Company Registry."""
    return {"companies": get_active_companies()}



@app.post("/api/resume/regenerate-cover-letter")
async def api_regenerate_cover_letter(payload: CoverLetterRegenRequest):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM jobs WHERE id = ?", (payload.job_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Lowongan tidak ditemukan")

    job = JobRequisition(**parse_job_row(dict(row)))
    new_letter = await generate_cover_letter_only(payload.resume, job)
    return {"cover_letter": new_letter}


@app.post("/api/resume/export-cover-letter-docx")
def api_export_cover_letter_docx(payload: CoverLetterExportRequest):
    candidate_name = payload.resolved_candidate_name
    company_name = payload.resolved_company_name
    file_stream = export_cover_letter_to_docx_bytes(
        candidate_name=candidate_name,
        company_name=company_name,
        job_title=payload.job_title,
        cover_letter_text=payload.cover_letter_text,
    )
    data_bytes = file_stream.getvalue()
    clean_name = candidate_name.strip().replace(" ", "_")
    clean_company = company_name.strip().replace(" ", "_")
    filename = f"Cover_Letter_{clean_name}_{clean_company}.docx"
    media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    return Response(
        content=data_bytes,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename}',
            "Content-Length": str(len(data_bytes)),
            "Content-Type": media_type,
            "Accept-Ranges": "bytes",
            "Access-Control-Expose-Headers": "Content-Disposition, Content-Length",
        },
    )


@app.post("/api/resume/export-cover-letter-pdf")
def api_export_cover_letter_pdf(payload: CoverLetterExportRequest):
    candidate_name = payload.resolved_candidate_name
    company_name = payload.resolved_company_name
    file_stream = export_cover_letter_to_pdf_bytes(
        candidate_name=candidate_name,
        company_name=company_name,
        job_title=payload.job_title,
        cover_letter_text=payload.cover_letter_text,
    )
    data_bytes = file_stream.getvalue()
    clean_name = candidate_name.strip().replace(" ", "_")
    clean_company = company_name.strip().replace(" ", "_")
    filename = f"Cover_Letter_{clean_name}_{clean_company}.pdf"
    media_type = "application/pdf"

    return Response(
        content=data_bytes,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename}',
            "Content-Length": str(len(data_bytes)),
            "Content-Type": media_type,
            "Accept-Ranges": "bytes",
            "Access-Control-Expose-Headers": "Content-Disposition, Content-Length",
        },
    )

@app.get("/api/discovery/stats")
def api_get_discovery_stats():
    """Mengambil statistik discovery dan verifikasi board ATS."""
    return get_discovery_stats()
    
@app.post("/api/discovery/trigger")
def api_trigger_discovery(background_tasks: BackgroundTasks):
    """Menjalankan automated web crawler & verifikasi kandidat discovery di background."""
    from discovery import run_public_web_discovery
    background_tasks.add_task(run_public_web_discovery)
    return {"status": "ok", "message": "Public Web Crawler & Discovery verification task scheduled in background"}

@app.post("/api/discovery/import-github")
def api_import_github_slugs(background_tasks: BackgroundTasks):
    """Mengimpor ribuan slug perusahaan aktif dari repositori GitHub (OpenJobs & Pupila)."""
    from discovery import ingest_github_slug_datasets
    background_tasks.add_task(ingest_github_slug_datasets)
    return {"status": "ok", "message": "GitHub OpenJobs & Pupila slug ingestion scheduled in background"}
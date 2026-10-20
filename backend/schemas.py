from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

# Versi aturan scoring AI. Naikkan setiap kali prompt/aturan match_score berubah
# agar cache AI tidak dipakai ulang dan lowongan lama bisa di-rescore (lihat rescore_jobs.py).
SCORING_VERSION = 2


class EmploymentType(str, Enum):
    FULL_TIME = "full_time"
    CONTRACT = "contract"
    EOR = "eor"                                   # Employer of Record (Deel, Remote.com, Oyster, dll)
    INDEPENDENT_CONTRACTOR = "independent_contractor"
    PART_TIME = "part_time"
    INTERNSHIP = "internship"
    UNKNOWN = "unknown"


class EligibilityStatus(str, Enum):
    VERIFIED_ELIGIBLE = "verified_eligible"
    LIKELY_ELIGIBLE = "likely_eligible"
    UNKNOWN = "unknown"
    INELIGIBLE = "ineligible"


class CompanySizeCategory(str, Enum):
    SMALL_STARTUP = "small_startup"       # 10-50 karyawan
    MEDIUM_STARTUP = "medium_startup"     # 51-100 karyawan
    AGENCY_STUDIO = "agency_studio"       # Web development agency, software house, digital product studio
    LARGE_ENTERPRISE = "large_enterprise" # 100+ karyawan
    UNKNOWN = "unknown"                   # Tidak ada informasi meyakinkan


class SizeConfidence(str, Enum):
    CONFIRMED = "confirmed"
    ESTIMATED = "estimated"
    UNKNOWN = "unknown"


class CandidateFitAnalysis(BaseModel):
    """Hasil kalkulasi kecocokan lowongan dengan profil talenta 0-3 tahun exp."""
    match_score: int = Field(..., ge=0, le=100, description="Skor kecocokan 0-100 HANYA berdasarkan relevansi stack, kecocokan level pengalaman, dan relevansi peran. Ukuran/reputasi perusahaan TIDAK memengaruhi skor.")
    is_recommended: bool = Field(..., description="True jika lowongan sangat realistis dan direkomendasikan untuk dilamar")
    match_reasons: List[str] = Field(..., description="Poin-poin mengapa lowongan ini cocok (misal: stack Laravel/Vue cocok, tim ramping)")
    missing_or_gap_skills: List[str] = Field(default=[], description="Kualifikasi yang menjadi tantangan/gap (jika ada)")


class JobIntelligence(BaseModel):
    """Hasil analisis AI terhadap satu lowongan kerja."""

    eligibility_status: EligibilityStatus = Field(
        ...,
        description="Status kelayakan pelamar domisili Indonesia (WIB/WITA/WIT)",
    )
    eligibility_quote: str = Field(
        ...,
        description="Kutipan verbatim bahasa Inggris dari teks lowongan yang membuktikan status kelayakan lokasi/kontrak",
    )
    summary_id: List[str] = Field(
        ...,
        description="Ringkasan 3-4 poin dalam Bahasa Indonesia mengenai pekerjaan ini dan perusahaannya",
    )
    translated_responsibilities: List[str] = Field(
        ...,
        description="Tanggung jawab utama yang diterjemahkan ke Bahasa Indonesia yang lugas dan profesional",
    )
    translated_requirements: List[str] = Field(
        ...,
        description="Persyaratan dan kualifikasi yang diterjemahkan ke Bahasa Indonesia",
    )
    skills_required: List[str] = Field(
        ...,
        description="Daftar keahlian teknis/hard skills yang wajib dikuasai (mis: Laravel, FastAPI, Docker, PyTorch)",
    )
    ghost_risk_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Estimasi risiko lowongan fiktif/ghost job (0.0 sangat aman, 1.0 sangat berisiko)",
    )
    ghost_risk_reason: str = Field(
        ...,
        description="Alasan penilaian risiko ghost job (misal: deskripsi sangat generik, atau sebaliknya sangat spesifik dengan tech stack jelas)",
    )

    # Identifikasi Ukuran & Karakteristik Perusahaan (Target: Independent Startups 10-100 orang)
    company_size_category: CompanySizeCategory = Field(
        default=CompanySizeCategory.UNKNOWN,
        description="Kategori ukuran perusahaan (small_startup: 10-50, medium_startup: 51-100, agency_studio, large_enterprise, unknown)"
    )
    company_size_raw: Optional[str] = Field(
        default=None,
        description="Kutipan/ekstraksi teks ukuran tim dari lowongan jika ada (misal: 'team of 25', '50-100 employees')"
    )
    company_size_confidence: SizeConfidence = Field(
        default=SizeConfidence.UNKNOWN,
        description="Tingkat kepastian estimasi ukuran perusahaan (confirmed, estimated, unknown)"
    )
    primary_industry: Optional[str] = Field(
        default="unknown",
        description="Industri primer bisnis perusahaan (misal: fintech, healthcare, e-commerce, logistics, edtech, developer_tools, devops)"
    )
    is_developer_platform: bool = Field(
        default=False,
        description="True jika produk/layanan utama perusahaan adalah platform/tools/infrastruktur khusus developer (mis: code hosting, CI/CD, dev tooling, API platform)"
    )
    is_tier1: bool = Field(
        default=False,
        description="True jika perusahaan adalah Big Tech, konglomerasi raksasa, atau korporasi multinasional Tier-1"
    )

    # Persyaratan keras yang dapat difilter (bukan bagian dari match_score)
    min_years_experience: Optional[int] = Field(
        default=None,
        ge=0,
        le=30,
        description="Minimal tahun pengalaman profesional yang DIWAJIBKAN lowongan (angka terkecil dari rentang, mis. '2-4 years' -> 2). null jika tidak disebutkan sama sekali."
    )
    experience_quote: Optional[str] = Field(
        default=None,
        description="Kutipan verbatim persyaratan pengalaman dari teks lowongan (null jika tidak ada)"
    )
    employment_type: EmploymentType = Field(
        default=EmploymentType.UNKNOWN,
        description="Jenis hubungan kerja: full_time, contract, eor, independent_contractor, part_time, internship, unknown"
    )

    # Personalized Match untuk Profil 0-3 Thn (PHP/Laravel, Go, Vue/TS, Python/AI)
    candidate_fit: Optional[CandidateFitAnalysis] = Field(
        default=None,
        description="Analisis kecocokan personal untuk kandidat level 1-3 tahun"
    )


class JobRequisition(BaseModel):
    """Data kanonik lowongan kerja sebelum dan sesudah diperkaya AI."""

    source: str
    id: str
    title: str
    company_name: str
    location: Optional[str] = ""
    country_restrictions: List[str] = []
    seniority: List[str] = []
    categories: List[str] = []
    min_salary: Optional[float] = None
    max_salary: Optional[float] = None
    currency: Optional[str] = None
    application_url: Optional[str] = None
    published_at: Optional[int] = None
    description: str

    # Lifecycle & Discovery Metadata
    original_job_id: Optional[str] = None
    company_id: Optional[str] = None
    lifecycle_status: Optional[str] = "active"
    first_discovered_at: Optional[int] = None

    # Field tambahan setelah diproses AI
    intelligence: Optional[JobIntelligence] = None

class TailoredBullet(BaseModel):
    original_experience: str = Field(..., description="Konteks pengalaman asli kandidat")
    optimized_bullet: str = Field(..., description="Bullet point yang telah dioptimasi ATS dengan action verb + formula X-Y-Z")
    keywords_matched: List[str] = Field(..., description="Keywords lowongan yang berhasil diintegrasikan")


class ResumeTailorResponse(BaseModel):
    match_score: int = Field(..., ge=0, le=100, description="Skor kecocokan ATS 0-100%")
    missing_critical_skills: List[str] = Field(..., description="Skill wajib di lowongan yang belum ada di CV kandidat")
    tailored_summary: str = Field(..., description="Professional Summary ringkas 2-3 kalimat yang disesuaikan dengan posisi target")
    optimized_bullets: List[TailoredBullet] = Field(..., description="Daftar bullet point pengalaman kerja yang sudah dioptimasi")
    cover_letter_draft: str = Field(..., description="Draf cover letter terarah yang singkat, padat, dan profesional")


class ResumeTailorRequest(BaseModel):
    resume_text: str = Field(..., description="Teks isi resume kandidat saat ini")
    job_id: str = Field(..., description="ID lowongan kerja target")

class ContactInfo(BaseModel):
    full_name: str = Field(..., description="Nama lengkap kandidat")
    email: str = Field(..., description="Alamat email profesional")
    phone: Optional[str] = Field("", description="Nomor telepon aktif")
    location: Optional[str] = Field("", description="Kota, Negara (mis: Jakarta, Indonesia)")
    linkedin_url: Optional[str] = Field("", description="URL profil LinkedIn")
    github_url: Optional[str] = Field("", description="URL profil GitHub atau Portfolio")


class WorkExperienceItem(BaseModel):
    company: str = Field(..., description="Nama perusahaan")
    position: str = Field(..., description="Jabatan atau peran")
    location: Optional[str] = Field("", description="Kota/Negara atau 'Remote'")
    start_date: str = Field(..., description="Bulan/Tahun mulai (mis: Jan 2023)")
    end_date: str = Field(..., description="Bulan/Tahun selesai atau 'Present'")
    bullets: List[str] = Field(
        ...,
        description="Pencapaian berbasis formula dampak Google X-Y-Z yang terukur dan menyatu dengan kata kunci lowongan",
    )


class EducationItem(BaseModel):
    institution: str = Field(..., description="Nama universitas atau institusi pendidikan")
    degree: str = Field(..., description="Gelar atau jenjang (mis: Bachelor of Computer Science)")
    field_of_study: Optional[str] = Field("", description="Jurusan (mis: Informatics, Software Engineering)")
    graduation_year: Optional[str] = Field("", description="Tahun kelulusan (mis: 2022)")
    gpa_or_honors: Optional[str] = Field("", description="IPK atau predikat kehormatan jika relevan (opsional)")


class CertificationItem(BaseModel):
    name: str = Field(..., description="Nama sertifikasi (mis: AWS Certified Developer, Meta Backend Professional)")
    issuer: str = Field(..., description="Penerbit sertifikat (mis: Amazon Web Services, Coursera)")
    year: Optional[str] = Field("", description="Tahun perolehan")


class FullResumeData(BaseModel):
    """Struktur lengkap dokumen resume standar ATS Harvard/MIT single-column."""

    contact: ContactInfo
    target_role_title: str = Field(..., description="Judul posisi yang ditargetkan")
    professional_summary: str = Field(
        ...,
        description="Ringkasan profesional 3-4 baris yang disesuaikan erat dengan kebutuhan lowongan",
    )
    technical_skills: List[str] = Field(
        ...,
        description="Daftar keahlian teknis terverifikasi (bahasa, framework, database, tools)",
    )
    work_experiences: List[WorkExperienceItem]
    educations: List[EducationItem] = []
    certifications: List[CertificationItem] = []


class ResumeAnalysisReport(BaseModel):
    """Laporan analisis kesesuaian dan transparansi gap."""

    match_score: int = Field(..., ge=0, le=100, description="Estimasi skor kecocokan ATS 0-100%")
    matched_keywords: List[str] = Field(..., description="Kata kunci yang berhasil diselaraskan dari lowongan")
    missing_skills: List[str] = Field(
        ...,
        description="Skill atau kualifikasi di lowongan yang belum dimiliki kandidat (tanpa mengarang)",
    )
    key_improvements: List[str] = Field(
        ...,
        description="Daftar perbaikan substantif yang dilakukan (mis: penambahan metrik, penyesuaian action verbs)",
    )
    ats_formatting_advice: str = Field(
        ...,
        description="Catatan kepatuhan ATS dan rekomendasi untuk wawancara",
    )


class OptimizedResumeResult(BaseModel):
    """Hasil akhir gabungan: resume lengkap siap cetak/edit + laporan analisis."""

    resume: FullResumeData
    analysis: ResumeAnalysisReport
    cover_letter: str = Field(..., description="Draf cover letter terarah yang singkat dan padat")


class ManualProfileBuildRequest(BaseModel):
    """Request untuk Mode B: membuat resume dari form informasi kandidat."""

    job_id: str
    contact: ContactInfo
    background_text: str = Field(..., description="Ringkasan pengalaman, proyek, dan latar belakang yang diceritakan kandidat")
    skills_input: List[str] = []

class LifecycleStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"
    EXPIRED = "expired"
    REMOVED = "removed"
    UNKNOWN = "unknown"


class ApplicationStatus(str, Enum):
    SAVED = "saved"
    NOT_APPLIED = "not_applied"
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    ASSESSMENT = "assessment"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class CompanyRegistry(BaseModel):
    id: str = Field(..., description="Canonical slug identifier, mis: gitlab, vanta")
    name: str = Field(..., description="Nama resmi perusahaan")
    website_url: Optional[str] = ""
    ats_provider: str = Field(..., description="greenhouse, lever, ashby, dll")
    ats_board_token: str = Field(..., description="Token board public ATS")
    industry: Optional[str] = ""
    country: Optional[str] = ""
    is_active: bool = True
    last_sync_at: Optional[str] = None
    last_status: Optional[str] = None
    consecutive_failures: int = 0


class JobApplication(BaseModel):
    id: Optional[int] = None
    job_id: str
    status: ApplicationStatus = ApplicationStatus.SAVED
    applied_date: Optional[str] = None
    notes: Optional[str] = ""
    follow_up_date: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ApplicationUpdateRequest(BaseModel):
    status: ApplicationStatus
    applied_date: Optional[str] = None
    notes: Optional[str] = None
    follow_up_date: Optional[str] = None


class SyncLog(BaseModel):
    id: Optional[int] = None
    source_name: str
    status: str
    jobs_discovered: int = 0
    jobs_new: int = 0
    jobs_closed: int = 0
    error_message: Optional[str] = None
    duration_ms: Optional[int] = 0
    created_at: Optional[str] = None


class UserPreferences(BaseModel):
    # 1. Job Search Preferences
    target_roles: List[str] = Field(
        default=["AI Engineer", "Backend Developer", "Laravel Developer", "Fullstack Developer", "Software Engineer"],
        description="Peran atau job title yang diminati"
    )
    target_skills: List[str] = Field(
        default=["PHP", "Laravel", "Vue", "TypeScript", "React", "Go", "Python", "Docker"],
        description="Teknologi dan stack keahlian utama"
    )
    remote_work_types: List[str] = Field(
        default=["fully_remote", "worldwide", "wfa"],
        description="Jenis remote: fully_remote, worldwide, wfa, wfh"
    )
    preferred_regions: List[str] = Field(
        default=["Worldwide", "Southeast Asia (SEA)", "APAC", "Remote"],
        description="Wilayah atau zona waktu yang diterima (prioritas Worldwide & SEA)"
    )
    experience_levels: List[str] = Field(
        default=["junior", "mid_level"],
        description="Tingkat pengalaman: junior, mid_level, senior, lead"
    )
    max_years_experience: Optional[int] = Field(
        default=3,
        description="Batas maksimal syarat pengalaman tahunan yang diinginkan (default: 3 tahun, yaitu < 4 tahun). Lowongan tanpa syarat eksplisit tetap lolos."
    )
    min_match_score: int = Field(
        default=80,
        ge=0,
        le=100,
        description="Minimal skor kecocokan profil (default: 80 untuk menyaring kecocokan tinggi)"
    )
    min_salary_usd: Optional[float] = Field(
        default=12000.0,
        description="Ekspektasi gaji minimal dalam USD tahunan (default: $1,000/bulan atau $12,000/tahun)"
    )
    max_salary_usd: Optional[float] = Field(
        default=None,
        description="Ekspektasi gaji maksimal dalam USD tahunan"
    )
    employment_types: List[str] = Field(
        default=["full_time", "contract", "eor", "independent_contractor"],
        description="Jenis kontrak: full_time, contract, eor, independent_contractor, part_time, internship"
    )

    # 2. Geographic Eligibility
    candidate_country: str = Field(
        default="Indonesia",
        description="Negara domisili kandidat"
    )
    candidate_timezone: str = Field(
        default="Asia/Jakarta",
        description="Zona waktu kandidat (WIB/WITA/WIT)"
    )
    strict_indonesia_eligible: bool = Field(
        default=True,
        description="Hanya tampilkan lowongan yang bukti eksplisitnya mengizinkan pelamar dari Indonesia"
    )
    prioritize_worldwide: bool = Field(
        default=True,
        description="Memprioritaskan lowongan tanpa batasan negara (Worldwide / Any location)"
    )
    excluded_regions: List[str] = Field(
        default=["US Only", "Europe Only", "UK Only", "Canada Only"],
        description="Wilayah terbatas yang langsung diabaikan"
    )

    # 3. Company Preferences
    only_small_companies: bool = Field(
        default=False,
        description="Filter opsional: jika True, hanya menampilkan startup ramping (10-100 orang). Default False agar mencakup seluruh ukuran perusahaan."
    )
    preferred_company_sizes: List[str] = Field(
        default=["small_startup", "medium_startup", "agency_studio", "large_enterprise", "unknown"],
        description="Kategori ukuran perusahaan yang diizinkan"
    )
    exclude_tier1_enterprises: bool = Field(
        default=False,
        description="Kecualikan korporasi raksasa Tier-1 jika diaktifkan (default: False)"
    )
    excluded_companies: List[str] = Field(
        default=[],
        description="Daftar nama perusahaan yang di-blacklist oleh pengguna"
    )

    # 4. Job Freshness & Discovery
    freshness_days: int = Field(
        default=14,
        ge=1,
        le=90,
        description="Batas usia lowongan maksimal dalam hari (default: 14 hari)"
    )
    max_ghost_risk: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Ambang batas toleransi risiko ghost job (0.0 - 1.0)"
    )
    show_unverified_queue: bool = Field(
        default=False,
        description="Apakah lowongan unverified dapat diakses di antrean peninjauan terpisah"
    )
    auto_refresh_interval_hours: int = Field(
        default=5,
        ge=1,
        le=24,
        description="Frekuensi siklus sinkronisasi latar belakang dalam jam"
    )

    # 5. Notifications & Display
    default_role_filter: str = Field(
        default="ALL",
        description="Pilihan pill filter peran default pada radar"
    )
    show_closed_jobs: bool = Field(
        default=False,
        description="Tampilkan lowongan yang sudah ditutup/closed"
    )
    compact_view: bool = Field(
        default=False,
        description="Tampilan kartu padat untuk perangkat layar kecil"
    )



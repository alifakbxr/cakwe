import sqlite3
import json
from pathlib import Path
from typing import List, Optional
from schemas import JobRequisition, JobIntelligence, UserPreferences
import time

DB_DIR = Path(__file__).resolve().parent.parent / "data" / "db"
DB_PATH = DB_DIR / "radar.sqlite3"


def get_connection() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Inisialisasi tabel jobs, companies, applications, dan logs di database SQLite."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id TEXT PRIMARY KEY,
        source TEXT,
        title TEXT,
        company_name TEXT,
        location TEXT,
        country_restrictions TEXT,
        seniority TEXT,
        categories TEXT,
        min_salary REAL,
        max_salary REAL,
        currency TEXT,
        application_url TEXT,
        published_at INTEGER,
        description TEXT,
        
        -- AI Intelligence Fields
        eligibility_status TEXT,
        eligibility_quote TEXT,
        summary_id TEXT,
        translated_responsibilities TEXT,
        translated_requirements TEXT,
        skills_required TEXT,
        ghost_risk_score REAL,
        ghost_risk_reason TEXT,
        
        -- Lifecycle & Metadata Fields
        lifecycle_status TEXT DEFAULT 'active',
        last_verified_at INTEGER,
        failed_verification_count INTEGER DEFAULT 0,
        first_discovered_at INTEGER,
        original_job_id TEXT,
        company_id TEXT,
        
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Migrasi idempotent untuk kolom baru pada tabel jobs jika sudah ada sebelumnya
    existing_cols = [row["name"] for row in cursor.execute("PRAGMA table_info(jobs)").fetchall()]
    new_cols = [
        ("lifecycle_status", "TEXT DEFAULT 'active'"),
        ("last_verified_at", "INTEGER"),
        ("failed_verification_count", "INTEGER DEFAULT 0"),
        ("first_discovered_at", "INTEGER"),
        ("original_job_id", "TEXT"),
        ("company_id", "TEXT"),
        ("company_size_category", "TEXT DEFAULT 'unknown'"),
        ("company_size_raw", "TEXT"),
        ("company_size_confidence", "TEXT DEFAULT 'unknown'"),
        ("match_score", "INTEGER"),
        ("is_recommended", "INTEGER DEFAULT 0"),
        ("match_reasons", "TEXT"),
        ("missing_skills", "TEXT"),
        ("dismiss_reason", "TEXT"),
        ("primary_industry", "TEXT DEFAULT 'unknown'"),
        ("is_developer_platform", "INTEGER DEFAULT 0"),
        ("is_tier1", "INTEGER DEFAULT 0"),
        ("min_years_experience", "INTEGER"),
        ("experience_quote", "TEXT"),
        ("employment_type", "TEXT DEFAULT 'unknown'"),
    ]
    for col_name, col_type in new_cols:
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_type};")

    # Indeks performa untuk query 14-hari dan match score
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_freshness ON jobs (published_at, lifecycle_status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs (company_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_match ON jobs (match_score, is_recommended);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_experience ON jobs (min_years_experience);")

    # Tabel Company Registry
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS companies (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        website_url TEXT,
        ats_provider TEXT NOT NULL,
        ats_board_token TEXT NOT NULL,
        industry TEXT,
        country TEXT,
        is_active INTEGER DEFAULT 1,
        last_sync_at TIMESTAMP,
        last_status TEXT,
        consecutive_failures INTEGER DEFAULT 0,
        discovery_source TEXT DEFAULT 'discovered',
        verification_status TEXT DEFAULT 'verified_active',
        last_verified_at TIMESTAMP,
        active_jobs_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Migrasi idempotent untuk kolom baru pada tabel companies
    existing_company_cols = [row["name"] for row in cursor.execute("PRAGMA table_info(companies)").fetchall()]
    new_company_cols = [
        ("discovery_source", "TEXT DEFAULT 'discovered'"),
        ("verification_status", "TEXT DEFAULT 'verified_active'"),
        ("last_verified_at", "TIMESTAMP"),
        ("active_jobs_count", "INTEGER DEFAULT 0"),
        ("size_category", "TEXT DEFAULT 'unknown'"),
        ("is_tier1", "INTEGER DEFAULT 0"),
        ("is_developer_platform", "INTEGER DEFAULT 0"),
    ]
    for col_name, col_type in new_company_cols:
        if col_name not in existing_company_cols:
            cursor.execute(f"ALTER TABLE companies ADD COLUMN {col_name} {col_type};")

    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_companies_ats_token ON companies (ats_provider, ats_board_token);")

    # Tabel Antrean Kandidat Discovery
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS discovery_candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ats_provider TEXT NOT NULL,
        ats_board_token TEXT NOT NULL,
        candidate_name TEXT,
        source_url TEXT,
        discovery_source TEXT NOT NULL,
        status TEXT DEFAULT 'pending', -- pending, verified, invalid, failed
        failure_reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(ats_provider, ats_board_token)
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_discovery_candidates_status ON discovery_candidates (status);")


    # Tabel Application Tracker
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS job_applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT NOT NULL UNIQUE,
        status TEXT NOT NULL DEFAULT 'saved',
        applied_date TEXT,
        notes TEXT,
        follow_up_date TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE
    );
    """)

    # Tabel Sync Logs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sync_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_name TEXT NOT NULL,
        status TEXT NOT NULL,
        jobs_discovered INTEGER DEFAULT 0,
        jobs_new INTEGER DEFAULT 0,
        jobs_closed INTEGER DEFAULT 0,
        error_message TEXT,
        duration_ms INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Tabel Resume Versions
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tailored_resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT,
        job_title TEXT,
        company_name TEXT,
        resume_data TEXT,
        analysis_data TEXT,
        cover_letter TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Tabel User Preferences (Persistent)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_preferences (
        user_id TEXT PRIMARY KEY,
        preferences_json TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Inisialisasi default preferences jika belum ada
    cursor.execute("SELECT user_id FROM user_preferences WHERE user_id = 'default'")
    if not cursor.fetchone():
        defaults = UserPreferences().model_dump()
        cursor.execute(
            "INSERT INTO user_preferences (user_id, preferences_json) VALUES (?, ?)",
            ("default", json.dumps(defaults))
        )


    # Tabel AI Analysis Cache (Deduplikasi Pemanggilan AI)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ai_analysis_cache (
        content_hash TEXT PRIMARY KEY,
        model_used TEXT NOT NULL,
        response_json TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ai_cache_hash ON ai_analysis_cache(content_hash);")

    # Tabel Job History (Audit Trail Perubahan Gaji dan Status Lowongan)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS job_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT NOT NULL,
        field_changed TEXT NOT NULL,
        old_value TEXT,
        new_value TEXT,
        recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_job_history_job_id ON job_history(job_id);")

    conn.commit()
    conn.close()


def save_job(job: JobRequisition):
    """Menyimpan atau memperbarui data lowongan yang sudah diperkaya AI."""
    conn = get_connection()
    cursor = conn.cursor()
    intel = job.intelligence

    # Ambil ukuran dan klasifikasi perusahaan dari tabel companies jika ada
    size_cat = intel.company_size_category.value if intel and intel.company_size_category else "unknown"
    size_conf = intel.company_size_confidence.value if intel and intel.company_size_confidence else "unknown"
    primary_industry = intel.primary_industry if intel and intel.primary_industry else "unknown"
    is_dev_platform = 1 if (intel and intel.is_developer_platform) else 0
    is_tier1 = 1 if (intel and intel.is_tier1) else 0

    if job.company_name:
        cursor.execute("SELECT size_category, is_tier1, is_developer_platform, industry FROM companies WHERE LOWER(name) = ? OR id = ? LIMIT 1", (job.company_name.lower().strip(), job.company_id or ""))
        c_row = cursor.fetchone()
        if c_row:
            if c_row["size_category"] and c_row["size_category"] != "unknown":
                size_cat = c_row["size_category"]
                size_conf = "confirmed"
            if c_row["is_tier1"] is not None:
                is_tier1 = 1 if c_row["is_tier1"] else 0
            if c_row["is_developer_platform"] is not None:
                is_dev_platform = 1 if c_row["is_developer_platform"] else 0
    min_years_exp = intel.min_years_experience if intel else None
    exp_quote = intel.experience_quote if intel else None
    emp_type = intel.employment_type.value if intel and intel.employment_type else "unknown"

    cursor.execute("""
    INSERT INTO jobs (
        id, source, title, company_name, location,
        country_restrictions, seniority, categories,
        min_salary, max_salary, currency, application_url,
        published_at, description,
        eligibility_status, eligibility_quote, summary_id,
        translated_responsibilities, translated_requirements,
        skills_required, ghost_risk_score, ghost_risk_reason,
        company_size_category, company_size_raw, company_size_confidence,
        match_score, is_recommended, match_reasons, missing_skills,
        primary_industry, is_developer_platform, is_tier1,
        min_years_experience, experience_quote, employment_type
    ) VALUES (
        ?, ?, ?, ?, ?,
        ?, ?, ?,
        ?, ?, ?, ?,
        ?, ?,
        ?, ?, ?,
        ?, ?,
        ?, ?, ?,
        ?, ?, ?,
        ?, ?, ?, ?,
        ?, ?, ?,
        ?, ?, ?
    )
    ON CONFLICT(id) DO UPDATE SET
        title = excluded.title,
        min_salary = excluded.min_salary,
        max_salary = excluded.max_salary,
        eligibility_status = excluded.eligibility_status,
        ghost_risk_score = excluded.ghost_risk_score,
        company_size_category = excluded.company_size_category,
        company_size_raw = excluded.company_size_raw,
        company_size_confidence = excluded.company_size_confidence,
        match_score = excluded.match_score,
        is_recommended = excluded.is_recommended,
        match_reasons = excluded.match_reasons,
        missing_skills = excluded.missing_skills,
        primary_industry = excluded.primary_industry,
        is_developer_platform = excluded.is_developer_platform,
        is_tier1 = excluded.is_tier1,
        min_years_experience = excluded.min_years_experience,
        experience_quote = excluded.experience_quote,
        employment_type = excluded.employment_type;
    """, (
        job.id,
        job.source,
        job.title,
        job.company_name,
        job.location or "",
        json.dumps(job.country_restrictions),
        json.dumps(job.seniority),
        json.dumps(job.categories),
        job.min_salary,
        job.max_salary,
        job.currency,
        job.application_url,
        job.published_at,
        job.description,
        intel.eligibility_status.value if intel else None,
        intel.eligibility_quote if intel else None,
        json.dumps(intel.summary_id if intel else []),
        json.dumps(intel.translated_responsibilities if intel else []),
        json.dumps(intel.translated_requirements if intel else []),
        json.dumps(intel.skills_required if intel else []),
        intel.ghost_risk_score if intel else None,
        intel.ghost_risk_reason if intel else None,
        size_cat,
        intel.company_size_raw if intel else None,
        size_conf,
        intel.candidate_fit.match_score if intel and intel.candidate_fit else None,
        1 if (intel and intel.candidate_fit and intel.candidate_fit.is_recommended) else 0,
        json.dumps(intel.candidate_fit.match_reasons if intel and intel.candidate_fit else []),
        json.dumps(intel.candidate_fit.missing_or_gap_skills if intel and intel.candidate_fit else []),
        primary_industry,
        is_dev_platform,
        is_tier1,
        min_years_exp,
        exp_quote,
        emp_type,
    ))

    # Simpan history jika ada perubahan gaji atau eligibility pada job yang sudah ada
    try:
        cursor.execute("SELECT min_salary, max_salary, eligibility_status FROM jobs WHERE id = ?", (job.id,))
        existing_job = cursor.fetchone()
        if existing_job:
            if existing_job["min_salary"] != job.min_salary or existing_job["max_salary"] != job.max_salary:
                cursor.execute("""
                INSERT INTO job_history (job_id, field_changed, old_value, new_value)
                VALUES (?, 'compensation', ?, ?)
                """, (
                    job.id,
                    f"{existing_job['min_salary']}-{existing_job['max_salary']}",
                    f"{job.min_salary}-{job.max_salary}"
                ))
            if intel and existing_job["eligibility_status"] != intel.eligibility_status.value:
                cursor.execute("""
                INSERT INTO job_history (job_id, field_changed, old_value, new_value)
                VALUES (?, 'eligibility_status', ?, ?)
                """, (
                    job.id,
                    existing_job["eligibility_status"],
                    intel.eligibility_status.value
                ))
    except Exception as e:
        print(f"[JOB-HISTORY-ERROR] {e}")

    conn.commit()
    conn.close()


def is_job_existing(job_id: str, title: Optional[str] = None, company_name: Optional[str] = None) -> bool:
    """Mengecek apakah lowongan sudah pernah disimpan (berdasarkan ID atau kombinasi title + company)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM jobs WHERE id = ?", (job_id,))
    if cursor.fetchone() is not None:
        conn.close()
        return True

    if title and company_name:
        clean_title = title.strip().lower()
        clean_company = company_name.strip().lower()
        cursor.execute(
            "SELECT 1 FROM jobs WHERE LOWER(title) = ? AND LOWER(company_name) = ? LIMIT 1",
            (clean_title, clean_company)
        )
        if cursor.fetchone() is not None:
            conn.close()
            return True

    conn.close()
    return False


def dismiss_job(job_id: str, reason: str = "other") -> bool:
    """Menandai lowongan sebagai dismissed agar tidak muncul di dashboard rekomendasi."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE jobs 
    SET lifecycle_status = 'dismissed',
        dismiss_reason = ?
    WHERE id = ?
    """, (reason, job_id))
    affected = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return affected



def get_all_jobs(
    status: Optional[str] = "verified_eligible",
    freshness_days: Optional[int] = None,
    include_closed: Optional[bool] = None,
    only_small_companies: Optional[bool] = None,
    target_role: Optional[str] = None,
    search: Optional[str] = None,
    min_match_score: Optional[int] = None,
    max_years_experience: Optional[int] = None,
    sort_by: str = "latest",
    user_id: str = "default",
    preferences: Optional[UserPreferences] = None,
) -> List[dict]:
    """Mengambil daftar lowongan dengan strict Stage A eligibility dan dynamic user preferences:
    1. Active lifecycle & freshness (sesuai user preferences atau parameter override)
    2. verified_eligible (reside in Indonesia/worldwide permitted)
    3. Match score threshold (default > 80% fit)
    4. Experience requirement (0-3 thn atau < 4 thn; unverified/tanpa syarat eksplisit tetap lolos)
    5. Company size & Tier-1 filters (hanya aktif jika only_small_companies eksplisit bernilai True)
    6. Excluded companies blacklist
    7. Min/Max Salary filter jika ada
    8. Not dismissed by candidate
    """
    if preferences is None:
        preferences = get_user_preferences(user_id=user_id)

    # Tentukan nilai efektif (parameter eksplisit mengambil prioritas jika diberikan, selain itu gunakan preferensi pengguna)
    eff_freshness = freshness_days if freshness_days is not None else preferences.freshness_days
    eff_include_closed = include_closed if include_closed is not None else preferences.show_closed_jobs
    eff_only_small = only_small_companies if only_small_companies is not None else preferences.only_small_companies

    conn = get_connection()
    cursor = conn.cursor()

    cutoff_timestamp = int(time.time() - (eff_freshness * 86400))

    query_parts = []
    params = []

    # 1. Filter freshness (usia lowongan)
    query_parts.append("(j.published_at IS NULL OR j.published_at >= ?)")
    params.append(cutoff_timestamp)

    # 2. Filter lifecycle active & bukan dismissed
    if not eff_include_closed:
        query_parts.append("(j.lifecycle_status = 'active' OR j.lifecycle_status IS NULL)")
    else:
        query_parts.append("(j.lifecycle_status != 'dismissed' OR j.lifecycle_status IS NULL)")

    # 3. Mandatory Stage A: Remote Jobs Only (No onsite, hybrid, or regular office attendance)
    # Aturan dasar ini tidak dapat di-bypass
    query_parts.append("""(
        (
            LOWER(j.location) LIKE '%remote%' OR 
            LOWER(j.location) LIKE '%anywhere%' OR 
            LOWER(j.location) LIKE '%worldwide%' OR 
            LOWER(j.location) LIKE '%telecommute%' OR
            LOWER(j.location) LIKE '%home based%' OR
            LOWER(j.title) LIKE '%remote%' OR
            LOWER(j.eligibility_quote) LIKE '%remote%' OR
            LOWER(j.eligibility_quote) LIKE '%worldwide%'
        ) 
        AND LOWER(j.location) NOT LIKE '%onsite%' 
        AND LOWER(j.location) NOT LIKE '%on-site%'
        AND LOWER(j.location) NOT LIKE '%hybrid%'
        AND LOWER(j.title) NOT LIKE '%hybrid%'
        AND LOWER(j.title) NOT LIKE '%onsite%'
    )""")

    # 4. Filter status kelayakan
    if status:
        query_parts.append("j.eligibility_status = ?")
        params.append(status)

    # 5. Filter Ukuran Perusahaan (Company Preferences)
    if eff_only_small:
        small_sizes = [s for s in (preferences.preferred_company_sizes or []) if s in ('small_startup', 'medium_startup', 'agency_studio')]
        if not small_sizes:
            small_sizes = ['small_startup', 'medium_startup', 'agency_studio']
        placeholders = ",".join("?" for _ in small_sizes)
        query_parts.append(f"j.company_size_category IN ({placeholders})")
        params.extend(small_sizes)

    # 6. Exclude Tier-1 Enterprises and Developer Platforms (hanya jika mode small company aktif)
    if eff_only_small:
        if preferences.exclude_tier1_enterprises:
            query_parts.append("(COALESCE(j.is_tier1, 0) = 0 AND (j.company_size_category != 'large_enterprise' OR j.company_size_category IS NULL))")
        # Exclude Developer Tools & Platforms from small company feed (prioritize independent non-dev startups)
        query_parts.append("(COALESCE(j.is_developer_platform, 0) = 0)")


    # 7. Excluded Companies (Blacklist dari User)
    if preferences.excluded_companies:
        for excluded_comp in preferences.excluded_companies:
            comp_clean = excluded_comp.strip()
            if comp_clean:
                query_parts.append("LOWER(j.company_name) != ?")
                params.append(comp_clean.lower())

    # 8. Minimum Salary (USD equivalent based on currency conversion)
    if preferences.min_salary_usd is not None and preferences.min_salary_usd > 0:
        query_parts.append("""(
            j.min_salary IS NULL OR 
            (
                CASE UPPER(COALESCE(j.currency, 'USD'))
                    WHEN 'EUR' THEN j.max_salary * 1.08
                    WHEN 'GBP' THEN j.max_salary * 1.28
                    WHEN 'AUD' THEN j.max_salary * 0.65
                    WHEN 'SGD' THEN j.max_salary * 0.75
                    WHEN 'CAD' THEN j.max_salary * 0.73
                    WHEN 'IDR' THEN j.max_salary / 16000.0
                    ELSE j.max_salary
                END
            ) >= ?
        )""")
        params.append(preferences.min_salary_usd)

    # 9. Maximum Ghost Risk Score (Default dari preferensi)
    if preferences.max_ghost_risk is not None:
        query_parts.append("(j.ghost_risk_score IS NULL OR j.ghost_risk_score <= ?)")
        params.append(preferences.max_ghost_risk)

    # 10. Filter role / technology stack
    if target_role and target_role.upper() != "ALL":
        role_term = f"%{target_role.lower()}%"
        query_parts.append("""(
            LOWER(j.title) LIKE ? OR
            LOWER(COALESCE(j.skills_required, '')) LIKE ? OR
            LOWER(COALESCE(j.categories, '')) LIKE ? OR
            LOWER(j.description) LIKE ?
        )""")
        params.extend([role_term, role_term, role_term, role_term])

    # 11. Search keyword
    if search:
        query_parts.append("(LOWER(j.title) LIKE ? OR LOWER(j.company_name) LIKE ? OR LOWER(j.skills_required) LIKE ?)")
        term = f"%{search.lower()}%"
        params.extend([term, term, term])

    # 12. Match Score Threshold (> 80% fit)
    eff_min_score = min_match_score if min_match_score is not None else getattr(preferences, "min_match_score", None)
    if eff_min_score is not None and eff_min_score > 0:
        query_parts.append("(j.match_score IS NOT NULL AND j.match_score >= ?)")
        params.append(eff_min_score)

    # 13. Experience Level Threshold (fewer than 4 years, e.g. <= 3 years)
    # Lowongan tanpa syarat eksplisit (NULL) tetap diloloskan agar tidak membuang peluang relevan
    eff_max_exp = max_years_experience if max_years_experience is not None else getattr(preferences, "max_years_experience", None)
    if eff_max_exp is not None:
        query_parts.append("(j.min_years_experience IS NULL OR j.min_years_experience <= ?)")
        params.append(eff_max_exp)

    where_clause = " AND ".join(query_parts)
    
    order_clause = "j.published_at DESC, composite_rank_score DESC" if sort_by == "latest" else "composite_rank_score DESC, j.published_at DESC"

    sql = f"""
    SELECT j.*, a.status as application_status, a.applied_date, a.notes as application_notes,
    (
        COALESCE(j.match_score, 50) +
        (CASE WHEN j.eligibility_status = 'verified_eligible' THEN 40 ELSE 0 END) +
        (CASE WHEN j.is_recommended = 1 THEN 20 ELSE 0 END) +
        (CASE WHEN j.employment_type IN ('full_time', 'contract', 'eor', 'independent_contractor') THEN 10 ELSE 0 END) -
        (CASE WHEN j.ghost_risk_score IS NOT NULL THEN j.ghost_risk_score * 30 ELSE 0 END)
    ) as composite_rank_score
    FROM jobs j
    LEFT JOIN job_applications a ON j.id = a.job_id
    WHERE {where_clause}
    ORDER BY {order_clause}
    """

    cursor.execute(sql, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_jobs_filter_diagnostics(user_id: str = "default") -> dict:
    """Mengembalikan metrik diagnostik filter untuk transparansi dashboard."""
    preferences = get_user_preferences(user_id=user_id)
    cutoff_timestamp = int(time.time() - (preferences.freshness_days * 86400))
    conn = get_connection()
    cursor = conn.cursor()

    total_jobs = cursor.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
    verified_eligible = cursor.execute("SELECT COUNT(*) FROM jobs WHERE eligibility_status = 'verified_eligible'").fetchone()[0]
    likely_eligible = cursor.execute("SELECT COUNT(*) FROM jobs WHERE eligibility_status = 'likely_eligible'").fetchone()[0]
    ineligible = cursor.execute("SELECT COUNT(*) FROM jobs WHERE eligibility_status = 'ineligible'").fetchone()[0]

    hidden_by_freshness = cursor.execute("""
        SELECT COUNT(*) FROM jobs 
        WHERE eligibility_status = 'verified_eligible' 
        AND published_at < ?
    """, (cutoff_timestamp,)).fetchone()[0]

    hidden_by_large_enterprise = cursor.execute("""
        SELECT COUNT(*) FROM jobs 
        WHERE eligibility_status = 'verified_eligible' 
        AND (company_size_category = 'large_enterprise' OR is_tier1 = 1)
    """).fetchone()[0]

    hidden_by_dev_platform = cursor.execute("""
        SELECT COUNT(*) FROM jobs 
        WHERE eligibility_status = 'verified_eligible' 
        AND is_developer_platform = 1
    """).fetchone()[0]

    conn.close()
    return {
        "total_in_db": total_jobs,
        "verified_eligible": verified_eligible,
        "likely_eligible": likely_eligible,
        "ineligible": ineligible,
        "hidden_by_freshness": hidden_by_freshness,
        "hidden_by_large_enterprise": hidden_by_large_enterprise,
        "hidden_by_developer_platform": hidden_by_dev_platform,
        "freshness_days_active": preferences.freshness_days,
        "only_small_active": preferences.only_small_companies,
    }


def save_tailored_resume_version(job_id: str, job_title: str, company: str, resume_dict: dict, analysis_dict: dict, cover_letter: str):
    """Menyimpan versi resume yang dihasilkan/diedit."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO tailored_resumes (job_id, job_title, company_name, resume_data, analysis_data, cover_letter)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        job_id,
        job_title,
        company,
        json.dumps(resume_dict),
        json.dumps(analysis_dict),
        cover_letter,
    ))
    conn.commit()
    conn.close()


def get_tailored_resumes_for_job(job_id: str) -> List[dict]:
    """Mengambil riwayat resume untuk lowongan tertentu."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tailored_resumes WHERE job_id = ? ORDER BY created_at DESC", (job_id,))
    rows = cursor.fetchall()
    conn.close()

    results = []
    for r in rows:
        d = dict(r)
        d["resume_data"] = json.loads(d["resume_data"])
        d["analysis_data"] = json.loads(d["analysis_data"])
        results.append(d)
    return results

def get_active_companies() -> List[dict]:
    """Mengambil daftar perusahaan terdaftar yang aktif."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM companies WHERE is_active = 1 ORDER BY name ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def upsert_company(company: dict):
    """Menyimpan atau memperbarui data perusahaan di registry."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO companies (
        id, name, website_url, ats_provider, ats_board_token, industry, country, is_active,
        discovery_source, verification_status, active_jobs_count, size_category, is_tier1, is_developer_platform
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(ats_provider, ats_board_token) DO UPDATE SET
        name = excluded.name,
        website_url = COALESCE(excluded.website_url, companies.website_url),
        industry = COALESCE(excluded.industry, companies.industry),
        country = COALESCE(excluded.country, companies.country),
        is_active = excluded.is_active,
        discovery_source = COALESCE(excluded.discovery_source, companies.discovery_source),
        verification_status = COALESCE(excluded.verification_status, companies.verification_status),
        active_jobs_count = COALESCE(excluded.active_jobs_count, companies.active_jobs_count),
        size_category = COALESCE(excluded.size_category, companies.size_category),
        is_tier1 = COALESCE(excluded.is_tier1, companies.is_tier1),
        is_developer_platform = COALESCE(excluded.is_developer_platform, companies.is_developer_platform);
    """, (
        company["id"],
        company["name"],
        company.get("website_url", ""),
        company["ats_provider"].lower(),
        company["ats_board_token"],
        company.get("industry", ""),
        company.get("country", ""),
        1 if company.get("is_active", True) else 0,
        company.get("discovery_source", "discovered"),
        company.get("verification_status", "verified_active"),
        company.get("active_jobs_count", 0),
        company.get("size_category", "unknown"),
        1 if company.get("is_tier1", False) else 0,
        1 if company.get("is_developer_platform", False) else 0,
    ))
    conn.commit()
    conn.close()


def update_company_sync_status(company_id: str, success: bool, error: Optional[str] = None):
    """Mencatat status sinkronisasi terakhir per perusahaan."""
    conn = get_connection()
    cursor = conn.cursor()
    if success:
        cursor.execute("""
        UPDATE companies
        SET last_sync_at = CURRENT_TIMESTAMP, last_status = 'success', consecutive_failures = 0
        WHERE id = ?
        """, (company_id,))
    else:
        cursor.execute("""
        UPDATE companies
        SET last_sync_at = CURRENT_TIMESTAMP, last_status = ?, consecutive_failures = consecutive_failures + 1
        WHERE id = ?
        """, (error or "failed", company_id))
    conn.commit()
    conn.close()


# Application Tracker Helpers
def get_application(job_id: str) -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM job_applications WHERE job_id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def upsert_application(job_id: str, status: str, applied_date: Optional[str] = None, notes: Optional[str] = None, follow_up_date: Optional[str] = None) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO job_applications (job_id, status, applied_date, notes, follow_up_date, updated_at)
    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(job_id) DO UPDATE SET
        status = excluded.status,
        applied_date = COALESCE(excluded.applied_date, job_applications.applied_date),
        notes = COALESCE(excluded.notes, job_applications.notes),
        follow_up_date = COALESCE(excluded.follow_up_date, job_applications.follow_up_date),
        updated_at = CURRENT_TIMESTAMP;
    """, (job_id, status, applied_date, notes, follow_up_date))
    conn.commit()
    cursor.execute("SELECT * FROM job_applications WHERE job_id = ?", (job_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row)


def get_all_tracked_applications(status: Optional[str] = None) -> List[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    if status:
        cursor.execute("""
        SELECT a.*, j.title as job_title, j.company_name, j.location, j.application_url, j.lifecycle_status
        FROM job_applications a
        JOIN jobs j ON a.job_id = j.id
        WHERE a.status = ?
        ORDER BY a.updated_at DESC
        """, (status,))
    else:
        cursor.execute("""
        SELECT a.*, j.title as job_title, j.company_name, j.location, j.application_url, j.lifecycle_status
        FROM job_applications a
        JOIN jobs j ON a.job_id = j.id
        ORDER BY a.updated_at DESC
        """)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# Sync Log Helper
def record_sync_log(source_name: str, status: str, discovered: int, new_count: int, closed_count: int, error: Optional[str] = None, duration_ms: int = 0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO sync_logs (source_name, status, jobs_discovered, jobs_new, jobs_closed, error_message, duration_ms)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (source_name, status, discovered, new_count, closed_count, error, duration_ms))
    conn.commit()
    conn.close()


def get_latest_sync_logs(limit: int = 20) -> List[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sync_logs ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# Discovery Helper Functions
def add_discovery_candidate(ats_provider: str, ats_board_token: str, candidate_name: Optional[str] = None, source_url: Optional[str] = None, discovery_source: str = "sniffed") -> bool:
    """Menambahkan kandidat board baru ke antrean verifikasi jika belum pernah terdaftar."""
    conn = get_connection()
    cursor = conn.cursor()
    token = ats_board_token.strip().lower()
    provider = ats_provider.strip().lower()

    # Jangan tambahkan jika sudah ada di tabel companies
    cursor.execute("SELECT id FROM companies WHERE ats_provider = ? AND LOWER(ats_board_token) = ?", (provider, token))
    if cursor.fetchone():
        conn.close()
        return False

    try:
        cursor.execute("""
        INSERT INTO discovery_candidates (ats_provider, ats_board_token, candidate_name, source_url, discovery_source, status)
        VALUES (?, ?, ?, ?, ?, 'pending')
        ON CONFLICT(ats_provider, ats_board_token) DO NOTHING;
        """, (provider, token, candidate_name, source_url, discovery_source))
        inserted = cursor.rowcount > 0
        conn.commit()
    except Exception:
        inserted = False
    finally:
        conn.close()
    return inserted


def get_pending_discovery_candidates(limit: int = 50) -> List[dict]:
    """Mengambil kandidat board yang belum diverifikasi."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM discovery_candidates
    WHERE status = 'pending'
    ORDER BY created_at ASC
    LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_discovery_candidate_status(candidate_id: int, status: str, failure_reason: Optional[str] = None):
    """Memperbarui status verifikasi kandidat."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE discovery_candidates
    SET status = ?, failure_reason = ?, updated_at = CURRENT_TIMESTAMP
    WHERE id = ?
    """, (status, failure_reason, candidate_id))
    conn.commit()
    conn.close()


def get_discovery_stats() -> dict:
    """Mengambil metrik ringkasan status discovery."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM discovery_candidates WHERE status = 'pending'")
    pending = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM discovery_candidates WHERE status = 'verified'")
    verified = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM discovery_candidates WHERE status = 'invalid'")
    invalid = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM companies")
    total_companies = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM companies WHERE is_active = 1")
    active_companies = cursor.fetchone()[0]
    conn.close()
    return {
        "pending_candidates": pending,
        "verified_candidates": verified,
        "invalid_candidates": invalid,
        "total_companies": total_companies,
        "active_companies": active_companies,
    }


def get_user_preferences(user_id: str = "default") -> UserPreferences:
    """Mengambil preferensi pengguna dari database. Jika belum ada, kembalikan default safe values."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT preferences_json FROM user_preferences WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row or not row["preferences_json"]:
        return UserPreferences()

    try:
        data = json.loads(row["preferences_json"])
        return UserPreferences(**data)
    except Exception as e:
        print(f"[PREFERENCES] Gagal mem-parse preferences_json untuk {user_id}: {e}. Gunakan default.")
        return UserPreferences()


def save_user_preferences(prefs: UserPreferences, user_id: str = "default") -> UserPreferences:
    """Menyimpan atau memperbarui preferensi pengguna secara atomik dan persisten."""
    conn = get_connection()
    cursor = conn.cursor()
    payload_json = json.dumps(prefs.model_dump())

    cursor.execute("""
    INSERT INTO user_preferences (user_id, preferences_json, updated_at)
    VALUES (?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(user_id) DO UPDATE SET
        preferences_json = excluded.preferences_json,
        updated_at = CURRENT_TIMESTAMP;
    """, (user_id, payload_json))

    conn.commit()
    conn.close()
    return prefs


def reset_user_preferences(user_id: str = "default") -> UserPreferences:
    """Mengembalikan preferensi pengguna ke nilai bawaan (factory default)."""
    default_prefs = UserPreferences()
    return save_user_preferences(default_prefs, user_id)


def get_cached_ai_analysis(content_hash: str) -> Optional[dict]:
    """Mengambil hasil analisis AI dari cache jika pernah diproses sebelumnya."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT response_json FROM ai_analysis_cache WHERE content_hash = ?", (content_hash,))
    row = cursor.fetchone()
    conn.close()
    if row and row["response_json"]:
        try:
            return json.loads(row["response_json"])
        except Exception:
            return None
    return None


def set_cached_ai_analysis(content_hash: str, model_used: str, response_dict: dict):
    """Menyimpan hasil analisis AI ke dalam cache SQLite."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO ai_analysis_cache (content_hash, model_used, response_json)
        VALUES (?, ?, ?)
        ON CONFLICT(content_hash) DO UPDATE SET
            model_used = excluded.model_used,
            response_json = excluded.response_json;
        """, (content_hash, model_used, json.dumps(response_dict)))
        conn.commit()
    except Exception as e:
        print(f"[CACHE] Gagal menyimpan ke ai_analysis_cache: {e}")
    finally:
        conn.close()


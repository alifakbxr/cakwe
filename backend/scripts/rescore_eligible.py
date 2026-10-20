import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Setup path to backend
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
load_dotenv(BACKEND_DIR / ".env")

from database import get_connection, save_job
from schemas import JobRequisition, LifecycleStatus
from ai_processor import process_job


async def rescore_all_eligible_jobs():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, source, title, company_name, location,
               country_restrictions, seniority, categories,
               min_salary, max_salary, currency, application_url,
               published_at, description, lifecycle_status,
               match_score, min_years_experience, employment_type
        FROM jobs
        WHERE eligibility_status IN ('verified_eligible', 'likely_eligible')
        ORDER BY published_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    print(f"[*] Ditemukan {len(rows)} lowongan eligible untuk dianalisis ulang dengan V2 scoring...")

    updated_count = 0
    for idx, r in enumerate(rows, start=1):
        job = JobRequisition(
            id=r["id"],
            source=r["source"] or "unknown",
            title=r["title"] or "",
            company_name=r["company_name"] or "",
            location=r["location"] or "",
            country_restrictions=[],
            seniority=[],
            categories=[],
            min_salary=r["min_salary"],
            max_salary=r["max_salary"],
            currency=r["currency"],
            application_url=r["application_url"],
            published_at=r["published_at"],
            description=r["description"] or "",
            lifecycle_status=LifecycleStatus.ACTIVE,
        )

        old_score = r["match_score"]
        print(f"[{idx}/{len(rows)}] Memproses: {job.company_name} - {job.title} (Skor lama: {old_score})...")
        try:
            processed = await process_job(job)
            save_job(processed)
            intel = processed.intelligence
            new_score = intel.candidate_fit.match_score if intel and intel.candidate_fit else None
            exp = intel.min_years_experience if intel else None
            emp = intel.employment_type.value if intel and intel.employment_type else "unknown"
            print(f"    -> SUKSES! Skor baru: {new_score} | Min Exp: {exp} thn | Type: {emp}")
            updated_count += 1
        except Exception as e:
            print(f"    -> GAGAL: {e}")

        # Jeda kecil agar tidak terkena rate limit
        await asyncio.sleep(0.5)

    print(f"\n[DONE] Selesai rescore! {updated_count}/{len(rows)} lowongan berhasil diperbarui.")


if __name__ == "__main__":
    asyncio.run(rescore_all_eligible_jobs())

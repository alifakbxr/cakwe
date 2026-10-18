import asyncio
import os
import time
from typing import List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import httpx

from ai_processor import process_job
from curate_samples import check_eligibility, fetch_jobs_by_query, SEARCH_QUERIES
from database import (
    get_active_companies,
    get_all_jobs,
    get_connection,
    get_latest_sync_logs,
    get_user_preferences,
    init_db,
    is_job_existing,
    record_sync_log,
    save_job,
    update_company_sync_status,
    upsert_company,
)
from schemas import JobRequisition, LifecycleStatus
from sources.ashby import AshbyAdapter
from sources.company_seeds import SEED_COMPANIES
from sources.greenhouse import GreenhouseAdapter
from sources.lever import LeverAdapter
from sources.remotive import RemotiveAdapter
from sources.jobicy import JobicyAdapter
from sources.jobspipe import JobsPipeAdapter
from sources.workable import WorkableAdapter
from sources.smartrecruiters import SmartRecruitersAdapter
from sources.recruitee import RecruiteeAdapter

from discovery import discover_from_job_listings, process_discovery_candidates


POLL_INTERVAL_HOURS = int(os.getenv("POLL_INTERVAL_HOURS", "5"))
FRESHNESS_WINDOW_SECONDS = 14 * 86400  # 14 Hari


def seed_initial_companies():
    """Memastikan company registry memiliki data awal boutique/small agencies, dan menonaktifkan seed tier-1 lama."""
    active_tokens = {comp["ats_board_token"].lower() for comp in SEED_COMPANIES}
    for comp in SEED_COMPANIES:
        upsert_company(comp)

    # Nonaktifkan seed lama yang tidak ada dalam daftar SEED_COMPANIES small/boutique
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, ats_board_token FROM companies WHERE discovery_source = 'seed'")
    for row in cursor.fetchall():
        if row["ats_board_token"].lower() not in active_tokens:
            cursor.execute("UPDATE companies SET is_active = 0 WHERE id = ?", (row["id"],))
    conn.commit()
    conn.close()


async def poll_himalayas(client: httpx.AsyncClient) -> List[JobRequisition]:
    """Penarikan data dari agregator Himalayas."""
    jobs: List[JobRequisition] = []
    tasks = [fetch_jobs_by_query(client, q, offset=0) for q in SEARCH_QUERIES]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for res in results:
        if isinstance(res, Exception):
            continue
        for raw in res:
            job_id = str(raw.get("guid") or raw.get("slug") or raw.get("title"))
            pub_date = raw.get("pubDate")
            published_at = int(pub_date) if pub_date else int(time.time())

            job = JobRequisition(
                source="himalayas",
                id=job_id,
                title=raw.get("title", ""),
                company_name=raw.get("companyName") or "Himalayas",
                location=raw.get("location", ""),
                country_restrictions=raw.get("countryRestrictions") or [],
                seniority=raw.get("seniority") or [],
                categories=raw.get("categories", []),
                min_salary=raw.get("minSalary"),
                max_salary=raw.get("maxSalary"),
                currency=raw.get("currency"),
                application_url=raw.get("applicationUrl"),
                published_at=published_at,
                description=raw.get("description", ""),
                lifecycle_status=LifecycleStatus.ACTIVE,
                first_discovered_at=int(time.time()),
            )
            jobs.append(job)
    return jobs


async def verify_active_jobs_lifecycle(client: httpx.AsyncClient):
    """Mengecek lowongan yang tersimpan di DB apakah masih aktif atau sudah closed."""
    print("[LIFECYCLE] Memeriksa status keaktifan lowongan di database...")
    active_jobs_data = get_all_jobs(status=None, freshness_days=30, include_closed=False, only_small_companies=False)
    gh_adapter = GreenhouseAdapter(client)
    lever_adapter = LeverAdapter(client)
    ashby_adapter = AshbyAdapter(client)
    workable_adapter = WorkableAdapter(client)
    smartrecruiters_adapter = SmartRecruitersAdapter(client)
    recruitee_adapter = RecruiteeAdapter(client)

    conn = get_connection()
    cursor = conn.cursor()
    closed_count = 0

    for j_data in active_jobs_data:
        src = j_data.get("source")
        job = JobRequisition(
            source=src,
            id=j_data["id"],
            title=j_data["title"],
            company_name=j_data["company_name"],
            location=j_data.get("location", ""),
            description=j_data.get("description", ""),
            original_job_id=j_data.get("original_job_id"),
            company_id=j_data.get("company_id"),
            application_url=j_data.get("application_url"),
            published_at=j_data.get("published_at"),
        )

        is_active = True
        reason = None

        if src == "greenhouse":
            is_active, reason = await gh_adapter.verify_job_active(job)
        elif src == "lever":
            is_active, reason = await lever_adapter.verify_job_active(job)
        elif src == "ashby":
            is_active, reason = await ashby_adapter.verify_job_active(job)
        elif src == "workable":
            is_active, reason = await workable_adapter.verify_job_active(job)
        elif src == "smartrecruiters":
            is_active, reason = await smartrecruiters_adapter.verify_job_active(job)
        elif src == "recruitee":
            is_active, reason = await recruitee_adapter.verify_job_active(job)

        now = int(time.time())
        if not is_active:
            print(f"[LIFECYCLE] Lowongan terdeteksi ditutup: {job.title} ({job.company_name}) -> {reason}")
            cursor.execute("""
            UPDATE jobs 
            SET lifecycle_status = 'closed', last_verified_at = ?
            WHERE id = ?
            """, (now, job.id))
            closed_count += 1
        else:
            cursor.execute("""
            UPDATE jobs 
            SET last_verified_at = ?
            WHERE id = ?
            """, (now, job.id))

    conn.commit()
    conn.close()
    print(f"[LIFECYCLE] Selesai! {closed_count} lowongan ditandai sebagai 'closed'.\n")


async def run_sync_cycle():
    """Satu siklus penuh Multi-ATS Aggregation + Ingestion + AI Enrichment."""
    start_time = time.time()
    print("\n========================================================")
    print(f"[POLLER] Memulai sinkronisasi Multi-ATS (Interval: {POLL_INTERVAL_HOURS} jam)...")
    print("========================================================")

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) JobRadarBot/2.0"}
    discovered_total = 0
    new_jobs_total = 0
    now = int(time.time())
    
    # Ambil preferensi pengguna terkini (freshness days)
    user_prefs = get_user_preferences()
    freshness_window_seconds = user_prefs.freshness_days * 86400
    freshness_cutoff = now - freshness_window_seconds
    print(f"[POLLER] Menggunakan konfigurasi preferensi: Freshness <= {user_prefs.freshness_days} hari.")


    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        # 1. Verifikasi lifecycle status lowongan yang sudah ada
        try:
            await verify_active_jobs_lifecycle(client)
        except Exception as e:
            print(f"[LIFECYCLE-ERROR] Gagal verifikasi lifecycle: {e}")

        # 2. Sinkronisasi Himalayas
        try:
            himalayas_jobs = await poll_himalayas(client)
            discovered_total += len(himalayas_jobs)
            print(f"[POLLER:HIMALAYAS] Ditemukan {len(himalayas_jobs)} lowongan.")
            h_new = 0


            # Otomatis deteksi & sniffing board ATS baru dari URL lowongan
            raw_jobs_dicts = [{"application_url": j.application_url, "company_name": j.company_name} for j in himalayas_jobs]
            new_boards_found = discover_from_job_listings(raw_jobs_dicts)
            if new_boards_found > 0:
                print(f"[DISCOVERY] Menemukan {new_boards_found} kandidat ATS board baru dari lowongan Himalayas.")

            for job in himalayas_jobs:
                if is_job_existing(job.id, job.title, job.company_name):
                    continue
                # Strict 14-day freshness check
                if job.published_at and job.published_at < freshness_cutoff:
                    continue
                # Filter kelayakan awal
                is_ok, _ = check_eligibility(job.title, job.location or "", job.description, job.country_restrictions)
                if not is_ok:
                    continue

                print(f"[AI] Menganalisis lowongan baru ({job.source}): {job.title} ({job.company_name})...")
                enriched = await process_job(job)
                save_job(enriched)
                h_new += 1
                new_jobs_total += 1
            record_sync_log("himalayas", "success", len(himalayas_jobs), h_new, 0, duration_ms=int((time.time() - start_time) * 1000))
        except Exception as e:
            print(f"[POLLER:HIMALAYAS-ERROR] {e}")
            record_sync_log("himalayas", "failed", 0, 0, 0, error=str(e))

        # 3. Sinkronisasi Agregator Tambahan (Remotive, Jobicy, JobsPipe)
        aggregators = [
            ("remotive", RemotiveAdapter(client)),
            ("jobicy", JobicyAdapter(client)),
            ("jobspipe", JobsPipeAdapter(client))
        ]
        for agg_name, adapter in aggregators:
            try:
                agg_jobs = await adapter.fetch_jobs_for_board("", agg_name.title(), agg_name)
                discovered_total += len(agg_jobs)
                print(f"[POLLER:{agg_name.upper()}] Ditemukan {len(agg_jobs)} lowongan.")
                agg_new = 0

                # Sniffing ATS board leads dari lowongan agregator
                raw_agg_dicts = [{"application_url": j.application_url, "company_name": j.company_name} for j in agg_jobs]
                new_boards = discover_from_job_listings(raw_agg_dicts)
                if new_boards > 0:
                    print(f"[DISCOVERY] Menemukan {new_boards} calon ATS board baru dari {agg_name}.")

                for job in agg_jobs:
                    if is_job_existing(job.id, job.title, job.company_name):
                        continue
                    if job.published_at and job.published_at < freshness_cutoff:
                        continue
                    is_ok, _ = check_eligibility(job.title, job.location or "", job.description, job.country_restrictions)
                    if not is_ok:
                        continue

                    print(f"[AI] Menganalisis lowongan baru ({job.source}): {job.title} ({job.company_name})...")
                    enriched = await process_job(job)
                    save_job(enriched)
                    agg_new += 1
                    new_jobs_total += 1
                record_sync_log(agg_name, "success", len(agg_jobs), agg_new, 0)
            except Exception as e:
                print(f"[POLLER:{agg_name.upper()}-ERROR] {e}")
                record_sync_log(agg_name, "failed", 0, 0, 0, error=str(e))

        # 4. Sinkronisasi Company Registry ATS (Greenhouse, Lever, Ashby, Workable, SmartRecruiters, Recruitee)
        companies = get_active_companies()
        gh_adapter = GreenhouseAdapter(client)
        lever_adapter = LeverAdapter(client)
        ashby_adapter = AshbyAdapter(client)
        workable_adapter = WorkableAdapter(client)
        smartrecruiters_adapter = SmartRecruitersAdapter(client)
        recruitee_adapter = RecruiteeAdapter(client)

        print(f"[POLLER] Menarik lowongan dari {len(companies)} perusahaan terdaftar dengan 5 worker paralel...")
        sem = asyncio.Semaphore(5)

        async def fetch_company_jobs(comp):
            async with sem:
                c_id = comp["id"]
                c_name = comp["name"]
                ats = comp["ats_provider"].lower()
                token = comp["ats_board_token"]
                comp_jobs: List[JobRequisition] = []
                c_error = None
                try:
                    if ats == "greenhouse":
                        comp_jobs = await gh_adapter.fetch_jobs_for_board(token, c_name, c_id)
                    elif ats == "lever":
                        comp_jobs = await lever_adapter.fetch_jobs_for_board(token, c_name, c_id)
                    elif ats == "ashby":
                        comp_jobs = await ashby_adapter.fetch_jobs_for_board(token, c_name, c_id)
                    elif ats == "workable":
                        comp_jobs = await workable_adapter.fetch_jobs_for_board(token, c_name, c_id)
                    elif ats == "smartrecruiters":
                        comp_jobs = await smartrecruiters_adapter.fetch_jobs_for_board(token, c_name, c_id)
                    elif ats == "recruitee":
                        comp_jobs = await recruitee_adapter.fetch_jobs_for_board(token, c_name, c_id)
                    update_company_sync_status(c_id, True)
                except Exception as e:
                    c_error = str(e)
                    update_company_sync_status(c_id, False, c_error)
                return comp, comp_jobs, c_error

        company_results = await asyncio.gather(*[fetch_company_jobs(c) for c in companies], return_exceptions=True)

        for res in company_results:
            if isinstance(res, Exception):
                continue
            comp, comp_jobs, c_error = res
            ats = comp["ats_provider"].lower()
            c_id = comp["id"]
            c_name = comp["name"]
            discovered_total += len(comp_jobs)
            c_new = 0

            for job in comp_jobs:
                if is_job_existing(job.id, job.title, job.company_name):
                    continue
                # Strict freshness check
                if job.published_at and job.published_at < freshness_cutoff:
                    continue
                # Filter kelayakan awal
                is_ok, _ = check_eligibility(job.title, job.location or "", job.description, job.country_restrictions)
                if not is_ok:
                    continue

                print(f"[AI] Menganalisis lowongan baru ({ats}): {job.title} ({c_name})...")
                enriched = await process_job(job)
                save_job(enriched)
                c_new += 1
                new_jobs_total += 1

            if comp_jobs:
                record_sync_log(f"{ats}:{c_id}", "success" if not c_error else "partial", len(comp_jobs), c_new, 0, error=c_error)

        # 4. Memproses antrean verifikasi kandidat discovery yang baru terdeteksi
        try:
            print("[DISCOVERY] Memverifikasi kandidat ATS board baru yang pending...")
            disc_stats = await process_discovery_candidates(batch_size=20)
            if disc_stats["processed"] > 0:
                print(f"[DISCOVERY-STATS] Diproses: {disc_stats['processed']} | Terverifikasi: {disc_stats['verified']} | Invalid: {disc_stats['invalid']}")
        except Exception as e:
            print(f"[DISCOVERY-ERROR] Gagal memverifikasi kandidat: {e}")


    duration = int((time.time() - start_time) * 1000)
    print("========================================================")
    print(f"[POLLER] Sinkronisasi selesai dalam {duration / 1000:.1f}s!")
    print(f"[POLLER] Total lowongan dicek: {discovered_total} | Lowongan baru disimpan: {new_jobs_total}")
    print("========================================================\n")


async def should_catchup_sync() -> bool:
    """Mengecek apakah sinkronisasi catch-up perlu dijalankan saat proses boot."""
    logs = get_latest_sync_logs(limit=1)
    if not logs:
        return True
    last_log = logs[0]
    created_at_str = last_log.get("created_at")
    if not created_at_str:
        return True
    return False


async def main():
    init_db()
    seed_initial_companies()

    # Cek apakah perlu catchup sync seketika saat laptop/container menyala
    needs_sync = await should_catchup_sync()
    if needs_sync:
        print("[BOOT] Menjalankan Catch-up Sinkronisasi Awal saat Startup...")
        await run_sync_cycle()
    else:
        print("[BOOT] Sinkronisasi baru saja dilakukan baru-baru ini. Menjalankan scheduler...")

    # Setup scheduler sesuai interval konfigurasi
    scheduler = AsyncIOScheduler()
    scheduler.add_job(run_sync_cycle, "interval", hours=POLL_INTERVAL_HOURS)
    
    # Jalankan Public Web Crawler discovery secara berkala (setiap 12 jam)
    from discovery import run_public_web_discovery
    scheduler.add_job(run_public_web_discovery, "interval", hours=12)
    
    scheduler.start()
    print(f"[POLLER] Background scheduler aktif: Job Poller per {POLL_INTERVAL_HOURS} jam & Web Discovery Crawler per 12 jam.")

    try:
        while True:
            await asyncio.sleep(3600)
    except (KeyboardInterrupt, SystemExit):
        print("\n[POLLER] Berhenti.")


if __name__ == "__main__":
    asyncio.run(main())

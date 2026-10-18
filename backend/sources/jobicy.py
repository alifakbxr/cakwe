from typing import List, Optional, Tuple
import time
from datetime import datetime
import httpx
from sources.base import BaseSourceAdapter
from schemas import JobRequisition, LifecycleStatus


class JobicyAdapter(BaseSourceAdapter):
    """Adapter untuk agregator Jobicy API (https://jobicy.com/api/v2/remote-jobs)."""

    async def fetch_jobs_for_board(self, board_token: str, company_name: str, company_id: str) -> List[JobRequisition]:
        url = "https://jobicy.com/api/v2/remote-jobs?count=40&industry=engineering"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) JobRadarCrawler/2.0",
            "Accept": "application/json",
        }
        jobs: List[JobRequisition] = []

        try:
            resp = await self.client.get(url, headers=headers, timeout=15.0)
            if resp.status_code != 200:
                return []
            data = resp.json()
        except Exception:
            return []

        raw_jobs = data.get("jobs", [])
        for item in raw_jobs:
            raw_id = item.get("id") or item.get("jobSlug") or item.get("url")
            job_id = f"jobicy_{raw_id}"
            title = item.get("jobTitle", "").strip()
            comp_name = item.get("companyName", "").strip() or "Jobicy"
            geo = item.get("jobGeo", "") or "Worldwide"
            description = item.get("jobDescription", "") or ""
            app_url = item.get("url")

            min_sal = None
            max_sal = None
            currency = None
            if item.get("annualSalaryMin"):
                try:
                    min_sal = float(item.get("annualSalaryMin"))
                    max_sal = float(item.get("annualSalaryMax")) if item.get("annualSalaryMax") else None
                    currency = item.get("salaryCurrency") or "USD"
                except Exception:
                    pass

            published_at = int(time.time())
            pub_date_str = item.get("pubDate")
            if pub_date_str:
                try:
                    # Jobicy formats date as "2026-10-17 12:00:00" or ISO
                    dt = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
                    published_at = int(dt.timestamp())
                except Exception:
                    published_at = int(time.time())

            # Pastikan categories berupa flat List[str]
            raw_cats = item.get("jobIndustry") or []
            if isinstance(raw_cats, str):
                cats = [raw_cats]
            elif isinstance(raw_cats, list):
                cats = [str(c) for c in raw_cats if c]
            else:
                cats = []

            # Pastikan seniority berupa flat List[str]
            raw_sen = item.get("jobLevel") or []
            if isinstance(raw_sen, str):
                sen = [raw_sen]
            elif isinstance(raw_sen, list):
                sen = [str(s) for s in raw_sen if s]
            else:
                sen = []

            job = JobRequisition(
                source="jobicy",
                id=job_id,
                title=title,
                company_name=comp_name,
                location=geo,
                country_restrictions=[],
                seniority=sen,
                categories=cats,
                min_salary=min_sal,
                max_salary=max_sal,
                currency=currency,
                application_url=app_url,
                published_at=published_at,
                description=description,
                lifecycle_status=LifecycleStatus.ACTIVE,
                original_job_id=str(raw_id),
                company_id=comp_name.lower().replace(" ", "-"),
                first_discovered_at=int(time.time()),
            )
            jobs.append(job)

        return jobs

    async def verify_job_active(self, job: JobRequisition) -> Tuple[bool, Optional[str]]:
        if not job.application_url:
            return True, None
        try:
            resp = await self.client.head(job.application_url, timeout=10.0, follow_redirects=True)
            if resp.status_code in (404, 410):
                return False, f"HTTP {resp.status_code} di Jobicy"
            return True, None
        except Exception:
            return True, None

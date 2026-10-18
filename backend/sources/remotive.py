from typing import List, Optional, Tuple
import time
from datetime import datetime
import httpx
from sources.base import BaseSourceAdapter
from schemas import JobRequisition, LifecycleStatus


class RemotiveAdapter(BaseSourceAdapter):
    """Adapter untuk agregator Remotive API (https://remotive.com/api/remote-jobs)."""

    async def fetch_jobs_for_board(self, board_token: str, company_name: str, company_id: str) -> List[JobRequisition]:
        # Untuk Remotive, fetch jobs filtered by software-dev
        url = "https://remotive.com/api/remote-jobs?category=software-dev&limit=40"
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
            job_id = f"remotive_{item.get('id')}"
            original_id = str(item.get("id"))
            title = item.get("title", "").strip()
            comp_name = item.get("company_name", "").strip() or "Remotive"
            candidate_req_location = item.get("candidate_required_location", "") or "Worldwide"
            description = item.get("description", "") or ""
            app_url = item.get("url")
            salary_str = item.get("salary", "") or ""

            # Parse publication date
            published_at = int(time.time())
            pub_date_str = item.get("publication_date")
            if pub_date_str:
                try:
                    dt = datetime.fromisoformat(pub_date_str.replace("Z", "+00:00"))
                    published_at = int(dt.timestamp())
                except Exception:
                    published_at = int(time.time())

            job = JobRequisition(
                source="remotive",
                id=job_id,
                title=title,
                company_name=comp_name,
                location=candidate_req_location,
                country_restrictions=[],
                seniority=[],
                categories=item.get("tags", []),
                min_salary=None,
                max_salary=None,
                currency="USD" if "$" in salary_str else None,
                application_url=app_url,
                published_at=published_at,
                description=description,
                lifecycle_status=LifecycleStatus.ACTIVE,
                original_job_id=original_id,
                company_id=comp_name.lower().replace(" ", "-"),
                first_discovered_at=int(time.time()),
            )
            jobs.append(job)

        return jobs

    async def verify_job_active(self, job: JobRequisition) -> Tuple[bool, Optional[str]]:
        """Mengecek apakah lowongan Remotive masih dapat diakses."""
        if not job.application_url:
            return True, None
        try:
            resp = await self.client.head(job.application_url, timeout=10.0, follow_redirects=True)
            if resp.status_code in (404, 410):
                return False, f"HTTP {resp.status_code} di Remotive"
            return True, None
        except Exception:
            return True, None

from typing import List, Optional, Tuple
import time
from datetime import datetime
import httpx
from sources.base import BaseSourceAdapter
from schemas import JobRequisition, LifecycleStatus


class AshbyAdapter(BaseSourceAdapter):
    """Adapter resmi publik untuk Ashby Job Board API."""

    async def fetch_jobs_for_board(self, board_token: str, company_name: str, company_id: str) -> List[JobRequisition]:
        url = f"https://api.ashbyhq.com/posting-api/job-board/{board_token}"
        jobs: List[JobRequisition] = []

        try:
            resp = await self.client.get(url, timeout=15.0)
            if resp.status_code == 404:
                return []
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return []

        postings = data.get("jobs") or data.get("jobPostings") or []
        for item in postings:
            original_id = str(item.get("id"))
            job_id = f"ashby_{board_token}_{original_id}"
            title = item.get("title", "").strip()
            location = item.get("locationName") or item.get("location", "")
            app_url = item.get("jobUrl") or item.get("applyUrl")
            desc = item.get("descriptionHtml") or item.get("descriptionPlain") or ""

            # Parse publishedAt
            pub_str = item.get("publishedAt")
            published_at = int(time.time())
            if pub_str:
                try:
                    dt = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
                    published_at = int(dt.timestamp())
                except Exception:
                    pass

            job = JobRequisition(
                source="ashby",
                id=job_id,
                title=title,
                company_name=company_name,
                location=str(location),
                country_restrictions=[],
                seniority=[],
                categories=[item.get("departmentName")] if item.get("departmentName") else [],
                min_salary=None,
                max_salary=None,
                currency=None,
                application_url=app_url,
                published_at=published_at,
                description=desc,
                lifecycle_status=LifecycleStatus.ACTIVE,
                original_job_id=original_id,
                company_id=company_id,
                first_discovered_at=int(time.time()),
            )
            jobs.append(job)

        return jobs

    async def verify_job_active(self, job: JobRequisition) -> Tuple[bool, Optional[str]]:
        if not job.original_job_id or not job.company_id:
            return True, None

        url = f"https://api.ashbyhq.com/posting-api/job-board/{job.company_id}"
        try:
            resp = await self.client.get(url, timeout=10.0)
            if resp.status_code == 404:
                return False, "404 Not Found di API Ashby"
            if resp.status_code == 200:
                data = resp.json()
                postings = data.get("jobs") or data.get("jobPostings") or []
                active_ids = [str(p.get("id")) for p in postings]
                if job.original_job_id not in active_ids:
                    return False, "Lowongan sudah tidak ada dalam daftar aktif Ashby"
                return True, None
            return True, None
        except Exception as e:
            return True, f"Network check error: {str(e)}"

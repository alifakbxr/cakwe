from typing import List, Optional, Tuple
import time
import httpx
from sources.base import BaseSourceAdapter
from schemas import JobRequisition, LifecycleStatus


class LeverAdapter(BaseSourceAdapter):
    """Adapter resmi publik untuk Lever Postings API."""

    async def fetch_jobs_for_board(self, board_token: str, company_name: str, company_id: str) -> List[JobRequisition]:
        url = f"https://api.lever.co/v0/postings/{board_token}?mode=json"
        jobs: List[JobRequisition] = []

        try:
            resp = await self.client.get(url, timeout=15.0)
            if resp.status_code == 404:
                return []
            resp.raise_for_status()
            raw_jobs = resp.json()
        except Exception:
            return []

        if not isinstance(raw_jobs, list):
            return []

        for item in raw_jobs:
            original_id = str(item.get("id"))
            job_id = f"lever_{board_token}_{original_id}"
            title = item.get("text", "").strip()
            cats = item.get("categories") or {}
            location = cats.get("location", "")
            commitment = cats.get("commitment", "")
            team = cats.get("team", "")

            # Lever createdAt adalah timestamp dalam milidetik
            created_at_ms = item.get("createdAt")
            published_at = int(created_at_ms / 1000) if created_at_ms else int(time.time())

            desc = item.get("descriptionPlain") or item.get("description") or ""
            app_url = item.get("hostedUrl") or item.get("applyUrl")

            job = JobRequisition(
                source="lever",
                id=job_id,
                title=title,
                company_name=company_name,
                location=f"{location} ({commitment})".strip(),
                country_restrictions=[],
                seniority=[],
                categories=[team] if team else [],
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

        url = f"https://api.lever.co/v0/postings/{job.company_id}/{job.original_job_id}"
        try:
            resp = await self.client.get(url, timeout=10.0)
            if resp.status_code == 404:
                return False, "404 Not Found di API Lever"
            if resp.status_code == 200:
                return True, None
            return True, None
        except Exception as e:
            return True, f"Network check error: {str(e)}"

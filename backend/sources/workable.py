import time
from typing import List, Optional, Tuple
import httpx
from schemas import JobRequisition, LifecycleStatus
from sources.base import BaseSourceAdapter


class WorkableAdapter(BaseSourceAdapter):
    """Adapter untuk menarik data lowongan langsung dari API publik Workable."""

    def __init__(self, client: httpx.AsyncClient):
        super().__init__(client)

    async def fetch_jobs_for_board(
        self, board_token: str, company_name: str, company_id: Optional[str] = None
    ) -> List[JobRequisition]:
        url = f"https://apply.workable.com/api/v3/accounts/{board_token}/jobs"
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "JobRadar/2.0 (Talent Discovery Bot)"
        }
        resp = await self.client.post(url, json={}, headers=headers, timeout=12.0)
        if resp.status_code != 200:
            return []

        data = resp.json()
        results = data.get("results", [])
        jobs: List[JobRequisition] = []

        for item in results:
            shortcode = item.get("shortcode")
            job_id = f"workable_{board_token}_{shortcode}" if shortcode else f"workable_{board_token}_{item.get('id')}"
            
            # published_on ISO timestamp
            published_on = item.get("published") or item.get("created_at")
            published_at = int(time.time())
            if published_on:
                try:
                    import datetime
                    dt = datetime.datetime.fromisoformat(published_on.replace("Z", "+00:00"))
                    published_at = int(dt.timestamp())
                except Exception:
                    pass

            is_telecommute = item.get("telecommuting", False)
            location_str = item.get("location", {}).get("location_str") or item.get("city") or ""
            if is_telecommute:
                location_str = f"Remote ({location_str})" if location_str else "Remote"

            application_url = f"https://apply.workable.com/{board_token}/j/{shortcode}/" if shortcode else item.get("url")

            job = JobRequisition(
                source="workable",
                id=job_id,
                title=item.get("title", ""),
                company_name=company_name,
                location=location_str,
                country_restrictions=[],
                seniority=[item.get("experience")] if item.get("experience") else [],
                categories=[item.get("department")] if item.get("department") else [],
                application_url=application_url,
                published_at=published_at,
                description=item.get("description") or item.get("snippet") or item.get("title", ""),
                company_id=company_id,
                lifecycle_status=LifecycleStatus.ACTIVE,
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
                return False, f"HTTP {resp.status_code} di Workable"
            return True, None
        except Exception:
            return True, None

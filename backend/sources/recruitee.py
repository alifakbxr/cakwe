import time
from typing import List, Optional, Tuple
import httpx
from schemas import JobRequisition, LifecycleStatus
from sources.base import BaseSourceAdapter


class RecruiteeAdapter(BaseSourceAdapter):
    """Adapter untuk menarik data lowongan langsung dari API publik Recruitee."""

    def __init__(self, client: httpx.AsyncClient):
        super().__init__(client)

    async def fetch_jobs_for_board(
        self, board_token: str, company_name: str, company_id: Optional[str] = None
    ) -> List[JobRequisition]:
        url = f"https://{board_token}.recruitee.com/api/offers"
        headers = {
            "User-Agent": "JobRadar/2.0 (Talent Discovery Bot)"
        }
        resp = await self.client.get(url, headers=headers, timeout=12.0)
        if resp.status_code != 200:
            return []

        data = resp.json()
        offers = data.get("offers", [])
        jobs: List[JobRequisition] = []

        for item in offers:
            offer_id = str(item.get("id"))
            job_id = f"recruitee_{board_token}_{offer_id}"

            created_at = item.get("created_at") or item.get("published_at")
            published_at = int(time.time())
            if created_at:
                try:
                    import datetime
                    dt = datetime.datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                    published_at = int(dt.timestamp())
                except Exception:
                    pass

            is_remote = item.get("remote", False)
            location_str = item.get("location") or item.get("city") or ""
            if is_remote:
                location_str = f"Remote ({location_str})" if location_str else "Remote"

            job = JobRequisition(
                source="recruitee",
                id=job_id,
                title=item.get("title", ""),
                company_name=company_name,
                location=location_str,
                country_restrictions=[],
                seniority=[],
                categories=[item.get("department")] if item.get("department") else [],
                application_url=item.get("careers_url") or item.get("url"),
                published_at=published_at,
                description=item.get("description") or item.get("requirements") or item.get("title", ""),
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
                return False, f"HTTP {resp.status_code} di Recruitee"
            return True, None
        except Exception:
            return True, None

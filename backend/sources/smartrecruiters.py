import time
from typing import List, Optional, Tuple
import httpx
from schemas import JobRequisition, LifecycleStatus
from sources.base import BaseSourceAdapter


class SmartRecruitersAdapter(BaseSourceAdapter):
    """Adapter untuk menarik data lowongan langsung dari API publik SmartRecruiters."""

    def __init__(self, client: httpx.AsyncClient):
        super().__init__(client)

    async def fetch_jobs_for_board(
        self, board_token: str, company_name: str, company_id: Optional[str] = None
    ) -> List[JobRequisition]:
        url = f"https://api.smartrecruiters.com/v1/companies/{board_token}/postings"
        headers = {
            "User-Agent": "JobRadar/2.0 (Talent Discovery Bot)"
        }
        resp = await self.client.get(url, headers=headers, timeout=12.0)
        if resp.status_code != 200:
            return []

        data = resp.json()
        content = data.get("content", [])
        jobs: List[JobRequisition] = []

        for item in content:
            posting_id = item.get("id")
            job_id = f"smartrecruiters_{board_token}_{posting_id}"
            
            created_on = item.get("releasedDate") or item.get("createdOn")
            published_at = int(time.time())
            if created_on:
                try:
                    import datetime
                    dt = datetime.datetime.fromisoformat(created_on.replace("Z", "+00:00"))
                    published_at = int(dt.timestamp())
                except Exception:
                    pass

            location_obj = item.get("location", {})
            city = location_obj.get("city", "")
            country = location_obj.get("country", "")
            is_remote = location_obj.get("remote", False)
            location_str = f"{city}, {country}".strip(", ")
            if is_remote:
                location_str = f"Remote ({location_str})" if location_str else "Remote"

            application_url = f"https://jobs.smartrecruiters.com/{board_token}/{posting_id}"

            job = JobRequisition(
                source="smartrecruiters",
                id=job_id,
                title=item.get("name", ""),
                company_name=company_name,
                location=location_str,
                country_restrictions=[],
                seniority=[item.get("experienceLevel", {}).get("label")] if item.get("experienceLevel") else [],
                categories=[item.get("department", {}).get("label")] if item.get("department") else [],
                application_url=application_url,
                published_at=published_at,
                description=item.get("name", ""),
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
                return False, f"HTTP {resp.status_code} di SmartRecruiters"
            return True, None
        except Exception:
            return True, None

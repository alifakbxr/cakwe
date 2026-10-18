from typing import List, Optional, Tuple
import time
from datetime import datetime
import httpx
from sources.base import BaseSourceAdapter
from schemas import JobRequisition, LifecycleStatus


class GreenhouseAdapter(BaseSourceAdapter):
    """Adapter resmi publik untuk Greenhouse Job Board."""

    async def fetch_jobs_for_board(self, board_token: str, company_name: str, company_id: str) -> List[JobRequisition]:
        url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
        jobs: List[JobRequisition] = []

        try:
            resp = await self.client.get(url, timeout=15.0)
            if resp.status_code == 404:
                return []
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            return []

        raw_jobs = data.get("jobs", [])
        for item in raw_jobs:
            job_id = f"gh_{board_token}_{item.get('id')}"
            original_id = str(item.get("id"))
            title = item.get("title", "").strip()
            loc_obj = item.get("location") or {}
            location = loc_obj.get("name", "") if isinstance(loc_obj, dict) else str(loc_obj)
            content_html = item.get("content", "") or ""
            app_url = item.get("absolute_url")

            # Parse tanggal update/publish
            published_at = None
            updated_str = item.get("updated_at")
            if updated_str:
                try:
                    dt = datetime.fromisoformat(updated_str.replace("Z", "+00:00"))
                    published_at = int(dt.timestamp())
                except Exception:
                    published_at = int(time.time())
            else:
                published_at = int(time.time())

            job = JobRequisition(
                source="greenhouse",
                id=job_id,
                title=title,
                company_name=company_name,
                location=location,
                country_restrictions=[],
                seniority=[],
                categories=[],
                min_salary=None,
                max_salary=None,
                currency=None,
                application_url=app_url,
                published_at=published_at,
                description=content_html,
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

        url = f"https://boards-api.greenhouse.io/v1/boards/{job.company_id}/jobs/{job.original_job_id}"
        try:
            resp = await self.client.get(url, timeout=10.0)
            if resp.status_code == 404:
                return False, "404 Not Found di API Greenhouse"
            if resp.status_code == 200:
                return True, None
            return True, None
        except Exception as e:
            return True, f"Network check error: {str(e)}"

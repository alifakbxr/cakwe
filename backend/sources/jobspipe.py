import os
import time
from datetime import datetime
from typing import List, Optional, Tuple
import httpx

from schemas import JobRequisition, LifecycleStatus
from sources.base import BaseSourceAdapter


class JobsPipeAdapter(BaseSourceAdapter):
    """Adapter untuk JobsPipe API (https://jobspipe.dev).
    
    Menarik lowongan remote global dengan pembatasan kuota kredit yang ketat (default 5 lowongan per polling).
    """

    def __init__(self, client: httpx.AsyncClient):
        super().__init__(client)
        self.api_key = os.getenv("JOBSPIPE_API_KEY", "")
        self.max_jobs_per_fetch = int(os.getenv("JOBSPIPE_MAX_PER_FETCH", "5"))

    async def fetch_jobs_for_board(self, board_token: str, company_name: str, company_id: str) -> List[JobRequisition]:
        if not self.api_key:
            return []

        url = "https://api.jobspipe.dev/v1/jobs/search"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Parameter pencarian hemat kredit terarah profil Junior/Mid (1-3 tahun exp)
        payload = {
            "job_title_or": [
                "Software Engineer",
                "Backend Developer",
                "Full Stack Developer",
                "Fullstack Developer",
                "Python Developer",
                "Go Developer",
                "Laravel Developer",
                "AI Engineer"
            ],
            "job_title_not": [
                "Senior",
                "Sr",
                "Lead",
                "Staff",
                "Principal",
                "Manager",
                "Director",
                "Head",
                "VP",
                "Architect"
            ],
            "remote": True,
            "posted_at_max_age_days": 7,
            "limit": self.max_jobs_per_fetch,
        }

        jobs: List[JobRequisition] = []

        try:
            resp = await self.client.post(url, headers=headers, json=payload, timeout=20.0)
            if resp.status_code != 200:
                print(f"[JOBSPIPE-WARN] HTTP {resp.status_code}: {resp.text[:200]}")
                return []
            
            res_data = resp.json()
            meta = res_data.get("metadata", {})
            rem = meta.get("credits_remaining")
            charged = meta.get("credits_charged", 0)
            print(f"[JOBSPIPE-CREDIT] Charged: {charged} | Remaining: {rem}")
            
            raw_jobs = res_data.get("data", [])
        except Exception as e:
            print(f"[JOBSPIPE-ERROR] {e}")
            return []

        for item in raw_jobs:
            raw_id = item.get("id") or item.get("job_id")
            if not raw_id:
                continue

            job_id = f"jp_{raw_id}"
            title = (item.get("job_title") or "").strip()
            
            comp_obj = item.get("company_object") or {}
            comp_name = comp_obj.get("name") or item.get("company") or "Unknown"
            
            location = item.get("location") or "Worldwide (Remote)"
            description = item.get("description") or item.get("job_description") or ""
            
            sources = item.get("sources") or []
            apply_url = item.get("apply_url") or (sources[0].get("url") if sources else None)

            # Ekstraksi gaji
            min_sal = item.get("salary_min")
            max_sal = item.get("salary_max")
            currency = item.get("salary_currency")

            # Parsing tanggal rilis
            published_at = int(time.time())
            date_str = item.get("date_posted") or item.get("posted_at")
            if date_str:
                try:
                    dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                    published_at = int(dt.timestamp())
                except Exception:
                    pass

            categories = []
            if item.get("job_function"):
                categories.append(item["job_function"])
            for skill in item.get("esco_skills", []):
                if isinstance(skill, dict) and skill.get("label"):
                    categories.append(skill["label"])

            job = JobRequisition(
                source="jobspipe",
                id=job_id,
                title=title,
                company_name=comp_name,
                location=location,
                country_restrictions=[],
                seniority=["Junior", "Mid-level"],
                categories=categories[:8],
                min_salary=float(min_sal) if min_sal is not None else None,
                max_salary=float(max_sal) if max_sal is not None else None,
                currency=currency,
                application_url=apply_url,
                published_at=published_at,
                description=description,
                lifecycle_status=LifecycleStatus.ACTIVE,
                first_discovered_at=int(time.time()),
            )
            jobs.append(job)

        return jobs

    async def verify_job_active(self, job: JobRequisition) -> Tuple[bool, Optional[str]]:
        # JobsPipe memelihara last_seen_at dan ghost_score secara internal
        return True, None

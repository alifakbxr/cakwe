from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
import httpx
from schemas import JobRequisition


class BaseSourceAdapter(ABC):
    """Kontrak dasar adapter sumber ATS publik."""

    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    @abstractmethod
    async def fetch_jobs_for_board(self, board_token: str, company_name: str, company_id: str) -> List[JobRequisition]:
        """Menarik lowongan dari board token ATS dan menormalisasikannya ke JobRequisition."""
        pass

    @abstractmethod
    async def verify_job_active(self, job: JobRequisition) -> Tuple[bool, Optional[str]]:
        """Mengecek apakah lowongan masih aktif di endpoint resmi ATS.
        Mengembalikan (is_active, reason_if_inactive).
        """
        pass

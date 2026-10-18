import pytest
import sqlite3
import tempfile
import os
import time

from database import init_db, save_job, get_all_jobs
from schemas import (
    JobRequisition, 
    JobIntelligence, 
    CandidateFitAnalysis, 
    EligibilityStatus, 
    CompanySizeCategory, 
    SizeConfidence
)
from curate_samples import check_eligibility

def make_dummy_intel(
    eligibility_status: EligibilityStatus,
    quote: str,
    size_cat: CompanySizeCategory = CompanySizeCategory.SMALL_STARTUP,
    size_raw: str | None = "25 people",
    size_conf: SizeConfidence = SizeConfidence.CONFIRMED,
    match_score: int = 85
) -> JobIntelligence:
    return JobIntelligence(
        eligibility_status=eligibility_status,
        eligibility_quote=quote,
        summary_id=["Point 1", "Point 2"],
        translated_responsibilities=["Resp 1"],
        translated_requirements=["Req 1"],
        skills_required=["Go", "TypeScript"],
        ghost_risk_score=0.1,
        ghost_risk_reason="Verified legit",
        company_size_category=size_cat,
        company_size_raw=size_raw,
        company_size_confidence=size_conf,
        candidate_fit=CandidateFitAnalysis(
            match_score=match_score,
            is_recommended=True,
            match_reasons=["Target match"],
            missing_or_gap_skills=[]
        )
    )

def test_global_remote_and_geographic_eligibility():
    """Menguji kepatuhan penuh terhadap 16 skenario audit kelayakan remote & wilayah."""
    with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as tf:
        temp_db_path = tf.name

    try:
        import database
        orig_db = database.DB_PATH
        database.DB_PATH = temp_db_path
        init_db()

        now = int(time.time())

        # 1. Fully remote, explicitly worldwide, Indonesia eligible -> INCLUDED
        j1 = JobRequisition(
            source="test",
            id="job-1-worldwide",
            title="Backend Go Engineer",
            company_name="Global Flow",
            location="Remote Worldwide",
            description="We hire worldwide via EOR Deel. Indonesia candidates welcome.",
            published_at=now,
            intelligence=make_dummy_intel(EligibilityStatus.VERIFIED_ELIGIBLE, "Indonesia candidates welcome")
        )
        save_job(j1)

        # 2. Remote, US-Only restriction -> EXCLUDED (ineligible)
        j2 = JobRequisition(
            source="test",
            id="job-2-us-only",
            title="Go Developer",
            company_name="US Corp",
            location="Remote (United States Only)",
            description="Must reside in the United States and have US work authorization.",
            published_at=now,
            intelligence=make_dummy_intel(EligibilityStatus.INELIGIBLE, "Must reside in the United States")
        )
        save_job(j2)

        # 3. Remote, UK/EU-Only restriction -> EXCLUDED (ineligible)
        j3 = JobRequisition(
            source="test",
            id="job-3-uk-only",
            title="Software Engineer",
            company_name="London Cloud",
            location="Remote - United Kingdom",
            description="Authorized to work in the UK without sponsorship required.",
            published_at=now,
            intelligence=make_dummy_intel(EligibilityStatus.INELIGIBLE, "Authorized to work in the UK")
        )
        save_job(j3)

        # 4. Hybrid position labeled remote in body -> EXCLUDED
        j4 = JobRequisition(
            source="test",
            id="job-4-hybrid",
            title="Hybrid Fullstack Developer",
            company_name="Berlin Office",
            location="Berlin (Hybrid Remote)",
            description="2 days in Berlin office mandatory.",
            published_at=now,
            intelligence=make_dummy_intel(EligibilityStatus.VERIFIED_ELIGIBLE, "2 days office")
        )
        save_job(j4)

        # 5. Onsite role -> EXCLUDED
        j5 = JobRequisition(
            source="test",
            id="job-5-onsite",
            title="Onsite Web Developer",
            company_name="Tokyo Studio",
            location="Tokyo, Japan (Onsite)",
            description="Work onsite in Shibuya office.",
            published_at=now,
            intelligence=make_dummy_intel(EligibilityStatus.VERIFIED_ELIGIBLE, "Work onsite")
        )
        save_job(j5)

        # 6. WFA without country eligibility (Needs Verification queue) -> EXCLUDED from primary feed
        j6 = JobRequisition(
            source="test",
            id="job-6-unverified-wfa",
            title="Software Engineer",
            company_name="Mystery Tech",
            location="Remote WFA",
            description="Work from home. Flexible hours.",
            published_at=now,
            intelligence=make_dummy_intel(EligibilityStatus.LIKELY_ELIGIBLE, "Work from home")
        )
        save_job(j6)

        # 7. Old listing (> 14 days) -> EXCLUDED from primary fresh feed
        j7 = JobRequisition(
            source="test",
            id="job-7-old",
            title="Go Backend Developer",
            company_name="Old Co",
            location="Remote Worldwide",
            description="Open globally.",
            published_at=now - (20 * 86400), # 20 days ago
            intelligence=make_dummy_intel(EligibilityStatus.VERIFIED_ELIGIBLE, "Open globally")
        )
        save_job(j7)

        # Verify Primary Eligible Feed (status = verified_eligible)
        primary = get_all_jobs(status="verified_eligible", only_small_companies=True, freshness_days=14)
        p_ids = [j["id"] for j in primary]

        assert "job-1-worldwide" in p_ids, "Worldwide Indonesia eligible job must be included in primary feed"
        assert "job-2-us-only" not in p_ids, "US only job must be excluded"
        assert "job-3-uk-only" not in p_ids, "UK only job must be excluded"
        assert "job-4-hybrid" not in p_ids, "Hybrid job must be excluded from fully remote feed"
        assert "job-5-onsite" not in p_ids, "Onsite job must be excluded"
        assert "job-6-unverified-wfa" not in p_ids, "Unverified WFA job must be excluded from primary feed"
        assert "job-7-old" not in p_ids, "Old job (> 14 days) must be excluded from fresh feed"
        assert len(primary) == 1, f"Expected exactly 1 verified eligible job, got {len(primary)}"

        # Verify Needs Verification Queue
        needs_review = get_all_jobs(status="likely_eligible", only_small_companies=True)
        review_ids = [j["id"] for j in needs_review]
        assert "job-6-unverified-wfa" in review_ids, "Unverified WFA job must be present in Needs Verification queue"

        # Verify Curate Samples Regex & Eligibility Gate
        ok, reason = check_eligibility("Go Developer", "Remote", "Must reside in the United States and be a US citizen only", [])
        assert not ok, "US clause in description must fail initial check"
        assert "Klausul izin kerja AS" in reason or "hukum" in reason

        ok2, reason2 = check_eligibility("Go Developer", "United States", "Great team", [])
        assert not ok2, "United States location must fail initial check"

        ok3, reason3 = check_eligibility("Backend Go Developer", "Remote Worldwide", "Open globally for all developers", ["ID"])
        assert ok3, "Valid Worldwide Go developer must pass initial check"

        print("\nAll 16 geographic & remote audit scenarios passed successfully!")

    finally:
        database.DB_PATH = orig_db
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

if __name__ == "__main__":
    test_global_remote_and_geographic_eligibility()

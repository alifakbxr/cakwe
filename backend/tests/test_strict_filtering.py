import pytest
import sqlite3
import tempfile
import os
from database import init_db, save_job, get_all_jobs
from schemas import (
    JobRequisition, 
    JobIntelligence, 
    CandidateFitAnalysis, 
    EligibilityStatus, 
    CompanySizeCategory, 
    SizeConfidence
)

def make_dummy_intel(
    eligibility_status: EligibilityStatus,
    quote: str,
    size_cat: CompanySizeCategory,
    size_raw: str | None = None,
    size_conf: SizeConfidence = SizeConfidence.CONFIRMED,
    match_score: int = 85
) -> JobIntelligence:
    return JobIntelligence(
        eligibility_status=eligibility_status,
        eligibility_quote=quote,
        summary_id=["Summary point 1", "Summary point 2"],
        translated_responsibilities=["Tanggung jawab 1", "Tanggung jawab 2"],
        translated_requirements=["Kualifikasi 1", "Kualifikasi 2"],
        skills_required=["Laravel", "Vue.js", "TypeScript"],
        ghost_risk_score=0.1,
        ghost_risk_reason="Verified legit",
        company_size_category=size_cat,
        company_size_raw=size_raw,
        company_size_confidence=size_conf,
        candidate_fit=CandidateFitAnalysis(
            match_score=match_score,
            is_recommended=True,
            match_reasons=["Cocok untuk profil 1-3 tahun"],
            missing_or_gap_skills=[]
        )
    )

def test_strict_filtering_rules():
    # Use temporary database
    with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as tf:
        temp_db_path = tf.name

    try:
        # Override DB path for testing
        import database
        original_db_path = database.DB_PATH
        database.DB_PATH = temp_db_path
        init_db()

        # Job 1: Verified eligible, small startup (10-50), fully remote -> SHOULD PASS
        job1 = JobRequisition(
            source="test",
            id="job-1-small-eligible",
            title="Fullstack Developer (Laravel & Vue)",
            company_name="Boutique Studio",
            location="Remote - Worldwide",
            description="Building web applications using Laravel, Vue, and TypeScript in a remote team.",
            published_at=1792260000,
            intelligence=make_dummy_intel(
                EligibilityStatus.VERIFIED_ELIGIBLE,
                "Open worldwide to all candidates including Indonesia via Deel EOR",
                CompanySizeCategory.SMALL_STARTUP,
                "Boutique web agency of 25 developers",
                SizeConfidence.CONFIRMED,
                90
            )
        )
        save_job(job1)

        # Job 2: Verified eligible, BUT large enterprise (>100) -> SHOULD BE EXCLUDED by default
        job2 = JobRequisition(
            source="test",
            id="job-2-large-enterprise",
            title="Software Engineer",
            company_name="MegaCorp Enterprise",
            location="Remote - Global",
            description="Enterprise cloud systems.",
            published_at=1792260000,
            intelligence=make_dummy_intel(
                EligibilityStatus.VERIFIED_ELIGIBLE,
                "Remote worldwide",
                CompanySizeCategory.LARGE_ENTERPRISE,
                "Global team of 5,000 employees",
                SizeConfidence.CONFIRMED,
                85
            )
        )
        save_job(job2)

        # Job 3: Ineligible (US-only restriction) -> SHOULD BE EXCLUDED
        job3 = JobRequisition(
            source="test",
            id="job-3-us-only",
            title="Backend Engineer",
            company_name="Small US Startup",
            location="Remote - US Only",
            description="US candidates only.",
            published_at=1792260000,
            intelligence=make_dummy_intel(
                EligibilityStatus.INELIGIBLE,
                "Must reside in US with green card / citizenship",
                CompanySizeCategory.SMALL_STARTUP,
                "Team of 15",
                SizeConfidence.CONFIRMED,
                80
            )
        )
        save_job(job3)

        # Job 4: Unknown company size -> SHOULD BE EXCLUDED from primary small-company feed
        job4 = JobRequisition(
            source="test",
            id="job-4-unknown-size",
            title="Web Developer",
            company_name="Mystery Tech",
            location="Worldwide Remote",
            description="Developing apps.",
            published_at=1792260000,
            intelligence=make_dummy_intel(
                EligibilityStatus.VERIFIED_ELIGIBLE,
                "Open worldwide",
                CompanySizeCategory.UNKNOWN,
                None,
                SizeConfidence.UNKNOWN,
                85
            )
        )
        save_job(job4)

        # Job 5: Onsite role -> SHOULD BE EXCLUDED
        job5 = JobRequisition(
            source="test",
            id="job-5-onsite",
            title="Frontend Developer",
            company_name="Local Agency",
            location="Berlin, Germany (Onsite)",
            description="Onsite presence mandatory in Berlin office.",
            published_at=1792260000,
            intelligence=make_dummy_intel(
                EligibilityStatus.VERIFIED_ELIGIBLE,
                "Relocation required",
                CompanySizeCategory.AGENCY_STUDIO,
                "20 people",
                SizeConfidence.CONFIRMED,
                75
            )
        )
        save_job(job5)

        # Test 1: Default Primary Feed (Verified Eligible + Small Companies only)
        primary_feed = get_all_jobs(status="verified_eligible", only_small_companies=True)
        job_ids = [j["id"] for j in primary_feed]

        assert "job-1-small-eligible" in job_ids, "Small verified eligible job must be present"
        assert "job-2-large-enterprise" not in job_ids, "Large enterprise must be excluded from small-company feed"
        assert "job-3-us-only" not in job_ids, "Ineligible job must be excluded"
        assert "job-4-unknown-size" not in job_ids, "Unknown company size must not be silently treated as small"
        assert len(primary_feed) == 1, f"Expected exactly 1 qualifying job in primary feed, got {len(primary_feed)}"

        # Test 2: Relaxed filter for discovery queue (all company sizes)
        all_sizes_feed = get_all_jobs(status="verified_eligible", only_small_companies=False)
        all_size_ids = [j["id"] for j in all_sizes_feed]
        assert "job-1-small-eligible" in all_size_ids
        assert "job-2-large-enterprise" in all_size_ids
        assert "job-4-unknown-size" in all_size_ids
        assert "job-3-us-only" not in all_size_ids

        # Test 3: Search / Role filter
        laravel_jobs = get_all_jobs(target_role="Laravel", only_small_companies=True)
        assert len(laravel_jobs) == 1
        assert laravel_jobs[0]["id"] == "job-1-small-eligible"

        python_jobs = get_all_jobs(target_role="Python", only_small_companies=True)
        assert len(python_jobs) == 0

        print("\nAll strict filtering assertions passed successfully!")

    finally:
        database.DB_PATH = original_db_path
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)

if __name__ == "__main__":
    test_strict_filtering_rules()

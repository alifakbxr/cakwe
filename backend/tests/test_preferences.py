import pytest
from database import init_db, get_user_preferences, save_user_preferences, reset_user_preferences, get_all_jobs
from schemas import UserPreferences


def test_user_preferences_defaults():
    init_db()
    prefs = get_user_preferences(user_id="test_user_defaults")
    # Verifikasi default Worldwide & SEA
    assert "Worldwide" in prefs.preferred_regions
    assert "Southeast Asia (SEA)" in prefs.preferred_regions
    # Verifikasi default min salary $1000/bln ($12000/thn)
    assert prefs.min_salary_usd == 12000.0
    assert prefs.candidate_country == "Indonesia"
    assert prefs.strict_indonesia_eligible is True
    assert prefs.only_small_companies is False
    assert prefs.min_match_score == 80
    assert prefs.max_years_experience == 3


def test_user_preferences_persistence():
    init_db()
    test_user = "test_user_123"
    custom_prefs = UserPreferences(
        preferred_regions=["Worldwide", "Southeast Asia (SEA)", "APAC"],
        min_salary_usd=15000.0,
        only_small_companies=False,
        excluded_companies=["SpammyCorp", "BadCo"],
        freshness_days=7,
    )
    save_user_preferences(custom_prefs, user_id=test_user)

    loaded = get_user_preferences(user_id=test_user)
    assert loaded.min_salary_usd == 15000.0
    assert loaded.only_small_companies is False
    assert "SpammyCorp" in loaded.excluded_companies
    assert loaded.freshness_days == 7


def test_user_preferences_reset():
    init_db()
    test_user = "test_user_reset"
    custom_prefs = UserPreferences(
        min_salary_usd=50000.0,
        candidate_country="Singapore"
    )
    save_user_preferences(custom_prefs, user_id=test_user)
    
    reset_user_preferences(user_id=test_user)
    reloaded = get_user_preferences(user_id=test_user)
    assert reloaded.min_salary_usd == 12000.0
    assert reloaded.candidate_country == "Indonesia"


def test_user_preferences_filtering_integration():
    init_db()
    # Test bahwa get_all_jobs menerima preferences dan tidak error
    custom_prefs = UserPreferences(
        min_salary_usd=12000.0,
        excluded_companies=["NonExistentCompany"]
    )
    jobs = get_all_jobs(preferences=custom_prefs)
    assert isinstance(jobs, list)
    for j in jobs:
        assert j.get("company_name", "").lower() != "nonexistentcompany"


def test_unbiased_matching_and_experience_filtering():
    import tempfile
    import database
    from schemas import JobRequisition, JobIntelligence, CandidateFitAnalysis, EligibilityStatus, CompanySizeCategory, EmploymentType, SizeConfidence

    def make_test_intel(size_cat, score, exp, emp_type):
        return JobIntelligence(
            eligibility_status=EligibilityStatus.VERIFIED_ELIGIBLE,
            eligibility_quote="Worldwide remote",
            summary_id=["Point 1", "Point 2"],
            translated_responsibilities=["Resp 1"],
            translated_requirements=["Req 1"],
            skills_required=["Go", "Laravel"],
            ghost_risk_score=0.1,
            ghost_risk_reason="Legit",
            company_size_category=size_cat,
            company_size_confidence=SizeConfidence.CONFIRMED,
            candidate_fit=CandidateFitAnalysis(match_score=score, is_recommended=(score >= 80), match_reasons=["Good fit"]),
            min_years_experience=exp,
            employment_type=emp_type
        )

    with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as tf:
        temp_db_path = tf.name

    try:
        database.DB_PATH = temp_db_path
        database.init_db()

        # Job A: Enterprise, Fit 85, Exp 2, Full-Time -> MUST PASS when only_small_companies=False
        job_a = JobRequisition(
            id="job-enterprise-highfit",
            source="test",
            title="Go Backend Engineer",
            company_name="Mega Enterprise Corp",
            location="Remote Worldwide",
            description="Go backend systems.",
            published_at=1792260000,
            intelligence=make_test_intel(CompanySizeCategory.LARGE_ENTERPRISE, 85, 2, EmploymentType.FULL_TIME)
        )
        database.save_job(job_a)

        # Job B: Startup, Fit 75, Exp 1 -> EXCLUDED by min_match_score=80
        job_b = JobRequisition(
            id="job-startup-lowfit",
            source="test",
            title="Java Developer",
            company_name="Small App Startup",
            location="Remote Worldwide",
            description="Java apps.",
            published_at=1792260000,
            intelligence=make_test_intel(CompanySizeCategory.SMALL_STARTUP, 75, 1, EmploymentType.CONTRACT)
        )
        database.save_job(job_b)

        # Job C: Startup, Fit 90, Exp 5 -> EXCLUDED by max_years_experience=3
        job_c = JobRequisition(
            id="job-senior-highfit",
            source="test",
            title="Senior Laravel Architect",
            company_name="Fast Startup",
            location="Remote Worldwide",
            description="Senior architect.",
            published_at=1792260000,
            intelligence=make_test_intel(CompanySizeCategory.SMALL_STARTUP, 90, 5, EmploymentType.FULL_TIME)
        )
        database.save_job(job_c)

        # Job D: Agency, Fit 88, Exp None (unstated) -> MUST PASS (unstated exp included)
        job_d = JobRequisition(
            id="job-agency-unstated-exp",
            source="test",
            title="Fullstack Vue & Laravel Developer",
            company_name="Digital Studio",
            location="Remote Worldwide",
            description="Vue and Laravel dev.",
            published_at=1792260000,
            intelligence=make_test_intel(CompanySizeCategory.AGENCY_STUDIO, 88, None, EmploymentType.EOR)
        )
        database.save_job(job_d)

        results = database.get_all_jobs(
            status="verified_eligible",
            only_small_companies=False,
            min_match_score=80,
            max_years_experience=3
        )
        res_ids = [j["id"] for j in results]

        assert "job-enterprise-highfit" in res_ids, "Enterprise job with fit>=80 and exp<=3 must pass"
        assert "job-agency-unstated-exp" in res_ids, "Job with unstated experience (None) and fit>=80 must pass"
        assert "job-startup-lowfit" not in res_ids, "Job with fit < 80 must be excluded"
        assert "job-senior-highfit" not in res_ids, "Job with exp > 3 must be excluded"
    finally:
        import os
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)


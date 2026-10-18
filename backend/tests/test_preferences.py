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
    assert prefs.only_small_companies is True


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

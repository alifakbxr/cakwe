import pytest
import httpx
from discovery import sniff_ats_from_url, verify_board
from database import init_db, add_discovery_candidate, get_pending_discovery_candidates, update_discovery_candidate_status


def test_sniff_greenhouse_urls():
    # Format embed query
    res = sniff_ats_from_url("https://boards.greenhouse.io/embed/job_board?for=stripe")
    assert res == ("greenhouse", "stripe")

    # Format direct board
    res = sniff_ats_from_url("https://boards.greenhouse.io/gitlab/jobs/12345")
    assert res == ("greenhouse", "gitlab")

    # Format job-boards subdomain
    res = sniff_ats_from_url("https://job-boards.greenhouse.io/cloudflare/jobs/6789")
    assert res == ("greenhouse", "cloudflare")


def test_sniff_lever_urls():
    res = sniff_ats_from_url("https://jobs.lever.co/postman/a1b2c3d4-5678-90ab")
    assert res == ("lever", "postman")

    res = sniff_ats_from_url("https://jobs.lever.co/supabase")
    assert res == ("lever", "supabase")


def test_sniff_ashby_urls():
    res = sniff_ats_from_url("https://jobs.ashbyhq.com/linear/f5c3818e-4a64-4e4b")
    assert res == ("ashby", "linear")

    res = sniff_ats_from_url("https://jobs.ashbyhq.com/perplexity")
    assert res == ("ashby", "perplexity")


def test_sniff_workable_urls():
    res = sniff_ats_from_url("https://apply.workable.com/clevertech/j/12345ABC/")
    assert res == ("workable", "clevertech")


def test_sniff_smartrecruiters_urls():
    res = sniff_ats_from_url("https://jobs.smartrecruiters.com/AcmeCorp/1234-engineer")
    assert res == ("smartrecruiters", "acmecorp")


def test_sniff_ignores_invalid_slugs():
    assert sniff_ats_from_url("https://boards.greenhouse.io/embed") is None
    assert sniff_ats_from_url("https://jobs.lever.co/careers") is None
    assert sniff_ats_from_url("https://google.com/careers") is None
    assert sniff_ats_from_url(None) is None


@pytest.mark.asyncio
async def test_verify_known_valid_board():
    async with httpx.AsyncClient() as client:
        # GitLab adalah board Greenhouse publik yang selalu ada
        status, jobs_count, reason = await verify_board(client, "greenhouse", "gitlab")
        assert status in ("verified_active", "verified_empty")
        assert reason is None


@pytest.mark.asyncio
async def test_verify_invalid_board():
    async with httpx.AsyncClient() as client:
        # Board acak yang pasti 404
        status, jobs_count, reason = await verify_board(client, "greenhouse", "non_existent_company_xyz_99999")
        assert status == "invalid"
        assert "404" in reason


def test_database_candidate_deduplication():
    import uuid
    init_db()
    # Tambah pertama kali dengan token acak unik -> sukses
    token = f"test_dup_{uuid.uuid4().hex[:8]}"
    added1 = add_discovery_candidate("greenhouse", token, candidate_name="Test Company", discovery_source="unit_test")
    assert added1 is True

    # Tambah kedua kali dengan token sama -> ditolak (idempotent / deduplicated)
    added2 = add_discovery_candidate("greenhouse", token, candidate_name="Test Company", discovery_source="unit_test")
    assert added2 is False


@pytest.mark.asyncio
async def test_crawl_company_career_page_blocks_ssrf():
    from discovery import crawl_company_career_page
    async with httpx.AsyncClient() as client:
        # Loopback IPv4
        res_local = await crawl_company_career_page(client, "http://127.0.0.1:8080/careers")
        assert res_local is None

        # Cloud metadata IP (AWS/GCP link-local)
        res_meta = await crawl_company_career_page(client, "http://169.254.169.254/latest/meta-data/")
        assert res_meta is None

        # Invalid protocol/scheme
        res_invalid = await crawl_company_career_page(client, "ftp://example.com")
        assert res_invalid is None

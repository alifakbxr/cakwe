"""Engine untuk mendeteksi, mengekstrak, dan memvalidasi board ATS perusahaan secara otomatis."""

import asyncio
import re
from typing import Dict, List, Optional, Tuple
import urllib.parse
import httpx

from database import (
    add_discovery_candidate,
    get_connection,
    get_pending_discovery_candidates,
    update_discovery_candidate_status,
    upsert_company,
)

# Pola Regex untuk mendeteksi berbagai format URL ATS populer
ATS_URL_PATTERNS = [
    # Greenhouse:
    # https://boards.greenhouse.io/companyname
    # https://boards.greenhouse.io/embed/job_board?for=companyname
    # https://job-boards.greenhouse.io/companyname
    (
        "greenhouse",
        re.compile(
            r"boards(?:-api)?\.greenhouse\.io/(?:embed/job_board\?for=|(?:v1/boards/)?)(?P<slug>[a-zA-Z0-9_\-]+)",
            re.IGNORECASE,
        ),
    ),
    (
        "greenhouse",
        re.compile(
            r"job-boards\.greenhouse\.io/(?P<slug>[a-zA-Z0-9_\-]+)",
            re.IGNORECASE,
        ),
    ),
    # Lever:
    # https://jobs.lever.co/companyname
    # https://api.lever.co/v0/postings/companyname
    (
        "lever",
        re.compile(
            r"(?:jobs|api)\.lever\.co/(?:v0/postings/)?(?P<slug>[a-zA-Z0-9_\-]+)",
            re.IGNORECASE,
        ),
    ),
    # Ashby:
    # https://jobs.ashbyhq.com/companyname
    # https://api.ashbyhq.com/posting-api/job-board/companyname
    (
        "ashby",
        re.compile(
            r"(?:jobs|api)\.ashbyhq\.com/(?:posting-api/job-board/)?(?P<slug>[a-zA-Z0-9_\-]+)",
            re.IGNORECASE,
        ),
    ),
    # Workable:
    # https://apply.workable.com/companyname
    (
        "workable",
        re.compile(
            r"apply\.workable\.com/(?P<slug>[a-zA-Z0-9_\-]+)",
            re.IGNORECASE,
        ),
    ),
    # SmartRecruiters:
    # https://careers.smartrecruiters.com/companyname
    # https://jobs.smartrecruiters.com/companyname
    (
        "smartrecruiters",
        re.compile(
            r"(?:careers|jobs)\.smartrecruiters\.com/(?P<slug>[a-zA-Z0-9_\-]+)",
            re.IGNORECASE,
        ),
    ),
    # Recruitee:
    # https://companyname.recruitee.com/api/offers
    # https://companyname.recruitee.com
    (
        "recruitee",
        re.compile(
            r"(?P<slug>[a-zA-Z0-9_\-]+)\.recruitee\.com",
            re.IGNORECASE,
        ),
    ),
]

IGNORE_SLUGS = {
    "embed", "job", "jobs", "search", "apply", "careers", "vacancies", "feed",
    "iframe", "api", "v1", "v0", "assets", "static", "default", "login", "auth"
}


def sniff_ats_from_url(url: Optional[str]) -> Optional[Tuple[str, str]]:
    """Mengekstrak (ats_provider, ats_board_token) dari URL jika berasal dari platform ATS yang didukung."""
    if not url or not isinstance(url, str):
        return None

    # Normalisasi decode URL jika ada URL redirect atau query params
    clean_url = urllib.parse.unquote(url)

    # Deteksi query parameter khusus (e.g. greenhouse embed `?for=slug`)
    if "greenhouse.io" in clean_url and "for=" in clean_url:
        parsed = urllib.parse.urlparse(clean_url)
        queries = urllib.parse.parse_qs(parsed.query)
        if "for" in queries and queries["for"][0]:
            slug = queries["for"][0].strip().lower()
            if slug not in IGNORE_SLUGS:
                return "greenhouse", slug

    for provider, pattern in ATS_URL_PATTERNS:
        match = pattern.search(clean_url)
        if match:
            slug = match.group("slug").strip().lower()
            if slug and slug not in IGNORE_SLUGS and len(slug) >= 2:
                return provider, slug

    return None


async def verify_board(client: httpx.AsyncClient, ats_provider: str, ats_board_token: str) -> Tuple[str, int, Optional[str]]:
    """
    Memverifikasi keberadaan dan keaktifan board ATS via public endpoint.
    Returns: (verification_status, active_jobs_count, error_or_reason)
    Status: 'verified_active', 'verified_empty', 'invalid', 'error'
    """
    provider = ats_provider.lower()
    token = ats_board_token.strip()

    try:
        if provider == "greenhouse":
            url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs"
            resp = await client.get(url, timeout=12.0)
            if resp.status_code == 200:
                data = resp.json()
                jobs = data.get("jobs", [])
                status = "verified_active" if len(jobs) > 0 else "verified_empty"
                return status, len(jobs), None
            elif resp.status_code == 404:
                return "invalid", 0, "Board tidak ditemukan (HTTP 404)"
            else:
                return "error", 0, f"HTTP {resp.status_code}"

        elif provider == "lever":
            url = f"https://api.lever.co/v0/postings/{token}?mode=json"
            resp = await client.get(url, timeout=12.0)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    status = "verified_active" if len(data) > 0 else "verified_empty"
                    return status, len(data), None
                return "invalid", 0, "Format data bukan list posting"
            elif resp.status_code == 404:
                return "invalid", 0, "Company slug tidak ditemukan (HTTP 404)"
            else:
                return "error", 0, f"HTTP {resp.status_code}"

        elif provider == "ashby":
            url = f"https://api.ashbyhq.com/posting-api/job-board/{token}"
            resp = await client.get(url, timeout=12.0)
            if resp.status_code == 200:
                data = resp.json()
                jobs = data.get("jobs", [])
                status = "verified_active" if len(jobs) > 0 else "verified_empty"
                return status, len(jobs), None
            elif resp.status_code in (404, 400):
                return "invalid", 0, f"Board slug tidak valid (HTTP {resp.status_code})"
            else:
                return "error", 0, f"HTTP {resp.status_code}"

        elif provider == "workable":
            # Workable public API v3 endpoint
            url = f"https://apply.workable.com/api/v3/accounts/{token}/jobs"
            resp = await client.post(url, json={}, timeout=12.0)
            if resp.status_code == 200:
                data = resp.json()
                jobs = data.get("results", [])
                status = "verified_active" if len(jobs) > 0 else "verified_empty"
                return status, len(jobs), None
            elif resp.status_code == 404:
                return "invalid", 0, "Workable account not found (404)"
            else:
                return "error", 0, f"HTTP {resp.status_code}"

        elif provider == "smartrecruiters":
            url = f"https://api.smartrecruiters.com/v1/companies/{token}/postings"
            resp = await client.get(url, timeout=12.0)
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("content", [])
                status = "verified_active" if len(content) > 0 else "verified_empty"
                return status, len(content), None
            elif resp.status_code == 404:
                return "invalid", 0, "SmartRecruiters company not found (404)"
            else:
                return "error", 0, f"HTTP {resp.status_code}"

        elif provider == "recruitee":
            url = f"https://{token}.recruitee.com/api/offers"
            resp = await client.get(url, timeout=12.0)
            if resp.status_code == 200:
                data = resp.json()
                offers = data.get("offers", [])
                status = "verified_active" if len(offers) > 0 else "verified_empty"
                return status, len(offers), None
            elif resp.status_code == 404:
                return "invalid", 0, "Recruitee company not found (404)"
            else:
                return "error", 0, f"HTTP {resp.status_code}"

        else:
            return "invalid", 0, f"Provider {provider} belum didukung"

    except httpx.TimeoutException:
        return "error", 0, "Connection Timeout"
    except Exception as e:
        return "error", 0, str(e)


async def process_discovery_candidates(batch_size: int = 30) -> Dict[str, int]:
    """
    Memproses kandidat discovery yang statusnya pending:
    - Memverifikasi endpoint ATS
    - Mendaftarkan kandidat yang valid ke tabel companies
    - Menandai kandidat yang invalid agar tidak diperiksa berulang kali
    """
    candidates = get_pending_discovery_candidates(limit=batch_size)
    if not candidates:
        return {"processed": 0, "verified": 0, "invalid": 0, "errors": 0}

    stats = {"processed": len(candidates), "verified": 0, "invalid": 0, "errors": 0}
    semaphore = asyncio.Semaphore(5)  # Batasi 5 request paralel agar tidak rate-limited

    async with httpx.AsyncClient(headers={"User-Agent": "JobRadarDiscovery/2.0"}) as client:
        async def verify_single(cand: dict):
            c_id = cand["id"]
            provider = cand["ats_provider"]
            token = cand["ats_board_token"]
            name = cand.get("candidate_name") or token.replace("-", " ").title()

            async with semaphore:
                status, job_count, reason = await verify_board(client, provider, token)

            if status in ("verified_active", "verified_empty"):
                # Simpan ke registry companies
                company_id = f"{provider}_{token}"
                upsert_company({
                    "id": company_id,
                    "name": name,
                    "website_url": cand.get("source_url") or "",
                    "ats_provider": provider,
                    "ats_board_token": token,
                    "industry": "Discovered Tech",
                    "country": "Global",
                    "is_active": True,
                    "discovery_source": cand.get("discovery_source", "discovered"),
                    "verification_status": status,
                    "active_jobs_count": job_count,
                })
                update_discovery_candidate_status(c_id, "verified", None)
                stats["verified"] += 1
                print(f"[DISCOVERY] Valid: {provider.upper()} -> {token} ({name}) | Jobs: {job_count} [{status}]")

            elif status == "invalid":
                update_discovery_candidate_status(c_id, "invalid", reason)
                stats["invalid"] += 1
                print(f"[DISCOVERY] Invalid: {provider.upper()} -> {token} ({reason})")

            else:
                # status == 'error', simpan reason tapi biarkan bisa diretry
                update_discovery_candidate_status(c_id, "failed", reason)
                stats["errors"] += 1

        await asyncio.gather(*(verify_single(c) for c in candidates), return_exceptions=True)

    return stats


def discover_from_job_listings(jobs_data: List[dict]) -> int:
    """
    Memeriksa application_url dari daftar lowongan yang baru ditarik (e.g. dari Himalayas)
    dan otomatis mendaftarkan board ATS yang terdeteksi ke antrean kandidat discovery.
    """
    discovered_count = 0
    for j in jobs_data:
        app_url = j.get("application_url") or j.get("applicationUrl")
        company_name = j.get("company_name") or j.get("companyName")

        detected = sniff_ats_from_url(app_url)
        if detected:
            provider, slug = detected
            added = add_discovery_candidate(
                ats_provider=provider,
                ats_board_token=slug,
                candidate_name=company_name,
                source_url=app_url,
                discovery_source="sniffed_from_aggregator",
            )
            if added:
                discovered_count += 1
                print(f"[DISCOVERY-SNIFFER] Menemukan calon board baru dari lowongan: {provider} -> {slug} ({company_name})")

    return discovered_count


# ==============================================================================
# AUTOMATED PUBLIC WEB CRAWLER & SEARCH ENGINE DISCOVERY
# ==============================================================================

SEARCH_DISCOVERY_QUERIES = [
    # Targeted queries untuk menemukan startup kecil, software houses & boutique agencies:
    'site:boards.greenhouse.io ("Laravel" OR "Vue" OR "PHP" OR "Go developer") "Remote"',
    'site:jobs.lever.co ("Laravel" OR "Go" OR "FastAPI" OR "Full Stack") "Remote"',
    'site:jobs.ashbyhq.com ("Laravel" OR "TypeScript" OR "Python" OR "AI") "Remote"',
    'site:apply.workable.com ("web agency" OR "software house" OR "startup") ("PHP" OR "Laravel" OR "Go") "Remote"',
]


async def crawl_public_search_discovery(client: httpx.AsyncClient, query: str) -> List[Tuple[str, str, str]]:
    """
    Melakukan query pencarian web publik menggunakan DuckDuckGo HTML (tanpa JS/tanpa API key).
    Mengekstrak URL publik yang mengarah ke boards Greenhouse, Lever, Ashby, atau Workable.
    Returns: List of (ats_provider, ats_board_token, result_url)
    """
    found = []
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    
    url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
    try:
        resp = await client.get(url, headers=headers, timeout=15.0)
        if resp.status_code != 200:
            return []

        html = resp.text
        # Cari semua link href yang ada di halaman pencarian
        raw_links = re.findall(r'<a class="result__url" href="([^"]+)"', html)
        if not raw_links:
            # Fallback format link alternatif
            raw_links = re.findall(r'href="(https?://[^"]+)"', html)

        for lk in raw_links:
            # DuckDuckGo membungkus link eksternal dengan redirect /uddg?uddg=...
            if "duckduckgo.com/l/?uddg=" in lk:
                parsed = urllib.parse.urlparse(lk)
                qs = urllib.parse.parse_qs(parsed.query)
                if "uddg" in qs:
                    lk = qs["uddg"][0]

            detected = sniff_ats_from_url(lk)
            if detected:
                provider, slug = detected
                found.append((provider, slug, lk))
    except Exception as e:
        print(f"[CRAWLER:SEARCH-ERROR] {e}")

    return found


async def crawl_company_career_page(client: httpx.AsyncClient, website_url: str) -> Optional[Tuple[str, str, str]]:
    """
    Mengecek halaman website/karir perusahaan dan mendeteksi apakah menyematkan link ke ATS resmi.
    """
    import ipaddress
    import socket

    parsed_url = urllib.parse.urlparse(website_url)
    hostname = parsed_url.hostname
    if not hostname:
        return None

    # SSRF Protection: Blokir localhost, private IPv4, loopback, link-local (169.254.x.x)
    try:
        resolved_ip = socket.gethostbyname(hostname)
        ip_obj = ipaddress.ip_address(resolved_ip)
        if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
            print(f"[SSRF-BLOCKED] Percobaan akses target IP privat/internal: {hostname} -> {resolved_ip}")
            return None
    except Exception:
        return None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) JobRadarCrawler/2.0",
    }

    try:
        resp = await client.get(website_url, headers=headers, timeout=10.0, follow_redirects=True)
        if resp.status_code != 200:
            return None

        # Ekstrak semua link href dari HTML halaman utama/karir
        hrefs = re.findall(r'href=["\']([^"\']+)["\']', resp.text, re.IGNORECASE)
        for h in hrefs:
            detected = sniff_ats_from_url(h)
            if detected:
                provider, slug = detected
                return provider, slug, h
    except Exception:
        pass

    return None


async def run_public_web_discovery() -> Dict[str, int]:
    """
    Pipeline Utama Web Discovery:
    1. Melakukan targeted web crawling pencarian publik untuk menemukan board ATS baru (Laravel, PHP, Go, Vue/TS, Small Startups).
    2. Menyimpan kandidat yang belum pernah dilihat ke antrean database.
    3. Memverifikasi kelayakan endpoint kandidat.
    """
    print("[CRAWLER] Memulai penjelajahan web publik untuk menemukan lowongan & perusahaan kecil baru...")
    new_candidates_count = 0

    async with httpx.AsyncClient() as client:
        for q in SEARCH_DISCOVERY_QUERIES:
            try:
                results = await crawl_public_search_discovery(client, q)
                for provider, slug, lk in results:
                    added = add_discovery_candidate(
                        ats_provider=provider,
                        ats_board_token=slug,
                        candidate_name=slug.replace("-", " ").title(),
                        source_url=lk,
                        discovery_source="public_web_crawler",
                    )
                    if added:
                        new_candidates_count += 1
                        print(f"[CRAWLER] Menemukan board baru via Web Search: {provider} -> {slug}")
                # Jeda sopan antar query
                await asyncio.sleep(1.5)
            except Exception as e:
                print(f"[CRAWLER-QUERY-ERROR] {q}: {e}")

    # Verifikasi langsung kandidat yang baru ditemukan
    verification_stats = await process_discovery_candidates(batch_size=30)
    return {
        "candidates_discovered": new_candidates_count,
        "verified": verification_stats["verified"],
        "invalid": verification_stats["invalid"],
    }


async def ingest_github_slug_datasets() -> Dict[str, int]:
    """
    Mengimpor ribuan slug perusahaan aktif dari repositori GitHub open-source:
    - outscal/OpenJobs (companies_v2.json)
    - FranRom/pupila (config/slugs.json)
    Memvalidasi dan memasukkan ke discovery_candidates tanpa middleware berbayar.
    """
    print("[GITHUB-INGEST] Mengunduh daftar slug perusahaan dari repositori open-source GitHub...")
    stats = {"discovered": 0, "sources": []}

    headers = {"User-Agent": "JobRadar/2.0 (OpenSource Talent Discovery)"}
    async with httpx.AsyncClient(headers=headers, timeout=20.0, follow_redirects=True) as client:
        # 1. Pupila (config/slugs.json)
        try:
            pupila_url = "https://raw.githubusercontent.com/FranRom/pupila/main/config/slugs.json"
            resp = await client.get(pupila_url)
            if resp.status_code == 200:
                data = resp.json()
                pupila_count = 0
                for provider in ["ashby", "greenhouse", "lever", "recruitee", "workable", "smartrecruiters"]:
                    slugs = data.get(provider, [])
                    for s in slugs:
                        clean_slug = str(s).strip().lower()
                        if clean_slug and clean_slug not in IGNORE_SLUGS:
                            added = add_discovery_candidate(
                                ats_provider=provider,
                                ats_board_token=clean_slug,
                                candidate_name=clean_slug.replace("-", " ").title(),
                                source_url=f"https://github.com/FranRom/pupila",
                                discovery_source="github_pupila",
                            )
                            if added:
                                pupila_count += 1
                                stats["discovered"] += 1
                stats["sources"].append(f"Pupila: {pupila_count} new slugs")
                print(f"[GITHUB-INGEST] Berhasil mengekstrak {pupila_count} slug baru dari Pupila.")
        except Exception as e:
            print(f"[GITHUB-INGEST:PUPILA-ERROR] {e}")

        # 2. Outscal OpenJobs (data/companies_v2.json)
        try:
            openjobs_url = "https://raw.githubusercontent.com/outscal/OpenJobs/main/data/companies_v2.json"
            resp = await client.get(openjobs_url)
            if resp.status_code == 200:
                companies_list = resp.json()
                oj_count = 0
                for comp in companies_list:
                    c_name = comp.get("name") or ""
                    ats_links = comp.get("ats_links", [])
                    for lk in ats_links:
                        detected = sniff_ats_from_url(lk)
                        if detected:
                            prov, slug = detected
                            added = add_discovery_candidate(
                                ats_provider=prov,
                                ats_board_token=slug,
                                candidate_name=c_name or slug.replace("-", " ").title(),
                                source_url=lk,
                                discovery_source="github_openjobs",
                            )
                            if added:
                                oj_count += 1
                                stats["discovered"] += 1
                stats["sources"].append(f"OpenJobs: {oj_count} new slugs")
                print(f"[GITHUB-INGEST] Berhasil mengekstrak {oj_count} slug baru dari OpenJobs.")
        except Exception as e:
            print(f"[GITHUB-INGEST:OPENJOBS-ERROR] {e}")

    # Otomatis verifikasi 50 kandidat pertama
    verified_stats = await process_discovery_candidates(batch_size=50)
    stats["verified_now"] = verified_stats["verified"]
    return stats



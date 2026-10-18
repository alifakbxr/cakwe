import asyncio
import json
import re
from pathlib import Path
import httpx

SEARCH_QUERIES = [
    "Laravel",
    "PHP Developer",
    "Go Backend",
    "Golang",
    "Full Stack Vue",
    "Full Stack TypeScript",
    "Python AI Engineer",
    "Junior Backend",
    "Junior Full Stack",
    "Web Developer Agency",
    "AI Engineer",
    "Forward Deployed Engineer",
    "Software Engineer Intern",
    "Backend Intern",
]

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "golden_set"
OUTPUT_FILE = OUTPUT_DIR / "raw_jobs.json"

# Peran target di judul (PHP, Laravel, Go, TypeScript/Vue/Next/React, Python/FastAPI/AI, Software Engineer, Product/Platform, Intern)
TARGET_TITLE_REGEX = re.compile(
    r"\b(laravel|php|golang|go developer|go backend|vue|fullstack|full stack|backend|software engineer|product engineer|platform engineer|infrastructure engineer|core engineer|core developer|systems engineer|ai engineer|ai application engineer|application engineer|python developer|web developer|programmer|intern|internship|trainee|apprentice)\b",
    re.IGNORECASE,
)

# Senioritas tinggi / role non-target yang dibuang dari judul
EXCLUDE_TITLE_REGEX = re.compile(
    r"\b(senior|sr\.|sr |lead|principal|staff|director|head|vp|architect|chief|manager|android|ios|flutter|react native|qa |devops|sre)\b",
    re.IGNORECASE,
)

# Klausul yang mewajibkan status mahasiswa aktif atau ijazah pendidikan tinggi formal (D3/S1/degree only)
MANDATORY_STUDENT_DEGREE_REGEX = re.compile(
    r"\b("
    r"must be (a )?(currently )?enrolled (in|at) (a |an )?(college|university|degree program|bachelor|master)|"
    r"currently pursuing (a |an )?(bachelor|degree|master|phd|diploma)|"
    r"registered as a student|"
    r"active student status required|"
    r"proof of enrollment required|"
    r"for students only|"
    r"must return to school (after|following)|"
    r"minimum (bachelor|master|d3|s1|degree) required(?!.*or equivalent practical experience)"
    r")\b",
    re.IGNORECASE,
)

# Klausul pembatasan hukum dan wilayah yang mutlak mengecualikan pelamar di luar yurisdiksi mereka
US_ONLY_CLAUSE_REGEX = re.compile(
    r"\b("
    r"must reside in (the )?(united states|us|u\.s\.|uk|united kingdom|canada|europe|eu|north america)|"
    r"us citizens? only|uk citizens? only|"
    r"authorized to work in the (us|united states|uk|united kingdom|eu|canada) without sponsorship|"
    r"work authorization in (the )?(us|united states|uk|canada|eu) required|"
    r"w-?2 only|no c2c|"
    r"active (secret|security) clearance|"
    r"located in (the )?(us|united states|uk|canada|europe|eu)|"
    r"remote (in|within) (the )?(us|united states|uk|canada|europe|eu|north america) only|"
    r"only open to residents of (the )?(us|united states|uk|canada|eu)"
    r")\b",
    re.IGNORECASE,
)

DISALLOWED_LOCATIONS = [
    "united states",
    "usa",
    "u.s.",
    "us only",
    "canada",
    "united kingdom",
    "uk only",
    "great britain",
    "england",
    "germany",
    "france",
    "europe only",
    "eu only",
    "north america",
    "latam only",
]


def check_eligibility(title: str, location: str, description: str, country_restrictions: list):
    title_lower = title.lower()
    loc_lower = (location or "").lower()
    desc_lower = (description or "").lower()

    # 1. Judul atau Lokasi berbau Onsite / Hybrid mutlak ditolak
    if any(h in title_lower or h in loc_lower for h in ["hybrid", "on-site", "onsite"]):
        return False, "Bukan fully remote (Hybrid/Onsite)"

    # 2. Judul harus sesuai target
    if not TARGET_TITLE_REGEX.search(title_lower):
        return False, "Bukan peran target"

    # 3. Judul tidak boleh level Senior/Lead/Staff
    if EXCLUDE_TITLE_REGEX.search(title_lower):
        return False, "Senior/Lead/Role di luar cakupan"

    # 4. Lokasi eksplisit negara barat
    if any(b in loc_lower for b in DISALLOWED_LOCATIONS) and not any(
        w in loc_lower for w in ["worldwide", "anywhere", "global", "apac"]
    ):
        return False, "Lokasi spesifik negara barat"

    # 5. Restriksi negara dari metadata
    if country_restrictions:
        cr_upper = [c.upper() for c in country_restrictions]
        allowed_tokens = {"ID", "INDONESIA", "WORLDWIDE", "APAC", "ASIA", "GLOBAL", "ANYWHERE"}
        if not any(token in cr_upper for token in allowed_tokens) and len(cr_upper) > 0:
            return False, "Country restriction tidak mencakup ID"

    # 6. Klausul hukum pembatasan domisili di teks
    if US_ONLY_CLAUSE_REGEX.search(description or ""):
        return False, "Klausul izin kerja AS/Barat di deskripsi"

    # 8. Pengecualian magang/posisi yang mewajibkan status mahasiswa aktif atau ijazah kaku tanpa jalur ekuivalen
    if MANDATORY_STUDENT_DEGREE_REGEX.search(description or ""):
        return False, "Mewajibkan status mahasiswa aktif atau gelar formal kaku (bukan degree-agnostic)"

    return True, "OK"


async def fetch_jobs_by_query(client: httpx.AsyncClient, query: str, offset: int = 0):
    url = "https://himalayas.app/jobs/api"
    params = {"q": query, "offset": offset}
    try:
        res = await client.get(url, params=params, timeout=20.0)
        if res.status_code == 200:
            return res.json().get("jobs", [])
    except Exception as e:
        print(f"[{query}] Error: {e}")
    return []


async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_raw_jobs = []

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }

    async with httpx.AsyncClient(headers=headers) as client:
        tasks = []
        # Ambil 3 halaman per query (offset 0, 20, 40)
        for q in SEARCH_QUERIES:
            for offset in [0, 20, 40]:
                tasks.append(fetch_jobs_by_query(client, q, offset=offset))

        results = await asyncio.gather(*tasks)
        for job_list in results:
            all_raw_jobs.extend(job_list)

    print(f"\nTotal lowongan mentah ditarik: {len(all_raw_jobs)}")

    seen_ids = set()
    filtered_jobs = []

    for job in all_raw_jobs:
        job_id = job.get("guid") or job.get("slug") or job.get("title")
        if job_id in seen_ids:
            continue
        seen_ids.add(job_id)

        title = job.get("title", "")
        location = job.get("location", "")
        country_restrictions = job.get("countryRestrictions") or []
        description = job.get("description", "")

        is_ok, reason = check_eligibility(title, location, description, country_restrictions)
        if not is_ok:
            continue

        filtered_jobs.append({
            "source": "himalayas",
            "id": str(job_id),
            "title": title,
            "company_name": job.get("companyName"),
            "location": location,
            "country_restrictions": country_restrictions,
            "seniority": job.get("seniority") or [],
            "categories": job.get("categories", []),
            "min_salary": job.get("minSalary"),
            "max_salary": job.get("maxSalary"),
            "currency": job.get("currency"),
            "application_url": job.get("applicationUrl"),
            "published_at": job.get("pubDate"),
            "description": description,
        })
        print(f"-> [LOLOS] {title} ({job.get('companyName')}) | Lokasi: {location or 'Worldwide'}")

    print(f"\nTotal lowongan relevan lolos: {len(filtered_jobs)}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(filtered_jobs, f, indent=2, ensure_ascii=False)

    print(f"Berhasil menyimpan {len(filtered_jobs)} lowongan ke {OUTPUT_FILE}")


if __name__ == "__main__":
    asyncio.run(main())

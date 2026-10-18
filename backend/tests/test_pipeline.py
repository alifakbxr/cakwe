import asyncio
import json
from pathlib import Path
from schemas import JobRequisition
from ai_processor import process_job

DATA_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "golden_set" / "raw_jobs.json"


async def main():
    if not DATA_FILE.exists():
        print(f"File {DATA_FILE} tidak ditemukan!")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        raw_list = json.load(f)

    if not raw_list:
        print("Data sampel kosong!")
        return

    # Ambil 1 sampel pertama untuk pengujian
    sample_raw = raw_list[0]
    print(f"Memproses sampel: {sample_raw.get('title')} ({sample_raw.get('company_name')})...\n")

    job = JobRequisition(**sample_raw)

    # Proses dengan AI (Gemini jika ada GEMINI_API_KEY di .env, jika tidak pakai Ollama)
    enriched_job = await process_job(job)

    if not enriched_job.intelligence:
        print("Gagal mengekstrak intelligence!")
        return

    intel = enriched_job.intelligence
    print("=" * 60)
    print("HASIL ANALISIS AI INTELLIGENCE ENGINE")
    print("=" * 60)
    print(f"Judul         : {enriched_job.title}")
    print(f"Perusahaan    : {enriched_job.company_name}")
    print(f"Status        : {intel.eligibility_status.value.upper()}")
    print(f"Kutipan Bukti : \"{intel.eligibility_quote}\"")
    print(f"Ghost Risk    : {intel.ghost_risk_score} (Alasan: {intel.ghost_risk_reason})")
    print("\nSkills Wajib  :")
    for s in intel.skills_required:
        print(f" - {s}")

    print("\nRingkasan (Bahasa Indonesia):")
    for sm in intel.summary_id:
        print(f" * {sm}")

    print("\nTanggung Jawab Utama (Terjemahan):")
    for r in intel.translated_responsibilities[:3]:
        print(f" - {r}")

    print("\nKualifikasi (Terjemahan):")
    for req in intel.translated_requirements[:3]:
        print(f" - {req}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

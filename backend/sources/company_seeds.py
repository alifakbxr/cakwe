"""Daftar awal seed fokus pada Small Software Companies, Web Agencies, Product Studios & Lean Startups (10-100 Karyawan).
Bukan korporasi raksasa Silicon Valley. Fokus pada perusahaan yang ramah talenta 1-3 tahun exp.
"""

SEED_COMPANIES = [
    # --- Boutique Web Development Agencies & Software Houses (10-100 Orang) ---
    {"id": "clevertech", "name": "Clevertech", "ats_provider": "lever", "ats_board_token": "clevertech", "industry": "Software Engineering Studio (Lean Remote)", "size_category": "agency_studio", "is_tier1": False},
    {"id": "toggl", "name": "Toggl", "ats_provider": "lever", "ats_board_token": "toggl", "industry": "Productivity SaaS (Small Remote Team)", "size_category": "small_startup", "is_tier1": False},
    {"id": "contra", "name": "Contra", "ats_provider": "lever", "ats_board_token": "contra", "industry": "Freelance Tech Network", "size_category": "small_startup", "is_tier1": False},
    {"id": "help-scout", "name": "Help Scout", "ats_provider": "lever", "ats_board_token": "helpscout", "industry": "Customer Support SaaS (Remote-First ~80 people)", "size_category": "medium_startup", "is_tier1": False},
    {"id": "buffer", "name": "Buffer", "ats_provider": "greenhouse", "ats_board_token": "buffer", "industry": "Social Media SaaS (~85 people, Remote)", "size_category": "medium_startup", "is_tier1": False},

    # --- Lean Tech Startups & Modern DevTools (10-80 orang) ---
    {"id": "resend", "name": "Resend", "ats_provider": "ashby", "ats_board_token": "resend", "industry": "Developer Email API (~15 people)", "size_category": "small_startup", "is_tier1": False},
    {"id": "linear", "name": "Linear", "ats_provider": "ashby", "ats_board_token": "linear", "industry": "Issue Tracking (~50 people, High Craft)", "size_category": "small_startup", "is_tier1": False},
    {"id": "posthog", "name": "PostHog", "ats_provider": "ashby", "ats_board_token": "posthog", "industry": "Product Analytics Open Source (~60 people)", "size_category": "medium_startup", "is_tier1": False},
    {"id": "incident-io", "name": "incident.io", "ats_provider": "ashby", "ats_board_token": "incident-io", "industry": "DevOps Incident Tools (~45 people)", "size_category": "small_startup", "is_tier1": False},
    {"id": "livekit", "name": "LiveKit", "ats_provider": "ashby", "ats_board_token": "livekit", "industry": "Realtime Audio/Video Infra (~30 people)", "size_category": "small_startup", "is_tier1": False},
    {"id": "modal", "name": "Modal Labs", "ats_provider": "ashby", "ats_board_token": "modal", "industry": "Serverless Python/AI Cloud (~25 people)", "size_category": "small_startup", "is_tier1": False},
    {"id": "together-ai", "name": "Together AI", "ats_provider": "ashby", "ats_board_token": "together-ai", "industry": "AI Infrastructure (~70 people)", "size_category": "medium_startup", "is_tier1": False},
    {"id": "anysphere", "name": "Cursor (Anysphere)", "ats_provider": "ashby", "ats_board_token": "anysphere", "industry": "AI Code Editor (~30 people)", "size_category": "small_startup", "is_tier1": False},
    {"id": "synthesia", "name": "Synthesia", "ats_provider": "ashby", "ats_board_token": "synthesia", "industry": "AI Video Generation (~90 people)", "size_category": "medium_startup", "is_tier1": False},
    {"id": "weaviate", "name": "Weaviate", "ats_provider": "ashby", "ats_board_token": "weaviate", "industry": "Vector Search Engine (~50 people)", "size_category": "small_startup", "is_tier1": False},
    {"id": "retool", "name": "Retool", "ats_provider": "ashby", "ats_board_token": "retool", "industry": "Low-Code Developer Tools", "size_category": "medium_startup", "is_tier1": False},
    {"id": "supabase", "name": "Supabase", "ats_provider": "lever", "ats_board_token": "supabase", "industry": "Open Source Backend & Postgres", "size_category": "medium_startup", "is_tier1": False},
    {"id": "hotjar", "name": "Hotjar", "ats_provider": "lever", "ats_board_token": "hotjar", "industry": "Product Analytics (Remote Friendly)", "size_category": "medium_startup", "is_tier1": False},

    # --- Tier-1 / Large Enterprises (Ground Truth Exclusions) ---
    {"id": "canonical", "name": "Canonical (Ubuntu)", "ats_provider": "greenhouse", "ats_board_token": "canonical", "industry": "Open Source OS & Enterprise Cloud", "size_category": "large_enterprise", "is_tier1": True},
    {"id": "gitlab", "name": "GitLab", "ats_provider": "greenhouse", "ats_board_token": "gitlab", "industry": "DevSecOps Platform", "size_category": "large_enterprise", "is_tier1": True},
    {"id": "automattic", "name": "Automattic (WordPress)", "ats_provider": "greenhouse", "ats_board_token": "automattic", "industry": "Web Publishing & Open Source", "size_category": "large_enterprise", "is_tier1": True},
    {"id": "elastic", "name": "Elastic", "ats_provider": "greenhouse", "ats_board_token": "elastic", "industry": "Search & Observability Enterprise", "size_category": "large_enterprise", "is_tier1": True},
]

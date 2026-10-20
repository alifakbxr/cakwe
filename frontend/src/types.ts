export interface ContactInfo {
  full_name: string
  email: string
  phone: string
  location: string
  linkedin_url: string
  github_url: string
}

export interface WorkExperienceItem {
  company: string
  position: string
  location: string
  start_date: string
  end_date: string
  bullets: string[]
}

export interface EducationItem {
  institution: string
  degree: string
  field_of_study: string
  graduation_year: string
  gpa_or_honors?: string
}

export interface CertificationItem {
  name: string
  issuer: string
  year: string
}

export interface FullResumeData {
  contact: ContactInfo
  target_role_title: string
  professional_summary: string
  technical_skills: string[]
  work_experiences: WorkExperienceItem[]
  educations: EducationItem[]
  certifications: CertificationItem[]
}

export interface ResumeAnalysisReport {
  match_score: number
  matched_keywords: string[]
  missing_skills: string[]
  key_improvements: string[]
  ats_formatting_advice: string
}

export interface OptimizedResumeResult {
  resume: FullResumeData
  analysis: ResumeAnalysisReport
  cover_letter: string
}

export interface Job {
  id: string
  source: string
  title: string
  company_name: string
  location: string
  categories: string[]
  min_salary: number | null
  max_salary: number | null
  currency: string | null
  application_url: string | null
  published_at: number | null
  eligibility_status: string
  eligibility_quote: string
  summary_id: string[]
  translated_responsibilities: string[]
  translated_requirements: string[]
  skills_required: string[]
  ghost_risk_score: number
  ghost_risk_reason: string
  company_size_category?: 'small_startup' | 'medium_startup' | 'agency_studio' | 'large_enterprise' | 'unknown'
  company_size_raw?: string | null
  company_size_confidence?: 'confirmed' | 'estimated' | 'unknown'
  primary_industry?: string | null
  is_developer_platform?: boolean | number
  is_tier1?: boolean | number
  match_score?: number | null
  is_recommended?: boolean | number | null
  match_reasons?: string | string[] | null
  missing_skills?: string | string[] | null
  min_years_experience?: number | null
  experience_quote?: string | null
  employment_type?: 'full_time' | 'contract' | 'eor' | 'independent_contractor' | 'part_time' | 'internship' | 'unknown' | string | null
  lifecycle_status?: 'active' | 'closed' | 'expired' | 'removed'
  application_status?: string | null
  applied_date?: string | null
  application_notes?: string | null
}

export interface SyncStatus {
  total_active_companies: number
  ats_breakdown: {
    greenhouse: number
    lever: number
    ashby: number
  }
  latest_logs: Array<{
    source_name: string
    status: string
    jobs_discovered: number
    jobs_new: number
    created_at: string
  }>
}

export interface Stats {
  total_jobs: number
  verified_eligible_jobs: number
  verified_small_company_jobs?: number
  low_ghost_risk_jobs: number
  average_ghost_risk_score: number
}

export type ResumeTemplate = 'HARVARD' | 'MODERN' | 'TECHNICAL'

export interface ATSValidationReport {
  score: number
  is_valid: boolean
  issues: string[]
  strengths: string[]
  word_count: number
  section_checks: {
    contact_complete: boolean
    has_summary: boolean
    has_skills: boolean
    has_experience: boolean
    has_education: boolean
    quantified_bullets_ratio: number
  }
}

export type ViewTab = 'DASHBOARD' | 'RADAR' | 'KANBAN' | 'RESUME_STUDIO' | 'SETTINGS'

export interface UserPreferences {
  // 1. Job Search Preferences
  target_roles: string[]
  target_skills: string[]
  remote_work_types: string[]
  preferred_regions: string[]
  experience_levels: string[]
  min_salary_usd: number | null
  max_salary_usd: number | null
  employment_types: string[]
  min_match_score?: number | null
  max_years_experience?: number | null

  // 2. Geographic Eligibility
  candidate_country: string
  candidate_timezone: string
  strict_indonesia_eligible: boolean
  prioritize_worldwide: boolean
  excluded_regions: string[]

  // 3. Company Preferences
  only_small_companies: boolean
  preferred_company_sizes: string[]
  exclude_tier1_enterprises: boolean
  excluded_companies: string[]

  // 4. Job Freshness & Discovery
  freshness_days: number
  max_ghost_risk: number
  show_unverified_queue: boolean
  auto_refresh_interval_hours: number

  // 5. Notifications & Display
  default_role_filter: string
  show_closed_jobs: boolean
  compact_view: boolean
}

export interface FilterDiagnostics {
  total_in_db: number
  verified_eligible: number
  likely_eligible: number
  ineligible: number
  hidden_by_freshness: number
  hidden_by_large_enterprise: number
  hidden_by_developer_platform?: number
  freshness_days_active: number
  only_small_active: boolean
}


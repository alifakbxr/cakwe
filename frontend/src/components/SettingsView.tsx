import React, { useState, useEffect } from 'react'
import { 
  Globe, 
  Building, 
  Clock, 
  Briefcase, 
  Save, 
  RotateCcw, 
  RefreshCw, 
  Check, 
  AlertCircle, 
  Plus, 
  X,
  Sliders,
  ChevronDown,
  ChevronUp
} from 'lucide-react'
import type { UserPreferences } from '../types'
import { Card } from './ui/card'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Badge } from './ui/badge'

interface SettingsViewProps {
  onPreferencesUpdated?: () => void
}

const DEFAULT_PREFERENCES: UserPreferences = {
  target_roles: ["AI Engineer", "Backend Developer", "Laravel Developer", "Fullstack Developer", "Software Engineer"],
  target_skills: ["PHP", "Laravel", "Vue", "TypeScript", "React", "Go", "Python", "Docker"],
  remote_work_types: ["fully_remote", "worldwide", "wfa"],
  preferred_regions: ["Worldwide", "Southeast Asia (SEA)", "APAC", "Remote"],
  experience_levels: ["junior", "mid_level"],
  min_salary_usd: 12000, // equivalent to ~$1000/month
  max_salary_usd: null,
  employment_types: ["full_time", "contract"],
  candidate_country: "Indonesia",
  candidate_timezone: "Asia/Jakarta",
  strict_indonesia_eligible: true,
  prioritize_worldwide: true,
  excluded_regions: ["US Only", "Europe Only", "UK Only", "Canada Only"],
  only_small_companies: true,
  preferred_company_sizes: ["small_startup", "medium_startup", "agency_studio"],
  exclude_tier1_enterprises: true,
  excluded_companies: [],
  freshness_days: 28,
  max_ghost_risk: 0.3,
  show_unverified_queue: false,
  auto_refresh_interval_hours: 1,
  default_role_filter: "ALL",
  show_closed_jobs: false,
  compact_view: false,
}

export const SettingsView: React.FC<SettingsViewProps> = ({ onPreferencesUpdated }) => {
  const [preferences, setPreferences] = useState<UserPreferences>(DEFAULT_PREFERENCES)
  const [initialPreferences, setInitialPreferences] = useState<UserPreferences>(DEFAULT_PREFERENCES)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [syncing, setSyncing] = useState(false)
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error', message: string } | null>(null)
  
  // Custom tag inputs
  const [newRoleInput, setNewRoleInput] = useState('')
  const [newSkillInput, setNewSkillInput] = useState('')
  const [newExcludedCompInput, setNewExcludedCompInput] = useState('')

  // Section collapsible state
  const [collapsed, setCollapsed] = useState({
    job_search: false,
    geographic: false,
    company: false,
    freshness: false,
    display: false,
  })

  const hasUnsavedChanges = JSON.stringify(preferences) !== JSON.stringify(initialPreferences)

  const fetchPreferences = async () => {
    try {
      setLoading(true)
      const res = await fetch('/api/preferences')
      if (res.ok) {
        const data: UserPreferences = await res.json()
        setPreferences(data)
        setInitialPreferences(data)
      }
    } catch (err) {
      console.error('Failed to load preferences:', err)
      setFeedback({ type: 'error', message: 'Failed to load preferences from server. Using default settings.' })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchPreferences()
  }, [])

  const handleSave = async () => {
    try {
      setSaving(true)
      setFeedback(null)
      const res = await fetch('/api/preferences', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(preferences)
      })
      if (!res.ok) throw new Error('Failed to save preferences')
      const data = await res.json()
      setPreferences(data.preferences)
      setInitialPreferences(data.preferences)
      setFeedback({ type: 'success', message: 'Preferences saved successfully to the system.' })
      if (onPreferencesUpdated) onPreferencesUpdated()
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message || 'An error occurred while saving preferences.' })
    } finally {
      setSaving(false)
    }
  }

  const handleReset = async () => {
    if (!window.confirm('Reset all preferences to factory defaults (Worldwide & SEA, Min Salary $1,000/month)?')) {
      return
    }
    try {
      setSaving(true)
      setFeedback(null)
      const res = await fetch('/api/preferences/reset', { method: 'POST' })
      if (!res.ok) throw new Error('Failed to reset preferences')
      const data = await res.json()
      setPreferences(data.preferences)
      setInitialPreferences(data.preferences)
      setFeedback({ type: 'success', message: 'Preferences have been restored to factory defaults.' })
      if (onPreferencesUpdated) onPreferencesUpdated()
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message || 'Failed to reset preferences.' })
    } finally {
      setSaving(false)
    }
  }

  const handleRerunDiscovery = async () => {
    try {
      setSyncing(true)
      setFeedback(null)
      const res = await fetch('/api/preferences/rerun-discovery', { method: 'POST' })
      if (!res.ok) throw new Error('Failed to trigger radar sync')
      setFeedback({ type: 'success', message: 'Job radar re-alignment with your preferences is running in the background.' })
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message || 'Failed to trigger sync.' })
    } finally {
      setSyncing(false)
    }
  }

  // Tag helper
  const addTag = (field: 'target_roles' | 'target_skills' | 'excluded_companies', value: string, clearFn: (s: string) => void) => {
    const trimmed = value.trim()
    if (!trimmed) return
    if (!preferences[field].includes(trimmed)) {
      setPreferences({
        ...preferences,
        [field]: [...preferences[field], trimmed]
      })
    }
    clearFn('')
  }

  const removeTag = (field: 'target_roles' | 'target_skills' | 'excluded_companies', value: string) => {
    setPreferences({
      ...preferences,
      [field]: preferences[field].filter(item => item !== value)
    })
  }

  const toggleArrayItem = (field: 'remote_work_types' | 'preferred_regions' | 'experience_levels' | 'employment_types' | 'preferred_company_sizes', item: string) => {
    const list = [...preferences[field]]
    const idx = list.indexOf(item)
    if (idx >= 0) {
      list.splice(idx, 1)
    } else {
      list.push(item)
    }
    setPreferences({ ...preferences, [field]: list })
  }

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto p-12 text-center text-slate-400">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-3 text-indigo-400" />
        <p className="text-sm">Loading user preferences...</p>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      {/* Top Header Card */}
      <Card className="bg-[#0f172a] border-slate-800 p-5 sm:p-6 shadow-md flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-indigo-600 to-indigo-400 flex items-center justify-center text-white shadow-lg shadow-indigo-500/20">
            <Sliders className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-bold text-white tracking-tight">Preferences & Discovery Settings</h1>
              {hasUnsavedChanges && (
                <Badge variant="amber" className="animate-pulse">
                  Unsaved Changes
                </Badge>
              )}
            </div>
            <p className="text-xs text-slate-400 mt-0.5">
              Configure radar search criteria, location, salary thresholds, and team characteristics in real-time.
            </p>
          </div>
        </div>

        {/* Global Action Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleReset}
            disabled={saving}
            className="gap-1.5"
            title="Restore all values to default"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Default</span>
          </Button>

          <Button
            variant="secondary"
            size="sm"
            onClick={handleRerunDiscovery}
            disabled={syncing}
            className="gap-1.5"
            title="Run sync with current criteria"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin text-indigo-400' : ''}`} />
            <span>Rerun Discovery</span>
          </Button>

          <Button
            variant="default"
            size="sm"
            onClick={handleSave}
            disabled={saving || !hasUnsavedChanges}
            className="gap-1.5 shadow-md"
          >
            {saving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
            <span>Save Changes</span>
          </Button>
        </div>
      </Card>

      {/* Feedback Banner */}
      {feedback && (
        <div className={`p-4 rounded-xl text-xs flex items-center justify-between gap-3 ${
          feedback.type === 'success' 
            ? 'bg-emerald-950/70 border border-emerald-800/80 text-emerald-300' 
            : 'bg-rose-950/70 border border-rose-800/80 text-rose-300'
        }`}>
          <div className="flex items-center gap-2">
            {feedback.type === 'success' ? <Check className="w-4 h-4 shrink-0" /> : <AlertCircle className="w-4 h-4 shrink-0" />}
            <span>{feedback.message}</span>
          </div>
          <button onClick={() => setFeedback(null)} className="text-slate-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* SECTION 1: Job Search Preferences */}
      <div className="bg-[#0f172a] border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
        <button
          onClick={() => setCollapsed({ ...collapsed, job_search: !collapsed.job_search })}
          className="w-full px-5 py-4 flex items-center justify-between text-left hover:bg-slate-900/40 transition border-b border-slate-800/60"
        >
          <div className="flex items-center gap-2.5">
            <Briefcase className="w-4 h-4 text-indigo-400" />
            <div>
              <h2 className="text-sm font-bold text-white">1. Job Search & Stack Preferences</h2>
              <p className="text-[11px] text-slate-400">Target roles, tech stack, experience level, and compensation expectations.</p>
            </div>
          </div>
          {collapsed.job_search ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronUp className="w-4 h-4 text-slate-400" />}
        </button>

        {!collapsed.job_search && (
          <div className="p-5 sm:p-6 space-y-5">
            {/* Target Roles */}
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                Target Roles / Positions:
              </label>
              <div className="flex flex-wrap gap-1.5 mb-2">
                {preferences.target_roles.map((role) => (
                  <span key={role} className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-700/80 text-slate-200 text-xs">
                    {role}
                    <button onClick={() => removeTag('target_roles', role)} className="text-slate-400 hover:text-rose-400">
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
              <div className="flex gap-2">
                <Input
                  type="text"
                  placeholder="Add target role (e.g. Golang Engineer)..."
                  value={newRoleInput}
                  onChange={(e) => setNewRoleInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') addTag('target_roles', newRoleInput, setNewRoleInput) }}
                  className="flex-1"
                />
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => addTag('target_roles', newRoleInput, setNewRoleInput)}
                  className="gap-1 h-9"
                >
                  <Plus className="w-3.5 h-3.5" /> Add
                </Button>
              </div>
            </div>

            {/* Target Skills */}
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                Core Tech Stack & Skills:
              </label>
              <div className="flex flex-wrap gap-1.5 mb-2">
                {preferences.target_skills.map((skill) => (
                  <span key={skill} className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-indigo-950/40 border border-indigo-800/50 text-indigo-200 text-xs">
                    {skill}
                    <button onClick={() => removeTag('target_skills', skill)} className="text-indigo-400 hover:text-rose-400">
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Add new skill (e.g. Next.js)..."
                  value={newSkillInput}
                  onChange={(e) => setNewSkillInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') addTag('target_skills', newSkillInput, setNewSkillInput) }}
                  className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                />
                <button
                  onClick={() => addTag('target_skills', newSkillInput, setNewSkillInput)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium flex items-center gap-1"
                >
                  <Plus className="w-3.5 h-3.5" /> Add
                </button>
              </div>
            </div>

            {/* Experience Levels & Employment Types */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-2">
                  Experience Level:
                </label>
                <div className="flex flex-wrap gap-2">
                  {[
                    { id: 'junior', label: 'Junior (1-2 yrs)' },
                    { id: 'mid_level', label: 'Mid-level (2-3 yrs)' },
                    { id: 'senior', label: 'Senior (4+ yrs)' },
                  ].map((lvl) => {
                    const active = preferences.experience_levels.includes(lvl.id)
                    return (
                      <button
                        key={lvl.id}
                        type="button"
                        onClick={() => toggleArrayItem('experience_levels', lvl.id)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
                          active 
                            ? 'bg-emerald-600 text-white border-emerald-500 shadow-sm' 
                            : 'bg-slate-950 text-slate-400 border-slate-800 hover:border-slate-700'
                        }`}
                      >
                        {lvl.label}
                      </button>
                    )
                  })}
                </div>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-300 block mb-2">
                  Employment Type:
                </label>
                <div className="flex flex-wrap gap-2">
                  {[
                    { id: 'full_time', label: 'Full-time' },
                    { id: 'contract', label: 'International Contract / EOR' },
                    { id: 'internship', label: 'Internship' },
                    { id: 'part_time', label: 'Part-time' },
                    { id: 'freelance', label: 'Freelance' }
                  ].map((emp) => {
                    const active = preferences.employment_types.includes(emp.id)
                    return (
                      <button
                        key={emp.id}
                        type="button"
                        onClick={() => toggleArrayItem('employment_types', emp.id)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
                          active 
                            ? 'bg-indigo-600 text-white border-indigo-500 shadow-sm' 
                            : 'bg-slate-950 text-slate-400 border-slate-800 hover:border-slate-700'
                        }`}
                      >
                        {emp.label}
                      </button>
                    )
                  })}
                </div>
              </div>
            </div>

            {/* Salary Expectations (USD) */}
            <div className="pt-2 border-t border-slate-800/80">
              <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                Minimum Salary Expectation:
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <span className="text-[11px] text-slate-400 block mb-1">Monthly Minimum (Est. USD)</span>
                  <div className="flex items-center gap-2">
                    <span className="text-slate-500 font-bold">$</span>
                    <input
                      type="number"
                      step="100"
                      value={preferences.min_salary_usd ? Math.round(preferences.min_salary_usd / 12) : 1000}
                      onChange={(e) => {
                        const val = parseFloat(e.target.value)
                        setPreferences({
                          ...preferences,
                          min_salary_usd: isNaN(val) ? null : val * 12
                        })
                      }}
                      className="w-full bg-transparent text-sm font-bold text-white focus:outline-none"
                    />
                    <span className="text-xs text-slate-400">/ month</span>
                  </div>
                  <p className="text-[10px] text-slate-500 mt-1">Equivalent to ~$1,000/month</p>
                </div>

                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <span className="text-[11px] text-slate-400 block mb-1">Annual Equivalent (USD)</span>
                  <div className="flex items-center gap-2">
                    <span className="text-slate-500 font-bold">$</span>
                    <input
                      type="number"
                      step="1000"
                      value={preferences.min_salary_usd || 12000}
                      onChange={(e) => {
                        const val = parseFloat(e.target.value)
                        setPreferences({
                          ...preferences,
                          min_salary_usd: isNaN(val) ? null : val
                        })
                      }}
                      className="w-full bg-transparent text-sm font-bold text-white focus:outline-none"
                    />
                    <span className="text-xs text-slate-400">/ year</span>
                  </div>
                  <p className="text-[10px] text-slate-500 mt-1">Only filters jobs that explicitly list a salary range</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* SECTION 2: Geographic Eligibility */}
      <div className="bg-[#0f172a] border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
        <button
          onClick={() => setCollapsed({ ...collapsed, geographic: !collapsed.geographic })}
          className="w-full px-5 py-4 flex items-center justify-between text-left hover:bg-slate-900/40 transition border-b border-slate-800/60"
        >
          <div className="flex items-center gap-2.5">
            <Globe className="w-4 h-4 text-emerald-400" />
            <div>
              <h2 className="text-sm font-bold text-white">2. Geographic & Remote Eligibility</h2>
              <p className="text-[11px] text-slate-400">Prioritize Worldwide & Southeast Asia (SEA), verify applicant location eligibility.</p>
            </div>
          </div>
          {collapsed.geographic ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronUp className="w-4 h-4 text-slate-400" />}
        </button>

        {!collapsed.geographic && (
          <div className="p-5 sm:p-6 space-y-5">
            {/* Preferred Regions Multi-Select */}
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-2">
                Preferred Regions:
              </label>
              <div className="flex flex-wrap gap-2">
                {[
                  'Worldwide',
                  'Southeast Asia (SEA)',
                  'APAC',
                  'Remote (Global)',
                  'LATAM',
                  'EMEA'
                ].map((region) => {
                  const active = preferences.preferred_regions.includes(region)
                  return (
                    <button
                      key={region}
                      type="button"
                      onClick={() => toggleArrayItem('preferred_regions', region)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-semibold border transition ${
                        active 
                          ? 'bg-emerald-600 text-white border-emerald-500 shadow-sm' 
                          : 'bg-slate-950 text-slate-400 border-slate-800 hover:border-slate-700'
                      }`}
                    >
                      {region}
                    </button>
                  )
                })}
              </div>
              <p className="text-[11px] text-slate-500 mt-2">
                Your default recommendations prioritize <strong>Worldwide</strong> and <strong>Southeast Asia (SEA)</strong>.
              </p>
            </div>

            {/* Candidate Country & Timezone */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Applicant's Country of Residence</label>
                <input
                  type="text"
                  value={preferences.candidate_country}
                  onChange={(e) => setPreferences({ ...preferences, candidate_country: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white"
                />
              </div>
              <div>
                <label className="text-xs font-semibold text-slate-400 block mb-1">Candidate Timezone</label>
                <input
                  type="text"
                  value={preferences.candidate_timezone}
                  onChange={(e) => setPreferences({ ...preferences, candidate_timezone: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white"
                />
              </div>
            </div>

            {/* Strict Gates Toggles */}
            <div className="space-y-3 pt-2 border-t border-slate-800/80">
              <label className="flex items-start gap-3 p-3 rounded-xl bg-slate-950 border border-slate-800/80 cursor-pointer hover:border-slate-700 transition">
                <input
                  type="checkbox"
                  checked={preferences.strict_indonesia_eligible}
                  onChange={(e) => setPreferences({ ...preferences, strict_indonesia_eligible: e.target.checked })}
                  className="mt-0.5 rounded border-slate-700 bg-slate-900 text-emerald-500 focus:ring-0"
                />
                <div>
                  <span className="text-xs font-bold text-white block">Strict Verified Eligibility (Indonesia / Global)</span>
                  <span className="text-[11px] text-slate-400 leading-relaxed block mt-0.5">
                    Only show jobs with explicit evidence (verbatim quote) that accept applicants from Indonesia or Worldwide.
                  </span>
                </div>
              </label>

              <label className="flex items-start gap-3 p-3 rounded-xl bg-slate-950 border border-slate-800/80 cursor-pointer hover:border-slate-700 transition">
                <input
                  type="checkbox"
                  checked={preferences.prioritize_worldwide}
                  onChange={(e) => setPreferences({ ...preferences, prioritize_worldwide: e.target.checked })}
                  className="mt-0.5 rounded border-slate-700 bg-slate-900 text-emerald-500 focus:ring-0"
                />
                <div>
                  <span className="text-xs font-bold text-white block">Prioritize Borderless Opportunities (Worldwide / Anywhere)</span>
                  <span className="text-[11px] text-slate-400 leading-relaxed block mt-0.5">
                    Ranks 'Work From Anywhere' jobs at the top of the radar feed.
                  </span>
                </div>
              </label>
            </div>
          </div>
        )}
      </div>

      {/* SECTION 3: Company Preferences */}
      <div className="bg-[#0f172a] border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
        <button
          onClick={() => setCollapsed({ ...collapsed, company: !collapsed.company })}
          className="w-full px-5 py-4 flex items-center justify-between text-left hover:bg-slate-900/40 transition border-b border-slate-800/60"
        >
          <div className="flex items-center gap-2.5">
            <Building className="w-4 h-4 text-blue-400" />
            <div>
              <h2 className="text-sm font-bold text-white">3. Company Size & Employer Preferences</h2>
              <p className="text-[11px] text-slate-400">Prefer small teams of 10–100 employees, digital agencies, and block large corporations.</p>
            </div>
          </div>
          {collapsed.company ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronUp className="w-4 h-4 text-slate-400" />}
        </button>

        {!collapsed.company && (
          <div className="p-5 sm:p-6 space-y-5">
            {/* Preferred Company Sizes */}
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-2">
                Preferred Team Size Categories:
              </label>
              <div className="flex flex-wrap gap-2">
                {[
                  { id: 'small_startup', label: 'Small Team (10–50 people)' },
                  { id: 'medium_startup', label: 'Mid Startup (51–100 people)' },
                  { id: 'agency_studio', label: 'Web Agency / Studio' },
                  { id: 'large_enterprise', label: 'Large Enterprise (>100 people)' }
                ].map((sz) => {
                  const active = preferences.preferred_company_sizes.includes(sz.id)
                  return (
                    <button
                      key={sz.id}
                      type="button"
                      onClick={() => toggleArrayItem('preferred_company_sizes', sz.id)}
                      className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition ${
                        active 
                          ? 'bg-blue-600 text-white border-blue-500 shadow-sm' 
                          : 'bg-slate-950 text-slate-400 border-slate-800 hover:border-slate-700'
                      }`}
                    >
                      {sz.label}
                    </button>
                  )
                })}
              </div>
            </div>

            {/* Toggle Only Small & Exclude Tier-1 */}
            <div className="space-y-3">
              <label className="flex items-start gap-3 p-3 rounded-xl bg-slate-950 border border-slate-800/80 cursor-pointer hover:border-slate-700 transition">
                <input
                  type="checkbox"
                  checked={preferences.only_small_companies}
                  onChange={(e) => setPreferences({ ...preferences, only_small_companies: e.target.checked })}
                  className="mt-0.5 rounded border-slate-700 bg-slate-900 text-indigo-500 focus:ring-0"
                />
                <div>
                  <span className="text-xs font-bold text-white block">Prioritize Small Companies (10–100 Employees)</span>
                  <span className="text-[11px] text-slate-400 leading-relaxed block mt-0.5">
                    Filter the main feed to focus on early-stage startups and software studios realistic for 1–3 years of experience.
                  </span>
                </div>
              </label>

              <label className="flex items-start gap-3 p-3 rounded-xl bg-slate-950 border border-slate-800/80 cursor-pointer hover:border-slate-700 transition">
                <input
                  type="checkbox"
                  checked={preferences.exclude_tier1_enterprises}
                  onChange={(e) => setPreferences({ ...preferences, exclude_tier1_enterprises: e.target.checked })}
                  className="mt-0.5 rounded border-slate-700 bg-slate-900 text-indigo-500 focus:ring-0"
                />
                <div>
                  <span className="text-xs font-bold text-white block">Hide Large Corporations / Big Tech (Tier-1)</span>
                  <span className="text-[11px] text-slate-400 leading-relaxed block mt-0.5">
                    Excludes companies with thousands of employees that have lengthy selection processes and low acceptance rates.
                  </span>
                </div>
              </label>
            </div>

            {/* Excluded Companies Blacklist */}
            <div>
              <label className="text-xs font-semibold text-slate-300 block mb-1.5">
                Company Blacklist (Excluded Companies):
              </label>
              {preferences.excluded_companies.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mb-2">
                  {preferences.excluded_companies.map((comp) => (
                    <span key={comp} className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-rose-950/40 border border-rose-800/50 text-rose-200 text-xs">
                      {comp}
                      <button onClick={() => removeTag('excluded_companies', comp)} className="text-rose-400 hover:text-white">
                        <X className="w-3 h-3" />
                      </button>
                    </span>
                  ))}
                </div>
              )}
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="Type a company name to block..."
                  value={newExcludedCompInput}
                  onChange={(e) => setNewExcludedCompInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') addTag('excluded_companies', newExcludedCompInput, setNewExcludedCompInput) }}
                  className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-3 py-1.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500"
                />
                <button
                  onClick={() => addTag('excluded_companies', newExcludedCompInput, setNewExcludedCompInput)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium flex items-center gap-1"
                >
                  <Plus className="w-3.5 h-3.5" /> Block
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* SECTION 4: Job Freshness & Discovery */}
      <div className="bg-[#0f172a] border border-slate-800 rounded-2xl overflow-hidden shadow-sm">
        <button
          onClick={() => setCollapsed({ ...collapsed, freshness: !collapsed.freshness })}
          className="w-full px-5 py-4 flex items-center justify-between text-left hover:bg-slate-900/40 transition border-b border-slate-800/60"
        >
          <div className="flex items-center gap-2.5">
            <Clock className="w-4 h-4 text-amber-400" />
            <div>
              <h2 className="text-sm font-bold text-white">4. Freshness, Quality & Sync Schedule</h2>
              <p className="text-[11px] text-slate-400">Maximum job age, ghost job protection, and sync interval settings.</p>
            </div>
          </div>
          {collapsed.freshness ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronUp className="w-4 h-4 text-slate-400" />}
        </button>

        {!collapsed.freshness && (
          <div className="p-5 sm:p-6 space-y-5">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Max Freshness Days */}
              <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-xs font-semibold text-slate-300">Maximum Job Age</span>
                  <span className="text-xs font-bold text-indigo-400">{preferences.freshness_days} Days</span>
                </div>
                <input
                  type="range"
                  min="3"
                  max="30"
                  step="1"
                  value={preferences.freshness_days}
                  onChange={(e) => setPreferences({ ...preferences, freshness_days: parseInt(e.target.value) || 14 })}
                  className="w-full accent-indigo-500"
                />
                <p className="text-[10px] text-slate-500 mt-1">Eliminates expired listings older than {preferences.freshness_days} days</p>
              </div>

              {/* Ghost Risk Tolerance */}
              <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                <div className="flex justify-between items-center mb-1">
                  <span className="text-xs font-semibold text-slate-300">Toleransi Risiko Ghost Job</span>
                  <span className="text-xs font-bold text-emerald-400">Max {(preferences.max_ghost_risk * 100).toFixed(0)}%</span>
                </div>
                <input
                  type="range"
                  min="0.1"
                  max="0.8"
                  step="0.05"
                  value={preferences.max_ghost_risk}
                  onChange={(e) => setPreferences({ ...preferences, max_ghost_risk: parseFloat(e.target.value) || 0.3 })}
                  className="w-full accent-emerald-500"
                />
                <p className="text-[10px] text-slate-500 mt-1">Rejects jobs without clear stack & team details</p>
              </div>
            </div>

            {/* Background Polling Interval */}
            <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
              <div className="flex justify-between items-center mb-1">
                <span className="text-xs font-semibold text-slate-300">Background Sync Interval</span>
                <span className="text-xs font-bold text-white">Every {preferences.auto_refresh_interval_hours} Hour{preferences.auto_refresh_interval_hours !== 1 ? 's' : ''}</span>
              </div>
              <input
                type="range"
                min="1"
                max="24"
                step="1"
                value={preferences.auto_refresh_interval_hours}
                onChange={(e) => setPreferences({ ...preferences, auto_refresh_interval_hours: parseInt(e.target.value) || 5 })}
                className="w-full accent-indigo-500"
              />
              <p className="text-[10px] text-slate-500 mt-1">
                How often the poller fetches new job data while the laptop/server is active.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Sticky Bottom Save Bar (Appears when changed) */}
      {hasUnsavedChanges && (
        <div className="sticky bottom-4 z-40 bg-[#0f172a]/95 backdrop-blur-md border border-indigo-500/40 rounded-2xl p-4 shadow-2xl flex items-center justify-between gap-4 animate-in slide-in-from-bottom duration-200">
          <div className="flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400 animate-ping" />
            <span className="text-xs font-bold text-white">You have unsaved preference changes.</span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setPreferences(initialPreferences)}
              className="px-3 py-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 text-xs font-semibold transition"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold shadow transition flex items-center gap-1.5"
            >
              {saving ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
              <span>Save Now</span>
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

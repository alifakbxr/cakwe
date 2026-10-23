import { useState, useEffect } from 'react'
import { 
  RefreshCw, 
  Briefcase, 
  ShieldCheck, 
  Search, 
  Sparkles, 
  Building,
  Clock
} from 'lucide-react'

import type { 
  Job, 
  Stats, 
  SyncStatus, 
  ViewTab, 
  OptimizedResumeResult, 
  ContactInfo,
  ResumeTemplate 
} from './types'

import { AppShell } from './components/AppShell'
import { DashboardView } from './components/DashboardView'
import { JobCard } from './components/JobCard'
import { KanbanBoard } from './components/KanbanBoard'
import { ATSStudioModal } from './components/ATSStudioModal'
import { TrackerModal } from './components/TrackerModal'
import { DismissModal } from './components/DismissModal'
import { SettingsView } from './components/SettingsView'
import { Button } from './components/ui/button'
import { Card } from './components/ui/card'
import { Input } from './components/ui/input'
import { Badge } from './components/ui/badge'

export default function App() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState(false)
  const [selectedRole, setSelectedRole] = useState('ALL')
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedJobId, setExpandedJobId] = useState<string | null>(null)

  // Navigation & View Mode
  const [currentTab, setCurrentTab] = useState<ViewTab>('DASHBOARD')
  const [showClosed, setShowClosed] = useState(false)
  const [onlyVerified, setOnlyVerified] = useState(true)
  const [onlySmallCompanies, setOnlySmallCompanies] = useState(false)
  const [minMatchScore, setMinMatchScore] = useState<number | null>(80)
  const [maxExpYears, setMaxExpYears] = useState<number | null>(3)
  const [sortBy, setSortBy] = useState<'latest' | 'fit'>('latest')
  const [syncStatus, setSyncStatus] = useState<SyncStatus | null>(null)
  const [diagnostics, setDiagnostics] = useState<any>(null)
  
  // Modals
  const [trackingModalJob, setTrackingModalJob] = useState<Job | null>(null)
  const [dismissModalJob, setDismissModalJob] = useState<Job | null>(null)
  const [dismissReason, setDismissReason] = useState('not_remote')
  const [trackingForm, setTrackingForm] = useState({
    status: 'saved',
    applied_date: new Date().toISOString().split('T')[0],
    notes: '',
    follow_up_date: ''
  })

  // ATS Studio Modal States
  const [activeJobForBuilder, setActiveJobForBuilder] = useState<Job | null>(null)
  const [builderTab, setBuilderTab] = useState<'MODE_A' | 'MODE_B' | 'HISTORY'>('MODE_A')
  const [documentView, setDocumentView] = useState<'RESUME' | 'COVER_LETTER'>('RESUME')
  const [isProcessing, setIsProcessing] = useState(false)
  const [isRegeneratingLetter, setIsRegeneratingLetter] = useState(false)
  const [optimizedResult, setOptimizedResult] = useState<OptimizedResumeResult | null>(null)
  const [editableCoverLetter, setEditableCoverLetter] = useState('')
  const [copiedLetter, setCopiedLetter] = useState(false)
  const [savedHistory, setSavedHistory] = useState<any[]>([])

  // Mode A
  const [rawResumeText, setRawResumeText] = useState('')
  const [uploadFileName, setUploadFileName] = useState('')
  const [isUploading, setIsUploading] = useState(false)

  // Mode B
  const [profileContact, setProfileContact] = useState<ContactInfo>({
    full_name: '',
    email: '',
    phone: '',
    location: 'Indonesia',
    linkedin_url: '',
    github_url: ''
  })
  const [backgroundStory, setBackgroundStory] = useState('')
  const [skillsInput, setSkillsInput] = useState('')

  const roles = [
    { label: 'Semua Peran', value: 'ALL' },
    { label: 'Internship (Open/No-Degree)', value: 'Intern' },
    { label: 'Laravel / PHP', value: 'Laravel' },
    { label: 'Vue.js / Inertia', value: 'Vue' },
    { label: 'Golang', value: 'Go' },
    { label: 'Fullstack / TS', value: 'Fullstack' },
    { label: 'AI Engineer / Python', value: 'AI' },
  ]

  const fetchSyncStatus = async () => {
    try {
      const res = await fetch('/api/sync/status')
      if (res.ok) {
        const data = await res.json()
        setSyncStatus(data)
      }
    } catch (err) {
      console.error('Failed to fetch sync status', err)
    }
  }

  const triggerManualSync = async () => {
    try {
      setSyncing(true)
      const res = await fetch('/api/sync', { method: 'POST' })
      if (res.ok) {
        await fetchJobsAndStats()
        await fetchSyncStatus()
      }
    } catch (err) {
      console.error('Manual sync failed', err)
    } finally {
      setSyncing(false)
    }
  }

  const handleUpdateApplicationStatus = async (jobId: string, newStatus: string) => {
    try {
      const res = await fetch(`/api/applications/${encodeURIComponent(jobId)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          status: newStatus,
          applied_date: newStatus === 'applied' ? new Date().toISOString().split('T')[0] : null,
          notes: ''
        })
      })
      if (res.ok) {
        setJobs(prev => prev.map(j => j.id === jobId ? { ...j, application_status: newStatus } : j))
      }
    } catch (err) {
      console.error('Failed to update status', err)
    }
  }

  const handleSaveTracking = async () => {
    if (!trackingModalJob) return
    try {
      const res = await fetch(`/api/applications/${encodeURIComponent(trackingModalJob.id)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(trackingForm)
      })
      if (res.ok) {
        setJobs(prev => prev.map(j => j.id === trackingModalJob.id ? { 
          ...j, 
          application_status: trackingForm.status,
          applied_date: trackingForm.applied_date,
          application_notes: trackingForm.notes
        } : j))
        setTrackingModalJob(null)
      }
    } catch (err) {
      console.error('Failed to save tracking record', err)
    }
  }

  const handleDismissJob = async () => {
    if (!dismissModalJob) return
    try {
      const res = await fetch(`/api/jobs/${encodeURIComponent(dismissModalJob.id)}/dismiss`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reason: dismissReason })
      })
      if (res.ok) {
        setJobs(prev => prev.filter(j => j.id !== dismissModalJob.id))
        setDismissModalJob(null)
      }
    } catch (err) {
      console.error('Failed to dismiss job', err)
    }
  }

  const fetchJobsAndStats = async () => {
    try {
      setLoading(true)
      const params = new URLSearchParams({
        status: onlyVerified ? 'verified_eligible' : '',
        only_small: onlySmallCompanies ? 'true' : 'false',
        include_closed: showClosed ? 'true' : 'false',
        role: selectedRole,
        sort_by: sortBy
      })
      if (minMatchScore !== null) {
        params.append('min_score', String(minMatchScore))
      } else {
        params.append('min_score', '0')
      }
      if (maxExpYears !== null) {
        params.append('max_exp', String(maxExpYears))
      } else {
        params.append('max_exp', '99')
      }
      const [jobsRes, statsRes] = await Promise.all([
        fetch(`/api/jobs?${params.toString()}`),
        fetch('/api/stats')
      ])

      if (jobsRes.ok) {
        const jobsData = await jobsRes.json()
        setJobs(jobsData.jobs)
        if (jobsData.diagnostics) {
          setDiagnostics(jobsData.diagnostics)
        }
      }

      if (statsRes.ok) {
        const statsData = await statsRes.json()
        setStats(statsData)
      }
    } catch (err) {
      console.error('Failed to fetch data', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchJobsAndStats()
  }, [onlyVerified, onlySmallCompanies, showClosed, selectedRole, minMatchScore, maxExpYears, sortBy])

  useEffect(() => {
    fetchSyncStatus()
    const saved = localStorage.getItem('user_resume_draft')
    if (saved) setRawResumeText(saved)
  }, [])

  const getApplicationUrl = (job: Job): string => {
    if (job.application_url && job.application_url.startsWith('http')) {
      return job.application_url
    }
    if (job.id && job.id.startsWith('http')) {
      return job.id
    }
    return `https://himalayas.app/jobs/${job.id}`
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)

    try {
      setIsUploading(true)
      const res = await fetch('/api/resume/parse-file', {
        method: 'POST',
        body: formData,
      })
      if (!res.ok) throw new Error('Failed to extract file')
      const data = await res.json()
      setRawResumeText(data.text)
      setUploadFileName(file.name)
      localStorage.setItem('user_resume_draft', data.text)
    } catch (err: any) {
      alert(`Failed to read file: ${err.message}`)
    } finally {
      setIsUploading(false)
    }
  }

  const handleOptimizeModeA = async () => {
    if (!activeJobForBuilder || !rawResumeText.trim()) return
    try {
      setIsProcessing(true)
      const res = await fetch('/api/resume/generate-mode-a', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: activeJobForBuilder.id,
          resume_text: rawResumeText
        })
      })
      if (!res.ok) throw new Error('Failed to optimize resume')
      const data = await res.json()
      setOptimizedResult(data)
      setEditableCoverLetter(data.cover_letter || '')
    } catch (err: any) {
      alert(`Error: ${err.message}`)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleGenerateModeB = async () => {
    if (!activeJobForBuilder) return
    try {
      setIsProcessing(true)
      const skillsArray = skillsInput.split(',').map(s => s.trim()).filter(Boolean)
      const res = await fetch('/api/resume/generate-mode-b', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: activeJobForBuilder.id,
          contact: profileContact,
          background_story: backgroundStory,
          skills: skillsArray
        })
      })
      if (!res.ok) throw new Error('Failed to build resume')
      const data = await res.json()
      setOptimizedResult(data)
      setEditableCoverLetter(data.cover_letter || '')
    } catch (err: any) {
      alert(`Error: ${err.message}`)
    } finally {
      setIsProcessing(false)
    }
  }

  const handleSaveVersion = async () => {
    if (!activeJobForBuilder || !optimizedResult) return
    try {
      const res = await fetch('/api/resume/save-version', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: activeJobForBuilder.id,
          job_title: activeJobForBuilder.title,
          company: activeJobForBuilder.company_name,
          resume: optimizedResult.resume,
          analysis: optimizedResult.analysis,
          cover_letter: editableCoverLetter
        })
      })
      if (res.ok) {
        alert('Resume version saved successfully!')
        loadHistory(activeJobForBuilder.id)
      }
    } catch (err) {
      alert('Failed to save resume version')
    }
  }

  const loadHistory = async (jobId: string) => {
    try {
      const res = await fetch(`/api/resume/history/${encodeURIComponent(jobId)}`)
      if (res.ok) {
        const data = await res.json()
        setSavedHistory(data)
      }
    } catch (err) {
      console.error(err)
    }
  }

  const handleExportDocx = async (template: string = 'HARVARD') => {
    if (!optimizedResult) return
    try {
      const res = await fetch(`/api/resume/export-docx?template=${encodeURIComponent(template)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(optimizedResult.resume)
      })
      if (!res.ok) throw new Error('Failed to generate DOCX')
      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `Resume_${optimizedResult.resume.contact.full_name.replace(/\s+/g, '_')}_${template}.docx`
      document.body.appendChild(a)
      a.click()
      a.remove()
      setTimeout(() => window.URL.revokeObjectURL(url), 1000)
    } catch (err: any) {
      alert(err.message)
    }
  }

  const handleExportCoverLetterDocx = async () => {
    if (!optimizedResult) return
    try {
      const res = await fetch('/api/resume/export-cover-letter-docx', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          applicant_name: optimizedResult.resume.contact.full_name,
          company: activeJobForBuilder?.company_name || 'Hiring Team',
          job_title: activeJobForBuilder?.title || 'Position',
          cover_letter_text: editableCoverLetter
        })
      })
      if (!res.ok) throw new Error('Failed to generate DOCX Cover Letter')
      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `Cover_Letter_${optimizedResult.resume.contact.full_name.replace(/\s+/g, '_')}.docx`
      document.body.appendChild(a)
      a.click()
      a.remove()
      setTimeout(() => window.URL.revokeObjectURL(url), 1000)
    } catch (err: any) {
      alert(err.message)
    }
  }

  const handleCopyCoverLetter = () => {
    navigator.clipboard.writeText(editableCoverLetter)
    setCopiedLetter(true)
    setTimeout(() => setCopiedLetter(false), 2000)
  }

  const handleRegenerateCoverLetter = async () => {
    if (!activeJobForBuilder || !optimizedResult) return
    try {
      setIsRegeneratingLetter(true)
      const res = await fetch('/api/resume/generate-cover-letter', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          job_id: activeJobForBuilder.id,
          resume: optimizedResult.resume
        })
      })
      if (!res.ok) throw new Error('Failed to regenerate cover letter')
      const data = await res.json()
      setEditableCoverLetter(data.cover_letter)
      const updated = { ...optimizedResult }
      updated.cover_letter = data.cover_letter
      setOptimizedResult(updated)
    } catch (err: any) {
      alert(err.message)
    } finally {
      setIsRegeneratingLetter(false)
    }
  }

  const handleExportPdf = async (template: ResumeTemplate = 'HARVARD') => {
    if (!optimizedResult) return
    try {
      const res = await fetch(`/api/resume/export-pdf?template=${encodeURIComponent(template)}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(optimizedResult.resume)
      })
      if (!res.ok) throw new Error('Failed to generate PDF Resume')
      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `Resume_${optimizedResult.resume.contact.full_name.replace(/\s+/g, '_')}_${template}.pdf`
      document.body.appendChild(a)
      a.click()
      a.remove()
      setTimeout(() => window.URL.revokeObjectURL(url), 1000)
    } catch (err: any) {
      alert(err.message)
    }
  }

  const handleExportCoverLetterPdf = async () => {
    if (!optimizedResult) return
    try {
      const res = await fetch('/api/resume/export-cover-letter-pdf', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          applicant_name: optimizedResult.resume.contact.full_name,
          company: activeJobForBuilder?.company_name || 'Hiring Team',
          job_title: activeJobForBuilder?.title || 'Position',
          cover_letter_text: editableCoverLetter
        })
      })
      if (!res.ok) throw new Error('Failed to generate PDF Cover Letter')
      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `Cover_Letter_${optimizedResult.resume.contact.full_name.replace(/\s+/g, '_')}.pdf`
      document.body.appendChild(a)
      a.click()
      a.remove()
      setTimeout(() => window.URL.revokeObjectURL(url), 1000)
    } catch (err: any) {
      alert(err.message)
    }
  }


  // Client search filtering (safe & defensive)
  const filteredJobs = jobs.filter(job => {
    const q = searchQuery.trim().toLowerCase()
    if (!q) {
      return !onlyVerified || job.eligibility_status === 'verified_eligible'
    }
    const matchTitle = Boolean(job.title?.toLowerCase().includes(q))
    const matchCompany = Boolean(job.company_name?.toLowerCase().includes(q))
    const matchSkills = Array.isArray(job.skills_required) && job.skills_required.some(s => typeof s === 'string' && s.toLowerCase().includes(q))
    const matchQuery = matchTitle || matchCompany || matchSkills
    const matchVerified = !onlyVerified || job.eligibility_status === 'verified_eligible'

    return matchQuery && matchVerified
  })

  return (
    <AppShell
      currentTab={currentTab}
      onSelectTab={setCurrentTab}
      onManualSync={triggerManualSync}
      syncing={syncing}
      syncStatus={syncStatus}
      activeTrackingCount={jobs.filter(j => Boolean(j.application_status)).length}
    >
      {/* View: Dashboard */}
      {currentTab === 'DASHBOARD' && (
        <DashboardView
          stats={stats}
          jobs={jobs}
          onNavigateTab={setCurrentTab}
          onOpenATSStudio={(job) => {
            setActiveJobForBuilder(job)
            setOptimizedResult(null)
            setEditableCoverLetter('')
            setBuilderTab('MODE_A')
            setDocumentView('RESUME')
            loadHistory(job.id)
          }}
          onOpenTracker={(job) => {
            setTrackingModalJob(job)
            setTrackingForm({
              status: job.application_status || 'saved',
              applied_date: job.applied_date || new Date().toISOString().split('T')[0],
              notes: job.application_notes || '',
              follow_up_date: ''
            })
          }}
        />
      )}

      {/* View: Settings */}
      {/* View: Settings / Preferences */}
      {currentTab === 'SETTINGS' && <SettingsView onPreferencesUpdated={fetchJobsAndStats} />}


      {/* View: Resume Studio Standalone Tab */}
      {currentTab === 'RESUME_STUDIO' && (
        <div className="space-y-6">
          <Card className="bg-[#0f172a] border-slate-800 p-5 sm:p-6">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-indigo-400" />
              ATS Resume & Cover Letter Studio
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Select one of the opportunities below to optimize your CV and generate a targeted Cover Letter following Harvard/MIT standards.
            </p>

            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {jobs.slice(0, 6).map((job) => (
                <Card 
                  key={job.id} 
                  onClick={() => {
                    setActiveJobForBuilder(job)
                    setOptimizedResult(null)
                    setEditableCoverLetter('')
                    setBuilderTab('MODE_A')
                    setDocumentView('RESUME')
                    loadHistory(job.id)
                  }}
                  className="p-3.5 bg-slate-950 border-slate-800 hover:border-indigo-500 cursor-pointer transition flex flex-col justify-between"
                >
                  <div>
                    <span className="text-[11px] font-semibold text-slate-400">{job.company_name}</span>
                    <h4 className="text-xs font-bold text-white line-clamp-1 mt-0.5">{job.title}</h4>
                  </div>
                  <div className="mt-3 flex items-center justify-between text-[11px]">
                    <span className="text-emerald-400 font-bold">{job.match_score || 0}% Fit</span>
                    <span className="text-indigo-400 font-semibold flex items-center gap-1">
                      Open Studio &rarr;
                    </span>
                  </div>
                </Card>
              ))}
            </div>
          </Card>
        </div>
      )}

      {/* View: Kanban */}
      {currentTab === 'KANBAN' && (
        <KanbanBoard
          jobs={jobs}
          onUpdateStatus={handleUpdateApplicationStatus}
          onOpenTrackerModal={(job) => {
            setTrackingModalJob(job)
            setTrackingForm({
              status: job.application_status || 'saved',
              applied_date: job.applied_date || new Date().toISOString().split('T')[0],
              notes: job.application_notes || '',
              follow_up_date: ''
            })
          }}
          onOpenATSBuilder={(job) => {
            setActiveJobForBuilder(job)
            setOptimizedResult(null)
            setEditableCoverLetter('')
            setBuilderTab('MODE_A')
            setDocumentView('RESUME')
            loadHistory(job.id)
          }}
          getApplicationUrl={getApplicationUrl}
        />
      )}

      {/* View: Radar Job Feed */}
      {currentTab === 'RADAR' && (
        <div className="space-y-6">
          {/* Stats Bar */}
          {stats && (
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <Card 
                onClick={() => {
                  setOnlyVerified(true)
                  setOnlySmallCompanies(false)
                  setMinMatchScore(null)
                  setMaxExpYears(null)
                  setSelectedRole('ALL')
                  setSearchQuery('')
                }}
                className={`p-4 transition cursor-pointer select-none border ${
                  onlyVerified && !onlySmallCompanies && minMatchScore === null && maxExpYears === null
                    ? 'bg-emerald-950/40 border-emerald-500/50 shadow-sm ring-1 ring-emerald-500/30'
                    : 'bg-[#0f172a] border-slate-800 hover:border-slate-700'
                }`}
                title="Click to show all verified roles open to Indonesia/Worldwide"
              >
                <div className="text-xs text-emerald-400 font-medium flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4" />
                    Verified Worldwide / Indonesia
                  </span>
                  <span className="text-[10px] text-emerald-400/80 bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-800/60 font-mono">
                    Total: {stats.verified_eligible_jobs}
                  </span>
                </div>
                <div className="text-2xl font-bold text-emerald-400 mt-1">
                  {stats.verified_eligible_jobs}
                </div>
                <div className="text-[11px] text-slate-400 mt-1">100% Remote / Verified Worldwide EOR Contract</div>
              </Card>

              <Card 
                onClick={() => {
                  setOnlyVerified(true)
                  setMinMatchScore(80)
                  setMaxExpYears(3)
                  setOnlySmallCompanies(false)
                }}
                className={`p-4 transition cursor-pointer select-none border ${
                  minMatchScore === 80 
                    ? 'bg-indigo-950/40 border-indigo-500/50 shadow-sm ring-1 ring-indigo-500/30' 
                    : 'bg-[#0f172a] border-slate-800 hover:border-slate-700'
                }`}
                title="Click to filter high fit matches (Fit > 80% & Exp 0-3 yrs)"
              >
                <div className="text-xs text-indigo-400 font-medium flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Sparkles className="w-4 h-4" />
                    Accurate Matches (Fit &gt; 80%)
                  </span>
                  <span className="text-[10px] text-indigo-300/80 bg-indigo-950/60 px-1.5 py-0.5 rounded border border-indigo-800/60 font-mono">
                    Top Priority
                  </span>
                </div>
                <div className="text-2xl font-bold text-white mt-1">
                  {jobs.filter(j => (j.match_score ?? 0) >= 80).length}
                </div>
                <div className="text-[11px] text-slate-400 mt-1">0–3 yrs experience, aligned stack</div>
              </Card>

              <Card className="p-4 bg-[#0f172a] border-slate-800">
                <div className="text-xs text-slate-400 font-medium flex items-center justify-between">
                  <span className="flex items-center gap-1.5">
                    <Briefcase className="w-4 h-4 text-slate-400" />
                    Total Tracked Opportunities
                  </span>
                  <span className="text-[10px] text-slate-500 font-mono">14 Days</span>
                </div>
                <div className="text-2xl font-bold text-white mt-1">{stats.total_jobs}</div>
                <div className="text-[11px] text-slate-500 mt-1">Multi-ATS Public Feeds (Active & Scanned)</div>
              </Card>
            </div>
          )}

          {/* Search, Roles, and Strict Filter Controls */}
          <Card className="bg-[#0f172a] border-slate-800 p-4 space-y-4">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
              {/* Role filter pills */}
              <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto pb-1 sm:pb-0">
                {roles.map(r => (
                  <Button
                    key={r.value}
                    size="sm"
                    variant={selectedRole === r.value ? "default" : "outline"}
                    onClick={() => setSelectedRole(r.value)}
                    className="whitespace-nowrap h-8"
                  >
                    {r.label}
                  </Button>
                ))}
              </div>

              {/* Search input with shadcn Input */}
              <div className="relative w-full sm:w-80">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 z-10" />
                <Input 
                  type="text"
                  placeholder="Search role, skill, company..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-9 pr-3 h-9"
                />
              </div>
            </div>

            {/* Filter checkboxes & application subtabs */}
            <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-800/80">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs text-slate-400 font-medium">Eligibility Status:</span>
                <Button
                  size="sm"
                  variant={onlyVerified ? "default" : "outline"}
                  onClick={() => setOnlyVerified(true)}
                  className="gap-1.5 h-7 text-xs"
                >
                  <ShieldCheck className="w-3.5 h-3.5" />
                  <span>Verified Eligible (Worldwide Open)</span>
                </Button>
                <Button
                  size="sm"
                  variant={!onlyVerified ? "secondary" : "outline"}
                  onClick={() => setOnlyVerified(false)}
                  className="gap-1.5 h-7 text-xs"
                >
                  <span>Review Queue (Needs Review)</span>
                </Button>
              </div>

              <div className="flex items-center gap-3 text-xs text-slate-400 flex-wrap">
                {/* High Fit Score Filter */}
                <label className={`flex items-center gap-1.5 cursor-pointer px-2.5 py-1 rounded-lg font-medium transition ${
                  minMatchScore !== null 
                    ? 'bg-emerald-950/60 border border-emerald-600/60 text-emerald-300' 
                    : 'bg-slate-900/60 border border-slate-800 text-slate-400 hover:text-slate-200'
                }`}>
                  <input
                    type="checkbox"
                    checked={minMatchScore !== null}
                    onChange={e => setMinMatchScore(e.target.checked ? 80 : null)}
                    className="rounded border-emerald-600 text-emerald-500 focus:ring-0"
                  />
                  <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
                  Fit &gt; 80% (All Companies)
                </label>

                {/* Experience <= 3 yrs Filter */}
                <label className={`flex items-center gap-1.5 cursor-pointer px-2.5 py-1 rounded-lg font-medium transition ${
                  maxExpYears !== null 
                    ? 'bg-cyan-950/60 border border-cyan-600/60 text-cyan-300' 
                    : 'bg-slate-900/60 border border-slate-800 text-slate-400 hover:text-slate-200'
                }`}>
                  <input
                    type="checkbox"
                    checked={maxExpYears !== null}
                    onChange={e => setMaxExpYears(e.target.checked ? 3 : null)}
                    className="rounded border-cyan-600 text-cyan-500 focus:ring-0"
                  />
                  <Clock className="w-3.5 h-3.5 text-cyan-400" />
                  0–3 Yrs Experience
                </label>

                {/* Small Companies Filter */}
                <label className={`flex items-center gap-1.5 cursor-pointer px-2.5 py-1 rounded-lg font-medium transition ${
                  onlySmallCompanies 
                    ? 'bg-blue-950/60 border border-blue-600/60 text-blue-300' 
                    : 'bg-slate-900/60 border border-slate-800 text-slate-400 hover:text-slate-200'
                }`}>
                  <input
                    type="checkbox"
                    checked={onlySmallCompanies}
                    onChange={e => setOnlySmallCompanies(e.target.checked)}
                    className="rounded border-blue-600 text-blue-500 focus:ring-0"
                  />
                  <Building className="w-3.5 h-3.5 text-blue-400" />
                  Small Startups Only (10–100)
                </label>

                <label className="flex items-center gap-1.5 cursor-pointer text-slate-400 hover:text-slate-200">
                  <input
                    type="checkbox"
                    checked={showClosed}
                    onChange={e => setShowClosed(e.target.checked)}
                    className="rounded border-slate-700 text-indigo-600 focus:ring-0"
                  />
                  Show closed jobs
                </label>

                {/* Sort Order Toggle */}
                <div className="flex items-center gap-1 bg-slate-900 border border-slate-800 p-0.5 rounded-lg ml-auto">
                  <span className="text-[11px] text-slate-400 px-2 font-medium">Sort by:</span>
                  <Button
                    size="sm"
                    variant={sortBy === 'latest' ? 'default' : 'ghost'}
                    onClick={() => setSortBy('latest')}
                    className="h-6 px-2.5 text-[11px]"
                  >
                    Latest
                  </Button>
                  <Button
                    size="sm"
                    variant={sortBy === 'fit' ? 'default' : 'ghost'}
                    onClick={() => setSortBy('fit')}
                    className="h-6 px-2.5 text-[11px]"
                  >
                    Best Fit
                  </Button>
                </div>
              </div>
            </div>
          </Card>

          {/* Filter Diagnostics Alert / Transparency Banner */}
          {onlySmallCompanies && diagnostics && (diagnostics.hidden_by_freshness > 0 || diagnostics.hidden_by_large_enterprise > 0 || (diagnostics.hidden_by_developer_platform && diagnostics.hidden_by_developer_platform > 0)) && (
            <div className="bg-slate-900/90 border border-indigo-500/30 rounded-xl p-3.5 px-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
              <div className="flex items-center gap-2.5 text-slate-300">
                <span className="flex h-2 w-2 rounded-full bg-indigo-400 animate-pulse" />
                <span>
                  Active Filter: Prioritizing independent startups. Hiding{' '}
                  {diagnostics.hidden_by_developer_platform ? <strong>{diagnostics.hidden_by_developer_platform} dev-tool platforms</strong> : null}
                  {diagnostics.hidden_by_large_enterprise > 0 ? `, ${diagnostics.hidden_by_large_enterprise} Tier-1 enterprises` : null}
                  {diagnostics.hidden_by_freshness > 0 ? `, and ${diagnostics.hidden_by_freshness} jobs &gt; ${diagnostics.freshness_days_active} days old.` : '.'}
                </span>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                {onlySmallCompanies && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setOnlySmallCompanies(false)}
                    className="h-7 text-indigo-300 border-slate-700"
                  >
                    Show All Categories
                  </Button>
                )}
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => {
                    setSelectedRole('ALL')
                    setSearchQuery('')
                    setOnlySmallCompanies(false)
                    setMinMatchScore(null)
                    setMaxExpYears(null)
                  }}
                  className="h-7 bg-indigo-600/40 hover:bg-indigo-600/60 text-indigo-200 border border-indigo-500/40"
                >
                  Reset Feed Filters
                </Button>
              </div>
            </div>
          )}

          {/* Feed Header with Live Count Synchronization */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 px-1 pt-2">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-sm font-bold text-white flex items-center gap-2">
                <span>Job Openings</span>
                <Badge variant="secondary" className="font-mono text-xs px-2 py-0.5">
                  {filteredJobs.length} roles
                </Badge>
              </h3>

              {stats && filteredJobs.length !== (onlyVerified ? stats.verified_eligible_jobs : stats.total_jobs) && (
                <span className="text-xs text-slate-400">
                  (filtered from <strong className="text-emerald-400">{onlyVerified ? stats.verified_eligible_jobs : stats.total_jobs}</strong> {onlyVerified ? 'verified' : 'total'} opportunities)
                </span>
              )}
            </div>

            {/* Quick Action: Reset or Show All */}
            {(onlySmallCompanies || minMatchScore !== null || maxExpYears !== null || selectedRole !== 'ALL' || searchQuery) && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setOnlySmallCompanies(false)
                  setMinMatchScore(null)
                  setMaxExpYears(null)
                  setSelectedRole('ALL')
                  setSearchQuery('')
                }}
                className="h-7 text-xs text-indigo-300 border-slate-700 hover:bg-slate-800"
              >
                Reset Filters (Show All {onlyVerified ? stats?.verified_eligible_jobs : stats?.total_jobs})
              </Button>
            )}
          </div>

          {/* Feed List Container */}
          {loading ? (
            <div className="text-center py-24 bg-[#0f172a] border border-slate-800 rounded-xl">
              <RefreshCw className="w-8 h-8 text-emerald-400 animate-spin mx-auto mb-3" />
              <p className="text-xs text-slate-400 font-medium">Loading verified opportunities...</p>
            </div>
          ) : filteredJobs.length === 0 ? (
            <div className="text-center py-20 bg-[#0f172a] border border-slate-800 rounded-xl p-8">
              <Briefcase className="w-10 h-10 text-slate-600 mx-auto mb-3" />
              <h3 className="text-sm font-semibold text-white">No jobs match your criteria</h3>
              <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto">
                Try adjusting your search filters or click "Sync Radar" to fetch the latest opportunities.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredJobs.map((job) => (
                <JobCard
                  key={job.id}
                  job={job}
                  isExpanded={expandedJobId === job.id}
                  onToggleExpand={() => setExpandedJobId(prev => prev === job.id ? null : job.id)}
                  onOpenTracker={(job) => {
                    setTrackingModalJob(job)
                    setTrackingForm({
                      status: job.application_status || 'saved',
                      applied_date: job.applied_date || new Date().toISOString().split('T')[0],
                      notes: job.application_notes || '',
                      follow_up_date: ''
                    })
                  }}
                  onOpenATSBuilder={(job) => {
                    setActiveJobForBuilder(job)
                    setOptimizedResult(null)
                    setEditableCoverLetter('')
                    setBuilderTab('MODE_A')
                    setDocumentView('RESUME')
                    loadHistory(job.id)
                  }}
                  onOpenDismiss={(job) => {
                    setDismissModalJob(job)
                    setDismissReason('not_remote')
                  }}
                  getApplicationUrl={getApplicationUrl}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Modal Application Tracker */}
      {trackingModalJob && (
        <TrackerModal
          job={trackingModalJob}
          onClose={() => setTrackingModalJob(null)}
          trackingForm={trackingForm}
          setTrackingForm={setTrackingForm}
          onSave={handleSaveTracking}
        />
      )}

      {/* Modal Dismiss Feedback */}
      {dismissModalJob && (
        <DismissModal
          job={dismissModalJob}
          onClose={() => setDismissModalJob(null)}
          dismissReason={dismissReason}
          setDismissReason={setDismissReason}
          onDismiss={handleDismissJob}
        />
      )}

      {/* Fullscreen ATS Resume Studio Modal */}
      {activeJobForBuilder && (
        <ATSStudioModal
          job={activeJobForBuilder}
          onClose={() => setActiveJobForBuilder(null)}
          builderTab={builderTab}
          setBuilderTab={setBuilderTab}
          documentView={documentView}
          setDocumentView={setDocumentView}
          rawResumeText={rawResumeText}
          setRawResumeText={setRawResumeText}
          uploadFileName={uploadFileName}
          isUploading={isUploading}
          onFileUpload={handleFileUpload}
          onOptimizeModeA={handleOptimizeModeA}
          profileContact={profileContact}
          setProfileContact={setProfileContact}
          backgroundStory={backgroundStory}
          setBackgroundStory={setBackgroundStory}
          skillsInput={skillsInput}
          setSkillsInput={setSkillsInput}
          onGenerateModeB={handleGenerateModeB}
          savedHistory={savedHistory}
          isProcessing={isProcessing}
          optimizedResult={optimizedResult}
          setOptimizedResult={setOptimizedResult}
          editableCoverLetter={editableCoverLetter}
          setEditableCoverLetter={setEditableCoverLetter}
          copiedLetter={copiedLetter}
          onCopyCoverLetter={handleCopyCoverLetter}
          onSaveVersion={handleSaveVersion}
          onExportDocx={handleExportDocx}
          onExportPdf={handleExportPdf}
          onExportCoverLetterDocx={handleExportCoverLetterDocx}
          onExportCoverLetterPdf={handleExportCoverLetterPdf}
          onRegenerateCoverLetter={handleRegenerateCoverLetter}
          isRegeneratingLetter={isRegeneratingLetter}
        />
      )}
    </AppShell>
  )
}

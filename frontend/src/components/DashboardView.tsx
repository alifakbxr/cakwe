import React from 'react'
import { 
  Building, 
  ShieldCheck, 
  Bookmark, 
  Clock, 
  ArrowRight, 
  FileText, 
  TrendingUp,
  MapPin,
  CheckCircle2,
  Calendar
} from 'lucide-react'
import type { Job, Stats } from '../types'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'

interface DashboardViewProps {
  stats: Stats | null
  jobs: Job[]
  onNavigateTab: (tab: 'RADAR' | 'KANBAN' | 'RESUME_STUDIO') => void
  onOpenATSStudio: (job: Job) => void
  onOpenTracker: (job: Job) => void
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  stats,
  jobs,
  onNavigateTab,
  onOpenATSStudio,
  onOpenTracker
}) => {
  const trackedJobs = jobs.filter(j => Boolean(j.application_status))
  const appliedJobs = jobs.filter(j => j.application_status === 'applied')
  const interviewJobs = jobs.filter(j => j.application_status === 'interviewing')
  const savedJobs = jobs.filter(j => j.application_status === 'saved')

  const topRecommendations = jobs
    .filter(j => j.eligibility_status === 'verified_eligible' && (!j.lifecycle_status || j.lifecycle_status === 'active'))
    .slice(0, 5)

  return (
    <div className="space-y-6">
      {/* Welcome Hero Card */}
      <Card className="relative overflow-hidden border-slate-800 bg-gradient-to-r from-slate-900 via-[#0f172a] to-slate-900 shadow-lg">
        <div className="relative z-10 p-6 sm:p-8 max-w-3xl">
          <Badge variant="default" className="gap-1.5 px-3 py-1 text-xs mb-3 font-semibold">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>Strict Verified Worldwide & Small Companies</span>
          </Badge>
          <h1 className="text-xl sm:text-2xl lg:text-3xl font-extrabold text-white tracking-tight leading-tight">
            Global Remote Career Command Center
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-2 leading-relaxed">
            Discover 100% remote job opportunities accepting worldwide candidates, manage your application pipeline in a structured Kanban board, and optimize ATS resumes following Harvard/MIT standards.
          </p>
          <div className="mt-5 flex flex-wrap items-center gap-3">
            <Button
              onClick={() => onNavigateTab('RADAR')}
              variant="default"
              size="default"
              className="gap-2 font-semibold shadow-md"
            >
              <span>Explore Verified Jobs</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Button>
            <Button
              onClick={() => onNavigateTab('KANBAN')}
              variant="secondary"
              size="default"
              className="gap-2 font-semibold"
            >
              <span>Open Kanban Pipeline ({trackedJobs.length})</span>
            </Button>
          </div>
        </div>
      </Card>

      {/* 4 Stat Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4 bg-[#0f172a] border-slate-800">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Verified Small Co (10-100)</span>
            <Building className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-2">
            {stats?.verified_small_company_jobs ?? 0}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Boutiques, Studios & Startups</div>
        </Card>

        <Card className="p-4 bg-[#0f172a] border-slate-800">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Indonesia Verified</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-2">
            {stats?.verified_eligible_jobs ?? 0}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Proof of EOR / Global contract</div>
        </Card>

        <Card className="p-4 bg-[#0f172a] border-slate-800">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Active Applications</span>
            <Bookmark className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-2">
            {trackedJobs.length}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">
            {appliedJobs.length} Applied • {interviewJobs.length} Interviewing
          </div>
        </Card>

        <Card className="p-4 bg-[#0f172a] border-slate-800">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Total Tracked Jobs</span>
            <TrendingUp className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-2">
            {stats?.total_jobs ?? 0}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Multi-ATS Public Feeds</div>
        </Card>
      </div>

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* Left Column: Top Curated Job Recommendations */}
        <div className="lg:col-span-8 space-y-4">
          <Card className="border-slate-800 bg-[#0f172a]">
            <CardHeader className="flex flex-row items-center justify-between p-4 pb-3">
              <div>
                <CardTitle className="text-sm font-bold text-white">Top Verified Recommendations</CardTitle>
                <CardDescription className="text-xs text-slate-400">Remote roles with highest verified eligibility proof matching your profile.</CardDescription>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => onNavigateTab('RADAR')}
                className="text-xs text-emerald-400 hover:text-emerald-300 font-semibold gap-1 h-8 px-2"
              >
                <span>View All</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Button>
            </CardHeader>
            <CardContent className="p-4 pt-1 space-y-3">
              {topRecommendations.length === 0 ? (
                <div className="text-center py-10 rounded-lg bg-slate-950/60 border border-slate-800/80 p-6">
                  <p className="text-xs text-slate-400">No active recommendations yet. Run radar sync to discover fresh job openings.</p>
                </div>
              ) : (
                topRecommendations.map((job) => (
                  <div 
                    key={job.id}
                    className="bg-slate-950 border border-slate-800/80 hover:border-slate-700 rounded-xl p-4 transition flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                  >
                    <div className="space-y-1.5 flex-1">
                      <div className="flex items-center gap-2 flex-wrap text-xs">
                        <span className="font-bold text-white text-sm">{job.company_name}</span>
                        <span className="text-slate-600">•</span>
                        <span className="text-slate-400 flex items-center gap-1 text-[11px]">
                          <MapPin className="w-3 h-3 text-slate-500" />
                          {job.location || 'Remote Worldwide'}
                        </span>
                        {job.match_score !== undefined && job.match_score !== null && (
                          <Badge variant="default" className="text-[10px] font-bold">
                            {job.match_score}% Fit
                          </Badge>
                        )}
                        {job.primary_industry && job.primary_industry !== 'unknown' && (
                          <Badge variant="secondary" className="capitalize text-[10px]">
                            {job.primary_industry}
                          </Badge>
                        )}
                      </div>
                      <h3 className="text-sm font-bold text-slate-200">{job.title}</h3>
                      {job.eligibility_quote && (
                        <p className="text-xs text-emerald-300/90 italic line-clamp-1">
                          "{job.eligibility_quote}"
                        </p>
                      )}
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <Button
                        size="sm"
                        variant="primary"
                        onClick={() => onOpenATSStudio(job)}
                        className="gap-1.5"
                      >
                        <FileText className="w-3.5 h-3.5" />
                        <span>ATS CV</span>
                      </Button>
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => onOpenTracker(job)}
                      >
                        Track
                      </Button>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Tracker Pipeline Snapshot & Quick Actions */}
        <div className="lg:col-span-4 space-y-4">
          {/* Tracker Activity Snapshot */}
          <Card className="border-slate-800 bg-[#0f172a]">
            <CardHeader className="flex flex-row items-center justify-between p-4 pb-2 border-b border-slate-800/80">
              <CardTitle className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                <Bookmark className="w-3.5 h-3.5 text-indigo-400" />
                Application Pipeline
              </CardTitle>
              <Button
                variant="link"
                size="sm"
                onClick={() => onNavigateTab('KANBAN')}
                className="text-[11px] text-indigo-400 hover:text-indigo-300 p-0 h-auto"
              >
                Open Board
              </Button>
            </CardHeader>

            <CardContent className="p-4 space-y-2 text-xs">
              <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950 border border-slate-800/80">
                <span className="text-amber-300 flex items-center gap-1.5 font-medium">
                  <Bookmark className="w-3.5 h-3.5" />
                  Wishlist / Saved
                </span>
                <span className="font-bold text-white">{savedJobs.length}</span>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950 border border-slate-800/80">
                <span className="text-blue-300 flex items-center gap-1.5 font-medium">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Applied
                </span>
                <span className="font-bold text-white">{appliedJobs.length}</span>
              </div>

              <div className="flex items-center justify-between p-2.5 rounded-lg bg-slate-950 border border-slate-800/80">
                <span className="text-purple-300 flex items-center gap-1.5 font-medium">
                  <Calendar className="w-3.5 h-3.5" />
                  Interviewing
                </span>
                <span className="font-bold text-white">{interviewJobs.length}</span>
              </div>
            </CardContent>
          </Card>

          {/* Quick System Information Box */}
          <Card className="border-slate-800/80 bg-slate-950 p-4 space-y-2">
            <span className="font-bold text-white flex items-center gap-1.5 text-xs">
              <Clock className="w-3.5 h-3.5 text-emerald-400" />
              Automatic Poller Cycle:
            </span>
            <p className="text-slate-400 leading-relaxed text-[11px]">
              The system automatically pulls new jobs every 5 hours from verified public ATS boards. Only positions with verified EOR/worldwide contract eligibility published within the freshness window are displayed.
            </p>
          </Card>
        </div>

      </div>
    </div>
  )
}

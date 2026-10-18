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
    .slice(0, 4)

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="relative overflow-hidden bg-gradient-to-r from-slate-900 via-[#0f172a] to-slate-900 border border-slate-800 rounded-2xl p-6 sm:p-8 shadow-lg">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold mb-3">
            <ShieldCheck className="w-4 h-4" />
            <span>Strict Verified Worldwide & Small Companies</span>
          </div>
          <h1 className="text-xl sm:text-2xl lg:text-3xl font-extrabold text-white tracking-tight leading-tight">
            Pusat Komando Karir Remote Global
          </h1>
          <p className="text-xs sm:text-sm text-slate-400 mt-2 leading-relaxed">
            Temukan lowongan kerja remote 100% yang menerima kandidat dari Indonesia, kelola progres lamaran dalam Kanban board terstruktur, dan optimasi resume berstandar Harvard/MIT.
          </p>
          <div className="mt-5 flex flex-wrap items-center gap-3">
            <button
              onClick={() => onNavigateTab('RADAR')}
              className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs shadow-md transition flex items-center gap-2"
            >
              <span>Jelajahi Lowongan Terverifikasi</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => onNavigateTab('KANBAN')}
              className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 font-semibold text-xs transition flex items-center gap-2"
            >
              <span>Buka Kanban Pipeline ({trackedJobs.length})</span>
            </button>
          </div>
        </div>
      </div>

      {/* 4 Stat Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-[#0f172a] border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Verified Small Co (10-100)</span>
            <Building className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-2">
            {stats?.verified_small_company_jobs ?? 0}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Boutique, Studios & Startups</div>
        </div>

        <div className="bg-[#0f172a] border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Indonesia Verified</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 mt-2">
            {stats?.verified_eligible_jobs ?? 0}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Bukti kontrak EOR / Global</div>
        </div>

        <div className="bg-[#0f172a] border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Total Lamaran Aktif</span>
            <Bookmark className="w-4 h-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-2">
            {trackedJobs.length}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">
            {appliedJobs.length} Applied • {interviewJobs.length} Interviewing
          </div>
        </div>

        <div className="bg-[#0f172a] border border-slate-800 rounded-xl p-4 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 text-xs">
            <span>Total Peluang Dipantau</span>
            <TrendingUp className="w-4 h-4 text-amber-400" />
          </div>
          <div className="text-2xl font-bold text-white mt-2">
            {stats?.total_jobs ?? 0}
          </div>
          <div className="text-[11px] text-slate-500 mt-1">Multi-ATS Public Feeds</div>
        </div>
      </div>

      {/* Main Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* Left Column: Top Curated Job Recommendations */}
        <div className="lg:col-span-8 space-y-4">
          <div className="flex items-center justify-between bg-[#0f172a] border border-slate-800 p-4 rounded-xl">
            <div>
              <h2 className="text-sm font-bold text-white">Rekomendasi Utama Terverifikasi</h2>
              <p className="text-xs text-slate-400">Peluang kerja remote dengan bukti kelayakan tertinggi untuk profil Anda.</p>
            </div>
            <button
              onClick={() => onNavigateTab('RADAR')}
              className="text-xs text-emerald-400 hover:text-emerald-300 font-semibold flex items-center gap-1"
            >
              <span>Lihat Semua</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-3">
            {topRecommendations.length === 0 ? (
              <div className="text-center py-12 bg-[#0f172a] border border-slate-800 rounded-xl p-6">
                <p className="text-xs text-slate-400">Belum ada rekomendasi aktif. Jalankan sinkronisasi untuk memuat lowongan terbaru.</p>
              </div>
            ) : (
              topRecommendations.map((job) => (
                <div 
                  key={job.id}
                  className="bg-[#0f172a] border border-slate-800 hover:border-slate-700 rounded-xl p-4 sm:p-5 transition flex flex-col sm:flex-row sm:items-center justify-between gap-4"
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
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-600">
                          {job.match_score}% Fit
                        </span>
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
                    <button
                      onClick={() => onOpenATSStudio(job)}
                      className="px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition flex items-center gap-1.5"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      <span>ATS CV</span>
                    </button>
                    <button
                      onClick={() => onOpenTracker(job)}
                      className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-medium transition"
                    >
                      Track
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Column: Tracker Pipeline Snapshot & Quick Actions */}
        <div className="lg:col-span-4 space-y-4">
          {/* Tracker Activity Snapshot */}
          <div className="bg-[#0f172a] border border-slate-800 rounded-xl p-4 space-y-3">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                <Bookmark className="w-3.5 h-3.5 text-indigo-400" />
                Status Pipeline Lamaran
              </h3>
              <button
                onClick={() => onNavigateTab('KANBAN')}
                className="text-[11px] text-indigo-400 hover:underline font-medium"
              >
                Buka Board
              </button>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex items-center justify-between p-2 rounded-lg bg-slate-950 border border-slate-800/80">
                <span className="text-amber-300 flex items-center gap-1.5 font-medium">
                  <Bookmark className="w-3.5 h-3.5" />
                  Wishlist / Saved
                </span>
                <span className="font-bold text-white">{savedJobs.length}</span>
              </div>

              <div className="flex items-center justify-between p-2 rounded-lg bg-slate-950 border border-slate-800/80">
                <span className="text-blue-300 flex items-center gap-1.5 font-medium">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Applied
                </span>
                <span className="font-bold text-white">{appliedJobs.length}</span>
              </div>

              <div className="flex items-center justify-between p-2 rounded-lg bg-slate-950 border border-slate-800/80">
                <span className="text-purple-300 flex items-center gap-1.5 font-medium">
                  <Calendar className="w-3.5 h-3.5" />
                  Interviewing
                </span>
                <span className="font-bold text-white">{interviewJobs.length}</span>
              </div>
            </div>
          </div>

          {/* Quick Guidance Box */}
          <div className="p-4 rounded-xl bg-slate-950 border border-slate-800/80 space-y-2 text-xs">
            <span className="font-bold text-white flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-emerald-400" />
              Siklus Poller Otomatis:
            </span>
            <p className="text-slate-400 leading-relaxed text-[11px]">
              Sistem secara otomatis menarik lowongan baru setiap 5 jam dari 66+ ATS board aktif. Hanya posisi dengan bukti kontrak EOR/Worldwide dan terbit dalam 14 hari terakhir yang ditampilkan.
            </p>
          </div>
        </div>

      </div>
    </div>
  )
}

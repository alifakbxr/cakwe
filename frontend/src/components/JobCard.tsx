import React from 'react'
import { 
  Building, 
  MapPin, 
  DollarSign, 
  ChevronDown, 
  ChevronUp, 
  ExternalLink, 
  Bookmark, 
  Sparkles, 
  EyeOff,
  ShieldCheck,
  Check,
  AlertTriangle
} from 'lucide-react'
import type { Job } from '../types'

interface JobCardProps {
  job: Job
  isExpanded: boolean
  onToggleExpand: () => void
  onOpenTracker: (job: Job) => void
  onOpenATSBuilder: (job: Job) => void
  onOpenDismiss: (job: Job) => void
  getApplicationUrl: (job: Job) => string
}

export const JobCard: React.FC<JobCardProps> = ({
  job,
  isExpanded,
  onToggleExpand,
  onOpenTracker,
  onOpenATSBuilder,
  onOpenDismiss,
  getApplicationUrl
}) => {
  const isClosed = job.lifecycle_status === 'closed'

  return (
    <article className={`rounded-xl border transition-all duration-200 ${
      isClosed 
        ? 'bg-slate-900/30 border-slate-800/60 opacity-70' 
        : 'bg-[#0f172a]/90 border-slate-800 hover:border-slate-700 shadow-sm'
    }`}>
      {/* Primary Card Header */}
      <div className="p-4 sm:p-5">
        <div className="flex flex-col lg:flex-row lg:items-start justify-between gap-4">
          
          {/* Role & Company Metadata */}
          <div className="space-y-2 flex-1">
            <div className="flex flex-wrap items-center gap-2 text-xs">
              <span className="font-semibold text-slate-200 text-sm">
                {job.company_name}
              </span>

              <span className="px-2 py-0.5 rounded-md bg-slate-950 text-slate-400 border border-slate-800 text-[10px] uppercase font-mono tracking-wider">
                {job.source}
              </span>

              {isClosed && (
                <span className="px-2 py-0.5 rounded-md bg-red-950/60 text-red-300 border border-red-800/60 text-[10px] font-bold uppercase">
                  Closed
                </span>
              )}

              <span className="text-slate-600">•</span>

              <span className="text-slate-400 flex items-center gap-1 text-xs">
                <MapPin className="w-3.5 h-3.5 text-slate-500" />
                {job.location || 'Remote Worldwide'}
              </span>

              {/* Company Size Badge */}
              {job.company_size_category === 'small_startup' && (
                <span className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-blue-950/70 text-blue-300 border border-blue-800/50 text-[11px] font-medium">
                  <Building className="w-3 h-3" />
                  Small Team (10–50)
                </span>
              )}
              {job.company_size_category === 'medium_startup' && (
                <span className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-cyan-950/70 text-cyan-300 border border-cyan-800/50 text-[11px] font-medium">
                  <Building className="w-3 h-3" />
                  Scaleup (51–100)
                </span>
              )}
              {job.company_size_category === 'agency_studio' && (
                <span className="flex items-center gap-1 px-2 py-0.5 rounded-md bg-purple-950/70 text-purple-300 border border-purple-800/50 text-[11px] font-medium">
                  <Building className="w-3 h-3" />
                  Digital Studio / Agency
                </span>
              )}

              {/* Match Score */}
              {job.match_score !== undefined && job.match_score !== null && (
                <span className={`px-2 py-0.5 rounded-md text-[11px] font-bold border ${
                  job.match_score >= 80
                    ? 'bg-emerald-950/80 border-emerald-500/80 text-emerald-300'
                    : job.match_score >= 60
                    ? 'bg-amber-950/80 border-amber-500/80 text-amber-300'
                    : 'bg-slate-800 border-slate-700 text-slate-400'
                }`}>
                  {job.match_score}% Candidate Fit
                </span>
              )}

              {job.min_salary && (
                <>
                  <span className="text-slate-600">•</span>
                  <span className="text-xs text-emerald-400 font-medium flex items-center gap-0.5">
                    <DollarSign className="w-3.5 h-3.5" />
                    ${job.min_salary.toLocaleString()} - ${job.max_salary?.toLocaleString()} / mo
                  </span>
                </>
              )}
            </div>

            <h3 className="text-base sm:text-lg font-bold text-white tracking-tight leading-snug">
              {job.title}
            </h3>

            {/* Indonesia Verified Eligibility Quote Card */}
            {job.eligibility_quote && (
              <div className="p-2.5 rounded-lg bg-emerald-950/30 border border-emerald-800/40 text-xs text-emerald-300 flex items-start gap-2 max-w-3xl">
                <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-emerald-200">Verified Remote Evidence: </span>
                  <span className="italic">"{job.eligibility_quote}"</span>
                </div>
              </div>
            )}
          </div>

          {/* Quick Action Buttons */}
          <div className="flex flex-wrap items-center gap-2 lg:self-center shrink-0">
            {/* Tracker status pill */}
            <button
              onClick={() => onOpenTracker(job)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold border transition ${
                job.application_status === 'applied'
                  ? 'bg-emerald-950/60 border-emerald-600 text-emerald-300'
                  : job.application_status === 'interviewing'
                  ? 'bg-purple-950/60 border-purple-600 text-purple-300'
                  : job.application_status === 'saved'
                  ? 'bg-amber-950/60 border-amber-600 text-amber-300'
                  : 'bg-slate-800/80 border-slate-700 text-slate-300 hover:bg-slate-700'
              }`}
            >
              <Bookmark className="w-3.5 h-3.5" />
              {job.application_status === 'applied' ? 'Applied' :
               job.application_status === 'interviewing' ? 'Interview' :
               job.application_status === 'saved' ? 'Saved' : '+ Track'}
            </button>

            {/* ATS Tailor Button */}
            <button
              onClick={() => onOpenATSBuilder(job)}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold transition shadow-sm"
              title="Generate ATS Resume & Tailored Cover Letter"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>ATS Resume Studio</span>
            </button>

            {/* External Direct Apply */}
            <a
              href={getApplicationUrl(job)}
              target="_blank"
              rel="noreferrer"
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold transition"
            >
              <span>Apply</span>
              <ExternalLink className="w-3 h-3" />
            </a>

            {/* Sembunyikan/Dismiss Button */}
            <button
              onClick={() => onOpenDismiss(job)}
              className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-red-400 hover:border-red-900/50 transition"
              title="Hide / Dismiss this job"
            >
              <EyeOff className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* AI Brief Summary (Indonesian) */}
        {job.summary_id && job.summary_id.length > 0 && (
          <div className="mt-3 pt-3 border-t border-slate-800/60">
            <h4 className="text-[11px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">
              Ringkasan Kunci (AI Intelligence)
            </h4>
            <ul className="grid grid-cols-1 md:grid-cols-2 gap-1 text-xs text-slate-300">
              {job.summary_id.map((point, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-emerald-400 font-bold shrink-0">•</span>
                  <span>{point}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Required Skills Chips */}
        {job.skills_required && job.skills_required.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1.5 items-center">
            <span className="text-[11px] text-slate-400 mr-1">Skills:</span>
            {job.skills_required.map((skill, i) => (
              <span key={i} className="px-2 py-0.5 rounded bg-slate-950 text-slate-300 border border-slate-800 text-[11px]">
                {skill}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Accordion Expand / Collapse Button */}
      <button
        onClick={onToggleExpand}
        className="w-full py-2 px-4 bg-slate-950/60 hover:bg-slate-950 border-t border-slate-800/80 rounded-b-xl text-xs font-medium text-slate-400 hover:text-slate-200 flex items-center justify-center gap-1.5 transition"
      >
        {isExpanded ? (
          <>
            <ChevronUp className="w-3.5 h-3.5" />
            <span>Sembunyikan Rincian Tanggung Jawab & Kualifikasi</span>
          </>
        ) : (
          <>
            <ChevronDown className="w-3.5 h-3.5" />
            <span>Lihat Rincian Tanggung Jawab, Kualifikasi & Fit Analisis</span>
          </>
        )}
      </button>

      {/* Expanded Details Section */}
      {isExpanded && (
        <div className="p-5 border-t border-slate-800 bg-slate-950/40 rounded-b-xl space-y-5 text-xs text-slate-300">
          
          {/* Fit Reasons & Gap Analysis */}
          {(job.match_reasons || job.missing_skills) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 rounded-xl bg-slate-900/60 border border-slate-800">
              <div>
                <h5 className="font-bold text-emerald-400 mb-1.5 flex items-center gap-1">
                  <Check className="w-3.5 h-3.5" />
                  Mengapa Cocok untuk Profil Anda:
                </h5>
                <ul className="space-y-1 text-slate-300">
                  {Array.isArray(job.match_reasons) ? job.match_reasons.map((r, i) => (
                    <li key={i} className="flex items-start gap-1.5">
                      <span className="text-emerald-400">•</span>
                      <span>{r}</span>
                    </li>
                  )) : (
                    <li>{job.match_reasons}</li>
                  )}
                </ul>
              </div>

              {job.missing_skills && (
                <div>
                  <h5 className="font-bold text-amber-400 mb-1.5 flex items-center gap-1">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    Potensi Gap / Hal yang Perlu Diperhatikan:
                  </h5>
                  <ul className="space-y-1 text-slate-300">
                    {Array.isArray(job.missing_skills) ? job.missing_skills.map((s, i) => (
                      <li key={i} className="flex items-start gap-1.5">
                        <span className="text-amber-400">•</span>
                        <span>{s}</span>
                      </li>
                    )) : (
                      <li>{job.missing_skills}</li>
                    )}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Responsibilities & Requirements */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h5 className="font-bold text-white mb-2 pb-1 border-b border-slate-800">
                Tanggung Jawab Utama (Terjemahan)
              </h5>
              <ul className="space-y-1.5 text-slate-300">
                {job.translated_responsibilities?.map((item, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-indigo-400 font-bold">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div>
              <h5 className="font-bold text-white mb-2 pb-1 border-b border-slate-800">
                Persyaratan & Kualifikasi (Terjemahan)
              </h5>
              <ul className="space-y-1.5 text-slate-300">
                {job.translated_requirements?.map((item, i) => (
                  <li key={i} className="flex items-start gap-2">
                    <span className="text-emerald-400 font-bold">•</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </article>
  )
}

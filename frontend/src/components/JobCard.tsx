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
import { Card } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'

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
    <Card className={`transition-all duration-200 overflow-hidden ${
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

              <Badge variant="outline" className="text-[10px] uppercase font-mono tracking-wider">
                {job.source}
              </Badge>

              {isClosed && (
                <Badge variant="destructive" className="text-[10px] font-bold uppercase">
                  Closed
                </Badge>
              )}

              <span className="text-slate-600">•</span>

              <span className="text-slate-400 flex items-center gap-1 text-xs">
                <MapPin className="w-3.5 h-3.5 text-slate-500" />
                {job.location || 'Remote Worldwide'}
              </span>

              {/* Company Size Badge */}
              {job.company_size_category === 'small_startup' && (
                <Badge variant="blue" className="gap-1 text-[11px] font-medium">
                  <Building className="w-3 h-3" />
                  Small Team (10–50)
                </Badge>
              )}
              {job.company_size_category === 'medium_startup' && (
                <Badge variant="indigo" className="gap-1 text-[11px] font-medium">
                  <Building className="w-3 h-3" />
                  Scaleup (51–100)
                </Badge>
              )}
              {job.company_size_category === 'agency_studio' && (
                <Badge variant="secondary" className="gap-1 text-[11px] font-medium">
                  <Building className="w-3 h-3" />
                  Digital Studio / Agency
                </Badge>
              )}
              {job.primary_industry && job.primary_industry !== 'unknown' && (
                <Badge variant="secondary" className="text-[11px] font-medium capitalize">
                  {job.primary_industry}
                </Badge>
              )}

              {/* Match Score */}
              {job.match_score !== undefined && job.match_score !== null && (
                <Badge
                  variant={job.match_score >= 80 ? "default" : job.match_score >= 60 ? "amber" : "secondary"}
                  className="text-[11px] font-bold"
                >
                  {job.match_score}% Candidate Fit
                </Badge>
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

          {/* Quick Action Buttons with shadcn Button */}
          <div className="flex flex-wrap items-center gap-2 lg:self-center shrink-0">
            {/* Tracker status button */}
            <Button
              size="sm"
              variant={
                job.application_status === 'applied' ? 'default' :
                job.application_status === 'interviewing' ? 'primary' :
                job.application_status === 'saved' ? 'outline' : 'secondary'
              }
              onClick={() => onOpenTracker(job)}
              className="gap-1.5"
            >
              <Bookmark className="w-3.5 h-3.5" />
              <span>
                {job.application_status === 'applied' ? 'Applied' :
                 job.application_status === 'interviewing' ? 'Interview' :
                 job.application_status === 'saved' ? 'Saved' : '+ Track'}
              </span>
            </Button>

            {/* ATS Tailor Button */}
            <Button
              size="sm"
              variant="primary"
              onClick={() => onOpenATSBuilder(job)}
              className="gap-1.5 shadow-sm"
              title="Generate ATS Resume & Tailored Cover Letter"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>ATS Resume Studio</span>
            </Button>

            {/* External Direct Apply */}
            <Button
              asChild
              size="sm"
              variant="default"
              className="gap-1.5"
            >
              <a
                href={getApplicationUrl(job)}
                target="_blank"
                rel="noreferrer"
              >
                <span>Apply</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </Button>

            {/* Sembunyikan/Dismiss Button */}
            <Button
              size="icon"
              variant="outline"
              onClick={() => onOpenDismiss(job)}
              className="text-slate-400 hover:text-red-400 hover:border-red-900/50"
              title="Hide / Dismiss this job"
            >
              <EyeOff className="w-3.5 h-3.5" />
            </Button>
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
              <Badge key={i} variant="outline" className="text-[11px] font-normal bg-slate-950/80">
                {skill}
              </Badge>
            ))}
          </div>
        )}
      </div>

      {/* Accordion Expand / Collapse Button */}
      <button
        onClick={onToggleExpand}
        className="w-full py-2 px-4 bg-slate-950/60 hover:bg-slate-950 border-t border-slate-800/80 text-xs font-medium text-slate-400 hover:text-slate-200 flex items-center justify-center gap-1.5 transition cursor-pointer select-none"
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
        <div className="p-5 border-t border-slate-800 bg-slate-950/40 space-y-5 text-xs text-slate-300">
          
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
    </Card>
  )
}

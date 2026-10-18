import React from 'react'
import { 
  Bookmark, 
  Sparkles, 
  ExternalLink, 
  Clock 
} from 'lucide-react'
import type { Job } from '../types'

interface KanbanBoardProps {
  jobs: Job[]
  onUpdateStatus: (jobId: string, newStatus: string) => void
  onOpenTrackerModal: (job: Job) => void
  onOpenATSBuilder: (job: Job) => void
  getApplicationUrl: (job: Job) => string
}

export const KanbanBoard: React.FC<KanbanBoardProps> = ({
  jobs,
  onUpdateStatus,
  onOpenTrackerModal,
  onOpenATSBuilder,
  getApplicationUrl
}) => {
  const [draggedJobId, setDraggedJobId] = React.useState<string | null>(null)
  const [dragOverCol, setDragOverCol] = React.useState<string | null>(null)

  const columns = [
    { id: 'saved', label: 'Wishlist / Saved', color: 'border-amber-500/40 text-amber-300 bg-amber-500/10' },
    { id: 'applied', label: 'Applied', color: 'border-blue-500/40 text-blue-300 bg-blue-500/10' },
    { id: 'interviewing', label: 'Interviewing', color: 'border-purple-500/40 text-purple-300 bg-purple-500/10' },
    { id: 'assessment', label: 'Assessment', color: 'border-cyan-500/40 text-cyan-300 bg-cyan-500/10' },
    { id: 'offer', label: 'Offer Received', color: 'border-emerald-500/40 text-emerald-300 bg-emerald-500/10' },
    { id: 'rejected', label: 'Rejected', color: 'border-slate-700 text-slate-400 bg-slate-800/40' },
  ]

  const handleDragStart = (e: React.DragEvent, id: string) => {
    e.dataTransfer.setData('text/plain', id)
    setDraggedJobId(id)
  }

  const handleDragOver = (e: React.DragEvent, colId: string) => {
    e.preventDefault()
    setDragOverCol(colId)
  }

  const handleDrop = (e: React.DragEvent, colId: string) => {
    e.preventDefault()
    const id = e.dataTransfer.getData('text/plain') || draggedJobId
    if (id) {
      onUpdateStatus(id, colId)
    }
    setDraggedJobId(null)
    setDragOverCol(null)
  }

  return (
    <div className="w-full">
      {/* Kanban Header Summary */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6 bg-[#0f172a] border border-slate-800 p-4 rounded-xl">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <span>Job Tracker Kanban Board</span>
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Tarik kartu (drag & drop) atau gunakan menu dropdown status di setiap kartu untuk memperbarui tahapan lamaran kerja.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs font-medium text-slate-400 bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-800 shrink-0">
          <span>Total Aktif:</span>
          <span className="text-emerald-400 font-bold">{jobs.filter(j => j.application_status).length} Lowongan Terlacak</span>
        </div>
      </div>

      {/* Columns Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 items-start">
        {columns.map((col) => {
          const colJobs = jobs.filter(j => (j.application_status || 'saved') === col.id)
          const isOver = dragOverCol === col.id

          return (
            <div
              key={col.id}
              onDragOver={(e) => handleDragOver(e, col.id)}
              onDragLeave={() => setDragOverCol(null)}
              onDrop={(e) => handleDrop(e, col.id)}
              className={`flex flex-col rounded-xl bg-[#0c1220]/90 border transition-all duration-200 min-h-[500px] ${
                isOver ? 'border-emerald-500 bg-emerald-950/20 ring-2 ring-emerald-500/20' : 'border-slate-800/80'
              }`}
            >
              {/* Column Title Bar */}
              <div className="p-3 border-b border-slate-800 flex items-center justify-between">
                <span className={`text-xs font-bold px-2 py-0.5 rounded-md border ${col.color}`}>
                  {col.label}
                </span>
                <span className="text-xs font-mono font-bold text-slate-400 bg-slate-900 px-2 py-0.5 rounded-full border border-slate-800">
                  {colJobs.length}
                </span>
              </div>

              {/* Cards List in Column */}
              <div className="p-2 space-y-2.5 flex-1 overflow-y-auto">
                {colJobs.length === 0 ? (
                  <div className="text-center py-10 px-2 text-[11px] text-slate-500 border border-dashed border-slate-800/80 rounded-lg">
                    Belum ada kartu
                  </div>
                ) : (
                  colJobs.map((job) => (
                    <div
                      key={job.id}
                      draggable
                      onDragStart={(e) => handleDragStart(e, job.id)}
                      className={`p-3 rounded-lg bg-[#141e33] border border-slate-700/60 hover:border-indigo-500/80 transition-all cursor-grab active:cursor-grabbing shadow-sm hover:shadow-md ${
                        draggedJobId === job.id ? 'opacity-40' : 'opacity-100'
                      }`}
                    >
                      {/* Company & Fit */}
                      <div className="flex items-center justify-between gap-1 mb-1.5 text-[11px]">
                        <span className="font-semibold text-slate-300 truncate max-w-[120px]">
                          {job.company_name}
                        </span>
                        {job.match_score !== undefined && job.match_score !== null && (
                          <span className="px-1.5 py-0.2 rounded bg-emerald-950/80 text-emerald-300 border border-emerald-500/50 text-[10px] font-bold">
                            {job.match_score}%
                          </span>
                        )}
                      </div>

                      {/* Job Title */}
                      <h4 className="text-xs font-bold text-white line-clamp-2 leading-snug mb-2">
                        {job.title}
                      </h4>

                      {/* Metadata Chips */}
                      <div className="flex flex-wrap gap-1 mb-2.5 text-[10px]">
                        <span className="px-1.5 py-0.5 rounded bg-slate-950 text-slate-400 border border-slate-800">
                          {job.location || 'Remote'}
                        </span>
                        {job.company_size_category === 'small_startup' && (
                          <span className="px-1.5 py-0.5 rounded bg-blue-950/70 text-blue-300 border border-blue-800/50">
                            10-50 staff
                          </span>
                        )}
                        {job.company_size_category === 'agency_studio' && (
                          <span className="px-1.5 py-0.5 rounded bg-purple-950/70 text-purple-300 border border-purple-800/50">
                            Agency
                          </span>
                        )}
                      </div>

                      {/* Applied Notes preview */}
                      {(job.applied_date || job.application_notes) && (
                        <div className="mb-2.5 p-2 rounded bg-slate-950 border border-slate-800 text-[10px] text-slate-400 space-y-1">
                          {job.applied_date && (
                            <div className="flex items-center gap-1 text-slate-300">
                              <Clock className="w-3 h-3 text-indigo-400" />
                              <span>{job.applied_date}</span>
                            </div>
                          )}
                          {job.application_notes && (
                            <p className="line-clamp-2 italic text-slate-400">
                              "{job.application_notes}"
                            </p>
                          )}
                        </div>
                      )}

                      {/* Action Controls & Accessible Dropdown */}
                      <div className="flex items-center justify-between pt-2 border-t border-slate-800/80 text-[11px]">
                        <select
                          value={job.application_status || 'saved'}
                          onChange={(e) => onUpdateStatus(job.id, e.target.value)}
                          className="bg-slate-950 border border-slate-800 rounded px-1.5 py-0.5 text-[10px] text-slate-300 focus:outline-none focus:border-indigo-500"
                        >
                          <option value="saved">Wishlist</option>
                          <option value="applied">Applied</option>
                          <option value="interviewing">Interview</option>
                          <option value="assessment">Assessment</option>
                          <option value="offer">Offer</option>
                          <option value="rejected">Rejected</option>
                        </select>

                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => onOpenTrackerModal(job)}
                            className="p-1 rounded text-slate-400 hover:text-white hover:bg-slate-800 transition"
                            title="Edit notes & details"
                          >
                            <Bookmark className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => onOpenATSBuilder(job)}
                            className="p-1 rounded bg-indigo-950/60 border border-indigo-700/60 text-indigo-300 hover:bg-indigo-900 transition"
                            title="Generate ATS Resume"
                          >
                            <Sparkles className="w-3.5 h-3.5" />
                          </button>
                          <a
                            href={getApplicationUrl(job)}
                            target="_blank"
                            rel="noreferrer"
                            className="p-1 rounded bg-slate-800 text-slate-300 hover:text-white transition"
                            title="Open vacancy link"
                          >
                            <ExternalLink className="w-3.5 h-3.5" />
                          </a>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

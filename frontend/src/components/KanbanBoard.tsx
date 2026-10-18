import React from 'react'
import { 
  Bookmark, 
  Sparkles, 
  ExternalLink, 
  Clock,
  Kanban as KanbanIcon
} from 'lucide-react'
import type { Job } from '../types'
import { Card } from './ui/card'
import { Button } from './ui/button'
import { Badge } from './ui/badge'

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
    { id: 'saved', label: 'Wishlist / Saved', badgeVariant: 'amber' as const },
    { id: 'applied', label: 'Applied', badgeVariant: 'blue' as const },
    { id: 'interviewing', label: 'Interviewing', badgeVariant: 'indigo' as const },
    { id: 'assessment', label: 'Assessment', badgeVariant: 'indigo' as const },
    { id: 'offer', label: 'Offer Received', badgeVariant: 'default' as const },
    { id: 'rejected', label: 'Rejected', badgeVariant: 'secondary' as const },
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
    <div className="w-full space-y-6">
      {/* Kanban Header Summary */}
      <Card className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 bg-[#0f172a] border-slate-800">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <KanbanIcon className="w-4 h-4 text-emerald-400" />
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
      </Card>

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
                <Badge variant={col.badgeVariant} className="text-xs font-bold">
                  {col.label}
                </Badge>
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
                    <Card
                      key={job.id}
                      draggable
                      onDragStart={(e) => handleDragStart(e, job.id)}
                      className={`p-3 bg-[#141e33] border-slate-700/60 hover:border-indigo-500/80 transition-all cursor-grab active:cursor-grabbing shadow-sm hover:shadow-md ${
                        draggedJobId === job.id ? 'opacity-40' : 'opacity-100'
                      }`}
                    >
                      {/* Company & Fit */}
                      <div className="flex items-center justify-between gap-1 mb-1.5 text-[11px]">
                        <span className="font-semibold text-slate-300 truncate max-w-[120px]">
                          {job.company_name}
                        </span>
                        {job.match_score !== undefined && job.match_score !== null && (
                          <Badge variant="default" className="text-[10px] font-bold px-1.5 py-0">
                            {job.match_score}%
                          </Badge>
                        )}
                      </div>

                      {/* Job Title */}
                      <h4 className="text-xs font-bold text-white line-clamp-2 leading-snug mb-2">
                        {job.title}
                      </h4>

                      {/* Metadata Chips */}
                      <div className="flex flex-wrap gap-1 mb-2.5 text-[10px]">
                        <Badge variant="outline" className="text-[10px] font-normal">
                          {job.location || 'Remote'}
                        </Badge>
                        {job.company_size_category === 'small_startup' && (
                          <Badge variant="blue" className="text-[10px] font-normal">
                            10-50 staff
                          </Badge>
                        )}
                        {job.company_size_category === 'agency_studio' && (
                          <Badge variant="secondary" className="text-[10px] font-normal">
                            Agency
                          </Badge>
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
                          className="bg-slate-950 border border-slate-800 rounded px-1.5 py-0.5 text-[10px] text-slate-300 focus:outline-none focus:border-indigo-500 cursor-pointer"
                        >
                          <option value="saved">Wishlist</option>
                          <option value="applied">Applied</option>
                          <option value="interviewing">Interview</option>
                          <option value="assessment">Assessment</option>
                          <option value="offer">Offer</option>
                          <option value="rejected">Rejected</option>
                        </select>

                        <div className="flex items-center gap-1">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => onOpenTrackerModal(job)}
                            className="h-6 w-6 text-slate-400 hover:text-white"
                            title="Edit notes & details"
                          >
                            <Bookmark className="w-3 h-3" />
                          </Button>
                          <Button
                            variant="primary"
                            size="icon"
                            onClick={() => onOpenATSBuilder(job)}
                            className="h-6 w-6 bg-indigo-950/60 border border-indigo-700/60 text-indigo-300 hover:bg-indigo-900"
                            title="Generate ATS Resume"
                          >
                            <Sparkles className="w-3 h-3" />
                          </Button>
                          <Button
                            asChild
                            variant="secondary"
                            size="icon"
                            className="h-6 w-6 text-slate-300 hover:text-white"
                            title="Open vacancy link"
                          >
                            <a
                              href={getApplicationUrl(job)}
                              target="_blank"
                              rel="noreferrer"
                            >
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          </Button>
                        </div>
                      </div>
                    </Card>
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

import React from 'react'
import { EyeOff, X } from 'lucide-react'
import type { Job } from '../types'
import { Card } from './ui/card'
import { Button } from './ui/button'

interface DismissModalProps {
  job: Job
  onClose: () => void
  dismissReason: string
  setDismissReason: (reason: string) => void
  onDismiss: () => void
}

export const DismissModal: React.FC<DismissModalProps> = ({
  job,
  onClose,
  dismissReason,
  setDismissReason,
  onDismiss
}) => {
  const reasons = [
    { id: 'not_remote', label: 'Not Truly Remote / Restricted to Other Regions' },
    { id: 'wrong_seniority', label: 'Seniority Level Too High / Low (> 4-5 yrs or Lead/Manager)' },
    { id: 'missing_skills', label: 'Tech Stack Gap Too Wide (.NET/Java/C++)' },
    { id: 'company_too_large', label: 'Large Enterprise (Not a Small Company / Studio)' },
    { id: 'salary_too_low', label: 'Compensation Out of Range' },
    { id: 'job_already_closed', label: 'Role Already Closed / Expired' },
    { id: 'other', label: 'Other Reason' },
  ]

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in-0">
      <Card className="bg-[#0f172a] border-slate-800 w-full max-w-md p-6 shadow-2xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
              <EyeOff className="w-4 h-4 text-red-400" />
              Dismiss Job
            </h3>
            <p className="text-xs text-slate-400 mt-0.5 line-clamp-1">
              {job.title} — {job.company_name}
            </p>
          </div>
          <Button 
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="text-slate-400 hover:text-white"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>

        <div className="space-y-3">
          <label className="text-xs font-medium text-slate-300">
            Select why this job is not a fit for your profile:
          </label>
          <div className="space-y-2">
            {reasons.map((item) => (
              <label 
                key={item.id}
                className={`flex items-center gap-2.5 p-2.5 rounded-lg border text-xs cursor-pointer transition select-none ${
                  dismissReason === item.id 
                    ? 'bg-red-950/40 border-red-800 text-white font-medium' 
                    : 'bg-slate-950 border-slate-800/80 text-slate-400 hover:border-slate-700'
                }`}
              >
                <input 
                  type="radio" 
                  name="dismiss_reason" 
                  value={item.id}
                  checked={dismissReason === item.id}
                  onChange={() => setDismissReason(item.id)}
                  className="accent-red-500"
                />
                <span>{item.label}</span>
              </label>
            ))}
          </div>
        </div>

        <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
          <Button
            variant="outline"
            size="sm"
            onClick={onClose}
          >
            Cancel
          </Button>
          <Button
            variant="destructive"
            size="sm"
            onClick={onDismiss}
          >
            Dismiss & Save Feedback
          </Button>
        </div>
      </Card>
    </div>
  )
}

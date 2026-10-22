import React from 'react'
import { Bookmark, X } from 'lucide-react'
import type { Job } from '../types'
import { Button } from './ui/button'
import { Card } from './ui/card'
import { Input } from './ui/input'

interface TrackerModalProps {
  job: Job
  onClose: () => void
  trackingForm: {
    status: string
    applied_date: string
    notes: string
    follow_up_date: string
  }
  setTrackingForm: React.Dispatch<React.SetStateAction<{
    status: string
    applied_date: string
    notes: string
    follow_up_date: string
  }>>
  onSave: () => void
}

export const TrackerModal: React.FC<TrackerModalProps> = ({
  job,
  onClose,
  trackingForm,
  setTrackingForm,
  onSave
}) => {
  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4 animate-in fade-in-0">
      <Card className="bg-[#0f172a] border-slate-800 w-full max-w-md p-6 shadow-2xl">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-4">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Bookmark className="w-4 h-4 text-indigo-400" />
              Manage Application Status
            </h3>
            <p className="text-xs text-slate-400 mt-0.5 truncate max-w-xs">{job.title}</p>
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

        <div className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-300 font-semibold mb-1">Application Stage</label>
            <select
              value={trackingForm.status}
              onChange={(e) => setTrackingForm({...trackingForm, status: e.target.value})}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-xs text-white focus:outline-none focus:border-indigo-500 cursor-pointer"
            >
              <option value="saved">⭐ Saved / Wishlist</option>
              <option value="applied">📝 Applied</option>
              <option value="interviewing">🎯 Interviewing</option>
              <option value="assessment">💻 Technical Assessment</option>
              <option value="offer">🎉 Offer Received</option>
              <option value="rejected">❌ Rejected</option>
              <option value="withdrawn">⛔ Withdrawn</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1">Applied Date</label>
            <Input
              type="date"
              value={trackingForm.applied_date}
              onChange={(e) => setTrackingForm({...trackingForm, applied_date: e.target.value})}
              className="w-full"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1">Private Notes</label>
            <textarea
              rows={4}
              value={trackingForm.notes}
              onChange={(e) => setTrackingForm({...trackingForm, notes: e.target.value})}
              placeholder="Stage notes, recruiter contact, salary expectations..."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500"
            />
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
              variant="primary"
              size="sm"
              onClick={onSave}
            >
              Save Status
            </Button>
          </div>
        </div>
      </Card>
    </div>
  )
}

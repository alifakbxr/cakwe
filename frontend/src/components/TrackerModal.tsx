import React from 'react'
import { Bookmark, X } from 'lucide-react'
import type { Job } from '../types'

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
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#0f172a] border border-slate-800 rounded-xl w-full max-w-md p-6 shadow-2xl">
        <div className="flex items-center justify-between pb-4 border-b border-slate-800 mb-4">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <Bookmark className="w-4 h-4 text-indigo-400" />
              Kelola Status Lamaran
            </h3>
            <p className="text-xs text-slate-400 mt-0.5 truncate max-w-xs">{job.title}</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="space-y-4 text-xs">
          <div>
            <label className="block text-slate-300 font-semibold mb-1">Tahap Progres</label>
            <select
              value={trackingForm.status}
              onChange={(e) => setTrackingForm({...trackingForm, status: e.target.value})}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white focus:outline-none focus:border-indigo-500"
            >
              <option value="saved">⭐ Tersimpan (Saved / Wishlist)</option>
              <option value="applied">📝 Sudah Dilamar (Applied)</option>
              <option value="interviewing">🎯 Proses Interview</option>
              <option value="assessment">💻 Technical Assessment</option>
              <option value="offer">🎉 Mendapat Penawaran (Offer)</option>
              <option value="rejected">❌ Belum Berhasil (Rejected)</option>
              <option value="withdrawn">⛔ Ditarik (Withdrawn)</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1">Tanggal Melamar</label>
            <input
              type="date"
              value={trackingForm.applied_date}
              onChange={(e) => setTrackingForm({...trackingForm, applied_date: e.target.value})}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-semibold mb-1">Catatan Pribadi</label>
            <textarea
              rows={4}
              value={trackingForm.notes}
              onChange={(e) => setTrackingForm({...trackingForm, notes: e.target.value})}
              placeholder="Catatan tahapan, kontak recruiter, ekspektasi salary..."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2 text-white placeholder-slate-600 focus:outline-none focus:border-indigo-500"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
            <button
              onClick={onClose}
              className="px-3.5 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium transition"
            >
              Batal
            </button>
            <button
              onClick={onSave}
              className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition"
            >
              Simpan Status
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

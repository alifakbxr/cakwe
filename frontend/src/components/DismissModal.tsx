import React from 'react'
import { EyeOff, X } from 'lucide-react'
import type { Job } from '../types'

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
    { id: 'not_remote', label: 'Bukan Remote Sebenarnya / Dibatasi Region Lain' },
    { id: 'wrong_seniority', label: 'Seniority Terlalu Tinggi / Rendah (> 4-5 thn atau Manager)' },
    { id: 'missing_skills', label: 'Gap Teknologi Terlalu Jauh (.NET/Java/C++)' },
    { id: 'company_too_large', label: 'Korporasi Besar (Bukan Small Company / Studio)' },
    { id: 'salary_too_low', label: 'Kompensasi Tidak Sesuai' },
    { id: 'job_already_closed', label: 'Lowongan Sudah Tutup / Expired' },
    { id: 'other', label: 'Lainnya' },
  ]

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-[#0f172a] border border-slate-800 rounded-xl w-full max-w-md p-6 shadow-2xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-1.5">
              <EyeOff className="w-4 h-4 text-red-400" />
              Sembunyikan Lowongan
            </h3>
            <p className="text-xs text-slate-400 mt-0.5 line-clamp-1">
              {job.title} — {job.company_name}
            </p>
          </div>
          <button 
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded-lg"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="space-y-3">
          <label className="text-xs font-medium text-slate-300">
            Pilih alasan lowongan ini tidak cocok untuk profil Anda:
          </label>
          <div className="space-y-2">
            {reasons.map((item) => (
              <label 
                key={item.id}
                className={`flex items-center gap-2.5 p-2.5 rounded-lg border text-xs cursor-pointer transition ${
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
          <button
            onClick={onClose}
            className="px-3.5 py-1.5 rounded-lg text-xs font-medium text-slate-400 hover:text-white transition"
          >
            Batal
          </button>
          <button
            onClick={onDismiss}
            className="px-4 py-1.5 rounded-lg text-xs font-semibold bg-red-600 hover:bg-red-500 text-white transition shadow-sm"
          >
            Sembunyikan & Simpan Feedback
          </button>
        </div>
      </div>
    </div>
  )
}

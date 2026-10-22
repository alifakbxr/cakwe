import React, { useRef, useState } from 'react'
import { 
  Sparkles, 
  Upload, 
  FileText, 
  Download, 
  Save, 
  Copy, 
  Check, 
  RefreshCw, 
  X,
  Layers,
  ShieldCheck
} from 'lucide-react'
import type { Job, OptimizedResumeResult, ContactInfo, ResumeTemplate, ATSValidationReport } from '../types'

interface ATSStudioModalProps {
  job: Job
  onClose: () => void
  builderTab: 'MODE_A' | 'MODE_B' | 'HISTORY'
  setBuilderTab: (tab: 'MODE_A' | 'MODE_B' | 'HISTORY') => void
  documentView: 'RESUME' | 'COVER_LETTER'
  setDocumentView: (view: 'RESUME' | 'COVER_LETTER') => void
  
  // Mode A
  rawResumeText: string
  setRawResumeText: (text: string) => void
  uploadFileName: string
  isUploading: boolean
  onFileUpload: (e: React.ChangeEvent<HTMLInputElement>) => void
  onOptimizeModeA: () => void

  // Mode B
  profileContact: ContactInfo
  setProfileContact: (contact: ContactInfo) => void
  backgroundStory: string
  setBackgroundStory: (story: string) => void
  skillsInput: string
  setSkillsInput: (skills: string) => void
  onGenerateModeB: () => void

  // History & Result
  savedHistory: any[]
  isProcessing: boolean
  optimizedResult: OptimizedResumeResult | null
  setOptimizedResult: React.Dispatch<React.SetStateAction<OptimizedResumeResult | null>>
  editableCoverLetter: string
  setEditableCoverLetter: (letter: string) => void
  copiedLetter: boolean
  onCopyCoverLetter: () => void
  onSaveVersion: () => void
  onExportDocx: (template?: ResumeTemplate) => void
  onExportPdf: (template?: ResumeTemplate) => void
  onExportCoverLetterDocx: () => void
  onExportCoverLetterPdf: () => void
  onRegenerateCoverLetter: () => void
  isRegeneratingLetter: boolean
}

export const ATSStudioModal: React.FC<ATSStudioModalProps> = ({
  job,
  onClose,
  builderTab,
  setBuilderTab,
  documentView,
  setDocumentView,
  rawResumeText,
  setRawResumeText,
  uploadFileName,
  isUploading,
  onFileUpload,
  onOptimizeModeA,
  profileContact,
  setProfileContact,
  backgroundStory,
  setBackgroundStory,
  skillsInput,
  setSkillsInput,
  onGenerateModeB,
  savedHistory,
  isProcessing,
  optimizedResult,
  setOptimizedResult,
  editableCoverLetter,
  setEditableCoverLetter,
  copiedLetter,
  onCopyCoverLetter,
  onSaveVersion,
  onExportDocx,
  onExportPdf,
  onExportCoverLetterDocx,
  onExportCoverLetterPdf,
  onRegenerateCoverLetter,
  isRegeneratingLetter,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [selectedTemplate, setSelectedTemplate] = useState<ResumeTemplate>('HARVARD')
  const [validationReport, setValidationReport] = useState<ATSValidationReport | null>(null)
  const [isValidating, setIsValidating] = useState(false)

  // Run instant local ATS validation audit against the CV structure
  const runATSValidation = async () => {
    if (!optimizedResult) return
    try {
      setIsValidating(true)
      const res = await fetch('/api/resume/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(optimizedResult.resume)
      })
      if (res.ok) {
        const data = await res.json()
        setValidationReport(data)
      }
    } catch (err) {
      console.error('Validation failed', err)
    } finally {
      setIsValidating(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex flex-col p-3 sm:p-6 overflow-hidden">
      {/* Studio Header */}
      <div className="bg-[#0f172a] border border-slate-800 rounded-xl px-5 py-3.5 flex flex-wrap items-center justify-between gap-3 mb-4 shadow-xl print:hidden">
        <div>
          <div className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            <h3 className="text-base font-bold text-white">
              ATS Resume & Cover Letter Studio
            </h3>
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Target Position: <span className="text-white font-semibold">{job.title}</span> at <span className="text-emerald-400">{job.company_name}</span>
          </p>
        </div>

        <div className="flex items-center gap-3">
          {/* Studio Workflow Tabs */}
          <div className="flex bg-slate-950 p-1 rounded-lg border border-slate-800 text-xs font-medium">
            <button
              onClick={() => setBuilderTab('MODE_A')}
              className={`px-3 py-1.5 rounded-md transition ${builderTab === 'MODE_A' ? 'bg-indigo-600 text-white font-semibold' : 'text-slate-400 hover:text-white'}`}
            >
              Mode A: Upload CV
            </button>
            <button
              onClick={() => setBuilderTab('MODE_B')}
              className={`px-3 py-1.5 rounded-md transition ${builderTab === 'MODE_B' ? 'bg-indigo-600 text-white font-semibold' : 'text-slate-400 hover:text-white'}`}
            >
              Mode B: Form Builder
            </button>
            <button
              onClick={() => setBuilderTab('HISTORY')}
              className={`px-3 py-1.5 rounded-md transition ${builderTab === 'HISTORY' ? 'bg-indigo-600 text-white font-semibold' : 'text-slate-400 hover:text-white'}`}
            >
              History ({savedHistory.length})
            </button>
          </div>

          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white p-2 rounded-lg bg-slate-800/80 hover:bg-slate-800 transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Studio Body */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-5 overflow-hidden">
        
        {/* Left Side: Builder Controls */}
        <div className="lg:col-span-5 bg-[#0f172a] border border-slate-800 rounded-xl p-4 sm:p-5 overflow-y-auto space-y-4 print:hidden">
          {builderTab === 'MODE_A' && (
            <div className="space-y-4">
              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2">
                  <Upload className="w-3.5 h-3.5 text-indigo-400" />
                  1. Upload Resume File (PDF/DOCX/TXT)
                </h4>
                <div 
                  onClick={() => fileInputRef.current?.click()}
                  className="mt-2 border-2 border-dashed border-slate-700 hover:border-indigo-500 rounded-xl p-5 text-center cursor-pointer bg-slate-950/60 transition group"
                >
                  <input 
                    type="file" 
                    ref={fileInputRef} 
                    onChange={onFileUpload} 
                    accept=".pdf,.docx,.txt" 
                    className="hidden" 
                  />
                  <Upload className={`w-7 h-7 mx-auto mb-2 transition ${isUploading ? 'animate-bounce text-indigo-400' : 'text-slate-500 group-hover:text-indigo-400'}`} />
                  <p className="text-xs font-medium text-slate-300">
                    {isUploading ? 'Extracting document text...' : uploadFileName ? uploadFileName : 'Click to select PDF / DOCX file'}
                  </p>
                  <p className="text-[11px] text-slate-500 mt-1">
                    Document is processed in-memory and never permanently stored on external servers.
                  </p>
                </div>
              </div>

              <div>
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-2 mb-2">
                  <FileText className="w-3.5 h-3.5 text-indigo-400" />
                  2. Review / Edit CV Text
                </h4>
                <textarea 
                  rows={10}
                  value={rawResumeText}
                  onChange={(e) => setRawResumeText(e.target.value)}
                  placeholder="Your resume text will appear here. You can also type or edit directly..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-indigo-500 font-mono"
                />
              </div>

              <button
                onClick={onOptimizeModeA}
                disabled={isProcessing || !rawResumeText.trim()}
                className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition shadow-lg disabled:opacity-50 flex items-center justify-center gap-2"
              >
                <Sparkles className={`w-4 h-4 ${isProcessing ? 'animate-spin' : ''}`} />
                {isProcessing ? 'AI is optimizing your CV...' : 'Optimize CV to ATS Harvard Standard'}
              </button>
            </div>
          )}

          {builderTab === 'MODE_B' && (
            <div className="space-y-3.5">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Complete Your Profile
              </h4>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-semibold text-slate-400 block mb-1">Full Name *</label>
                  <input 
                    type="text" 
                    value={profileContact.full_name}
                    onChange={(e) => setProfileContact({...profileContact, full_name: e.target.value})}
                    placeholder="Alif Akbar"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-semibold text-slate-400 block mb-1">Email *</label>
                  <input 
                    type="email" 
                    value={profileContact.email}
                    onChange={(e) => setProfileContact({...profileContact, email: e.target.value})}
                    placeholder="developer@example.com"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-semibold text-slate-400 block mb-1">WhatsApp / Phone Number</label>
                  <input 
                    type="text" 
                    value={profileContact.phone}
                    onChange={(e) => setProfileContact({...profileContact, phone: e.target.value})}
                    placeholder="+62 812-3456-7890"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-semibold text-slate-400 block mb-1">Location / City</label>
                  <input 
                    type="text" 
                    value={profileContact.location}
                    onChange={(e) => setProfileContact({...profileContact, location: e.target.value})}
                    placeholder="Jakarta, Indonesia"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white"
                  />
                </div>
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-400 block mb-1">Technical Skills (comma-separated)</label>
                <input 
                  type="text" 
                  value={skillsInput}
                  onChange={(e) => setSkillsInput(e.target.value)}
                  placeholder="PHP, Laravel, Vue.js, Go, TypeScript, PostgreSQL, Docker"
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-[11px] font-semibold text-slate-400 block mb-1">LinkedIn Profile</label>
                  <input 
                    type="text" 
                    value={profileContact.linkedin_url}
                    onChange={(e) => setProfileContact({...profileContact, linkedin_url: e.target.value})}
                    placeholder="https://linkedin.com/in/username"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white"
                  />
                </div>
                <div>
                  <label className="text-[11px] font-semibold text-slate-400 block mb-1">GitHub / Portfolio</label>
                  <input 
                    type="text" 
                    value={profileContact.github_url}
                    onChange={(e) => setProfileContact({...profileContact, github_url: e.target.value})}
                    placeholder="https://github.com/username"
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-white"
                  />
                </div>
              </div>

              <div>
                <label className="text-[11px] font-semibold text-slate-400 block mb-1">Experience & Project Background</label>
                <textarea 
                  rows={6}
                  value={backgroundStory}
                  onChange={(e) => setBackgroundStory(e.target.value)}
                  placeholder="Describe real projects you've built, frameworks used, challenges solved, and their impact..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg p-2.5 text-xs text-white focus:outline-none focus:border-indigo-500"
                />
              </div>

              <button
                onClick={onGenerateModeB}
                disabled={isProcessing || !profileContact.full_name || !profileContact.email}
                className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-xs transition disabled:opacity-50 flex items-center justify-center gap-2"
              >
                <Sparkles className={`w-4 h-4 ${isProcessing ? 'animate-spin' : ''}`} />
                {isProcessing ? 'Building Documents...' : 'Generate Resume & Cover Letter'}
              </button>
            </div>
          )}

          {builderTab === 'HISTORY' && (
            <div className="space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-300">
                Saved Versions
              </h4>
              {savedHistory.length === 0 ? (
                <p className="text-xs text-slate-500 italic py-4">No saved versions for this job yet.</p>
              ) : (
                savedHistory.map((item) => (
                  <div
                    key={item.id}
                    onClick={() => {
                      setOptimizedResult({
                        resume: item.resume_data,
                        analysis: item.analysis_data,
                        cover_letter: item.cover_letter,
                      })
                      setEditableCoverLetter(item.cover_letter || '')
                    }}
                    className="bg-slate-950 border border-slate-800 hover:border-indigo-500 rounded-xl p-3 cursor-pointer transition"
                  >
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-white">Version #{item.id}</span>
                      <span className="text-[10px] text-slate-500">{item.created_at}</span>
                    </div>
                    <div className="text-xs text-emerald-400 mt-1 font-semibold">
                      ATS Score: {item.analysis_data?.match_score || 0}%
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* Right Side: Document Preview Canvas */}
        <div className="lg:col-span-7 bg-[#0f172a] border border-slate-800 rounded-xl overflow-hidden flex flex-col">
          {optimizedResult ? (
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* Document Toolbar */}
              <div className="p-3 bg-slate-950 border-b border-slate-800 flex flex-wrap items-center justify-between gap-3 print:hidden">
                <div className="flex items-center gap-2 flex-wrap">
                  {/* Doc Toggle */}
                  <div className="flex bg-slate-900 p-0.5 rounded-lg border border-slate-800 text-xs">
                    <button
                      onClick={() => setDocumentView('RESUME')}
                      className={`px-3 py-1 rounded-md font-semibold transition ${documentView === 'RESUME' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'}`}
                    >
                      Resume ATS
                    </button>
                    <button
                      onClick={() => setDocumentView('COVER_LETTER')}
                      className={`px-3 py-1 rounded-md font-semibold transition ${documentView === 'COVER_LETTER' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'}`}
                    >
                      Cover Letter
                    </button>
                  </div>

                  {/* Template Picker (For Resume) */}
                  {documentView === 'RESUME' && (
                    <div className="flex items-center gap-1 bg-slate-900 p-0.5 rounded-lg border border-slate-800 text-xs">
                      <Layers className="w-3.5 h-3.5 text-slate-400 ml-1.5" />
                      {(['HARVARD', 'MODERN', 'TECHNICAL'] as ResumeTemplate[]).map(tpl => (
                        <button
                          key={tpl}
                          onClick={() => setSelectedTemplate(tpl)}
                          className={`px-2 py-0.5 rounded text-[11px] font-medium transition ${
                            selectedTemplate === tpl 
                              ? 'bg-slate-800 text-white font-bold' 
                              : 'text-slate-400 hover:text-slate-200'
                          }`}
                        >
                          {tpl === 'HARVARD' ? 'Harvard' : tpl === 'MODERN' ? 'Modern' : 'Tech CV'}
                        </button>
                      ))}
                    </div>
                  )}

                  <span className="text-xs bg-emerald-950/80 text-emerald-300 border border-emerald-600/60 px-2 py-0.5 rounded font-bold">
                    {optimizedResult.analysis?.match_score ?? (optimizedResult as any)?.match_score ?? 0}% ATS Fit
                  </span>
                </div>

                <div className="flex items-center gap-2 flex-wrap">
                  {/* ATS Validator Button */}
                  {documentView === 'RESUME' && (
                    <button
                      onClick={runATSValidation}
                      disabled={isValidating}
                      className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg bg-emerald-950/70 border border-emerald-700/60 text-emerald-300 text-xs font-semibold hover:bg-emerald-900 transition disabled:opacity-50"
                      title="Audit struktur ATS & deteksi potensi masalah"
                    >
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                      <span>{isValidating ? 'Audit...' : 'Audit ATS'}</span>
                    </button>
                  )}

                  <button
                    onClick={onSaveVersion}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-medium transition"
                  >
                    <Save className="w-3.5 h-3.5" />
                    <span>Save</span>
                  </button>

                  {documentView === 'RESUME' ? (
                    <>
                      <button
                        onClick={() => onExportDocx(selectedTemplate)}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>DOCX ({selectedTemplate})</span>
                      </button>
                      <button
                        onClick={() => onExportPdf(selectedTemplate)}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium transition"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Download PDF ({selectedTemplate})</span>
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        onClick={onCopyCoverLetter}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition"
                      >
                        {copiedLetter ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                        <span>{copiedLetter ? 'Copied!' : 'Copy'}</span>
                      </button>
                      <button
                        onClick={onExportCoverLetterDocx}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>DOCX</span>
                      </button>
                      <button
                        onClick={onExportCoverLetterPdf}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-medium transition"
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Download PDF</span>
                      </button>
                      <button
                        onClick={onRegenerateCoverLetter}
                        disabled={isRegeneratingLetter}
                        className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-medium transition"
                      >
                        <RefreshCw className={`w-3.5 h-3.5 ${isRegeneratingLetter ? 'animate-spin' : ''}`} />
                        <span>Regenerate</span>
                      </button>
                    </>
                  )}
                </div>
              </div>

              {/* Document Canvas Content */}
              <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
                {documentView === 'RESUME' ? (
                  <>
                    {/* Validation Panel (If Ran) */}
                    {validationReport && (
                      <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-xs space-y-2 print:hidden">
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-white flex items-center gap-1.5">
                            <ShieldCheck className="w-4 h-4 text-emerald-400" />
                            ATS Readability Audit Report:
                          </span>
                          <span className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                            validationReport.score >= 85 ? 'bg-emerald-950 text-emerald-300 border border-emerald-700' : 'bg-amber-950 text-amber-300 border border-amber-700'
                          }`}>
                            Structure Score: {validationReport.score}/100
                          </span>
                        </div>
                        {validationReport.issues.length > 0 ? (
                          <ul className="text-amber-300 space-y-1 list-disc pl-5">
                            {validationReport.issues.map((iss, i) => (
                              <li key={i}>{iss}</li>
                            ))}
                          </ul>
                        ) : (
                          <p className="text-emerald-400 flex items-center gap-1">
                            <Check className="w-3.5 h-3.5" /> Document format is clean, structured, and 100% compatible with modern ATS parsers.
                          </p>
                        )}
                      </div>
                    )}

                    {/* Keyword Chips */}
                    <div className="bg-slate-950 border border-slate-800 rounded-lg p-3 text-xs space-y-2 print:hidden">
                      <div className="flex flex-wrap items-center gap-1">
                        <span className="text-slate-400 font-semibold mr-1">ATS Keywords:</span>
                        {(optimizedResult.analysis?.matched_keywords || []).map((kw, i) => (
                          <span key={i} className="bg-emerald-950/70 text-emerald-300 border border-emerald-800/60 px-1.5 py-0.5 rounded text-[10px]">
                            {kw}
                          </span>
                        ))}
                      </div>
                      {Boolean(optimizedResult.analysis?.missing_skills?.length) && (
                        <div className="flex flex-wrap items-center gap-1 pt-2 border-t border-slate-900">
                          <span className="text-amber-400 font-semibold mr-1">Skill Gaps:</span>
                          {(optimizedResult.analysis?.missing_skills || []).map((sk, i) => (
                            <span key={i} className="bg-amber-950/70 text-amber-300 border border-amber-800/60 px-1.5 py-0.5 rounded text-[10px]">
                              {sk}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Dynamic Paper Document Container */}
                    <div 
                      id="printable-resume" 
                      className={`bg-white text-slate-900 rounded-lg p-8 shadow-xl text-xs leading-relaxed max-w-2xl mx-auto border border-slate-200 ${
                        selectedTemplate === 'HARVARD' 
                          ? 'font-serif' 
                          : selectedTemplate === 'MODERN' 
                          ? 'font-sans' 
                          : 'font-mono'
                      }`}
                    >
                      {/* Name & Contact */}
                      <div className={`pb-3 ${
                        selectedTemplate === 'MODERN' 
                          ? 'border-b-2 border-slate-900 text-left' 
                          : 'border-b border-slate-300 text-center'
                      }`}>
                        <input 
                          type="text" 
                          value={optimizedResult.resume.contact.full_name}
                          onChange={(e) => {
                            const updated = {...optimizedResult}
                            updated.resume.contact.full_name = e.target.value
                            setOptimizedResult(updated)
                          }}
                          className={`text-xl font-bold uppercase tracking-wider text-slate-900 w-full focus:outline-none focus:bg-slate-50 ${
                            selectedTemplate === 'MODERN' ? 'text-left' : 'text-center'
                          }`}
                        />
                        <div className={`text-[11px] text-slate-600 mt-1 flex flex-wrap gap-x-2 ${
                          selectedTemplate === 'MODERN' ? 'justify-start' : 'justify-center'
                        }`}>
                          <span>{optimizedResult.resume.contact.email}</span>
                          <span>•</span>
                          <span>{optimizedResult.resume.contact.phone}</span>
                          <span>•</span>
                          <span>{optimizedResult.resume.contact.location}</span>
                          {optimizedResult.resume.contact.linkedin_url && (
                            <>
                              <span>•</span>
                              <span>{optimizedResult.resume.contact.linkedin_url}</span>
                            </>
                          )}
                          {optimizedResult.resume.contact.github_url && (
                            <>
                              <span>•</span>
                              <span>{optimizedResult.resume.contact.github_url}</span>
                            </>
                          )}
                        </div>
                      </div>

                      {/* Summary */}
                      <div className="mt-3 print-page-break-avoid">
                        <h5 className={`font-bold uppercase tracking-wider text-xs pb-0.5 mb-1 text-slate-900 ${
                          selectedTemplate === 'MODERN' 
                            ? 'border-b border-indigo-600 text-indigo-900' 
                            : 'border-b border-slate-300'
                        }`}>
                          Professional Summary
                        </h5>
                        <textarea 
                          rows={3}
                          value={optimizedResult.resume.professional_summary}
                          onChange={(e) => {
                            const updated = {...optimizedResult}
                            updated.resume.professional_summary = e.target.value
                            setOptimizedResult(updated)
                          }}
                          className="w-full text-slate-800 leading-normal focus:outline-none focus:bg-slate-50 p-1 rounded font-inherit"
                        />
                      </div>

                      {/* Technical Skills */}
                      <div className="mt-3 print-page-break-avoid">
                        <h5 className={`font-bold uppercase tracking-wider text-xs pb-0.5 mb-1 text-slate-900 ${
                          selectedTemplate === 'MODERN' 
                            ? 'border-b border-indigo-600 text-indigo-900' 
                            : 'border-b border-slate-300'
                        }`}>
                          Technical Skills
                        </h5>
                        <div className="text-slate-800 leading-normal p-1">
                          <span className="font-bold">Core Competencies: </span>
                          <span>{optimizedResult.resume.technical_skills.join(', ')}</span>
                        </div>
                      </div>

                      {/* Work Experiences */}
                      <div className="mt-3 print-page-break-avoid">
                        <h5 className={`font-bold uppercase tracking-wider text-xs pb-0.5 mb-1 text-slate-900 ${
                          selectedTemplate === 'MODERN' 
                            ? 'border-b border-indigo-600 text-indigo-900' 
                            : 'border-b border-slate-300'
                        }`}>
                          Professional Experience
                        </h5>
                        <div className="space-y-3 mt-2">
                          {optimizedResult.resume.work_experiences.map((exp, expIdx) => (
                            <div key={expIdx} className="space-y-1">
                              <div className="flex justify-between items-baseline font-bold text-slate-900">
                                <span>{exp.position} — <span className="font-normal italic">{exp.company}</span></span>
                                <span className="text-[11px] text-slate-600">{exp.start_date} – {exp.end_date}</span>
                              </div>
                              <ul className="list-disc pl-5 space-y-1 text-slate-800">
                                {exp.bullets.map((bullet, bIdx) => (
                                  <li key={bIdx}>
                                    <textarea 
                                      rows={2}
                                      value={bullet}
                                      onChange={(e) => {
                                        const updated = {...optimizedResult}
                                        updated.resume.work_experiences[expIdx].bullets[bIdx] = e.target.value
                                        setOptimizedResult(updated)
                                      }}
                                      className="w-full text-slate-800 leading-tight focus:outline-none focus:bg-slate-50 p-1 rounded text-xs font-inherit"
                                    />
                                  </li>
                                ))}
                              </ul>
                            </div>
                          ))}
                        </div>
                      </div>

                      {/* Education */}
                      {optimizedResult.resume.educations.length > 0 && (
                        <div className="mt-3 print-page-break-avoid">
                          <h5 className={`font-bold uppercase tracking-wider text-xs pb-0.5 mb-1 text-slate-900 ${
                            selectedTemplate === 'MODERN' 
                              ? 'border-b border-indigo-600 text-indigo-900' 
                              : 'border-b border-slate-300'
                          }`}>
                            Education
                          </h5>
                          {optimizedResult.resume.educations.map((edu, eIdx) => (
                            <div key={eIdx} className="flex justify-between items-baseline text-slate-800 mt-1 p-1">
                              <div>
                                <span className="font-bold">{edu.institution}</span>, {edu.degree} in {edu.field_of_study}
                              </div>
                              <span className="text-[11px] text-slate-600">{edu.graduation_year}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </>
                ) : (
                  /* Live Cover Letter Paper */
                  <div id="printable-cover-letter" className="bg-white text-slate-900 rounded-lg p-8 shadow-xl font-sans text-xs leading-relaxed max-w-2xl mx-auto border border-slate-200">
                    <div className="text-center pb-3 border-b border-slate-300 mb-6">
                      <h4 className="text-lg font-bold uppercase tracking-wider">{optimizedResult.resume.contact.full_name}</h4>
                      <p className="text-[11px] text-slate-600">{optimizedResult.resume.contact.email} • {optimizedResult.resume.contact.phone} • {optimizedResult.resume.contact.location}</p>
                    </div>

                    <div className="mb-4 text-slate-600">
                      <p>{new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}</p>
                      <p className="mt-2 font-bold text-slate-900">Hiring Manager</p>
                      <p>{job.company_name}</p>
                    </div>

                    <textarea 
                      rows={18}
                      value={editableCoverLetter}
                      onChange={(e) => setEditableCoverLetter(e.target.value)}
                      className="w-full text-slate-800 leading-relaxed focus:outline-none focus:bg-slate-50 p-1 rounded font-sans text-xs"
                    />

                    <div className="mt-6 pt-4 border-t border-slate-200 text-slate-700 text-xs">
                      <p>Sincerely,</p>
                      <p className="font-bold mt-4">{optimizedResult.resume.contact.full_name}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-slate-500 print:hidden">
              <FileText className="w-12 h-12 text-slate-700 mb-3" />
              <h4 className="text-sm font-semibold text-slate-300">No Document Yet</h4>
              <p className="text-xs text-slate-500 mt-1 max-w-sm">
                Upload a CV file or fill out the form on the left to generate an ATS resume and cover letter instantly.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

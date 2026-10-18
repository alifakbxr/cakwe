import React, { useState } from 'react'
import { 
  Radar, 
  Kanban as KanbanIcon, 
  FileText, 
  Settings as SettingsIcon,
  RefreshCw,
  ShieldCheck,
  LayoutDashboard,
  Menu,
  X
} from 'lucide-react'
import type { ViewTab, SyncStatus } from '../types'

interface AppShellProps {
  currentTab: ViewTab
  onSelectTab: (tab: ViewTab) => void
  onManualSync: () => void
  syncing: boolean
  syncStatus: SyncStatus | null
  activeTrackingCount?: number
  children: React.ReactNode
}

export const AppShell: React.FC<AppShellProps> = ({
  currentTab,
  onSelectTab,
  onManualSync,
  syncing,
  syncStatus,
  activeTrackingCount = 0,
  children
}) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const navItems = [
    { id: 'DASHBOARD' as ViewTab, label: 'Dashboard', icon: LayoutDashboard, badge: null },
    { id: 'RADAR' as ViewTab, label: 'Find Jobs', icon: Radar, badge: null },
    { 
      id: 'KANBAN' as ViewTab, 
      label: 'Job Tracker', 
      icon: KanbanIcon, 
      badge: activeTrackingCount > 0 ? `${activeTrackingCount}` : null 
    },
    { id: 'RESUME_STUDIO' as ViewTab, label: 'ATS Studio', icon: FileText, badge: 'Pro' },
    { id: 'SETTINGS' as ViewTab, label: 'Preferences', icon: SettingsIcon, badge: null },
  ]

  const handleNavClick = (tab: ViewTab) => {
    onSelectTab(tab)
    setMobileMenuOpen(false)
  }

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col font-sans">
      {/* Top Application Bar */}
      <header className="sticky top-0 z-40 bg-[#0c1220]/95 backdrop-blur-md border-b border-slate-800/80 px-4 sm:px-6 py-3 print:hidden">
        <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
          
          {/* Brand Identity */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-white md:hidden"
              aria-label="Toggle navigation menu"
            >
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>

            <div 
              onClick={() => onSelectTab('DASHBOARD')}
              className="flex items-center gap-2.5 cursor-pointer group"
            >
              <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/10 border border-emerald-400/30 group-hover:scale-105 transition">
                <Radar className="w-4 h-4 sm:w-5 sm:h-5 text-slate-950 font-bold" />
              </div>
              <div>
                <div className="flex items-center gap-1.5">
                  <span className="text-base font-extrabold tracking-tight text-white">Cakwe</span>
                  <span className="text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-1.5 py-0.2 rounded-full">
                    Radar
                  </span>
                </div>
                <p className="text-[10px] text-slate-400 hidden lg:block leading-none">
                  Global Remote • Small Teams • ID Eligible
                </p>
              </div>
            </div>
          </div>

          {/* Desktop Navigation Tabs */}
          <nav className="hidden md:flex items-center gap-1 bg-slate-950/80 p-1 rounded-xl border border-slate-800/80">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = currentTab === item.id
              return (
                <button
                  key={item.id}
                  onClick={() => handleNavClick(item.id)}
                  className={`flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                    isActive
                      ? 'bg-emerald-600 text-white shadow-sm shadow-emerald-900/30'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                  {item.badge && (
                    <span className={`text-[9px] uppercase tracking-wider px-1.5 py-0.2 rounded font-bold ${
                      item.id === 'KANBAN'
                        ? 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                        : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                    }`}>
                      {item.badge}
                    </span>
                  )}
                </button>
              )
            })}
          </nav>

          {/* Right Action: Sync Button & System Status */}
          <div className="flex items-center gap-2 sm:gap-3">
            {syncStatus && (
              <div className="hidden xl:flex items-center gap-2 text-[11px] text-slate-400 bg-slate-900/60 px-3 py-1.5 rounded-lg border border-slate-800">
                <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
                <span>{syncStatus.total_active_companies} verified boards</span>
              </div>
            )}

            <button
              onClick={onManualSync}
              disabled={syncing}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-slate-800 text-slate-200 border border-slate-700/80 text-xs font-semibold transition shadow-sm disabled:opacity-50"
              title="Crawl and poll active ATS boards"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin text-emerald-400' : 'text-slate-400'}`} />
              <span className="hidden sm:inline">{syncing ? 'Syncing...' : 'Sync Radar'}</span>
            </button>
          </div>
        </div>

        {/* Mobile Navigation Drawer / Menu */}
        {mobileMenuOpen && (
          <div className="md:hidden pt-3 mt-3 border-t border-slate-800/80 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon
              const isActive = currentTab === item.id
              return (
                <button
                  key={item.id}
                  onClick={() => handleNavClick(item.id)}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition ${
                    isActive
                      ? 'bg-emerald-600 text-white font-bold'
                      : 'text-slate-300 hover:bg-slate-900'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon className="w-4 h-4" />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className="text-[10px] px-2 py-0.5 rounded bg-slate-950 font-mono font-bold">
                      {item.badge}
                    </span>
                  )}
                </button>
              )
            })}
          </div>
        )}
      </header>

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 py-6 print:p-0 print:max-w-none">
        {children}
      </main>

      {/* Clean Global Footer */}
      <footer className="border-t border-slate-800/80 bg-[#0c1220]/60 py-6 px-4 sm:px-6 text-center text-xs text-slate-500 print:hidden mt-auto">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-slate-400 text-xs">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>Strict Verification: 100% Fully Remote • Indonesia Eligible • Boutique & Small Teams</span>
          </div>
          <div className="text-[11px] text-slate-500">
            Local-First Architecture • SQLite Database • Automated Multi-ATS Ingestion
          </div>
        </div>
      </footer>
    </div>
  )
}

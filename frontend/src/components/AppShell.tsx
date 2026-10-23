import React from 'react'
import { 
  Radar, 
  Kanban as KanbanIcon, 
  FileText, 
  Settings as SettingsIcon,
  RefreshCw,
  LayoutDashboard,
  Menu,
  Globe2,
  Sparkles
} from 'lucide-react'
import type { ViewTab, SyncStatus } from '../types'
import { 
  SidebarProvider, 
  Sidebar, 
  SidebarHeader, 
  SidebarContent, 
  SidebarFooter, 
  SidebarGroup, 
  SidebarGroupLabel, 
  SidebarMenu, 
  SidebarMenuItem, 
  SidebarMenuButton, 
  SidebarTrigger, 
  useSidebar 
} from './ui/sidebar'
import { 
  Breadcrumb, 
  BreadcrumbItem, 
  BreadcrumbLink, 
  BreadcrumbList, 
  BreadcrumbPage, 
  BreadcrumbSeparator 
} from './ui/breadcrumb'
import { Button } from './ui/button'
import { Badge } from './ui/badge'

interface AppShellProps {
  currentTab: ViewTab
  onSelectTab: (tab: ViewTab) => void
  onManualSync: () => void
  syncing: boolean
  syncStatus: SyncStatus | null
  activeTrackingCount?: number
  children: React.ReactNode
}

function AppHeader({
  currentTab,
  onSelectTab,
  onManualSync,
  syncing,
  syncStatus,
}: {
  currentTab: ViewTab
  onSelectTab: (tab: ViewTab) => void
  onManualSync: () => void
  syncing: boolean
  syncStatus: SyncStatus | null
}) {
  const { setIsMobileOpen } = useSidebar()

  const tabLabels: Record<ViewTab, string> = {
    DASHBOARD: 'Dashboard & Overview',
    RADAR: 'Job Discovery Radar',
    KANBAN: 'Job Application Tracker',
    RESUME_STUDIO: 'ATS Resume & Cover Letter Studio',
    SETTINGS: 'Preferences & Targeting'
  }

  return (
    <header className="sticky top-0 z-20 flex h-16 shrink-0 items-center justify-between border-b border-slate-800/80 bg-[#090d16]/90 px-4 sm:px-6 backdrop-blur-md">
      <div className="flex items-center gap-3">
        {/* Mobile menu trigger button */}
        <Button
          variant="outline"
          size="icon"
          onClick={() => setIsMobileOpen(true)}
          className="md:hidden h-8 w-8 text-slate-300"
          aria-label="Open Navigation Menu"
        >
          <Menu className="w-4 h-4" />
        </Button>

        {/* Desktop sidebar toggle trigger */}
        <SidebarTrigger />

        {/* Breadcrumb path */}
        <Breadcrumb className="hidden sm:block">
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink onClick={() => onSelectTab('DASHBOARD')}>
                Cakwe
              </BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbPage>{tabLabels[currentTab]}</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>
      </div>

      {/* Header Right Action & Status */}
      <div className="flex items-center gap-2.5">
        {syncStatus && (
          <div className="hidden lg:flex items-center gap-2 text-[11px] text-slate-400 bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="font-mono">{syncStatus.total_active_companies} verified boards</span>
          </div>
        )}

        <Button
          variant="outline"
          size="sm"
          onClick={onManualSync}
          disabled={syncing}
          className="h-8 gap-1.5 text-xs font-semibold text-slate-200 border-slate-700/80 hover:border-emerald-500/50"
          title="Synchronize jobs from public ATS job boards"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${syncing ? 'animate-spin text-emerald-400' : 'text-slate-400'}`} />
          <span className="hidden sm:inline">{syncing ? 'Syncing...' : 'Sync Radar'}</span>
        </Button>
      </div>
    </header>
  )
}

function SidebarNav({
  currentTab,
  onSelectTab,
  activeTrackingCount,
}: {
  currentTab: ViewTab
  onSelectTab: (tab: ViewTab) => void
  activeTrackingCount: number
}) {
  const { isCollapsed } = useSidebar()

  return (
    <>
      <SidebarHeader>
        <div 
          onClick={() => onSelectTab('DASHBOARD')}
          className="flex items-center gap-3 cursor-pointer group select-none"
        >
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center shadow-lg shadow-emerald-500/10 border border-emerald-400/30 group-hover:scale-105 transition shrink-0">
            <Radar className="w-4 h-4 text-slate-950 font-bold" />
          </div>
          {!isCollapsed && (
            <div className="overflow-hidden">
              <div className="flex items-center gap-1.5">
                <span className="text-sm font-extrabold tracking-tight text-white">Cakwe</span>
              </div>
              <p className="text-[10px] text-slate-400 truncate">
                AI Job Radar & Studio
              </p>
            </div>
          )}
        </div>
      </SidebarHeader>

      <SidebarContent>
        {/* Main Workflows */}
        <SidebarGroup>
          <SidebarGroupLabel>Discovery & Tracking</SidebarGroupLabel>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton
                active={currentTab === 'DASHBOARD'}
                onClick={() => onSelectTab('DASHBOARD')}
                icon={LayoutDashboard}
                label="Dashboard"
              />
            </SidebarMenuItem>
            <SidebarMenuItem>
              <SidebarMenuButton
                active={currentTab === 'RADAR'}
                onClick={() => onSelectTab('RADAR')}
                icon={Radar}
                label="Find Jobs"
              />
            </SidebarMenuItem>
            <SidebarMenuItem>
              <SidebarMenuButton
                active={currentTab === 'KANBAN'}
                onClick={() => onSelectTab('KANBAN')}
                icon={KanbanIcon}
                label="Job Tracker"
                badge={activeTrackingCount > 0 ? (
                  <Badge variant="indigo" className="font-mono text-[9px] px-1.5 py-0">
                    {activeTrackingCount}
                  </Badge>
                ) : null}
              />
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarGroup>

        {/* AI & Optimization Suite */}
        <SidebarGroup>
          <SidebarGroupLabel>Applications & Tools</SidebarGroupLabel>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton
                active={currentTab === 'RESUME_STUDIO'}
                onClick={() => onSelectTab('RESUME_STUDIO')}
                icon={FileText}
                label="ATS Studio"
                badge={<Badge variant="default" className="text-[9px] px-1 py-0 uppercase">Pro</Badge>}
              />
            </SidebarMenuItem>
            <SidebarMenuItem>
              <SidebarMenuButton
                active={currentTab === 'SETTINGS'}
                onClick={() => onSelectTab('SETTINGS')}
                icon={SettingsIcon}
                label="Preferences"
              />
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarGroup>

        {/* Quick Informational / Status Card in expanded sidebar */}
        {!isCollapsed && (
          <div className="mx-2 mt-4 rounded-xl bg-slate-900/80 border border-slate-800 p-3 space-y-2 text-xs">
            <div className="flex items-center gap-1.5 text-emerald-400 font-semibold text-[11px]">
              <Globe2 className="w-3.5 h-3.5" />
              <span>Worldwide Remote</span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              Filtering global remote & EOR roles eligible for developers worldwide.
            </p>
          </div>
        )}
      </SidebarContent>

      <SidebarFooter>
        {!isCollapsed ? (
          <div className="flex items-center justify-between text-[11px] text-slate-500">
            <span>Cakwe Radar Engine</span>
            <span className="flex items-center gap-1 text-slate-400">
              <Sparkles className="w-3 h-3 text-emerald-400" />
              Online
            </span>
          </div>
        ) : (
          <div className="flex justify-center text-slate-500">
            <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
          </div>
        )}
      </SidebarFooter>
    </>
  )
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
  return (
    <SidebarProvider defaultCollapsed={false}>
      <Sidebar>
        <SidebarNav
          currentTab={currentTab}
          onSelectTab={onSelectTab}
          activeTrackingCount={activeTrackingCount}
        />
      </Sidebar>

      {/* Main App Inset Layout */}
      <div className="flex-1 flex flex-col min-w-0 bg-[#090d16]">
        <AppHeader
          currentTab={currentTab}
          onSelectTab={onSelectTab}
          onManualSync={onManualSync}
          syncing={syncing}
          syncStatus={syncStatus}
        />

        <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 print:p-0 print:max-w-none">
          {children}
        </main>
      </div>
    </SidebarProvider>
  )
}

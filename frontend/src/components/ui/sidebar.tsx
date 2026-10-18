import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { PanelLeft, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"

interface SidebarContextValue {
  isCollapsed: boolean
  setIsCollapsed: (collapsed: boolean | ((prev: boolean) => boolean)) => void
  isMobileOpen: boolean
  setIsMobileOpen: (open: boolean | ((prev: boolean) => boolean)) => void
}

const SidebarContext = React.createContext<SidebarContextValue | null>(null)

export function useSidebar() {
  const context = React.useContext(SidebarContext)
  if (!context) {
    throw new Error("useSidebar must be used within a SidebarProvider")
  }
  return context
}

export function SidebarProvider({
  children,
  defaultCollapsed = false,
}: {
  children: React.ReactNode
  defaultCollapsed?: boolean
}) {
  const [isCollapsed, setIsCollapsed] = React.useState(defaultCollapsed)
  const [isMobileOpen, setIsMobileOpen] = React.useState(false)

  // Persist sidebar state in localStorage
  React.useEffect(() => {
    const saved = localStorage.getItem("cakwe_sidebar_collapsed")
    if (saved !== null) {
      setIsCollapsed(saved === "true")
    }
  }, [])

  const setCollapsedWithStorage = (val: boolean | ((prev: boolean) => boolean)) => {
    setIsCollapsed(prev => {
      const next = typeof val === "function" ? val(prev) : val
      localStorage.setItem("cakwe_sidebar_collapsed", String(next))
      return next
    })
  }

  return (
    <SidebarContext.Provider
      value={{
        isCollapsed,
        setIsCollapsed: setCollapsedWithStorage,
        isMobileOpen,
        setIsMobileOpen,
      }}
    >
      <TooltipProvider delayDuration={0}>
        <div className="min-h-screen bg-[#090d16] text-slate-100 flex w-full font-sans antialiased">
          {children}
        </div>
      </TooltipProvider>
    </SidebarContext.Provider>
  )
}

export function Sidebar({ className, children }: { className?: string; children: React.ReactNode }) {
  const { isCollapsed, isMobileOpen, setIsMobileOpen } = useSidebar()

  return (
    <>
      {/* Mobile Drawer Overlay */}
      {isMobileOpen && (
        <div
          className="fixed inset-0 z-50 bg-black/70 backdrop-blur-xs md:hidden animate-in fade-in-0"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Desktop Persistent Sidebar */}
      <aside
        className={cn(
          "hidden md:flex flex-col shrink-0 border-r border-slate-800/80 bg-[#0c1220] transition-all duration-300 ease-in-out z-30 sticky top-0 h-screen",
          isCollapsed ? "w-16" : "w-64",
          className
        )}
      >
        {children}
      </aside>

      {/* Mobile Slide-in Sidebar Sheet */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 flex flex-col w-72 bg-[#0c1220] border-r border-slate-800 shadow-2xl transition-transform duration-300 ease-in-out md:hidden",
          isMobileOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div className="flex items-center justify-between p-4 border-b border-slate-800">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-emerald-600 to-teal-400 flex items-center justify-center font-bold text-slate-950 text-sm">
              C
            </div>
            <span className="font-extrabold text-white text-base">Cakwe Radar</span>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsMobileOpen(false)}
            aria-label="Tutup Menu"
          >
            <X className="w-5 h-5" />
          </Button>
        </div>
        <div className="flex-1 overflow-y-auto p-3 space-y-4">{children}</div>
      </aside>
    </>
  )
}

export function SidebarHeader({ className, children }: { className?: string; children: React.ReactNode }) {
  return <div className={cn("p-4 border-b border-slate-800/80 shrink-0", className)}>{children}</div>
}

export function SidebarContent({ className, children }: { className?: string; children: React.ReactNode }) {
  return <div className={cn("flex-1 overflow-y-auto px-2 py-4 space-y-6", className)}>{children}</div>
}

export function SidebarFooter({ className, children }: { className?: string; children: React.ReactNode }) {
  return <div className={cn("p-3 border-t border-slate-800/80 shrink-0 bg-[#090d16]/50", className)}>{children}</div>
}

export function SidebarGroup({ className, children }: { className?: string; children: React.ReactNode }) {
  return <div className={cn("space-y-1.5", className)}>{children}</div>
}

export function SidebarGroupLabel({ className, children }: { className?: string; children: React.ReactNode }) {
  const { isCollapsed } = useSidebar()
  if (isCollapsed) return null
  return (
    <h4 className={cn("px-3 text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1", className)}>
      {children}
    </h4>
  )
}

export function SidebarMenu({ className, children }: { className?: string; children: React.ReactNode }) {
  return <nav className={cn("space-y-1", className)}>{children}</nav>
}

export function SidebarMenuItem({ children }: { children: React.ReactNode }) {
  return <div>{children}</div>
}

const sidebarButtonVariants = cva(
  "w-full flex items-center gap-3 rounded-lg text-xs font-medium transition-all group relative cursor-pointer",
  {
    variants: {
      active: {
        true: "bg-emerald-600 text-white font-semibold shadow-sm shadow-emerald-950/40",
        false: "text-slate-400 hover:text-slate-200 hover:bg-slate-900/80",
      },
      collapsed: {
        true: "justify-center p-2.5",
        false: "px-3 py-2",
      },
    },
    defaultVariants: {
      active: false,
      collapsed: false,
    },
  }
)

interface SidebarMenuButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof sidebarButtonVariants> {
  icon?: React.ComponentType<{ className?: string }>
  badge?: React.ReactNode
  label: string
}

export function SidebarMenuButton({
  active,
  icon: Icon,
  badge,
  label,
  className,
  ...props
}: SidebarMenuButtonProps) {
  const { isCollapsed, setIsMobileOpen } = useSidebar()

  const buttonContent = (
    <button
      className={cn(sidebarButtonVariants({ active, collapsed: isCollapsed }), className)}
      onClick={(e) => {
        setIsMobileOpen(false)
        props.onClick?.(e)
      }}
      {...props}
    >
      {Icon && <Icon className={cn("w-4 h-4 shrink-0", active ? "text-white" : "text-slate-400 group-hover:text-slate-200")} />}
      {!isCollapsed && <span className="truncate flex-1 text-left">{label}</span>}
      {!isCollapsed && badge && (
        <span className="shrink-0">{badge}</span>
      )}
    </button>
  )

  if (isCollapsed) {
    return (
      <Tooltip>
        <TooltipTrigger asChild>{buttonContent}</TooltipTrigger>
        <TooltipContent side="right" className="flex items-center gap-2">
          <span>{label}</span>
          {badge}
        </TooltipContent>
      </Tooltip>
    )
  }

  return buttonContent
}

export function SidebarTrigger({ className }: { className?: string }) {
  const { isCollapsed, setIsCollapsed } = useSidebar()

  return (
    <Button
      variant="ghost"
      size="icon"
      className={cn("hidden md:inline-flex text-slate-400 hover:text-white", className)}
      onClick={() => setIsCollapsed(!isCollapsed)}
      aria-label="Toggle Sidebar"
    >
      <PanelLeft className="w-4 h-4" />
    </Button>
  )
}

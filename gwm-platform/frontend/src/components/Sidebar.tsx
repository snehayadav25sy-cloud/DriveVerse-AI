import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Clapperboard, Briefcase,
  Cpu, ChevronRight, LogOut, Folder, BarChart3, Globe, Sparkles
} from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

const NAV = [
  { to: '/',              icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/projects',      icon: Folder,          label: 'Projects' },
  { to: '/generate',      icon: Clapperboard,    label: 'Generate Dataset' },
  { to: '/generate-prompt', icon: Sparkles,      label: 'AI Prompt Engine' },
  { to: '/jobs',          icon: Briefcase,       label: 'Simulations' },
  { to: '/quality',       icon: BarChart3,       label: 'Dataset Quality' },
  { to: '/countries',     icon: Globe,           label: 'Country Profiles' },
  { to: '/geography',     icon: Globe,           label: 'Geography Engine' },
]

export default function Sidebar() {
  const { logout } = useAuth()

  return (
    <aside className="fixed inset-y-0 left-0 z-40 flex flex-col w-64 bg-slate-900/80 border-r border-slate-800/60 backdrop-blur-xl">
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-slate-800/60">
        <div className="relative flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-brand-600 to-violet-600 shadow-glow-violet">
          <Cpu size={18} className="text-white" />
          <span className="absolute -top-0.5 -right-0.5 h-2.5 w-2.5 rounded-full bg-neon-green border-2 border-slate-900 animate-pulse-slow" />
        </div>
        <div>
          <p className="text-sm font-bold text-white tracking-tight">DriveVerse AI</p>
          <p className="text-xs text-slate-500">v1.0 · Pilot</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
        {NAV.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `group flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 ${
                isActive
                  ? 'bg-gradient-to-r from-brand-600/20 to-violet-600/10 text-brand-300 border border-brand-500/20'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`
            }
          >
            {({ isActive }) => (
              <>
                <Icon size={17} className={isActive ? 'text-brand-400' : 'text-slate-500 group-hover:text-slate-300'} />
                <span className="flex-1">{label}</span>
                {isActive && <ChevronRight size={13} className="text-brand-500" />}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-slate-800/60 space-y-4">
        <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-slate-800/40">
          <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse-slow" />
          <span className="text-xs text-slate-400">Backend <span className="text-emerald-400 font-medium">connected</span></span>
        </div>
        <button onClick={logout} className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors text-sm">
          <LogOut size={16} />
          Log Out
        </button>
      </div>
    </aside>
  )
}

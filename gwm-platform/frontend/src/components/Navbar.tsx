import { Bell, Search, User, Settings, LogOut } from 'lucide-react'
import { useState, useRef, useEffect } from 'react'
import { useAuth } from '../contexts/AuthContext'

interface NavbarProps { title: string; subtitle?: string }

export default function Navbar({ title, subtitle }: NavbarProps) {
  const [showNotifications, setShowNotifications] = useState(false)
  const [showProfile, setShowProfile] = useState(false)
  const notifRef = useRef<HTMLDivElement>(null)
  const profileRef = useRef<HTMLDivElement>(null)
  const { logout } = useAuth()

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (notifRef.current && !notifRef.current.contains(event.target as Node)) setShowNotifications(false)
      if (profileRef.current && !profileRef.current.contains(event.target as Node)) setShowProfile(false)
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  return (
    <header className="sticky top-0 z-30 flex items-center gap-4 px-8 py-4 bg-slate-950/70 border-b border-slate-800/60 backdrop-blur-xl">
      <div className="flex-1">
        <h1 className="text-lg font-bold text-white tracking-tight">{title}</h1>
        {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
      </div>
      <div className="flex items-center gap-3">
        <div className="relative hidden md:flex items-center mr-2">
          <Search size={14} className="absolute left-3 text-slate-500" />
          <input
            placeholder="Search…"
            className="pl-8 pr-4 py-2 text-sm bg-slate-800/60 border border-slate-700/50 rounded-xl
                       text-slate-300 placeholder:text-slate-600 focus:outline-none focus:ring-2
                       focus:ring-brand-500/30 focus:border-brand-500/40 w-48 transition-all"
          />
        </div>

        {/* Notifications */}
        <div className="relative" ref={notifRef}>
          <button 
            className={`relative btn-ghost p-2 transition-colors ${showNotifications ? 'bg-slate-800/80 text-white' : ''}`}
            onClick={() => setShowNotifications(!showNotifications)}
          >
            <Bell size={18} />
            <span className="absolute top-1.5 right-1.5 h-2 w-2 rounded-full bg-brand-500 animate-pulse" />
          </button>
          
          {showNotifications && (
            <div className="absolute right-0 mt-2 w-72 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl py-2 z-50 overflow-hidden transform origin-top-right transition-all">
              <div className="px-4 py-2 border-b border-slate-800 flex justify-between items-center bg-slate-900/50">
                <span className="text-sm font-semibold text-slate-200">Notifications</span>
                <span className="text-xs text-brand-400 cursor-pointer hover:text-brand-300">Mark all read</span>
              </div>
              <div className="max-h-64 overflow-y-auto">
                <div className="px-4 py-8 text-center text-sm text-slate-500">
                  No new notifications
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Profile */}
        <div className="relative" ref={profileRef}>
          <button 
            className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-brand-600 to-violet-600 text-sm font-bold text-white shadow-lg hover:shadow-brand-500/20 transition-all hover:scale-105 active:scale-95"
            onClick={() => setShowProfile(!showProfile)}
          >
            DV
          </button>
          
          {showProfile && (
            <div className="absolute right-0 mt-2 w-48 bg-slate-900 border border-slate-800 rounded-xl shadow-2xl py-1 z-50 overflow-hidden transform origin-top-right transition-all">
              <div className="px-4 py-3 border-b border-slate-800 bg-slate-900/50">
                <p className="text-sm font-medium text-white">DriveVerse Admin</p>
                <p className="text-xs text-slate-400 mt-0.5">admin@driveverse.ai</p>
              </div>
              <div className="py-1">
                <button className="w-full px-4 py-2 text-left text-sm text-slate-300 hover:bg-slate-800 hover:text-white flex items-center gap-2">
                  <User size={14} /> Profile Settings
                </button>
                <button className="w-full px-4 py-2 text-left text-sm text-slate-300 hover:bg-slate-800 hover:text-white flex items-center gap-2">
                  <Settings size={14} /> Organization
                </button>
              </div>
              <div className="border-t border-slate-800 py-1">
                <button onClick={logout} className="w-full px-4 py-2 text-left text-sm text-red-400 hover:bg-red-500/10 hover:text-red-300 flex items-center gap-2">
                  <LogOut size={14} /> Sign out
                </button>
              </div>
            </div>
          )}

        </div>
      </div>
    </header>
  )
}

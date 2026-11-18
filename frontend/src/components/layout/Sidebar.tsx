import { NavLink, useNavigate } from 'react-router-dom'
import {
  BellRing,
  Building2,
  LayoutDashboard,
  LogOut,
  ShieldCheck,
  X,
} from 'lucide-react'

import { useAlertSocket } from '../../context/WebSocketContext'
import { useAuth } from '../../context/AuthContext'
import { cn, initials } from '../../lib/utils'

interface SidebarProps {
  open: boolean
  onClose: () => void
}

const links = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/obras', label: 'Obras', icon: Building2, end: false },
  { to: '/alertas', label: 'Alertas', icon: BellRing, end: false },
]

export function Sidebar({ open, onClose }: SidebarProps) {
  const { user, logout } = useAuth()
  const { alerts } = useAlertSocket()
  const navigate = useNavigate()
  const pending = alerts.filter((alert) => !alert.resuelta).length

  const handleLogout = () => {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <aside
      className={cn(
        'fixed inset-y-0 left-0 z-40 flex w-[264px] -translate-x-full flex-col border-r border-slate-200 bg-white/95 backdrop-blur-xl transition-transform duration-300 dark:border-slate-800/80 dark:bg-panel/95 lg:translate-x-0',
        open && 'translate-x-0',
      )}
    >
      <div className="flex h-20 shrink-0 items-center justify-between border-b border-slate-200 px-6 dark:border-slate-800/80">
        <div className="flex items-center gap-3">
          <div className="relative flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-accent-400 to-accent-600 shadow-lg shadow-accent-500/30">
            <ShieldCheck className="h-5 w-5 text-white" />
          </div>
          <div>
            <p className="text-sm font-extrabold leading-tight tracking-tight text-slate-900 dark:text-white">
              SUPERVISOR <span className="text-accent-500">IA</span>
            </p>
            <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-slate-400">
              Safety operations
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="Cerrar menú"
          className="rounded-lg p-1 text-slate-400 hover:bg-slate-100 dark:hover:bg-white/10 lg:hidden"
        >
          <X className="h-5 w-5" />
        </button>
      </div>

      <nav className="flex-1 space-y-1 overflow-y-auto px-4 py-6">
        <p className="mb-3 px-3 text-[10px] font-bold uppercase tracking-[0.2em] text-slate-400">
          Menú principal
        </p>
        {links.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            onClick={onClose}
            className={({ isActive }) =>
              cn(
                'group flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-semibold transition-all',
                isActive
                  ? 'bg-accent-500/10 text-accent-600 shadow-[inset_2px_0_0_0_#0d8bff] dark:text-accent-100'
                  : 'muted hover:bg-slate-100 hover:text-slate-900 dark:hover:bg-white/5 dark:hover:text-white',
              )
            }
          >
            <Icon className="h-[18px] w-[18px]" />
            <span className="flex-1">{label}</span>
            {label === 'Alertas' && pending > 0 && (
              <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-rose-500/15 px-1.5 text-[10px] font-bold text-rose-500">
                {pending}
              </span>
            )}
          </NavLink>
        ))}

        <div className="mt-8 rounded-xl border border-dashed border-slate-300 p-4 dark:border-slate-700">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-700 dark:text-slate-200">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-pulse-ring rounded-full bg-emerald-400" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
            </span>
            Motor de visión activo
          </div>
          <p className="muted mt-2 text-[11px] leading-relaxed">
            Detección automática de personas en tiempo real mediante YOLOv8.
          </p>
        </div>
      </nav>

      <div className="shrink-0 border-t border-slate-200 p-4 dark:border-slate-800/80">
        <div className="mb-3 flex items-center gap-3 rounded-xl bg-slate-100 p-3 dark:bg-white/5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-slate-700 to-slate-900 text-xs font-bold text-white dark:from-accent-500 dark:to-accent-600">
            {initials(user?.email ?? '?')}
          </div>
          <div className="min-w-0">
            <p className="truncate text-xs font-bold text-slate-800 dark:text-slate-100">
              {user?.email?.split('@')[0] ?? 'Usuario'}
            </p>
            <p className="muted truncate text-[10px]">{user?.email ?? ''}</p>
          </div>
        </div>
        <button
          type="button"
          onClick={handleLogout}
          className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold text-slate-500 transition hover:bg-rose-500/10 hover:text-rose-600 dark:text-slate-400 dark:hover:text-rose-400"
        >
          <LogOut className="h-[18px] w-[18px]" />
          Cerrar sesión
        </button>
      </div>
    </aside>
  )
}

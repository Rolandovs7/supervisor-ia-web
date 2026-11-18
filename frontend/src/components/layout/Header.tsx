import { useLocation } from 'react-router-dom'
import { Menu, Moon, Sun, Wifi, WifiOff } from 'lucide-react'

import { useAlertSocket } from '../../context/WebSocketContext'
import { useAuth } from '../../context/AuthContext'
import { useTheme } from '../../context/ThemeContext'
import { cn, initials } from '../../lib/utils'

interface HeaderProps {
  onMenuClick: () => void
}

const pageCopy: Record<string, { title: string; subtitle: string }> = {
  '/dashboard': {
    title: 'Centro de operaciones',
    subtitle: 'Visión general de seguridad en tus obras',
  },
  '/obras': {
    title: 'Obras',
    subtitle: 'Administra los proyectos supervisados',
  },
  '/alertas': {
    title: 'Alertas',
    subtitle: 'Historial y resolución de incidentes',
  },
}

export function Header({ onMenuClick }: HeaderProps) {
  const { pathname } = useLocation()
  const { user } = useAuth()
  const { isConnected } = useAlertSocket()
  const { theme, toggleTheme } = useTheme()
  const copy = pageCopy[pathname] ?? pageCopy['/dashboard']

  return (
    <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/80 backdrop-blur-xl dark:border-slate-800/80 dark:bg-canvas/80">
      <div className="mx-auto flex h-20 max-w-[1500px] items-center justify-between gap-4 px-4 sm:px-6 lg:px-8">
        <div className="flex min-w-0 items-center gap-3">
          <button
            type="button"
            onClick={onMenuClick}
            aria-label="Abrir menú"
            className="rounded-lg p-2 text-slate-500 transition hover:bg-slate-100 dark:hover:bg-white/10 lg:hidden"
          >
            <Menu className="h-5 w-5" />
          </button>
          <div className="min-w-0">
            <p className="hidden text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400 sm:block">
              Workspace / {copy.title}
            </p>
            <h1 className="truncate text-lg font-extrabold tracking-tight text-slate-900 dark:text-white sm:text-xl">
              {copy.title}
            </h1>
            <p className="muted hidden text-xs sm:block">{copy.subtitle}</p>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-2 sm:gap-3">
          <div
            className={cn(
              'hidden items-center gap-2 rounded-full border px-3 py-2 text-[11px] font-bold sm:flex',
              isConnected
                ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300'
                : 'border-slate-300 bg-slate-100 text-slate-500 dark:border-slate-700 dark:bg-slate-800/60 dark:text-slate-400',
            )}
            title={isConnected ? 'WebSocket conectado' : 'Reconectando…'}
          >
            {isConnected ? (
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-pulse-ring rounded-full bg-emerald-400" />
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500" />
              </span>
            ) : (
              <WifiOff className="h-3.5 w-3.5" />
            )}
            {isConnected ? 'WebSocket Activa' : 'Sin conexión'}
          </div>

          <span
            className={cn(
              'rounded-full p-2 sm:hidden',
              isConnected
                ? 'text-emerald-500'
                : 'text-slate-400',
            )}
            title={isConnected ? 'WebSocket conectado' : 'Sin conexión'}
          >
            {isConnected ? <Wifi className="h-4 w-4" /> : <WifiOff className="h-4 w-4" />}
          </span>

          <button
            type="button"
            onClick={toggleTheme}
            aria-label="Cambiar tema"
            className="rounded-xl border border-slate-200 p-2.5 text-slate-500 transition hover:bg-slate-100 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-white/10"
          >
            {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
          </button>

          <div className="hidden h-9 w-px bg-slate-200 dark:bg-slate-700 sm:block" />

          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-accent-400 to-accent-600 text-xs font-bold text-white">
              {initials(user?.email ?? '?')}
            </div>
            <div className="hidden text-right xl:block">
              <p className="text-xs font-bold text-slate-800 dark:text-slate-100">
                {user?.email?.split('@')[0] ?? 'Supervisor'}
              </p>
              <p className="muted text-[10px]">Supervisor</p>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}

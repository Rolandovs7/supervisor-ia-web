import type { ReactNode } from 'react'

import { cn } from '../../lib/utils'

export type Tone = 'alto' | 'medio' | 'baja' | 'success' | 'info' | 'neutral'
export type LevelTone = 'alto' | 'medio' | 'baja'

const tones: Record<Tone, string> = {
  alto: 'border-rose-500/30 bg-rose-500/10 text-rose-600 dark:text-rose-300',
  medio: 'border-amber-500/30 bg-amber-500/10 text-amber-700 dark:text-amber-300',
  baja: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300',
  success: 'border-emerald-500/30 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300',
  info: 'border-accent-500/30 bg-accent-500/10 text-accent-600 dark:text-accent-100',
  neutral: 'border-slate-300 bg-slate-100 text-slate-600 dark:border-slate-700 dark:bg-slate-800/70 dark:text-slate-300',
}

interface BadgeProps {
  children: ReactNode
  tone?: Tone
  dot?: boolean
  className?: string
}

export function levelTone(nivel: string): LevelTone {
  const value = nivel.toLowerCase()
  if (['alto', 'high', 'critical'].includes(value)) return 'alto'
  if (['medio', 'medium', 'media'].includes(value)) return 'medio'
  return 'baja'
}

export function Badge({ children, tone = 'neutral', dot = false, className }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider',
        tones[tone],
        className,
      )}
    >
      {dot && <span className="h-1.5 w-1.5 rounded-full bg-current" />}
      {children}
    </span>
  )
}

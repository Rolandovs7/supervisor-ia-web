import { CheckCircle2, Clock3, ShieldAlert } from 'lucide-react'

import type { Alerta } from '../lib/types'
import { cn, formatTime, shortId } from '../lib/utils'
import { Badge, levelTone } from './ui/Badge'

interface AlertCardProps {
  alerta: Alerta
  obraNombre?: string
  isLive?: boolean
}

const borderByTone: Record<'alto' | 'medio' | 'baja', string> = {
  alto: 'border-l-rose-500',
  medio: 'border-l-amber-500',
  baja: 'border-l-emerald-500',
}

export function AlertCard({ alerta, obraNombre, isLive = false }: AlertCardProps) {
  const tone = levelTone(alerta.nivel)

  return (
    <article
      className={cn(
        'surface animate-fade-up rounded-xl border-l-4 p-4 transition-all hover:-translate-y-0.5 hover:shadow-lg',
        borderByTone[tone],
      )}
    >
      <div className="flex items-start gap-3">
        <div
          className={cn(
            'flex h-10 w-10 shrink-0 items-center justify-center rounded-xl',
            tone === 'alto' && 'bg-rose-500/10 text-rose-500',
            tone === 'medio' && 'bg-amber-500/10 text-amber-500',
            tone === 'baja' && 'bg-emerald-500/10 text-emerald-500',
          )}
        >
          <ShieldAlert className="h-5 w-5" />
        </div>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <p className="text-sm font-bold text-slate-900 dark:text-white">
              {alerta.descripcion}
            </p>
            {isLive && (
              <span className="inline-flex items-center gap-1 rounded-full bg-accent-500/10 px-2 py-0.5 text-[9px] font-extrabold uppercase tracking-wider text-accent-600 dark:text-accent-100">
                <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-accent-500" />
                En vivo
              </span>
            )}
          </div>

          <div className="mt-2 flex flex-wrap items-center gap-2">
            <Badge tone={tone} dot>
              Nivel {alerta.nivel}
            </Badge>
            {alerta.resuelta ? (
              <Badge tone="success">
                <CheckCircle2 className="mr-0.5 h-3 w-3" /> Resuelta
              </Badge>
            ) : (
              <Badge tone="neutral">Pendiente</Badge>
            )}
            <Badge tone="info">{alerta.tipo}</Badge>
          </div>

          <div className="muted mt-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px]">
            <span className="inline-flex items-center gap-1.5">
              <Clock3 className="h-3.5 w-3.5" />
              {alerta.created_at ? formatTime(alerta.created_at) : 'Ahora'}
            </span>
            {obraNombre && <span>OBRA · {obraNombre}</span>}
            {alerta.imagen_id && <span>IMG · {shortId(alerta.imagen_id)}</span>}
          </div>
        </div>
      </div>
    </article>
  )
}

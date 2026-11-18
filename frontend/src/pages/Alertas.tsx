import { useEffect, useMemo, useState } from 'react'
import { BellRing, CheckCircle2, Clock3, RefreshCw } from 'lucide-react'

import { Badge, levelTone } from '../components/ui/Badge'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Select } from '../components/ui/Select'
import { Toast } from '../components/ui/Toast'
import { alertasApi, errorMessage, obrasApi } from '../lib/api'
import type { Alerta, Obra } from '../lib/types'
import { cn, formatDate, formatTime } from '../lib/utils'

type StatusFilter = 'todas' | 'pendientes' | 'resueltas'

export function Alertas() {
  const [alertas, setAlertas] = useState<Alerta[]>([])
  const [obras, setObras] = useState<Obra[]>([])
  const [loading, setLoading] = useState(true)
  const [obraFilter, setObraFilter] = useState('')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('todas')
  const [resolvingId, setResolvingId] = useState<string | null>(null)
  const [toast, setToast] = useState<{ message: string; tone: 'success' | 'error' } | null>(
    null,
  )

  const load = () => {
    setLoading(true)
    void Promise.all([alertasApi.list(), obrasApi.list()])
      .then(([rows, obraRows]) => {
        setAlertas([...rows].reverse())
        setObras(obraRows)
      })
      .catch((cause: unknown) =>
        setToast({ message: errorMessage(cause, 'No se pudieron cargar las alertas.'), tone: 'error' }),
      )
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [])

  const filtered = useMemo(() => {
    return alertas.filter((alerta) => {
      if (obraFilter && alerta.obra_id !== obraFilter) return false
      if (statusFilter === 'pendientes' && alerta.resuelta) return false
      if (statusFilter === 'resueltas' && !alerta.resuelta) return false
      return true
    })
  }, [alertas, obraFilter, statusFilter])

  const pendingCount = alertas.filter((alerta) => !alerta.resuelta).length
  const obraNames = useMemo(
    () => new Map(obras.map((obra) => [obra.id, obra.nombre])),
    [obras],
  )

  const handleResolve = async (alerta: Alerta) => {
    setResolvingId(alerta.id)
    try {
      const updated = await alertasApi.resolve(alerta.id)
      setAlertas((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      )
      setToast({ message: 'Alerta marcada como resuelta.', tone: 'success' })
    } catch (cause) {
      setToast({ message: errorMessage(cause, 'No se pudo resolver la alerta.'), tone: 'error' })
    } finally {
      setResolvingId(null)
    }
  }

  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-3">
        {[
          { label: 'Total alertas', value: alertas.length, icon: BellRing, tone: 'blue' },
          { label: 'Pendientes', value: pendingCount, icon: Clock3, tone: 'amber' },
          {
            label: 'Resueltas',
            value: alertas.length - pendingCount,
            icon: CheckCircle2,
            tone: 'emerald',
          },
        ].map(({ label, value, icon: Icon, tone }) => (
          <div key={label} className="surface flex items-center gap-4 rounded-2xl p-4">
            <div
              className={cn(
                'flex h-11 w-11 items-center justify-center rounded-xl',
                tone === 'blue' && 'bg-accent-500/10 text-accent-500',
                tone === 'amber' && 'bg-amber-500/10 text-amber-500',
                tone === 'emerald' && 'bg-emerald-500/10 text-emerald-500',
              )}
            >
              <Icon className="h-5 w-5" />
            </div>
            <div>
              <p className="muted text-[11px] font-bold uppercase tracking-wider">{label}</p>
              <p className="text-xl font-extrabold text-slate-900 dark:text-white">{value}</p>
            </div>
          </div>
        ))}
      </div>

      <Card
        title="Historial de alertas"
        subtitle="Todos los eventos de seguridad registrados"
        bodyClassName="p-0"
        action={
          <Button
            variant="outline"
            size="sm"
            onClick={load}
            leftIcon={<RefreshCw className={loading ? 'h-3.5 w-3.5 animate-spin' : 'h-3.5 w-3.5'} />}
          >
            Actualizar
          </Button>
        }
      >
        <div className="flex flex-wrap gap-3 border-b border-slate-200 p-5 dark:border-slate-800/80">
          <div className="w-full sm:w-56">
            <Select value={obraFilter} onChange={(event) => setObraFilter(event.target.value)}>
              <option value="">Todas las obras</option>
              {obras.map((obra) => (
                <option key={obra.id} value={obra.id}>
                  {obra.nombre}
                </option>
              ))}
            </Select>
          </div>
          <div className="w-full sm:w-48">
            <Select
              value={statusFilter}
              onChange={(event) => setStatusFilter(event.target.value as StatusFilter)}
            >
              <option value="todas">Todos los estados</option>
              <option value="pendientes">Pendientes</option>
              <option value="resueltas">Resueltas</option>
            </Select>
          </div>
        </div>

        {loading ? (
          <div className="space-y-3 p-6">
            {[0, 1, 2, 3].map((key) => (
              <div key={key} className="h-14 animate-pulse rounded-xl bg-slate-100 dark:bg-white/5" />
            ))}
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex flex-col items-center py-14 text-center">
            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-400 dark:bg-white/5">
              <BellRing className="h-6 w-6" />
            </div>
            <p className="text-sm font-bold text-slate-800 dark:text-slate-100">
              No hay alertas que coincidan
            </p>
            <p className="muted mt-2 text-xs">Prueba con otro filtro o espera nuevos eventos.</p>
          </div>
        ) : (
          <div className="scrollbar-thin overflow-x-auto">
            <table className="w-full min-w-[860px] text-left text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-[10px] font-bold uppercase tracking-[0.14em] text-slate-400 dark:border-slate-800/80">
                  <th className="px-5 py-3.5">Alerta</th>
                  <th className="px-4 py-3.5">Obra</th>
                  <th className="px-4 py-3.5">Nivel</th>
                  <th className="px-4 py-3.5">Estado</th>
                  <th className="px-4 py-3.5">Fecha</th>
                  <th className="px-5 py-3.5 text-right">Acción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-800/80">
                {filtered.map((alerta) => (
                  <tr
                    key={alerta.id}
                    className="transition-colors hover:bg-slate-50 dark:hover:bg-white/[0.03]"
                  >
                    <td className="px-5 py-4">
                      <p className="font-bold text-slate-800 dark:text-slate-100">
                        {alerta.descripcion}
                      </p>
                      <p className="muted mt-1 text-[11px] uppercase tracking-wider">
                        {alerta.tipo}
                      </p>
                    </td>
                    <td className="px-4 py-4 text-xs text-slate-600 dark:text-slate-300">
                      {alerta.obra_id ? (obraNames.get(alerta.obra_id) ?? 'Obra eliminada') : '—'}
                    </td>
                    <td className="px-4 py-4">
                      <Badge tone={levelTone(alerta.nivel)} dot>
                        {alerta.nivel}
                      </Badge>
                    </td>
                    <td className="px-4 py-4">
                      {alerta.resuelta ? (
                        <Badge tone="success">Resuelta</Badge>
                      ) : (
                        <Badge tone="neutral">Pendiente</Badge>
                      )}
                    </td>
                    <td className="muted px-4 py-4 text-xs">
                      <p>{formatDate(alerta.created_at)}</p>
                      <p className="mt-0.5">{formatTime(alerta.created_at)}</p>
                    </td>
                    <td className="px-5 py-4 text-right">
                      {alerta.resuelta ? (
                        <span className="muted inline-flex items-center gap-1.5 text-xs">
                          <CheckCircle2 className="h-4 w-4 text-emerald-500" /> Completada
                        </span>
                      ) : (
                        <Button
                          size="sm"
                          variant="outline"
                          loading={resolvingId === alerta.id}
                          onClick={() => void handleResolve(alerta)}
                          leftIcon={<CheckCircle2 className="h-3.5 w-3.5" />}
                        >
                          Resolver
                        </Button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Toast
        message={toast?.message ?? null}
        tone={toast?.tone ?? 'success'}
        onDismiss={() => setToast(null)}
      />
    </div>
  )
}

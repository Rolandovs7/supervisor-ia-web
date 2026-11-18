import { useEffect, useMemo, useRef, useState, type DragEvent } from 'react'
import {
  Activity,
  Building2,
  Camera,
  CircleAlert,
  CloudUpload,
  FileImage,
  Images,
  Radio,
  X,
  type LucideIcon,
} from 'lucide-react'

import { AlertCard } from '../components/AlertCard'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Select } from '../components/ui/Select'
import { Toast } from '../components/ui/Toast'
import { useAlertSocket } from '../context/WebSocketContext'
import { alertasApi, errorMessage, metricsApi, obrasApi, uploadImage } from '../lib/api'
import type { Alerta, Metrics, Obra } from '../lib/types'
import { cn, formatDate } from '../lib/utils'

interface MetricCardProps {
  label: string
  value: number | null
  hint: string
  icon: LucideIcon
  accent: 'blue' | 'amber' | 'emerald'
}

const accentStyles = {
  blue: 'bg-accent-500/10 text-accent-500',
  amber: 'bg-amber-500/10 text-amber-500',
  emerald: 'bg-emerald-500/10 text-emerald-500',
}

function MetricCard({ label, value, hint, icon: Icon, accent }: MetricCardProps) {
  return (
    <div className="surface surface-hover relative overflow-hidden rounded-2xl p-5">
      <div className={cn('mb-5 inline-flex rounded-xl p-3', accentStyles[accent])}>
        <Icon className="h-5 w-5" />
      </div>
      <p className="muted text-[11px] font-bold uppercase tracking-[0.14em]">{label}</p>
      <p className="mt-1.5 text-3xl font-extrabold tracking-tight text-slate-900 dark:text-white">
        {value ?? '—'}
      </p>
      <p className="muted mt-2 text-[11px]">{hint}</p>
      <div className="pointer-events-none absolute -right-8 -top-10 h-28 w-28 rounded-full bg-current opacity-[0.04]" />
    </div>
  )
}

export function Dashboard() {
  const { alerts: liveAlerts, isConnected } = useAlertSocket()
  const [today] = useState(() => formatDate(new Date().toISOString()))

  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [obras, setObras] = useState<Obra[]>([])
  const [history, setHistory] = useState<Alerta[]>([])
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [obraId, setObraId] = useState('')
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [toast, setToast] = useState<{ message: string; tone: 'success' | 'error' } | null>(
    null,
  )
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    let active = true
    void Promise.all([obrasApi.list(), metricsApi.get(), alertasApi.list()])
      .then(([obraRows, metricRows, alertRows]) => {
        if (!active) return
        setObras(obraRows)
        setMetrics(metricRows)
        setHistory([...alertRows].reverse().slice(0, 6))
      })
      .catch(() => {
        if (active) setToast({ message: 'No se pudieron cargar los datos.', tone: 'error' })
      })
    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    if (!file) {
      setPreview(null)
      return
    }
    const url = URL.createObjectURL(file)
    setPreview(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  const liveIds = useMemo(() => new Set(liveAlerts.map((alert) => alert.id)), [liveAlerts])

  const feed = useMemo(() => {
    const merged = new Map<string, Alerta>()
    for (const alert of [...liveAlerts, ...history]) {
      merged.set(alert.id, alert)
    }
    return [...merged.values()]
      .sort((a, b) =>
        (b.created_at ?? '').localeCompare(a.created_at ?? ''),
      )
      .slice(0, 7)
  }, [liveAlerts, history])

  const obraNames = useMemo(
    () => new Map(obras.map((obra) => [obra.id, obra.nombre])),
    [obras],
  )

  const acceptFile = (candidate?: File | null) => {
    if (!candidate) return
    setFile(candidate)
    setToast(null)
  }

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setDragging(false)
    acceptFile(event.dataTransfer.files[0])
  }

  const handleUpload = async () => {
    if (!file) {
      setToast({ message: 'Selecciona una imagen antes de subirla.', tone: 'error' })
      return
    }
    setUploading(true)
    try {
      await uploadImage(file, obraId || undefined)
      setToast({
        message: 'Imagen enviada. La alerta aparecerá en tiempo real.',
        tone: 'success',
      })
      setFile(null)
      if (inputRef.current) inputRef.current.value = ''
      const refreshed = await metricsApi.get()
      setMetrics(refreshed)
    } catch (cause) {
      setToast({ message: errorMessage(cause, 'No se pudo subir la imagen.'), tone: 'error' })
    } finally {
      setUploading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-[11px] font-bold uppercase tracking-[0.2em] text-accent-500">
            Resumen operativo
          </p>
          <p className="muted mt-1 text-sm">
            Actualizado el {today}
          </p>
        </div>
        <div
          className={cn(
            'inline-flex items-center gap-2 rounded-full border px-3 py-2 text-[11px] font-bold',
            isConnected
              ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-600 dark:text-emerald-300'
              : 'border-slate-300 text-slate-500 dark:border-slate-700 dark:text-slate-400',
          )}
        >
          <Radio className={cn('h-3.5 w-3.5', isConnected && 'animate-pulse')} />
          {isConnected ? 'Streaming en vivo' : 'Reconectando stream'}
        </div>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        <MetricCard
          label="Total obras"
          value={metrics?.total_obras ?? null}
          hint="Proyectos bajo supervisión"
          icon={Building2}
          accent="blue"
        />
        <MetricCard
          label="Alertas pendientes"
          value={metrics?.alertas_pendientes ?? null}
          hint="Requieren revisión del supervisor"
          icon={CircleAlert}
          accent="amber"
        />
        <MetricCard
          label="Imágenes procesadas"
          value={metrics?.imagenes_procesadas ?? null}
          hint="Analizadas por el modelo"
          icon={Images}
          accent="emerald"
        />
      </div>

      <div className="grid gap-6 xl:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)]">
        <Card
          title="Subida rápida"
          subtitle="Carga una imagen para analizarla automáticamente"
          action={
            <span className="inline-flex items-center gap-1.5 rounded-lg bg-accent-500/10 px-2.5 py-1.5 text-[10px] font-bold uppercase tracking-wider text-accent-600 dark:text-accent-100">
              <Activity className="h-3.5 w-3.5" /> YOLOv8
            </span>
          }
        >
          <div
            onDragOver={(event) => {
              event.preventDefault()
              setDragging(true)
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            className={cn(
              'group relative flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed px-5 py-9 text-center transition-all',
              dragging
                ? 'border-accent-500 bg-accent-500/5'
                : 'border-slate-300 bg-slate-50 hover:border-accent-500/60 hover:bg-accent-500/[0.03] dark:border-slate-700 dark:bg-slate-900/40',
            )}
          >
            <input
              ref={inputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(event) => acceptFile(event.target.files?.[0])}
            />
            {preview ? (
              <div className="flex w-full flex-col items-center gap-3">
                <img
                  src={preview}
                  alt="Vista previa"
                  className="h-32 w-full rounded-xl object-cover ring-1 ring-slate-200 dark:ring-slate-700"
                />
                <div className="flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-200">
                  <FileImage className="h-4 w-4 text-accent-500" />
                  <span className="max-w-[220px] truncate">{file?.name}</span>
                  <span
                    role="button"
                    tabIndex={0}
                    onClick={(event) => {
                      event.stopPropagation()
                      setFile(null)
                    }}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter') setFile(null)
                    }}
                    className="rounded-md p-1 text-slate-400 hover:bg-slate-200 hover:text-rose-500 dark:hover:bg-white/10"
                  >
                    <X className="h-3.5 w-3.5" />
                  </span>
                </div>
              </div>
            ) : (
              <>
                <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-accent-500/10 text-accent-500 transition-transform group-hover:scale-105">
                  <CloudUpload className="h-7 w-7" />
                </div>
                <p className="text-sm font-bold text-slate-800 dark:text-slate-100">
                  Arrastra una imagen aquí
                </p>
                <p className="muted mt-1 text-xs">o haz clic para seleccionar un archivo</p>
                <p className="muted mt-3 text-[10px] uppercase tracking-wider">
                  PNG, JPG o WEBP
                </p>
              </>
            )}
          </div>

          <div className="mt-5 grid gap-4 sm:grid-cols-[1fr_auto] sm:items-end">
            <Select
              label="Obra asociada (opcional)"
              value={obraId}
              onChange={(event) => setObraId(event.target.value)}
            >
              <option value="">Sin obra asignada</option>
              {obras.map((obra) => (
                <option key={obra.id} value={obra.id}>
                  {obra.nombre}
                </option>
              ))}
            </Select>
            <Button
              onClick={() => void handleUpload()}
              loading={uploading}
              disabled={!file}
              leftIcon={<Camera className="h-4 w-4" />}
              className="h-11"
            >
              Analizar imagen
            </Button>
          </div>

          {obras.length === 0 && (
            <p className="muted mt-3 text-[11px]">
              Aún no hay obras registradas. Puedes subir la imagen sin asociarla.
            </p>
          )}
        </Card>

        <Card
          title="Actividad en tiempo real"
          subtitle="Alertas recibidas por WebSocket"
          bodyClassName="p-4 sm:p-5"
          action={
            <span className="muted inline-flex items-center gap-1.5 text-[11px] font-semibold">
              <span className="h-1.5 w-1.5 rounded-full bg-accent-500" />
              {liveAlerts.length} en vivo
            </span>
          }
        >
          {feed.length === 0 ? (
            <div className="flex min-h-[280px] flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 p-8 text-center dark:border-slate-700">
              <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-400 dark:bg-white/5">
                <Radio className="h-6 w-6" />
              </div>
              <p className="text-sm font-bold text-slate-700 dark:text-slate-200">
                Esperando eventos
              </p>
              <p className="muted mt-2 max-w-xs text-xs leading-relaxed">
                Las alertas aparecerán aquí en cuanto se detecten personas en una imagen.
              </p>
            </div>
          ) : (
            <div className="scrollbar-thin max-h-[520px] space-y-3 overflow-y-auto pr-1">
              {feed.map((alert) => (
                <AlertCard
                  key={alert.id}
                  alerta={alert}
                  obraNombre={alert.obra_id ? obraNames.get(alert.obra_id) : undefined}
                  isLive={liveIds.has(alert.id)}
                />
              ))}
            </div>
          )}
        </Card>
      </div>

      <Toast
        message={toast?.message ?? null}
        tone={toast?.tone ?? 'success'}
        onDismiss={() => setToast(null)}
      />
    </div>
  )
}

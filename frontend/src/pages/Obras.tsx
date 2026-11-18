import { useEffect, useState, type FormEvent } from 'react'
import {
  Building2,
  CalendarDays,
  FileDown,
  MapPin,
  Plus,
  RefreshCw,
} from 'lucide-react'

import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Input } from '../components/ui/Input'
import { Modal } from '../components/ui/Modal'
import { Toast } from '../components/ui/Toast'
import { errorMessage, obrasApi } from '../lib/api'
import type { Obra, ObraInput } from '../lib/types'
import { formatDate, shortId } from '../lib/utils'

const emptyForm: ObraInput = {
  nombre: '',
  ubicacion: '',
  fecha_inicio: '',
  fecha_fin: '',
}

export function Obras() {
  const [obras, setObras] = useState<Obra[]>([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState<ObraInput>(emptyForm)
  const [formError, setFormError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [downloadingId, setDownloadingId] = useState<string | null>(null)
  const [toast, setToast] = useState<{ message: string; tone: 'success' | 'error' } | null>(
    null,
  )

  const load = () => {
    setLoading(true)
    obrasApi
      .list()
      .then(setObras)
      .catch((cause: unknown) =>
        setToast({ message: errorMessage(cause, 'No se pudieron cargar las obras.'), tone: 'error' }),
      )
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    load()
  }, [])

  const handleCreate = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setFormError(null)

    if (!form.nombre.trim()) {
      setFormError('El nombre de la obra es obligatorio.')
      return
    }
    if (form.fecha_inicio && form.fecha_fin && form.fecha_inicio > form.fecha_fin) {
      setFormError('La fecha de fin debe ser posterior a la de inicio.')
      return
    }

    setSaving(true)
    try {
      const created = await obrasApi.create({
        nombre: form.nombre.trim(),
        ubicacion: form.ubicacion?.trim() || null,
        fecha_inicio: form.fecha_inicio || null,
        fecha_fin: form.fecha_fin || null,
      })
      setObras((current) => [created, ...current])
      setModalOpen(false)
      setForm(emptyForm)
      setToast({ message: 'Obra registrada correctamente.', tone: 'success' })
    } catch (cause) {
      setFormError(errorMessage(cause, 'No se pudo registrar la obra.'))
    } finally {
      setSaving(false)
    }
  }

  const handleDownload = async (obra: Obra) => {
    setDownloadingId(obra.id)
    try {
      await obrasApi.downloadReport(obra)
      setToast({ message: 'Reporte PDF descargado correctamente.', tone: 'success' })
    } catch (cause) {
      setToast({ message: errorMessage(cause, 'No se pudo descargar el reporte.'), tone: 'error' })
    } finally {
      setDownloadingId(null)
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-accent-500/10 text-accent-500">
            <Building2 className="h-5 w-5" />
          </div>
          <div>
            <p className="text-lg font-extrabold text-slate-900 dark:text-white">
              {obras.length} {obras.length === 1 ? 'obra registrada' : 'obras registradas'}
            </p>
            <p className="muted text-xs">Proyectos bajo supervisión de seguridad</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={load}
            leftIcon={<RefreshCw className={loading ? 'h-4 w-4 animate-spin' : 'h-4 w-4'} />}
          >
            Actualizar
          </Button>
          <Button onClick={() => setModalOpen(true)} leftIcon={<Plus className="h-4 w-4" />}>
            Nueva obra
          </Button>
        </div>
      </div>

      {loading ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {[0, 1, 2].map((key) => (
            <div key={key} className="surface h-44 animate-pulse rounded-2xl" />
          ))}
        </div>
      ) : obras.length === 0 ? (
        <Card>
          <div className="flex flex-col items-center py-10 text-center">
            <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-slate-100 text-slate-400 dark:bg-white/5">
              <Building2 className="h-6 w-6" />
            </div>
            <p className="text-sm font-bold text-slate-800 dark:text-slate-100">
              Aún no hay obras registradas
            </p>
            <p className="muted mt-2 max-w-sm text-xs">
              Registra tu primera obra para asociar imágenes y alertas a un proyecto.
            </p>
            <Button
              className="mt-5"
              onClick={() => setModalOpen(true)}
              leftIcon={<Plus className="h-4 w-4" />}
            >
              Registrar obra
            </Button>
          </div>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {obras.map((obra) => (
            <article
              key={obra.id}
              className="surface surface-hover group animate-fade-up relative overflow-hidden rounded-2xl p-5"
            >
              <div className="absolute right-0 top-0 h-20 w-20 rounded-bl-[3rem] bg-accent-500/[0.06]" />
              <div className="mb-5 flex items-start justify-between">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-slate-700 to-slate-900 text-white dark:from-accent-500 dark:to-accent-600">
                  <Building2 className="h-5 w-5" />
                </div>
                <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-emerald-600 dark:text-emerald-300">
                  Activa
                </span>
              </div>
              <h3 className="text-base font-extrabold text-slate-900 dark:text-white">
                {obra.nombre}
              </h3>
              <div className="muted mt-3 space-y-2 text-xs">
                <p className="flex items-center gap-2">
                  <MapPin className="h-3.5 w-3.5 shrink-0" />
                  <span className="truncate">{obra.ubicacion || 'Sin ubicación'}</span>
                </p>
                <p className="flex items-center gap-2">
                  <CalendarDays className="h-3.5 w-3.5 shrink-0" />
                  <span>
                    {formatDate(obra.fecha_inicio)} — {formatDate(obra.fecha_fin)}
                  </span>
                </p>
              </div>
              <div className="mt-5 border-t border-slate-200 pt-4 dark:border-slate-800/80">
                <p className="font-mono text-[10px] text-slate-400">ID · {shortId(obra.id)}</p>
                <Button
                  variant="outline"
                  size="sm"
                  className="mt-3 w-full"
                  loading={downloadingId === obra.id}
                  leftIcon={<FileDown className="h-3.5 w-3.5" />}
                  onClick={() => void handleDownload(obra)}
                >
                  Descargar Reporte PDF
                </Button>
              </div>
            </article>
          ))}
        </div>
      )}

      <Modal
        open={modalOpen}
        onClose={() => {
          setModalOpen(false)
          setFormError(null)
        }}
        title="Registrar nueva obra"
        description="Los datos se guardarán en la base de datos del proyecto."
      >
        <form onSubmit={(event) => void handleCreate(event)} className="space-y-4">
          {formError && (
            <p className="rounded-xl border border-rose-500/30 bg-rose-500/10 px-3 py-2 text-xs font-medium text-rose-600 dark:text-rose-300">
              {formError}
            </p>
          )}
          <Input
            label="Nombre de la obra *"
            placeholder="Ej. Torre Norte"
            value={form.nombre}
            onChange={(event) => setForm({ ...form, nombre: event.target.value })}
          />
          <Input
            label="Ubicación"
            placeholder="Ej. Av. Principal 123, Lima"
            value={form.ubicacion ?? ''}
            onChange={(event) => setForm({ ...form, ubicacion: event.target.value })}
          />
          <div className="grid gap-4 sm:grid-cols-2">
            <Input
              label="Fecha de inicio"
              type="date"
              value={form.fecha_inicio ?? ''}
              onChange={(event) => setForm({ ...form, fecha_inicio: event.target.value })}
            />
            <Input
              label="Fecha de fin"
              type="date"
              value={form.fecha_fin ?? ''}
              onChange={(event) => setForm({ ...form, fecha_fin: event.target.value })}
            />
          </div>
          <div className="flex justify-end gap-2 pt-3">
            <Button variant="ghost" onClick={() => setModalOpen(false)}>
              Cancelar
            </Button>
            <Button type="submit" loading={saving}>
              Guardar obra
            </Button>
          </div>
        </form>
      </Modal>

      <Toast
        message={toast?.message ?? null}
        tone={toast?.tone ?? 'success'}
        onDismiss={() => setToast(null)}
      />
    </div>
  )
}

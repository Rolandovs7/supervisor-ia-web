import axios from 'axios'

import { clearSession, getToken } from './auth'
import type { Alerta, LoginResponse, Metrics, Obra, ObraInput } from './types'

export const API_BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60_000,
})

api.interceptors.request.use((config) => {
  const token = getToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      clearSession()
      if (!window.location.pathname.startsWith('/login')) {
        window.location.replace('/login')
      }
    }
    return Promise.reject(error)
  },
)

export function errorMessage(error: unknown, fallback = 'Algo salió mal. Inténtalo de nuevo.'): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail as string | { msg?: string } | undefined
    if (typeof detail === 'string') return detail
    if (detail && typeof detail === 'object' && detail.msg) return detail.msg
    return error.message || fallback
  }
  return fallback
}

export const authApi = {
  async login(email: string, password: string): Promise<LoginResponse> {
    const { data } = await api.post<LoginResponse>('/login', { email, password })
    return data
  },
}

export const obrasApi = {
  async list(): Promise<Obra[]> {
    const { data } = await api.get<Obra[]>('/obras')
    return data
  },
  async create(payload: ObraInput): Promise<Obra> {
    const { data } = await api.post<Obra>('/obras', payload)
    return data
  },
  async downloadReport(obra: Obra): Promise<void> {
    const response = await api.get<Blob>(
      `/obras/${encodeURIComponent(obra.id)}/reporte`,
      { responseType: 'blob' },
    )
    const disposition = response.headers['content-disposition'] as string | undefined
    const match = disposition ? /filename="?([^";]+)"?/.exec(disposition) : null
    const slug = obra.nombre
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^A-Za-z0-9_-]+/g, '-')
      .replace(/^-+|-+$/g, '')
    const filename = match?.[1] ?? `reporte-${slug || 'obra'}.pdf`

    const url = URL.createObjectURL(response.data)
    const anchor = document.createElement('a')
    anchor.href = url
    anchor.download = filename
    document.body.appendChild(anchor)
    anchor.click()
    anchor.remove()
    window.setTimeout(() => URL.revokeObjectURL(url), 1000)
  },
}

export const alertasApi = {
  async list(obraId?: string): Promise<Alerta[]> {
    const { data } = await api.get<Alerta[]>('/alertas', {
      params: obraId ? { obra_id: obraId } : undefined,
    })
    return data
  },
  async resolve(alertaId: string): Promise<Alerta> {
    const { data } = await api.put<Alerta>(
      `/alertas/${encodeURIComponent(alertaId)}/resolver`,
    )
    return data
  },
}

export const metricsApi = {
  async get(): Promise<Metrics> {
    const { data } = await api.get<Metrics>('/metrics')
    return data
  },
}

export async function uploadImage(file: File, obraId?: string): Promise<void> {
  const form = new FormData()
  form.append('file', file)
  if (obraId) form.append('obra_id', obraId)
  await api.post('/upload', form)
}

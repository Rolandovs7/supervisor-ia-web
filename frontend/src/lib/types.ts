export interface AuthUser {
  id: string
  email: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user: AuthUser
}

export interface Obra {
  id: string
  nombre: string
  ubicacion?: string | null
  fecha_inicio?: string | null
  fecha_fin?: string | null
}

export type ObraInput = Pick<
  Obra,
  'nombre' | 'ubicacion' | 'fecha_inicio' | 'fecha_fin'
>

export interface Alerta {
  id: string
  obra_id?: string | null
  analisis_id?: string | null
  imagen_id?: string | null
  tipo: string
  descripcion: string
  nivel: string
  resuelta: boolean
  created_at?: string
}

export interface WsAlertMessage {
  type: 'alerta'
  alerta: Alerta
}

export interface Metrics {
  total_obras: number
  alertas_pendientes: number
  imagenes_procesadas: number
}

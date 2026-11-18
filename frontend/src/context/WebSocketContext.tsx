import {
  createContext,
  useContext,
  useMemo,
  type ReactNode,
} from 'react'

import { useWebSocket } from '../hooks/useWebSocket'
import type { Alerta } from '../lib/types'
import { useAuth } from './AuthContext'

interface WebSocketContextValue {
  alerts: Alerta[]
  isConnected: boolean
}

const WebSocketContext = createContext<WebSocketContextValue | null>(null)

export function WebSocketProvider({ children }: { children: ReactNode }) {
  const { token } = useAuth()
  const { alerts, isConnected } = useWebSocket(token)

  const value = useMemo<WebSocketContextValue>(
    () => ({ alerts, isConnected }),
    [alerts, isConnected],
  )

  return (
    <WebSocketContext.Provider value={value}>{children}</WebSocketContext.Provider>
  )
}

export function useAlertSocket(): WebSocketContextValue {
  const context = useContext(WebSocketContext)
  if (!context) {
    throw new Error('useAlertSocket debe usarse dentro de WebSocketProvider')
  }
  return context
}

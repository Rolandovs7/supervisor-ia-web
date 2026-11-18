import { useCallback, useEffect, useRef, useState } from 'react'

import type { Alerta, WsAlertMessage } from '../lib/types'
import { buildWsUrl } from '../lib/ws'

const MAX_BACKOFF_MS = 30_000

export interface UseWebSocketResult {
  alerts: Alerta[]
  isConnected: boolean
}

/** Connects to /ws/alertas, reconnects with backoff and collects live alerts. */
export function useWebSocket(token: string | null): UseWebSocketResult {
  const [alerts, setAlerts] = useState<Alerta[]>([])
  const [isConnected, setIsConnected] = useState(false)

  const socketRef = useRef<WebSocket | null>(null)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const attemptsRef = useRef(0)
  const mountedRef = useRef(true)
  const connectRef = useRef<() => void>(() => {})

  useEffect(() => {
    mountedRef.current = true
    return () => {
      mountedRef.current = false
    }
  }, [])

  const scheduleReconnect = useCallback(() => {
    if (timerRef.current || !mountedRef.current || !token) return
    const delay = Math.min(1_000 * 2 ** attemptsRef.current, MAX_BACKOFF_MS)
    attemptsRef.current += 1
    timerRef.current = setTimeout(() => {
      timerRef.current = null
      connectRef.current()
    }, delay)
  }, [token])

  const connect = useCallback(() => {
    if (!token || !mountedRef.current) return

    let socket: WebSocket
    try {
      socket = new WebSocket(buildWsUrl(token))
    } catch {
      scheduleReconnect()
      return
    }
    socketRef.current = socket

    socket.onopen = () => {
      if (!mountedRef.current) return
      setIsConnected(true)
      attemptsRef.current = 0
    }

    socket.onmessage = (event: MessageEvent<string>) => {
      try {
        const payload = JSON.parse(event.data) as WsAlertMessage
        if (payload.type !== 'alerta' || !payload.alerta?.id) return
        setAlerts((current) =>
          [
            payload.alerta,
            ...current.filter((item) => item.id !== payload.alerta.id),
          ].slice(0, 50),
        )
      } catch {
        // Ignore malformed frames.
      }
    }

    socket.onclose = () => {
      if (socketRef.current === socket) socketRef.current = null
      if (!mountedRef.current || !token) return
      setIsConnected(false)
      scheduleReconnect()
    }

    socket.onerror = () => {
      // onclose performs the reconnect.
    }
  }, [token, scheduleReconnect])

  useEffect(() => {
    connectRef.current = connect
  }, [connect])

  useEffect(() => {
    if (!token) {
      setAlerts([])
      setIsConnected(false)
      return
    }

    attemptsRef.current = 0
    connect()

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current)
        timerRef.current = null
      }
      const socket = socketRef.current
      socketRef.current = null
      if (socket) {
        socket.onclose = null
        socket.close()
      }
      setIsConnected(false)
    }
  }, [token, connect])

  return { alerts, isConnected }
}

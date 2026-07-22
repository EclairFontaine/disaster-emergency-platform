import { useEffect, useRef, useState, useCallback } from 'react'

interface WsMessage {
  event?: string
  data?: any
  type?: string
}

interface UseWebSocketOptions {
  onEvent?: (event: string, data: any) => void
}

export function useWebSocket({ onEvent }: UseWebSocketOptions = {}) {
  const [connected, setConnected] = useState(false)
  const [lastMessage, setLastMessage] = useState<WsMessage | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const retryRef = useRef(0)
  const maxRetries = 10

  const connect = useCallback(() => {
    const token = localStorage.getItem('token')
    if (!token) return

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = window.location.host
    const url = `${protocol}//${host}/api/ws?token=${token}`

    try {
      const ws = new WebSocket(url)
      wsRef.current = ws

      ws.onopen = () => {
        setConnected(true)
        retryRef.current = 0
      }

      ws.onmessage = (event) => {
        try {
          const msg: WsMessage = JSON.parse(event.data)
          if (msg.type === 'pong') return
          setLastMessage(msg)
          onEvent?.(msg.event || '', msg.data)
        } catch {}
      }

      ws.onclose = (e) => {
        setConnected(false)
        wsRef.current = null
        if (e.code !== 4001 && retryRef.current < maxRetries) {
          retryRef.current++
          const delay = Math.min(1000 * Math.pow(2, retryRef.current), 30000)
          setTimeout(connect, delay)
        }
      }

      ws.onerror = () => {
        ws.close()
      }
    } catch {
      if (retryRef.current < maxRetries) {
        retryRef.current++
        setTimeout(connect, 5000)
      }
    }
  }, [onEvent])

  useEffect(() => {
    connect()
    return () => {
      wsRef.current?.close()
      wsRef.current = null
    }
  }, [connect])

  return { connected, lastMessage }
}

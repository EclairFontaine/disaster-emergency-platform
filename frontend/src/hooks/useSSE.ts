import { useState, useEffect, useRef } from 'react'

export function useSSE(url: string | null) {
  const [data, setData] = useState<any>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const retryRef = useRef(0)

  useEffect(() => {
    if (!url) return

    const token = localStorage.getItem('token')
    const fullUrl = `${url}${url.includes('?') ? '&' : '?'}token=${token}`
    const es = new EventSource(fullUrl)

    es.onopen = () => {
      setIsConnected(true)
      setError(null)
      retryRef.current = 0
    }

    es.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data)
        setData(parsed)
      } catch {
        setData(event.data)
      }
    }

    es.addEventListener('status', (event: any) => {
      try {
        setData(JSON.parse(event.data))
      } catch {
        setData(event.data)
      }
    })

    es.addEventListener('result', (event: any) => {
      try {
        setData(JSON.parse(event.data))
      } catch {
        setData(event.data)
      }
    })

    es.onerror = () => {
      setIsConnected(false)
      es.close()
      if (retryRef.current < 3) {
        retryRef.current++
      } else {
        setError('连接失败')
      }
    }

    return () => {
      es.close()
    }
  }, [url])

  return { data, isConnected, error }
}

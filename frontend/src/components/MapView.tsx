import { useEffect, useRef, useState } from 'react'

const AMAP_KEY = '3dccc7b093b657abea3c51b11f4e4e93'

interface MapViewProps {
  incidents?: any[]
  resources?: any[]
  onMapClick?: (pos: { lng: number; lat: number }) => void
  center?: { lng: number; lat: number }
  zoom?: number
  height?: string | number
}

export default function MapView({ incidents, resources, onMapClick, center, zoom, height }: MapViewProps) {
  const mapRef = useRef<HTMLDivElement>(null)
  const [status, setStatus] = useState<'loading' | 'loaded' | 'error'>('loading')
  const mapInstanceRef = useRef<any>(null)

  useEffect(() => {
    let cancelled = false

    async function initMap() {
      try {
        const AMapLoader = await import('@amap/amap-jsapi-loader')
        const AMap = await AMapLoader.default.load({
          key: AMAP_KEY,
          version: '2.0',
        })

        if (cancelled || !mapRef.current) return

        const map = new AMap.Map(mapRef.current, {
          zoom: zoom || 8,
          center: center ? [center.lng, center.lat] : [102.7, 25.0],
          resizeEnable: true,
        })
        mapInstanceRef.current = map

        if (onMapClick) {
          map.on('click', (e: any) => {
            onMapClick({ lng: e.lnglat.getLng(), lat: e.lnglat.getLat() })
          })
        }

        setStatus('loaded')
      } catch {
        if (!cancelled) setStatus('error')
      }
    }

    initMap()
    return () => { cancelled = true }
  }, [])

  useEffect(() => {
    if (status !== 'loaded' || !mapInstanceRef.current) return
    const AMap = (window as any).AMap
    if (!AMap) return

    mapInstanceRef.current.clearMap()
    ;(incidents || []).forEach((inc: any) => {
      if (inc.latitude && inc.longitude) {
        const marker = new AMap.Marker({ position: [inc.longitude, inc.latitude], title: inc.title })
        marker.setLabel({
          content: `<div style="background:#f5222d;color:#fff;padding:2px 6px;border-radius:4px;font-size:12px">${inc.title}</div>`,
          direction: 'top',
        })
        mapInstanceRef.current.add(marker)
      }
    })
    ;(resources || []).forEach((res: any) => {
      if (res.latitude && res.longitude) {
        const marker = new AMap.Marker({ position: [res.longitude, res.latitude], title: res.name })
        marker.setLabel({
          content: `<div style="background:#1890ff;color:#fff;padding:2px 6px;border-radius:4px;font-size:12px">${res.name}</div>`,
          direction: 'bottom',
        })
        mapInstanceRef.current.add(marker)
      }
    })
  }, [incidents, resources, status])

  return (
    <div
      ref={mapRef}
      style={{
        height: height || 400,
        width: '100%',
        background: status === 'error' ? '#e6f7ff' : '#f5f5f5',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: '#999',
        fontSize: 14,
      }}
    >
      {status === 'loading' && '地图加载中…'}
      {status === 'error' && '地图初始化失败，请配置高德地图 Key 后刷新'}
    </div>
  )
}

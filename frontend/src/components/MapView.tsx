import { useEffect, useRef, useState } from 'react'

const AMAP_KEY = '3dccc7b093b657abea3c51b11f4e4e93'

const severityColors: Record<string, string> = { P1: '#f5222d', P2: '#fa8c16', P3: '#1890ff', P4: '#52c41a' }
const statusLabels: Record<string, string> = { pending_review: '待核验', confirmed: '已确认', in_progress: '处置中', closed: '已结束' }
const categoryLabels: Record<string, string> = { earthquake: '地震', flood: '洪水', landslide: '山体滑坡', fire: '火灾', other: '其他' }

interface MapViewProps {
  incidents?: any[]
  resources?: any[]
  onMapClick?: (pos: { lng: number; lat: number }) => void
  onIncidentClick?: (incident: any) => void
  center?: { lng: number; lat: number }
  zoom?: number
  height?: string | number
}

export default function MapView({ incidents, resources, onMapClick, onIncidentClick, center, zoom, height }: MapViewProps) {
  const mapRef = useRef<HTMLDivElement>(null)
  const [status, setStatus] = useState<'loading' | 'loaded' | 'error'>('loading')
  const mapInstanceRef = useRef<any>(null)
  const infoWindowRef = useRef<any>(null)

  useEffect(() => {
    let cancelled = false
    async function initMap() {
      try {
        const AMapLoader = await import('@amap/amap-jsapi-loader')
        const AMap = await AMapLoader.default.load({
          key: AMAP_KEY, version: '2.0', plugins: ['AMap.InfoWindow'],
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
    const map = mapInstanceRef.current
    map.clearMap()
    if (infoWindowRef.current) { infoWindowRef.current.close(); infoWindowRef.current = null }

    ;(incidents || []).forEach((inc: any) => {
      if (!inc.latitude || !inc.longitude) return
      const color = severityColors[inc.severity] || '#f5222d'
      const cat = categoryLabels[inc.category] || '未知'
      const st = statusLabels[inc.status] || '未知'
      const marker = new AMap.Marker({ position: [inc.longitude, inc.latitude], title: inc.title })
      marker.setLabel({
        content: `<div style="background:${color};color:#fff;padding:2px 6px;border-radius:4px;font-size:12px;white-space:nowrap;max-width:100px;overflow:hidden;text-overflow:ellipsis">${inc.title}</div>`,
        direction: 'top',
      })
      const infoHtml = `<div style="padding:10px;min-width:220px;font-size:13px">
        <h4 style="margin:0 0 6px;font-size:15px">${inc.title}</h4>
        <p style="margin:3px 0"><b>类型:</b> ${cat}</p>
        <p style="margin:3px 0"><b>严重度:</b> <span style="color:${color};font-weight:bold">${inc.severity}</span></p>
        <p style="margin:3px 0"><b>状态:</b> ${st}</p>
        <p style="margin:3px 0"><b>影响人数:</b> ${inc.affected_count || '未知'}</p>
        <p style="margin:3px 0;color:#666;font-size:12px">${(inc.description || '').substring(0, 80)}</p>
        ${onIncidentClick ? '<p style="margin:8px 0 0;color:#1890ff;font-size:12px;cursor:pointer">👉 点击查看详情</p>' : ''}
      </div>`
      marker.on('click', () => {
        if (infoWindowRef.current) infoWindowRef.current.close()
        const iw = new AMap.InfoWindow({ content: infoHtml, offset: new AMap.Pixel(0, -30) })
        iw.open(map, marker.getPosition())
        infoWindowRef.current = iw
        setTimeout(() => {
          const links = document.querySelectorAll('.amap-info-content p[style*="cursor:pointer"]')
          links.forEach((el: any) => el.onclick = () => onIncidentClick && onIncidentClick(inc))
        }, 100)
      })
      map.add(marker)
    })

    ;(resources || []).forEach((res: any) => {
      if (!res.latitude || !res.longitude) return
      const marker = new AMap.Marker({ position: [res.longitude, res.latitude], title: res.name })
      marker.setLabel({
        content: `<div style="background:#1890ff;color:#fff;padding:2px 6px;border-radius:4px;font-size:12px">${res.name}</div>`,
        direction: 'bottom',
      })
      map.add(marker)
    })
  }, [incidents, resources, status, onIncidentClick])

  return (
    <div ref={mapRef} style={{
      height: height || 400, width: '100%',
      background: status === 'error' ? '#e6f7ff' : '#f5f5f5',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      color: '#999', fontSize: 14,
    }}>
      {status === 'loading' && '地图加载中…'}
      {status === 'error' && '地图初始化失败，请配置高德地图 Key 后刷新'}
    </div>
  )
}

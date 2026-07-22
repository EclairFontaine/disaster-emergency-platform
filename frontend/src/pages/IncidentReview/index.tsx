import { useState, useEffect } from 'react'
import { Card, Table, Tag, Button, Modal, Descriptions, Space, message, Tabs } from 'antd'
import MapView from '../../components/MapView'
import { api } from '../../services/api'
import { useAppStore } from '../../store'

const severityColors: Record<string, string> = { P1: 'red', P2: 'orange', P3: 'blue', P4: 'green' }
const statusLabels: Record<string, string> = { pending_review: '待核验', confirmed: '已确认', in_progress: '处置中', closed: '已结束' }

export default function IncidentReview() {
  const [incidents, setIncidents] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [detail, setDetail] = useState<any>(null)
  const [reports, setReports] = useState<any[]>([])
  const [tab, setTab] = useState('pending_review')
  const user = useAppStore((s) => s.user)

  const loadIncidents = async (status: string) => {
    setLoading(true)
    const data = await api.listIncidents({ status, limit: 100 })
    setIncidents(data)
    setLoading(false)
  }

  useEffect(() => {
    loadIncidents(tab)
  }, [tab])

  const viewDetail = async (incident: any) => {
    setDetail(incident)
    try {
      const reps = await api.listReports(incident.id)
      setReports(reps)
    } catch { setReports([]) }
  }

  const handleConfirm = async (id: number) => {
    try {
      await api.updateIncidentStatus(id, { status: 'confirmed' })
      message.success('灾情已确认')
      try { await api.generatePlan(id) } catch {}
      setDetail(null)
      loadIncidents(tab)
    } catch (err: any) { message.error(err.response?.data?.detail || '操作失败') }
  }

  const handleClose = async (id: number) => {
    try {
      await api.updateIncidentStatus(id, { status: 'closed', reason: '误报' })
      message.success('已标记为误报')
      setDetail(null)
      loadIncidents(tab)
    } catch (err: any) { message.error(err.response?.data?.detail || '操作失败') }
  }

  const columns = [
    { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
    { title: '类型', dataIndex: 'category', key: 'category', width: 80 },
    { title: '严重度', dataIndex: 'severity', key: 'severity', width: 80, render: (s: string) => <Tag color={severityColors[s]}>{s}</Tag> },
    { title: '位置', key: 'location', width: 120, render: (_: any, r: any) => r.latitude ? `${r.latitude?.toFixed(2)}, ${r.longitude?.toFixed(2)}` : '-' },
    { title: '时间', dataIndex: 'created_at', key: 'created_at', render: (t: string) => t ? new Date(t).toLocaleString('zh-CN') : '-' },
    {
      title: '操作', key: 'actions', width: 120,
      render: (_: any, r: any) => (
        <Button type="link" onClick={() => viewDetail(r)}>查看详情</Button>
      ),
    },
  ]

  const tabItems = [
    { key: 'pending_review', label: '待核验' },
    { key: 'confirmed', label: '已确认' },
    { key: 'in_progress', label: '处置中' },
    { key: 'closed', label: '已归档' },
  ]

  return (
    <div>
      <Card title="灾情审核">
        <Tabs activeKey={tab} onChange={(k) => { setTab(k); setDetail(null) }} items={tabItems} />
        <Table dataSource={incidents} columns={columns} rowKey="id" loading={loading} size="small" />
      </Card>

      <Modal title="灾情详情" open={!!detail} onCancel={() => setDetail(null)} width={800} footer={null}>
        {detail && (
          <>
            <Descriptions column={2} bordered size="small" style={{ marginBottom: 16 }}>
              <Descriptions.Item label="标题">{detail.title}</Descriptions.Item>
              <Descriptions.Item label="类型">{detail.category || '-'}</Descriptions.Item>
              <Descriptions.Item label="严重程度"><Tag color={severityColors[detail.severity]}>{detail.severity}</Tag></Descriptions.Item>
              <Descriptions.Item label="状态">{statusLabels[detail.status] || detail.status}</Descriptions.Item>
              <Descriptions.Item label="影响人数">{detail.affected_count || '-'}</Descriptions.Item>
              <Descriptions.Item label="位置">{detail.latitude ? `${detail.latitude}, ${detail.longitude}` : '-'}</Descriptions.Item>
              <Descriptions.Item label="描述" span={2}>{detail.description || '-'}</Descriptions.Item>
            </Descriptions>

            {reports.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <h4>灾情报告</h4>
                {reports.map((r: any) => (
                  <Card key={r.id} size="small" style={{ marginBottom: 8 }}>
                    <p>{r.content}</p>
                    {r.images?.length > 0 && (
                      <Space>
                        {r.images.map((img: string, i: number) => (
                          <img key={i} src={img} alt="" style={{ width: 80, height: 80, objectFit: 'cover', borderRadius: 4 }} />
                        ))}
                      </Space>
                    )}
                  </Card>
                ))}
              </div>
            )}

            {detail.latitude && detail.longitude && (
              <MapView incidents={[detail]} height={250} />
            )}

            {detail.status === 'pending_review' && (
              <div style={{ marginTop: 16, textAlign: 'right' }}>
                <Space>
                  <Button type="primary" onClick={() => handleConfirm(detail.id)}>确认灾情</Button>
                  <Button danger onClick={() => handleClose(detail.id)}>标记误报</Button>
                </Space>
              </div>
            )}
          </>
        )}
      </Modal>
    </div>
  )
}

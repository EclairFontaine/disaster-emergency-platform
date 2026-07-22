import { useEffect, useState } from 'react'
import { Row, Col, Card, Statistic, Table, Tag, Spin, Alert, Progress } from 'antd'
import { AlertOutlined, CheckCircleOutlined, DatabaseOutlined, CarOutlined } from '@ant-design/icons'
import MapView from '../../components/MapView'
import { api } from '../../services/api'

const severityColors: Record<string, string> = { P1: 'red', P2: 'orange', P3: 'blue', P4: 'green' }
const statusColors: Record<string, string> = { pending_review: 'gold', confirmed: 'blue', in_progress: 'orange', closed: 'green' }
const statusLabels: Record<string, string> = { pending_review: '待核验', confirmed: '已确认', in_progress: '处置中', closed: '已结束' }
const categoryLabels: Record<string, string> = { earthquake: '地震', flood: '洪水', landslide: '山体滑坡', fire: '火灾', other: '其他' }

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.getStatistics()
      .then(setStats)
      .catch((err) => setError(err?.response?.data?.detail || err?.message || '网络请求失败'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Spin size="large" style={{ display: 'block', margin: '100px auto' }} />
  if (!stats) return <Alert message="大屏加载失败" description={error || '请检查后端服务是否正常运行'} type="error" showIcon />

  const columns = [
    { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
    { title: '类型', dataIndex: 'category', key: 'category', render: (c: string) => categoryLabels[c] || c || '-' },
    { title: '严重度', dataIndex: 'severity', key: 'severity', render: (s: string) => <Tag color={severityColors[s]}>{s}</Tag> },
    { title: '状态', dataIndex: 'status', key: 'status', render: (s: string) => <Tag color={statusColors[s]}>{statusLabels[s]}</Tag> },
    { title: '时间', dataIndex: 'created_at', key: 'created_at', render: (t: string) => t ? new Date(t).toLocaleString('zh-CN') : '-' },
  ]

  return (
    <div>
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card title="灾情态势地图" bodyStyle={{ padding: 0, height: 450 }}>
            <MapView incidents={stats.recent_incidents} height={450} />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Row gutter={[8, 8]}>
            <Col span={12}>
              <Card><Statistic title="总灾情数" value={stats.total_incidents} prefix={<AlertOutlined />} /></Card>
            </Col>
            <Col span={12}>
              <Card><Statistic title="活跃灾情" value={stats.active_incidents} prefix={<CheckCircleOutlined />} valueStyle={{ color: '#cf1322' }} /></Card>
            </Col>
            <Col span={12}>
              <Card><Statistic title="可用资源" value={stats.total_resources} prefix={<DatabaseOutlined />} /></Card>
            </Col>
            <Col span={12}>
              <Card><Statistic title="已调度" value={stats.dispatched_resources} prefix={<CarOutlined />} valueStyle={{ color: '#1890ff' }} /></Card>
            </Col>
          </Row>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} md={12}>
          <Card title="灾情分类统计">
            {Object.entries(stats.incidents_by_category || {}).map(([k, v]) => (
              <div key={k} style={{ marginBottom: 8 }}>
                <span style={{ width: 80, display: 'inline-block' }}>{categoryLabels[k] || k}</span>
                <Progress percent={Math.round((v as number) / Math.max(stats.total_incidents, 1) * 100)} format={() => v as number} size="small" />
              </div>
            ))}
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card title="严重程度分布">
            {Object.entries(stats.incidents_by_severity || {}).map(([k, v]) => (
              <div key={k} style={{ marginBottom: 8 }}>
                <Tag color={severityColors[k]}>{k}</Tag>
                <Progress percent={Math.round((v as number) / Math.max(stats.total_incidents, 1) * 100)} format={() => v as number} size="small" />
              </div>
            ))}
          </Card>
        </Col>
      </Row>

      <Card title="最近灾情" style={{ marginTop: 16 }}>
        <Table dataSource={stats.recent_incidents || []} columns={columns} rowKey="id" size="small" pagination={false} />
      </Card>
    </div>
  )
}

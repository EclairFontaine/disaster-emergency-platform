import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Row, Col, Card, Statistic, Table, Tag, Spin, Alert, Progress, Descriptions, Badge, Steps, List, Space, Button, Modal } from 'antd'
import { AlertOutlined, CheckCircleOutlined, DatabaseOutlined, CarOutlined, CloudOutlined, UserOutlined } from '@ant-design/icons'
import MapView from '../../components/MapView'
import { api } from '../../services/api'
import { useAppStore } from '../../store'

const severityColors: Record<string, string> = { P1: 'red', P2: 'orange', P3: 'blue', P4: 'green' }
const statusColors: Record<string, string> = { pending_review: 'gold', confirmed: 'blue', in_progress: 'orange', closed: 'green' }
const statusLabels: Record<string, string> = { pending_review: '待核验', confirmed: '已确认', in_progress: '处置中', closed: '已结束' }
const categoryLabels: Record<string, string> = { earthquake: '地震', flood: '洪水', landslide: '山体滑坡', fire: '火灾', other: '其他' }

const roleSteps: Record<string, { title: string; items: string[]; color: string }> = {
  admin: {
    title: '系统管理员面板',
    items: ['管理用户账号与权限', '维护知识库和应急预案', '审核数据源和Agent执行记录', '查看全局审计日志'],
    color: '#722ed1',
  },
  info_reporter: {
    title: '信息员工作台 — 我的任务',
    items: ['点击「灾情上报」提交灾情信息', '在地图上标注准确位置', '上传现场图片作为佐证', '跟踪上报灾情的审核状态'],
    color: '#1890ff',
  },
  emergency_commander: {
    title: '应急指挥工作台 — 待办事项',
    items: ['在「信息审核」中核验灾情真实性', '对确认的灾情使用AI生成处置方案', '审批方案并自动调度救援资源', '在「资源调度」中跟踪物资到位情况'],
    color: '#f5222d',
  },
  resource_manager: {
    title: '资源管理工作台 — 今日概览',
    items: ['查看资源分布和可用状态', '响应调度指令，锁定所需资源', '在「调度管理」中跟踪运输和到达', '及时更新资源数量和使用状态'],
    color: '#fa8c16',
  },
}

function RoleTaskGuide({ stats }: { stats: any }) {
  const user = useAppStore((s) => s.user)
  const roleName = user?.role?.name || 'info_reporter'
  const config = roleSteps[roleName] || roleSteps.info_reporter

  return (
    <Row gutter={[16, 16]} style={{ marginTop: 4 }}>
      <Col span={24}>
        <Card
          size="small"
          title={
            <span style={{ color: config.color }}>
              <UserOutlined style={{ marginRight: 8 }} />
              {config.title} — 当前角色: {user?.real_name || user?.username}
            </span>
          }
          extra={
            <Space>
              {roleName === 'info_reporter' && <Tag color="blue">今天已有 {stats.total_incidents} 条灾情</Tag>}
              {roleName === 'emergency_commander' && <Tag color="red">待审核: {stats.active_incidents} 条活跃灾情</Tag>}
              {roleName === 'resource_manager' && <Tag color="orange">可调度资源: {stats.total_resources} 项</Tag>}
            </Space>
          }
        >
          <List
            size="small"
            dataSource={config.items}
            renderItem={(item: string, index: number) => (
              <List.Item>
                <Space>
                  <Tag color={config.color}>{index + 1}</Tag>
                  <span>{item}</span>
                </Space>
              </List.Item>
            )}
          />
        </Card>
      </Col>
    </Row>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [rtStatus, setRtStatus] = useState<any>(null)
  const [collectedEvents, setCollectedEvents] = useState<any[]>([])
  const [allIncidents, setAllIncidents] = useState<any[]>([])
  const [selectedIncident, setSelectedIncident] = useState<any>(null)
  const [eventsExpanded, setEventsExpanded] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    Promise.all([
      api.getStatistics().then(setStats),
      api.listIncidents({ limit: 100 }).then(setAllIncidents),
      fetchRealTimeStatus(),
      fetchLatestEvents(),
    ]).finally(() => setLoading(false))
  }, [])

  const fetchRealTimeStatus = () => {
    api.getCollectorStatus().then(setRtStatus).catch(() => {})
  }

  const fetchLatestEvents = () => {
    return api.getLatestEvents({ limit: 50 }).then(setCollectedEvents).catch(() => {})
  }

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
          <Card title="灾情态势地图" styles={{ body: { padding: 0, height: 450 } }}>
            <MapView incidents={allIncidents} height={450} onIncidentClick={setSelectedIncident} />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Row gutter={[8, 8]}>
            <Col span={12}><Card><Statistic title="总灾情数" value={stats.total_incidents} prefix={<AlertOutlined />} /></Card></Col>
            <Col span={12}><Card><Statistic title="活跃灾情" value={stats.active_incidents} prefix={<CheckCircleOutlined />} valueStyle={{ color: '#e03131' }} /></Card></Col>
            <Col span={12}><Card><Statistic title="可用资源" value={stats.total_resources} prefix={<DatabaseOutlined />} /></Card></Col>
            <Col span={12}><Card><Statistic title="已调度" value={stats.dispatched_resources} prefix={<CarOutlined />} valueStyle={{ color: '#1971c2' }} /></Card></Col>
          </Row>
        </Col>
      </Row>

      {/* 实时采集 - 状态+事件合一 */}
      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col span={24}>
          <Card size="small" title={<span><CloudOutlined style={{ marginRight: 8 }} />实时采集</span>}
            extra={
              <Space>
                <Button size="small" onClick={() => setEventsExpanded(!eventsExpanded)}>
                  {eventsExpanded ? '收起' : `展开全部(${collectedEvents.length})`}
                </Button>
                <Button size="small" onClick={() => { fetchLatestEvents(); fetchRealTimeStatus() }}>刷新</Button>
              </Space>
            }>
            {collectedEvents.length > 0 ? (
              <Table 
                dataSource={eventsExpanded ? collectedEvents : collectedEvents.slice(0, 6)} 
                rowKey="id" size="small" 
                pagination={eventsExpanded ? { pageSize: 20, size: 'small', showSizeChanger: false } : false}
                columns={[
                  { title: '来源', dataIndex: 'source', key: 'src', width: 70,
                    render: (v: string) => <Tag>{v}</Tag> },
                  { title: '事件', dataIndex: 'title', key: 't', ellipsis: true },
                  { title: '数值', dataIndex: 'magnitude', key: 'v', width: 80,
                    render: (v: number, r: any) => r.event_type==='earthquake'?`M${v}`:r.event_type==='weather'?`${v}°C`:`${v||'-'}` },
                  { title: '时间', dataIndex: 'collected_at', key: 'tm', width: 140,
                    render: (t: string) => t ? new Date(t).toLocaleString('zh-CN') : '-' },
                ]} />
            ) : (
              <div style={{ textAlign: 'center', padding: 16, color: '#999' }}>暂无采集数据，点刷新获取</div>
            )}
          </Card>
        </Col>
      </Row>

      <RoleTaskGuide stats={stats} />

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

      {/* 地图点击详情弹窗 */}
      <Modal
        title={selectedIncident?.title}
        open={!!selectedIncident}
        onCancel={() => setSelectedIncident(null)}
        width={640}
        footer={
          <Space>
            <Button onClick={() => setSelectedIncident(null)}>关闭</Button>
            <Button type="primary" onClick={() => { navigate('/review'); setSelectedIncident(null) }}>去审核</Button>
            <Button onClick={() => { navigate('/plan-workbench'); setSelectedIncident(null) }}>生成方案</Button>
          </Space>
        }
      >
        {selectedIncident && (
          <Descriptions column={2} size="small" bordered>
            <Descriptions.Item label="ID">#{selectedIncident.id}</Descriptions.Item>
            <Descriptions.Item label="类型">
              <Tag>{categoryLabels[selectedIncident.category] || selectedIncident.category || '未知'}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="严重程度">
              <Tag color={severityColors[selectedIncident.severity]}>{selectedIncident.severity}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={statusColors[selectedIncident.status]}>{statusLabels[selectedIncident.status] || selectedIncident.status}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="位置">
              {selectedIncident.latitude?.toFixed(4)}, {selectedIncident.longitude?.toFixed(4)}
            </Descriptions.Item>
            <Descriptions.Item label="影响人数">{selectedIncident.affected_count || '未统计'}</Descriptions.Item>
            <Descriptions.Item label="风险半径">{selectedIncident.risk_radius ? `${selectedIncident.risk_radius}m` : '-'}</Descriptions.Item>
            <Descriptions.Item label="上报时间">{selectedIncident.created_at ? new Date(selectedIncident.created_at).toLocaleString('zh-CN') : '-'}</Descriptions.Item>
            <Descriptions.Item label="描述" span={2}>{selectedIncident.description || '暂无描述'}</Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  )
}

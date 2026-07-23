import { useEffect, useState } from 'react'
import { Row, Col, Card, Statistic, Table, Tag, Spin, Alert, Progress, Descriptions, Badge, Steps, List, Space } from 'antd'
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

  useEffect(() => {
    Promise.all([
      api.getStatistics().then(setStats),
      fetchRealTimeStatus(),
    ]).finally(() => setLoading(false))
  }, [])

  const fetchRealTimeStatus = () => {
    api.getCollectorStatus().then(setRtStatus).catch(() => {})
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
        <Col span={24}>
          <Card
            title={<span><CloudOutlined style={{ marginRight: 8 }} />实时数据采集</span>}
            extra={<Badge status="processing" text="每30分钟自动采集" />}
            size="small"
          >
            <Descriptions size="small" column={4}>
              {rtStatus?.earthquake && (
                <Descriptions.Item label="USGS 地震监测">
                  <Badge status={rtStatus.earthquake.last_fetch ? 'success' : 'processing'} text={rtStatus.earthquake.last_fetch ? `${rtStatus.earthquake.count}条` : '采集中'} />
                </Descriptions.Item>
              )}
              {rtStatus?.weather && (
                <>
                  <Descriptions.Item label="和风天气">
                    {rtStatus.weather.sources?.qweather?.configured
                      ? <Badge status="processing" text="运行中" />
                      : <Badge status="default" text="需配置 QWEATHER_API_KEY" />
                    }
                  </Descriptions.Item>
                  <Descriptions.Item label="OpenWeatherMap">
                    {rtStatus.weather.sources?.openweather?.configured
                      ? <Badge status="processing" text="运行中" />
                      : <Badge status="default" text="需配置 OPENWEATHER_API_KEY" />
                    }
                  </Descriptions.Item>
                </>
              )}
              {rtStatus?.warning && (
                <Descriptions.Item label="国家预警信息">
                  <Badge status={rtStatus.warning.last_fetch ? 'success' : 'warning'} text={rtStatus.warning.last_fetch ? `${rtStatus.warning.count}条` : '未获取'} />
                </Descriptions.Item>
              )}
              <Descriptions.Item label="地震最新采集">
                {rtStatus?.earthquake?.last_fetch || '数据采集中...'}
              </Descriptions.Item>
            </Descriptions>
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
    </div>
  )
}

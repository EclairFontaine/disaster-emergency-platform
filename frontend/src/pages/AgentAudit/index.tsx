import { useState, useEffect } from 'react'
import { Card, Table, Tag, Button, Modal, Descriptions, Space, Typography, message } from 'antd'
import { api } from '../../services/api'

const { Paragraph } = Typography

export default function AgentAudit() {
  const [runs, setRuns] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [detail, setDetail] = useState<any>(null)
  const [detailOpen, setDetailOpen] = useState(false)

  const load = () => api.listAgentRuns({ limit: 100 }).then(setRuns).finally(() => setLoading(false))
  useEffect(() => { load() }, [])

  const viewDetail = async (run: any) => {
    try {
      const res = await api.getAgentRunDetail(run.id)
      setDetail({ run: res.run, citations: res.citations })
      setDetailOpen(true)
    } catch { message.error('加载失败') }
  }

  const handleRetry = async (id: number) => {
    try {
      await api.retryAgentRun(id)
      message.success('重试已触发')
      load()
    } catch (err: any) { message.error(err.response?.data?.detail || '重试失败') }
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: '灾情ID', dataIndex: 'incident_id', key: 'incident_id', width: 80 },
    { title: '类型', dataIndex: 'run_type', key: 'run_type', width: 90,
      render: (v: string) => ({ extract: '事件抽取', retrieve: '预案检索', generate: '方案生成', review: '方案审查' }[v] || v) },
    { title: '状态', dataIndex: 'status', key: 'status', width: 90,
      render: (s: string) => <Tag color={s === 'completed' ? 'green' : s === 'running' ? 'blue' : 'red'}>{s === 'completed' ? '完成' : s === 'running' ? '运行中' : '失败'}</Tag> },
    { title: '开始时间', dataIndex: 'started_at', key: 'started_at', render: (t: string) => t ? new Date(t).toLocaleString('zh-CN') : '-' },
    { title: '结束时间', dataIndex: 'finished_at', key: 'finished_at', render: (t: string) => t ? new Date(t).toLocaleString('zh-CN') : '-' },
    {
      title: '操作', key: 'actions', width: 150,
      render: (_: any, r: any) => (
        <Space>
          <Button type="link" size="small" onClick={() => viewDetail(r)}>详情</Button>
          {r.status === 'failed' && <Button type="link" size="small" onClick={() => handleRetry(r.id)}>重试</Button>}
        </Space>
      ),
    },
  ]

  return (
    <Card title="Agent 审计日志">
      <Table dataSource={runs} columns={columns} rowKey="id" loading={loading} size="small" />
      <Modal title="Agent 执行详情" open={detailOpen} onCancel={() => setDetailOpen(false)} width={800} footer={null}>
        {detail && (
          <>
            <Descriptions column={2} size="small" bordered style={{ marginBottom: 16 }}>
              <Descriptions.Item label="类型">{detail.run.run_type}</Descriptions.Item>
              <Descriptions.Item label="状态"><Tag color={detail.run.status === 'completed' ? 'green' : 'red'}>{detail.run.status}</Tag></Descriptions.Item>
              <Descriptions.Item label="开始时间">{detail.run.started_at ? new Date(detail.run.started_at).toLocaleString('zh-CN') : '-'}</Descriptions.Item>
              <Descriptions.Item label="结束时间">{detail.run.finished_at ? new Date(detail.run.finished_at).toLocaleString('zh-CN') : '-'}</Descriptions.Item>
            </Descriptions>

            {detail.run.error_message && (
              <Card title="错误信息" size="small" style={{ marginBottom: 16, borderColor: 'red' }}>
                <Paragraph type="danger">{detail.run.error_message}</Paragraph>
              </Card>
            )}

            {detail.citations?.length > 0 && (
              <Card title="引用来源" size="small" style={{ marginBottom: 16 }}>
                {detail.citations.map((c: any) => (
                  <Card key={c.id} size="small" style={{ marginBottom: 8 }}>
                    <p><strong>{c.doc_name}</strong> <Tag>相关度: {c.relevance_score?.toFixed(2)}</Tag></p>
                    <Paragraph ellipsis={{ rows: 3 }} type="secondary">{c.chunk_text}</Paragraph>
                  </Card>
                ))}
              </Card>
            )}

            {detail.run.output_data && (
              <Card title="输出数据" size="small">
                <pre style={{ maxHeight: 300, overflow: 'auto', background: '#f5f5f5', padding: 12, borderRadius: 4, fontSize: 12 }}>
                  {JSON.stringify(detail.run.output_data, null, 2)}
                </pre>
              </Card>
            )}
          </>
        )}
      </Modal>
    </Card>
  )
}

import { useState, useEffect, useMemo } from 'react'
import { Card, Select, Button, Steps, Input, Space, Tag, message, Spin, Typography, List, Divider, Empty, Table } from 'antd'
import { LoadingOutlined, HistoryOutlined, SendOutlined, RocketOutlined } from '@ant-design/icons'
import { api } from '../../services/api'

const { TextArea } = Input

const typeLabels: Record<string, string> = { personnel: '人员', vehicle: '车辆', material: '物资', shelter: '避难场所' }
const statusLabels: Record<string, string> = { pending_review: '待核验', confirmed: '已确认', in_progress: '处置中', closed: '已结束' }
const planStatusColors: Record<string, string> = { draft: 'gold', approved: 'green', rejected: 'red' }
const planStatusLabels: Record<string, string> = { draft: '草稿', approved: '已批准', rejected: '已驳回' }

export default function PlanWorkbench() {
  const [incidents, setIncidents] = useState<any[]>([])
  const [selectedIncident, setSelectedIncident] = useState<number | null>(null)
  const [allPlans, setAllPlans] = useState<any[]>([])
  const [generating, setGenerating] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [generatedPlan, setGeneratedPlan] = useState<any>(null)
  const [editContent, setEditContent] = useState('')
  const [generateMsg, setGenerateMsg] = useState('')

  useEffect(() => {
    api.listIncidents({ limit: 200 }).then(setIncidents)
    api.listPlans().then(setAllPlans)
  }, [])

  const incidentPlans = useMemo(() => {
    if (!selectedIncident) return allPlans
    return allPlans.filter((p: any) => p.incident_id === selectedIncident || !p.incident_id)
  }, [allPlans, selectedIncident])

  const refreshPlans = () => api.listPlans().then(setAllPlans)

  const handleGenerate = async () => {
    if (!selectedIncident) return
    setGenerating(true)
    setCurrentStep(0)
    setGeneratedPlan(null)
    setEditContent('')
    setGenerateMsg('正在分析灾情信息...')

    // Auto-advance steps via timer
    const t1 = setTimeout(() => { setCurrentStep(1); setGenerateMsg('正在检索相关预案...') }, 1500)
    const t2 = setTimeout(() => { setCurrentStep(2); setGenerateMsg('DeepSeek 正在生成应急方案...') }, 3500)

    try {
      const res = await api.generatePlan(selectedIncident)
      clearTimeout(t1); clearTimeout(t2)
      setCurrentStep(3)
      setGenerateMsg('方案生成完成')
      setGenerating(false)

      // Load the generated plan from the agent run
      const detail = await api.getAgentRunDetail(res.agent_run_id)
      const od = detail.run.output_data || {}
      setGeneratedPlan(od)
      setEditContent(od.plan_content || '')
      refreshPlans()
    } catch (err: any) {
      clearTimeout(t1); clearTimeout(t2)
      setGenerating(false)
      setCurrentStep(0)
      message.error('生成失败: ' + (err?.response?.data?.detail || err?.message || ''))
    }
  }

  const handleSave = async () => {
    if (!generatedPlan?.plan_id) { message.warning('未找到方案ID'); return }
    try {
      await api.updatePlan(generatedPlan.plan_id, { content: editContent })
      message.success('方案已保存')
      refreshPlans()
    } catch (err: any) {
      message.error('保存失败: ' + (err?.response?.data?.detail || err?.message || ''))
    }
  }

  const handleReview = async (status: string) => {
    if (!generatedPlan?.plan_id) { message.warning('未找到方案ID'); return }
    try {
      await api.reviewPlan(generatedPlan.plan_id, { status })
      message.success(status === 'approved' ? '方案已批准，调度单已自动执行！' : '方案已驳回')
      refreshPlans()
    } catch (err: any) {
      message.error('操作失败: ' + (err?.response?.data?.detail || err?.message || ''))
    }
  }

  const loadPlan = (plan: any) => {
    setGeneratedPlan(plan)
    setEditContent(plan.content)
    setGenerating(false)
  }

  return (
    <div>
      <Card title="应急方案生成">
        <Space style={{ marginBottom: 16 }}>
          <Select
            placeholder="选择灾情工单"
            style={{ width: 360 }}
            value={selectedIncident}
            onChange={setSelectedIncident}
            allowClear
            options={incidents.map((i) => ({
              value: i.id,
              label: `${i.title} [${statusLabels[i.status] || i.status}]`,
            }))}
          />
          <Button type="primary" icon={<RocketOutlined />} onClick={handleGenerate} disabled={!selectedIncident} loading={generating}>
            AI 生成方案
          </Button>
        </Space>

        {generating && (
          <Steps
            current={currentStep}
            size="small"
            status={currentStep === 3 ? 'finish' : 'process'}
            items={[
              { title: '分析灾情' },
              { title: '检索预案' },
              { title: 'AI 生成方案' },
              { title: '完成' },
            ]}
            style={{ marginBottom: 16 }}
          />
        )}
        {generating && <p style={{ color: '#1890ff' }}>{generateMsg}</p>}
      </Card>

      <div style={{ display: 'flex', gap: 16, marginTop: 16 }}>
        <Card title="方案编辑" style={{ flex: 2 }}>
          {generatedPlan ? (
            <>
              <div style={{ marginBottom: 8 }}>
                <Tag>AI生成</Tag>
                {generatedPlan.plan_id && (
                  <Button type="link" size="small" onClick={() => api.getPlan(generatedPlan.plan_id).then(p => {
                    setGeneratedPlan({ ...generatedPlan, status: p.status })
                    refreshPlans()
                  })}>
                    状态: {planStatusLabels[generatedPlan.status] || generatedPlan.status || '草稿'}
                  </Button>
                )}
              </div>
              <TextArea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                rows={20}
                style={{ fontFamily: 'monospace' }}
              />
              <div style={{ marginTop: 12 }}>
                <Space>
                  <Button onClick={handleSave}>保存修改</Button>
                  <Button type="primary" onClick={() => handleReview('approved')}>批准方案并调度</Button>
                  <Button danger onClick={() => handleReview('rejected')}>驳回方案</Button>
                </Space>
              </div>

              {generatedPlan?.source_refs?.length > 0 && (
                <>
                  <Divider>引用来源</Divider>
                  <List size="small" dataSource={generatedPlan.source_refs}
                    renderItem={(ref: any) => (
                      <List.Item>
                        <Typography.Text strong>{ref.doc_name}</Typography.Text>
                        <Typography.Text type="secondary" style={{ marginLeft: 8 }}>
                          相关度: {ref.score?.toFixed(2)}
                        </Typography.Text>
                      </List.Item>
                    )}
                  />
                </>
              )}

              {(generatedPlan?.auto_dispatches?.length > 0) && (
                <>
                  <Divider>建议调度资源</Divider>
                  <div style={{ background: '#f6ffed', padding: 12, borderRadius: 8, marginBottom: 8 }}>
                    <Typography.Text strong style={{ color: '#52c41a' }}>
                      AI 推荐 {generatedPlan.auto_dispatches.length} 项资源 — 审批方案后自动执行
                    </Typography.Text>
                  </div>
                  <Table dataSource={generatedPlan.auto_dispatches} rowKey="dispatch_id" size="small" pagination={false}
                    columns={[
                      { title: '资源', dataIndex: 'resource_name', key: 'name' },
                      { title: '数量', dataIndex: 'quantity', key: 'qty', width: 80 },
                      {
                        title: '操作', key: 'action', width: 80,
                        render: (_: any, r: any) => (
                          <Button type="link" size="small" onClick={async () => {
                            try {
                              await api.updateDispatchStatus(r.dispatch_id, { status: 'approved' })
                              message.success('已批准')
                            } catch { message.error('失败') }
                          }}>单独批准</Button>
                        ),
                      },
                    ]}
                  />
                </>
              )}
            </>
          ) : (
            <div style={{ textAlign: 'center', padding: 60, color: '#999' }}>
              <HistoryOutlined style={{ fontSize: 48, marginBottom: 16 }} />
              <br />
              {generating ? (
                <Spin indicator={<LoadingOutlined />} tip={`生成中... ${currentStep + 1}/4`} />
              ) : (
                <div>
                  <p>选择灾情后点击「AI 生成方案」</p>
                  <p>或从右侧「历史方案」加载已有方案</p>
                </div>
              )}
            </div>
          )}
        </Card>

        <Card title="历史方案" style={{ flex: 1 }}>
          {incidentPlans.length > 0 ? (
            <List dataSource={incidentPlans} renderItem={(p: any) => {
              const isActive = generatedPlan?.plan_id === p.id || generatedPlan?.id === p.id
              return (
                <List.Item
                  style={{ background: isActive ? '#e6f7ff' : undefined, cursor: 'pointer', padding: '8px 12px' }}
                  onClick={() => loadPlan(p)}
                  actions={[
                    <Button type="link" size="small" key="load" onClick={(e) => { e.stopPropagation(); loadPlan(p) }}>
                      {isActive ? '编辑中' : '加载'}
                    </Button>,
                  ]}
                >
                  <List.Item.Meta
                    title={<Space size={4}>
                      <Tag color={planStatusColors[p.status]}>{planStatusLabels[p.status] || p.status}</Tag>
                      <Typography.Text style={{ fontSize: 13 }}>{p.title?.substring(0, 20) || '无标题'}</Typography.Text>
                    </Space>}
                    description={<Typography.Text type="secondary" style={{ fontSize: 12 }}>
                      {p.generated_by === 'ai' ? 'AI生成' : '手动'} | {p.created_at ? new Date(p.created_at).toLocaleDateString('zh-CN') : '-'}
                    </Typography.Text>}
                  />
                </List.Item>
              )
            }} />
          ) : (
            <Empty description="暂无方案" image={Empty.PRESENTED_IMAGE_SIMPLE} />
          )}
        </Card>
      </div>
    </div>
  )
}

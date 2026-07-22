import { useState, useEffect } from 'react'
import { Card, Select, Button, Steps, Input, Space, Tag, message, Spin, Typography, List, Divider } from 'antd'
import { LoadingOutlined } from '@ant-design/icons'
import { api } from '../../services/api'

const { TextArea } = Input

const statusLabels: Record<string, string> = { pending_review: '待核验', confirmed: '已确认', in_progress: '处置中', closed: '已结束' }
const planStatusColors: Record<string, string> = { draft: 'gold', approved: 'green', rejected: 'red' }

export default function PlanWorkbench() {
  const [incidents, setIncidents] = useState<any[]>([])
  const [selectedIncident, setSelectedIncident] = useState<number | null>(null)
  const [plans, setPlans] = useState<any[]>([])
  const [generating, setGenerating] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)
  const [generatedPlan, setGeneratedPlan] = useState<any>(null)
  const [editContent, setEditContent] = useState('')
  const [sseUrl, setSseUrl] = useState<string | null>(null)
  const [sseData, setSseData] = useState<any>(null)

  useEffect(() => {
    api.listIncidents({ status: 'confirmed', limit: 100 }).then(setIncidents)
  }, [])

  useEffect(() => {
    if (selectedIncident) {
      api.listPlans({ incident_id: selectedIncident }).then(setPlans)
    }
  }, [selectedIncident])

  useEffect(() => {
    if (!sseUrl) return
    const es = new EventSource(sseUrl)
    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        setSseData(data)
        if (data.status === 'extracting') setCurrentStep(0)
        else if (data.status === 'retrieving') setCurrentStep(1)
        else if (data.status === 'generating') setCurrentStep(2)
        else if (data.status === 'completed') {
          setCurrentStep(3)
          setGeneratedPlan(data.output_data)
          setEditContent(data.output_data?.plan_content || '')
          setGenerating(false)
          es.close()
          api.listPlans({ incident_id: selectedIncident! }).then(setPlans)
        } else if (data.status === 'error') {
          message.error('生成失败')
          setGenerating(false)
          es.close()
        }
      } catch {}
    }
    es.onerror = () => { es.close(); setGenerating(false) }
    return () => es.close()
  }, [sseUrl])

  const handleGenerate = async () => {
    if (!selectedIncident) return
    setGenerating(true)
    setCurrentStep(0)
    setGeneratedPlan(null)
    try {
      const res = await api.generatePlan(selectedIncident)
      setSseUrl(`/api/plans/generate/${res.agent_run_id}/stream`)
    } catch (err: any) {
      message.error('触发生成失败')
      setGenerating(false)
    }
  }

  const handleSave = async () => {
    if (!generatedPlan?.plan_id) {
      message.warning('未找到方案ID，请先生成方案')
      return
    }
    try {
      await api.updatePlan(generatedPlan.plan_id, { content: editContent })
      message.success('方案已保存')
    } catch (err: any) {
      message.error('保存失败: ' + (err?.response?.data?.detail || err?.message || ''))
    }
  }

  const handleReview = async (status: string) => {
    if (!generatedPlan?.plan_id) {
      message.warning('未找到方案ID，请先生成方案')
      return
    }
    try {
      await api.reviewPlan(generatedPlan.plan_id, { status })
      message.success(status === 'approved' ? '方案已批准' : '方案已驳回')
      api.listPlans({ incident_id: selectedIncident! }).then(setPlans)
    } catch (err: any) {
      message.error('操作失败: ' + (err?.response?.data?.detail || err?.message || ''))
    }
  }

  return (
    <div>
      <Card title="应急方案生成">
        <Space style={{ marginBottom: 16 }}>
          <Select
            placeholder="选择灾情工单"
            style={{ width: 300 }}
            value={selectedIncident}
            onChange={setSelectedIncident}
            options={incidents.map((i) => ({ value: i.id, label: `${i.title} [${statusLabels[i.status] || i.status}]` }))}
          />
          <Button type="primary" onClick={handleGenerate} disabled={!selectedIncident} loading={generating}>
            生成方案
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
              { title: '生成方案' },
              { title: '完成' },
            ]}
            style={{ marginBottom: 24 }}
          />
        )}
      </Card>

      <div style={{ display: 'flex', gap: 16, marginTop: 16 }}>
        <Card title="方案编辑" style={{ flex: 2 }}>
          {generatedPlan ? (
            <>
              <TextArea
                value={editContent}
                onChange={(e) => setEditContent(e.target.value)}
                rows={18}
                style={{ fontFamily: 'monospace' }}
              />
              <div style={{ marginTop: 12 }}>
                <Space>
                  <Button onClick={handleSave}>保存修改</Button>
                  <Button type="primary" onClick={() => handleReview('approved')}>批准方案</Button>
                  <Button danger onClick={() => handleReview('rejected')}>驳回方案</Button>
                </Space>
              </div>

              {generatedPlan?.source_refs?.length > 0 && (
                <>
                  <Divider>引用来源</Divider>
                  <List
                    size="small"
                    dataSource={generatedPlan.source_refs}
                    renderItem={(ref: any) => (
                      <List.Item>
                        <Typography.Text strong>{ref.doc_name}</Typography.Text>
                        <Typography.Text type="secondary" style={{ marginLeft: 8 }}>
                          相关度: {ref.score?.toFixed(2)}
                        </Typography.Text>
                        <br />
                        <Typography.Text type="secondary" ellipsis>{ref.chunk_text}</Typography.Text>
                      </List.Item>
                    )}
                  />
                </>
              )}
            </>
          ) : (
            <div style={{ textAlign: 'center', padding: 60, color: '#999' }}>
              {generating ? <Spin indicator={<LoadingOutlined />} tip="正在生成方案..." /> : '选择灾情工单后点击"生成方案"'}
            </div>
          )}
        </Card>

        <Card title="历史方案" style={{ flex: 1 }}>
          <List
            dataSource={plans}
            renderItem={(p: any) => (
              <List.Item actions={[
                <Button type="link" size="small" key="load" onClick={() => {
                  setGeneratedPlan(p)
                  setEditContent(p.content)
                }}>加载</Button>,
              ]}>
                <List.Item.Meta
                  title={p.title}
                  description={
                    <Space>
                      <Tag color={planStatusColors[p.status]}>{p.status === 'approved' ? '已批准' : p.status === 'rejected' ? '已驳回' : '草稿'}</Tag>
                      <span>{p.generated_by === 'ai' ? 'AI生成' : '手动创建'}</span>
                    </Space>
                  }
                />
              </List.Item>
            )}
            locale={{ emptyText: '暂无方案' }}
          />
        </Card>
      </div>
    </div>
  )
}

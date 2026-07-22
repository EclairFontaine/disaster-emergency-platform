import { useState, useEffect } from 'react'
import { Card, Table, Button, Modal, Form, Input, Space, message, Popconfirm } from 'antd'
import { PlusOutlined, SearchOutlined } from '@ant-design/icons'
import { api } from '../../services/api'

const { TextArea } = Input

export default function KnowledgeBase() {
  const [plans, setPlans] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<any>(null)
  const [searchText, setSearchText] = useState('')
  const [form] = Form.useForm()

  const loadPlans = () => api.listPlans().then(setPlans).finally(() => setLoading(false))
  useEffect(() => { loadPlans() }, [])

  const handleSave = async (values: any) => {
    try {
      if (editing) {
        await api.updatePlan(editing.id, values)
        message.success('更新成功')
      } else {
        await api.createPlan({ ...values, generated_by: 'manual' })
        message.success('创建成功')
      }
      setOpen(false)
      setEditing(null)
      form.resetFields()
      loadPlans()
    } catch { message.error('操作失败') }
  }

  const handleDelete = async (id: number) => {
    try {
      await api.deletePlan(id)
      message.success('删除成功')
      loadPlans()
    } catch { message.error('删除失败') }
  }

  const handleEdit = (plan: any) => {
    setEditing(plan)
    form.setFieldsValue({ title: plan.title, content: plan.content })
    setOpen(true)
  }

  const handleSearch = async () => {
    if (!searchText.trim()) { loadPlans(); return }
    setLoading(true)
    const results = await api.searchPlans(searchText)
    setPlans(results)
    setLoading(false)
  }

  const columns = [
    { title: '标题', dataIndex: 'title', key: 'title', ellipsis: true },
    { title: '来源', dataIndex: 'generated_by', key: 'generated_by', width: 80, render: (v: string) => v === 'ai' ? 'AI' : '手动' },
    { title: '关联灾情ID', dataIndex: 'incident_id', key: 'incident_id', width: 100 },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', render: (t: string) => t ? new Date(t).toLocaleString('zh-CN') : '-' },
    {
      title: '操作', key: 'actions', width: 150,
      render: (_: any, r: any) => (
        <Space>
          <Button type="link" size="small" onClick={() => handleEdit(r)}>编辑</Button>
          <Popconfirm title="确定删除?" onConfirm={() => handleDelete(r.id)}>
            <Button type="link" size="small" danger>删除</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ]

  return (
    <Card title="知识库管理" extra={
      <Button icon={<PlusOutlined />} onClick={() => { setEditing(null); form.resetFields(); setOpen(true) }}>添加预案</Button>
    }>
      <Space style={{ marginBottom: 16 }}>
        <Input.Search
          placeholder="搜索预案..."
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
          onSearch={handleSearch}
          enterButton={<Button icon={<SearchOutlined />}>搜索</Button>}
          style={{ width: 400 }}
        />
      </Space>

      <Table dataSource={plans} columns={columns} rowKey="id" loading={loading} size="small" />

      <Modal
        title={editing ? '编辑预案' : '添加预案'}
        open={open}
        onCancel={() => { setOpen(false); setEditing(null) }}
        onOk={() => form.submit()}
        width={700}
      >
        <Form form={form} onFinish={handleSave} layout="vertical">
          <Form.Item name="title" label="标题" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="content" label="内容" rules={[{ required: true }]}><TextArea rows={15} /></Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}

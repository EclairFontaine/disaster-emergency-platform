import { useState, useEffect } from 'react'
import { Card, Table, Button, Modal, Form, Input, InputNumber, Select, Switch, Space, message, Popconfirm, Tag } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { api } from '../../services/api'

const typeLabels: Record<string, string> = { weather: '气象', warning: '预警', news: '新闻', sensor: '传感器' }

export default function DataSources() {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<any>(null)
  const [form] = Form.useForm()

  const load = () => api.listDatasources().then(setData).finally(() => setLoading(false))
  useEffect(() => { load() }, [])

  const handleSave = async (values: any) => {
    try {
      if (editing) { await api.updateDatasource(editing.id, values); message.success('已更新') }
      else { await api.createDatasource(values); message.success('已创建') }
      setOpen(false); setEditing(null); form.resetFields(); load()
    } catch { message.error('操作失败') }
  }

  const handleDelete = async (id: number) => { await api.deleteDatasource(id); message.success('已删除'); load() }
  const handleEdit = (ds: any) => { setEditing(ds); form.setFieldsValue(ds); setOpen(true) }

  const columns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '类型', dataIndex: 'type', key: 'type', render: (t: string) => <Tag>{typeLabels[t] || t || '-'}</Tag> },
    { title: '采集间隔(秒)', dataIndex: 'fetch_interval', key: 'fetch_interval' },
    { title: '状态', dataIndex: 'is_active', key: 'is_active', render: (v: boolean) => <Tag color={v ? 'green' : 'red'}>{v ? '启用' : '停用'}</Tag> },
    { title: '上次采集', dataIndex: 'last_fetch_at', key: 'last_fetch_at', render: (t: string) => t ? new Date(t).toLocaleString('zh-CN') : '-' },
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
    <Card title="数据源管理" extra={<Button icon={<PlusOutlined />} onClick={() => { setEditing(null); form.resetFields(); setOpen(true) }}>添加数据源</Button>}>
      <Table dataSource={data} columns={columns} rowKey="id" loading={loading} size="small" />
      <Modal title={editing ? '编辑数据源' : '添加数据源'} open={open} onCancel={() => setOpen(false)} onOk={() => form.submit()}>
        <Form form={form} onFinish={handleSave} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="type" label="类型"><Select options={Object.entries(typeLabels).map(([k, v]) => ({ value: k, label: v }))} /></Form.Item>
          <Form.Item name="url" label="URL"><Input /></Form.Item>
          <Form.Item name="fetch_interval" label="采集间隔(秒)"><InputNumber min={60} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="is_active" label="启用" valuePropName="checked"><Switch /></Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}

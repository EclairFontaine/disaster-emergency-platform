import { useState, useEffect } from 'react'
import { Card, Table, Tag, Button, Modal, Form, Input, Select, InputNumber, Space, message, Tabs, Descriptions } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import MapView from '../../components/MapView'
import { api } from '../../services/api'

const statusColors: Record<string, string> = { idle: 'green', dispatched: 'blue', malfunction: 'red' }
const typeLabels: Record<string, string> = { personnel: '人员', vehicle: '车辆', material: '物资', shelter: '避难场所' }

export default function ResourceBoard() {
  const [resources, setResources] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [createOpen, setCreateOpen] = useState(false)
  const [lockOpen, setLockOpen] = useState(false)
  const [dispatchOpen, setDispatchOpen] = useState(false)
  const [selectedResource, setSelectedResource] = useState<any>(null)
  const [orders, setOrders] = useState<any[]>([])
  const [incidents, setIncidents] = useState<any[]>([])
  const [lockPos, setLockPos] = useState<any>(null)
  const [form] = Form.useForm()
  const [lockForm] = Form.useForm()
  const [dispatchForm] = Form.useForm()

  const loadResources = () => api.listResources().then(setResources).finally(() => setLoading(false))
  const loadOrders = () => api.listDispatchOrders().then(setOrders)
  const loadIncidents = () => api.listIncidents({ status: 'confirmed' }).then(setIncidents)

  useEffect(() => { loadResources(); loadOrders(); loadIncidents() }, [])

  const createResource = async (values: any) => {
    try {
      await api.createResource(values)
      message.success('资源创建成功')
      setCreateOpen(false)
      form.resetFields()
      loadResources()
    } catch { message.error('创建失败') }
  }

  const handleLock = async (values: any) => {
    try {
      await api.lockResource(selectedResource.id, { incident_id: values.incident_id, quantity: values.quantity })
      message.success('资源已锁定')
      setLockOpen(false)
      setSelectedResource(null)
      loadResources()
    } catch (err: any) { message.error(err.response?.data?.detail || '锁定失败') }
  }

  const createDispatch = async (values: any) => {
    try {
      await api.createDispatchOrder({ ...values, dest_latitude: lockPos?.lat, dest_longitude: lockPos?.lng })
      message.success('调度单已创建')
      setDispatchOpen(false)
      dispatchForm.resetFields()
      loadOrders()
    } catch { message.error('创建失败') }
  }

  const updateDispatchStatus = async (id: number, status: string) => {
    try {
      await api.updateDispatchStatus(id, { status })
      message.success('状态已更新')
      loadOrders()
    } catch { message.error('更新失败') }
  }

  const resColumns = [
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '类型', dataIndex: 'type', key: 'type', render: (t: string) => typeLabels[t] || t },
    { title: '可用/总量', key: 'qty', render: (_: any, r: any) => `${r.available_qty} / ${r.quantity}` },
    { title: '已锁定', dataIndex: 'locked_qty', key: 'locked_qty' },
    { title: '状态', dataIndex: 'status', key: 'status', render: (s: string) => <Tag color={statusColors[s]}>{s}</Tag> },
    {
      title: '操作', key: 'actions',
      render: (_: any, r: any) => (
        <Space>
          <Button type="link" size="small" onClick={() => { setSelectedResource(r); setLockOpen(true) }}>锁定</Button>
        </Space>
      ),
    },
  ]

  const orderColumns = [
    { title: '调度单ID', dataIndex: 'id', key: 'id', width: 80 },
    { title: '资源ID', dataIndex: 'resource_id', key: 'resource_id', width: 80 },
    { title: '数量', dataIndex: 'quantity', key: 'quantity', width: 60 },
    { title: '状态', dataIndex: 'status', key: 'status', render: (s: string) => {
      const labels: Record<string, string> = { pending: '待审批', approved: '已批准', in_transit: '运输中', arrived: '已到达', released: '已释放' }
      return <Tag>{labels[s] || s}</Tag>
    }},
    {
      title: '操作', key: 'actions', width: 150,
      render: (_: any, r: any) => (
        <Space size="small">
          {r.status === 'pending' && <Button size="small" onClick={() => updateDispatchStatus(r.id, 'approved')}>批准</Button>}
          {r.status === 'approved' && <Button size="small" onClick={() => updateDispatchStatus(r.id, 'in_transit')}>发出</Button>}
          {r.status === 'in_transit' && <Button size="small" onClick={() => updateDispatchStatus(r.id, 'arrived')}>到达</Button>}
          {(r.status === 'arrived' || r.status === 'in_transit') && <Button size="small" onClick={() => updateDispatchStatus(r.id, 'released')}>释放</Button>}
        </Space>
      ),
    },
  ]

  return (
    <div>
      <Card title="资源看板" extra={<Button icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>添加资源</Button>}>
        <div style={{ marginBottom: 16 }}>
          <MapView resources={resources} height={300} />
        </div>
        <Table dataSource={resources} columns={resColumns} rowKey="id" loading={loading} size="small" />
      </Card>

      <Card title="调度管理" style={{ marginTop: 16 }} extra={<Button onClick={() => setDispatchOpen(true)}>新建调度单</Button>}>
        <Table dataSource={orders} columns={orderColumns} rowKey="id" size="small" />
      </Card>

      <Modal title="添加资源" open={createOpen} onCancel={() => setCreateOpen(false)} onOk={() => form.submit()}>
        <Form form={form} onFinish={createResource} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="type" label="类型" rules={[{ required: true }]}>
            <Select options={Object.entries(typeLabels).map(([k, v]) => ({ value: k, label: v }))} />
          </Form.Item>
          <Form.Item name="quantity" label="总数"><InputNumber min={1} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="available_qty" label="可用数量"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="latitude" label="纬度"><Input /></Form.Item>
          <Form.Item name="longitude" label="经度"><Input /></Form.Item>
        </Form>
      </Modal>

      <Modal title="锁定资源" open={lockOpen} onCancel={() => { setLockOpen(false); setSelectedResource(null) }} onOk={() => lockForm.submit()}>
        <p>资源: {selectedResource?.name} (可用: {selectedResource?.available_qty})</p>
        <Form form={lockForm} onFinish={handleLock} layout="vertical">
          <Form.Item name="incident_id" label="关联灾情" rules={[{ required: true }]}>
            <Select options={incidents.map((i: any) => ({ value: i.id, label: i.title }))} />
          </Form.Item>
          <Form.Item name="quantity" label="数量" rules={[{ required: true }]}>
            <InputNumber min={1} max={selectedResource?.available_qty} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal title="新建调度单" open={dispatchOpen} onCancel={() => setDispatchOpen(false)} onOk={() => dispatchForm.submit()}>
        <Form form={dispatchForm} onFinish={createDispatch} layout="vertical">
          <Form.Item name="incident_id" label="灾情" rules={[{ required: true }]}>
            <Select options={incidents.map((i: any) => ({ value: i.id, label: i.title }))} />
          </Form.Item>
          <Form.Item name="resource_id" label="资源" rules={[{ required: true }]}>
            <Select options={resources.map((r: any) => ({ value: r.id, label: `${r.name} (${r.available_qty}可用)` }))} />
          </Form.Item>
          <Form.Item name="quantity" label="数量" rules={[{ required: true }]}><InputNumber min={1} style={{ width: '100%' }} /></Form.Item>
          <Form.Item label="目标位置"><MapView onMapClick={(p) => setLockPos(p)} height={200} /></Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

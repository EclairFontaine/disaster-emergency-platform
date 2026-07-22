import { useState, useEffect } from 'react'
import { Card, Table, Button, Modal, Form, Input, Select, Switch, Space, message, Popconfirm, Tag } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { api } from '../../services/api'

const roleLabels: Record<string, string> = {
  admin: '系统管理员', emergency_commander: '应急指挥', info_reporter: '信息员', resource_manager: '资源管理员',
}

export default function UserManage() {
  const [users, setUsers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<any>(null)
  const [form] = Form.useForm()

  const load = () => api.listUsers().then(setUsers).finally(() => setLoading(false))
  useEffect(() => { load() }, [])

  const handleSave = async (values: any) => {
    try {
      if (editing) {
        const payload: any = { ...values }
        if (!payload.password) delete payload.password
        await api.updateUser(editing.id, payload)
        message.success('已更新')
      } else {
        await api.createUser(values)
        message.success('已创建')
      }
      setOpen(false); setEditing(null); form.resetFields(); load()
    } catch (err: any) { message.error(err.response?.data?.detail || '操作失败') }
  }

  const handleDelete = async (id: number) => {
    try { await api.deleteUser(id); message.success('已删除'); load() }
    catch (err: any) { message.error(err.response?.data?.detail || '删除失败') }
  }

  const columns = [
    { title: '用户名', dataIndex: 'username', key: 'username' },
    { title: '姓名', dataIndex: 'real_name', key: 'real_name' },
    { title: '电话', dataIndex: 'phone', key: 'phone' },
    { title: '角色', dataIndex: ['role', 'name'], key: 'role', render: (v: string) => <Tag>{roleLabels[v] || v}</Tag> },
    { title: '状态', dataIndex: 'is_active', key: 'is_active', render: (v: boolean) => <Tag color={v ? 'green' : 'red'}>{v ? '启用' : '禁用'}</Tag> },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', render: (t: string) => t ? new Date(t).toLocaleString('zh-CN') : '-' },
    {
      title: '操作', key: 'actions', width: 150,
      render: (_: any, r: any) => (
        <Space>
          <Button type="link" size="small" onClick={() => { setEditing(r); form.setFieldsValue({ ...r, password: '' }); setOpen(true) }}>编辑</Button>
          {r.username !== 'admin' && (
            <Popconfirm title="确定删除?" onConfirm={() => handleDelete(r.id)}>
              <Button type="link" size="small" danger>删除</Button>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ]

  return (
    <Card title="用户管理" extra={<Button icon={<PlusOutlined />} onClick={() => { setEditing(null); form.resetFields(); setOpen(true) }}>添加用户</Button>}>
      <Table dataSource={users} columns={columns} rowKey="id" loading={loading} size="small" />
      <Modal title={editing ? '编辑用户' : '添加用户'} open={open} onCancel={() => setOpen(false)} onOk={() => form.submit()}>
        <Form form={form} onFinish={handleSave} layout="vertical">
          <Form.Item name="username" label="用户名" rules={[{ required: true }]}><Input /></Form.Item>
          <Form.Item name="password" label={editing ? '新密码(留空不变)' : '密码'} rules={editing ? [] : [{ required: true, message: '请输入密码' }]}>
            <Input.Password />
          </Form.Item>
          <Form.Item name="real_name" label="姓名"><Input /></Form.Item>
          <Form.Item name="phone" label="电话"><Input /></Form.Item>
          <Form.Item name="role_id" label="角色" rules={[{ required: true }]}>
            <Select options={Object.entries(roleLabels).map(([k, v], i) => ({ value: i + 1, label: v }))} />
          </Form.Item>
          <Form.Item name="is_active" label="启用" valuePropName="checked" initialValue={true}><Switch /></Form.Item>
        </Form>
      </Modal>
    </Card>
  )
}

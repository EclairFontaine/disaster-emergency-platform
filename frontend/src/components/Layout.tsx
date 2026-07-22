import { useEffect } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { Layout, Menu, Button, Dropdown, Space, Typography, Badge, Drawer, List, Tag } from 'antd'
import {
  DashboardOutlined, AlertOutlined, CheckCircleOutlined, FileTextOutlined,
  DatabaseOutlined, SettingOutlined, AuditOutlined, UserOutlined,
  LogoutOutlined, EnvironmentOutlined, BellOutlined,
} from '@ant-design/icons'
import { useState } from 'react'
import { useAppStore } from '../store'
import { useWebSocket } from '../hooks/useWebSocket'

const { Header, Sider, Content } = Layout

const roleMenus: Record<string, { key: string; icon: React.ReactNode; label: string; path: string }[]> = {
  admin: [
    { key: 'dashboard', icon: <DashboardOutlined />, label: '态势大屏', path: '/dashboard' },
    { key: 'report', icon: <AlertOutlined />, label: '灾情上报', path: '/report' },
    { key: 'review', icon: <CheckCircleOutlined />, label: '信息审核', path: '/review' },
    { key: 'plan-workbench', icon: <FileTextOutlined />, label: '方案工作台', path: '/plan-workbench' },
    { key: 'resources', icon: <EnvironmentOutlined />, label: '资源调度', path: '/resources' },
    { key: 'knowledge', icon: <DatabaseOutlined />, label: '知识库', path: '/knowledge' },
    { key: 'datasources', icon: <SettingOutlined />, label: '数据源', path: '/datasources' },
    { key: 'agent-audit', icon: <AuditOutlined />, label: 'Agent审计', path: '/agent-audit' },
    { key: 'users', icon: <UserOutlined />, label: '用户管理', path: '/users' },
  ],
  emergency_commander: [
    { key: 'dashboard', icon: <DashboardOutlined />, label: '态势大屏', path: '/dashboard' },
    { key: 'review', icon: <CheckCircleOutlined />, label: '信息审核', path: '/review' },
    { key: 'plan-workbench', icon: <FileTextOutlined />, label: '方案工作台', path: '/plan-workbench' },
    { key: 'resources', icon: <EnvironmentOutlined />, label: '资源调度', path: '/resources' },
  ],
  info_reporter: [
    { key: 'dashboard', icon: <DashboardOutlined />, label: '态势大屏', path: '/dashboard' },
    { key: 'report', icon: <AlertOutlined />, label: '灾情上报', path: '/report' },
  ],
  resource_manager: [
    { key: 'dashboard', icon: <DashboardOutlined />, label: '态势大屏', path: '/dashboard' },
    { key: 'resources', icon: <EnvironmentOutlined />, label: '资源调度', path: '/resources' },
  ],
}

const eventLabels: Record<string, { label: string; color: string }> = {
  'incident:status': { label: '灾情状态', color: 'blue' },
  'resource:lock': { label: '资源锁定', color: 'orange' },
  'resource:release': { label: '资源释放', color: 'green' },
  'dispatch:created': { label: '调度创建', color: 'purple' },
}

let notifId = 0

export default function AppLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout, notifications, pushNotification, clearNotifications } = useAppStore()
  const [drawerOpen, setDrawerOpen] = useState(false)

  const handleWsEvent = (event: string, data: any) => {
    notifId++
    const info = eventLabels[event] || { label: event, color: 'default' }
    let message = event
    if (event === 'incident:status') message = `灾情 #${data.id} 状态变更: ${data.status}`
    else if (event === 'resource:lock') message = `资源 #${data.resource_id} 已锁定 ${data.quantity} 单位`
    else if (event === 'resource:release') message = `资源 #${data.resource_id} 已释放`
    else if (event === 'dispatch:created') message = `新建调度单 #${data.id}`

    pushNotification({ id: notifId, event: info.label, message, time: Date.now() })
  }

  useWebSocket({ onEvent: handleWsEvent })

  const roleName = user?.role?.name || 'info_reporter'
  const menus = roleMenus[roleName] || roleMenus.info_reporter
  const selectedKey = menus.find((m) => location.pathname.startsWith(m.path))?.key || 'dashboard'

  return (
    <Layout>
      <Sider width={220} theme="dark" style={{ minHeight: '100vh' }}>
        <div style={{ height: 64, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Typography.Title level={4} style={{ color: '#fff', margin: 0, fontSize: 16 }}>
            应急协同决策平台
          </Typography.Title>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menus.map((m) => ({
            key: m.key,
            icon: m.icon,
            label: m.label,
            onClick: () => navigate(m.path),
          }))}
        />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}>
          <Space>
            <Badge count={notifications.length} size="small">
              <Button type="text" icon={<BellOutlined />} onClick={() => setDrawerOpen(true)} />
            </Badge>
            <Dropdown
              menu={{
                items: [
                  { key: 'logout', icon: <LogoutOutlined />, label: '退出登录', onClick: () => { logout(); navigate('/login') } },
                ],
              }}
            >
              <Button type="text" icon={<UserOutlined />}>
                {user?.real_name || user?.username}
                <Typography.Text type="secondary" style={{ marginLeft: 8 }}>
                  {roleName === 'admin' ? '系统管理员' : roleName === 'emergency_commander' ? '应急指挥' : roleName === 'resource_manager' ? '资源管理员' : '信息员'}
                </Typography.Text>
              </Button>
            </Dropdown>
          </Space>
        </Header>
        <Content style={{ margin: 16, padding: 24, background: '#fff', borderRadius: 8, minHeight: 360 }}>
          <Outlet />
        </Content>
      </Layout>

      <Drawer title="实时通知" open={drawerOpen} onClose={() => setDrawerOpen(false)} extra={<Button size="small" onClick={clearNotifications}>清空</Button>}>
        <List
          dataSource={notifications}
          locale={{ emptyText: '暂无通知' }}
          renderItem={(n) => {
            const info = eventLabels[n.event.split(':')[0] + ':' + n.event.split(':')[1]] || ({ color: 'default' } as any)
            return (
              <List.Item>
                <List.Item.Meta
                  title={<><Tag color={info.color}>{n.event}</Tag> {n.message}</>}
                  description={new Date(n.time).toLocaleTimeString('zh-CN')}
                />
              </List.Item>
            )
          }}
        />
      </Drawer>
    </Layout>
  )
}

import { Routes, Route, Navigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { Spin } from 'antd'
import { useAppStore } from './store'
import { api } from './services/api'
import AppLayout from './components/Layout'
import Login from './pages/Login/index'
import Dashboard from './pages/Dashboard/index'
import IncidentReport from './pages/IncidentReport/index'
import IncidentReview from './pages/IncidentReview/index'
import PlanWorkbench from './pages/PlanWorkbench/index'
import ResourceBoard from './pages/ResourceBoard/index'
import KnowledgeBase from './pages/KnowledgeBase/index'
import DataSources from './pages/DataSources/index'
import AgentAudit from './pages/AgentAudit/index'
import UserManage from './pages/UserManage/index'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = useAppStore((s) => s.token)
  if (!token) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  const { setAuth, token, user } = useAppStore()
  const [loading, setLoading] = useState(!!token)

  useEffect(() => {
    const storedToken = localStorage.getItem('token')
    const storedUser = localStorage.getItem('user')
    if (storedToken && storedUser) {
      try {
        const u = JSON.parse(storedUser)
        setAuth(storedToken, u)
      } catch {}
    }
    if (storedToken) {
      api.getMe()
        .then((u) => {
          setAuth(storedToken, u)
          localStorage.setItem('user', JSON.stringify(u))
        })
        .catch(() => {
          localStorage.removeItem('token')
          localStorage.removeItem('user')
          setAuth('', null as any)
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [])

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" tip="加载中..." />
      </div>
    )
  }

  return (
    <Routes>
      <Route path="/login" element={token ? <Navigate to="/dashboard" replace /> : <Login />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="report" element={<IncidentReport />} />
        <Route path="review" element={<IncidentReview />} />
        <Route path="plan-workbench" element={<PlanWorkbench />} />
        <Route path="resources" element={<ResourceBoard />} />
        <Route path="knowledge" element={<KnowledgeBase />} />
        <Route path="datasources" element={<DataSources />} />
        <Route path="agent-audit" element={<AgentAudit />} />
        <Route path="users" element={<UserManage />} />
      </Route>
    </Routes>
  )
}

import axios from 'axios'

const http = axios.create({
  baseURL: '',
  timeout: 30000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

interface User {
  id: number; username: string; real_name?: string; phone?: string
  role_id: number; role?: { id: number; name: string }; is_active: boolean; created_at?: string
}
interface Incident {
  id: number; title: string; description?: string; category?: string; severity: string
  status: string; latitude?: number; longitude?: number; risk_radius?: number
  affected_count?: number; reported_by?: number; confirmed_by?: number
  confirmed_at?: string; resolved_at?: string; metadata?: any; created_at?: string; updated_at?: string
}
interface Resource {
  id: number; type: string; name: string; description?: string; quantity: number
  available_qty: number; latitude?: number; longitude?: number
  contact_info?: string; status: string; locked_qty: number; created_at?: string
}
interface DispatchOrder {
  id: number; incident_id: number; plan_id?: number; resource_id: number
  quantity: number; dest_latitude?: number; dest_longitude?: number
  status: string; approved_by?: number; dispatched_at?: string; arrived_at?: string; created_at?: string
}
interface Plan {
  id: number; incident_id?: number; title: string; content: string; generated_by: string
  source_refs?: any; status: string; reviewed_by?: number; reviewed_at?: string; created_at?: string
}
interface AgentRun {
  id: number; incident_id: number; run_type: string; input_data?: any; output_data?: any
  status: string; error_message?: string; started_at?: string; finished_at?: string
}
interface AuditLog {
  id: number; user_id?: number; action: string; resource_type: string
  resource_id?: number; detail?: any; ip_address?: string; created_at?: string
}

export const api = {
  login: (data: { username: string; password: string }) =>
    http.post('/api/auth/login', data).then((r) => r.data),
  getMe: () => http.get('/api/auth/me').then((r) => r.data),

  getStatistics: () => http.get('/api/statistics').then((r) => r.data),

  listIncidents: (params?: any) => http.get('/api/incidents', { params }).then((r) => r.data as Incident[]),
  createIncident: (data: any) => http.post('/api/incidents', data).then((r) => r.data as Incident),
  getIncident: (id: number) => http.get(`/api/incidents/${id}`).then((r) => r.data as Incident),
  updateIncident: (id: number, data: any) => http.put(`/api/incidents/${id}`, data).then((r) => r.data as Incident),
  updateIncidentStatus: (id: number, data: { status: string; reason?: string }) =>
    http.put(`/api/incidents/${id}/status`, data).then((r) => r.data as Incident),
  getNearbyIncidents: (lat: number, lng: number, radius: number) =>
    http.get('/api/incidents/nearby', { params: { lat, lng, radius } }).then((r) => r.data as Incident[]),
  createReport: (id: number, data: any) => http.post(`/api/incidents/${id}/reports`, data).then((r) => r.data),
  listReports: (id: number) => http.get(`/api/incidents/${id}/reports`).then((r) => r.data),
  uploadImage: (id: number, file: File) => {
    const fd = new FormData(); fd.append('file', file); return http.post(`/api/incidents/${id}/upload`, fd).then((r) => r.data)
  },

  listResources: (params?: any) => http.get('/api/resources', { params }).then((r) => r.data as Resource[]),
  createResource: (data: any) => http.post('/api/resources', data).then((r) => r.data as Resource),
  getResource: (id: number) => http.get(`/api/resources/${id}`).then((r) => r.data as Resource),
  updateResource: (id: number, data: any) => http.put(`/api/resources/${id}`, data).then((r) => r.data as Resource),
  deleteResource: (id: number) => http.delete(`/api/resources/${id}`),
  lockResource: (id: number, data: { incident_id: number; quantity: number }) =>
    http.post(`/api/resources/${id}/lock`, data).then((r) => r.data),
  releaseResource: (id: number) => http.post(`/api/resources/${id}/release`).then((r) => r.data),

  listDispatchOrders: (params?: any) => http.get('/api/dispatch-orders', { params }).then((r) => r.data as DispatchOrder[]),
  createDispatchOrder: (data: any) => http.post('/api/dispatch-orders', data).then((r) => r.data as DispatchOrder),
  getDispatchOrder: (id: number) => http.get(`/api/dispatch-orders/${id}`).then((r) => r.data as DispatchOrder),
  updateDispatchStatus: (id: number, data: { status: string }) =>
    http.put(`/api/dispatch-orders/${id}/status`, data).then((r) => r.data as DispatchOrder),

  listPlans: (params?: any) => http.get('/api/plans', { params }).then((r) => r.data as Plan[]),
  createPlan: (data: any) => http.post('/api/plans', data).then((r) => r.data as Plan),
  getPlan: (id: number) => http.get(`/api/plans/${id}`).then((r) => r.data as Plan),
  updatePlan: (id: number, data: any) => http.put(`/api/plans/${id}`, data).then((r) => r.data as Plan),
  deletePlan: (id: number) => http.delete(`/api/plans/${id}`),
  searchPlans: (query: string) => http.post('/api/plans/search', { query }).then((r) => r.data as Plan[]),
  generatePlan: (incident_id: number) => http.post('/api/plans/generate', { incident_id }).then((r) => r.data),
  reviewPlan: (id: number, data: { status: string; comment?: string }) =>
    http.post(`/api/plans/${id}/review`, data).then((r) => r.data as Plan),

  getPlanStreamUrl: (agentRunId: number) => `/api/plans/generate/${agentRunId}/stream`,

  listAgentRuns: (params?: any) => http.get('/api/agent/runs', { params }).then((r) => r.data as AgentRun[]),
  getAgentRunDetail: (id: number) => http.get(`/api/agent/runs/${id}`).then((r) => r.data),
  retryAgentRun: (id: number) => http.post(`/api/agent/runs/${id}/retry`).then((r) => r.data),

  listDatasources: () => http.get('/api/datasources').then((r) => r.data),
  createDatasource: (data: any) => http.post('/api/datasources', data).then((r) => r.data),
  getDatasource: (id: number) => http.get(`/api/datasources/${id}`).then((r) => r.data),
  updateDatasource: (id: number, data: any) => http.put(`/api/datasources/${id}`, data).then((r) => r.data),
  deleteDatasource: (id: number) => http.delete(`/api/datasources/${id}`),

  listUsers: () => http.get('/api/users').then((r) => r.data as User[]),
  createUser: (data: any) => http.post('/api/users', data).then((r) => r.data as User),
  getUser: (id: number) => http.get(`/api/users/${id}`).then((r) => r.data as User),
  updateUser: (id: number, data: any) => http.put(`/api/users/${id}`, data).then((r) => r.data as User),
  deleteUser: (id: number) => http.delete(`/api/users/${id}`),

  listAuditLogs: (params?: any) => http.get('/api/audit', { params }).then((r) => r.data as AuditLog[]),

  getCollectorStatus: () => http.get('/api/collector/status').then((r) => r.data),
  getLatestEvents: (params?: any) => http.get('/api/collector/events', { params }).then((r) => r.data),
}

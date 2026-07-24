import { describe, it, expect } from 'vitest'
import { api } from '../services/api'

describe('API Service Layer', () => {
  it('api object has all expected methods', () => {
    expect(api.login).toBeDefined()
    expect(api.getMe).toBeDefined()
    expect(api.getStatistics).toBeDefined()
    expect(api.listIncidents).toBeDefined()
    expect(api.createIncident).toBeDefined()
    expect(api.updateIncidentStatus).toBeDefined()
    expect(api.listResources).toBeDefined()
    expect(api.listPlans).toBeDefined()
    expect(api.generatePlan).toBeDefined()
    expect(api.listUsers).toBeDefined()
    expect(api.listAgentRuns).toBeDefined()
    expect(api.listAuditLogs).toBeDefined()
  })

  it('api login function exists and is callable', () => {
    expect(typeof api.login).toBe('function')
  })
})

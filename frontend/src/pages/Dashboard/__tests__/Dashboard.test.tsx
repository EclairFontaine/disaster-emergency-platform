import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '../../../test/test-utils'
import Dashboard from '../index'

vi.mock('../../services/api', () => ({
  api: {
    getStatistics: vi.fn().mockResolvedValue({
      total_incidents: 10,
      active_incidents: 3,
      total_resources: 17,
      dispatched_resources: 2,
      incidents_by_category: { earthquake: 5, flood: 3, landslide: 2 },
      incidents_by_severity: { P1: 1, P2: 3, P3: 4, P4: 2 },
      recent_incidents: [],
    }),
    getCollectorStatus: vi.fn().mockResolvedValue({
      earthquake: { count: 0, last_fetch: '2024-01-01T00:00:00' },
      weather: { sources: { qweather: { configured: false }, openweather: { configured: false } } },
      warning: { count: 0, last_fetch: null },
    }),
    getLatestEvents: vi.fn().mockResolvedValue([]),
  },
}))

describe('Dashboard Page', () => {
  it('renders without crashing', async () => {
    const { container } = render(<Dashboard />)
    expect(container).toBeTruthy()
  })
})

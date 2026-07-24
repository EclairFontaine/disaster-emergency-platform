import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '../../../test/test-utils'
import IncidentReview from '../index'

vi.mock('../../../services/api', () => ({
  api: {
    listIncidents: vi.fn().mockResolvedValue([]),
    listReports: vi.fn().mockResolvedValue([]),
    updateIncidentStatus: vi.fn().mockResolvedValue({}),
    generatePlan: vi.fn().mockResolvedValue({ agent_run_id: 1 }),
  },
}))

vi.mock('../../../store', () => ({
  useAppStore: (selector: any) => {
    const state = { user: { role: { name: 'emergency_commander' }, username: 'commander1' } }
    return selector(state)
  },
}))

describe('IncidentReview Page', () => {
  it('renders page title', async () => {
    render(<IncidentReview />)
    await waitFor(() => {
      expect(screen.getByText('灾情审核')).toBeInTheDocument()
    })
  })

  it('renders tab bar with filter options', async () => {
    render(<IncidentReview />)
    await waitFor(() => {
      expect(screen.getByText('待核验')).toBeInTheDocument()
      expect(screen.getByText('已确认')).toBeInTheDocument()
      expect(screen.getByText('处置中')).toBeInTheDocument()
      expect(screen.getByText('已归档')).toBeInTheDocument()
    })
  })

  it('renders empty table initially', async () => {
    render(<IncidentReview />)
    await waitFor(() => {
      expect(screen.getByText('灾情审核')).toBeInTheDocument()
    })
  })
})

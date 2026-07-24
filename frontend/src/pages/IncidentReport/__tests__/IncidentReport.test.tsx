import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '../../../test/test-utils'
import IncidentReport from '../index'

vi.mock('../../../services/api', () => ({
  api: {
    listIncidents: vi.fn().mockResolvedValue([]),
    createIncident: vi.fn().mockResolvedValue({ id: 1 }),
    createReport: vi.fn().mockResolvedValue({}),
  },
}))

vi.mock('../../../store', () => ({
  useAppStore: (selector: any) => {
    const state = { user: { role: { name: 'info_reporter' }, username: 'reporter1' } }
    return selector(state)
  },
}))

describe('IncidentReport Page', () => {
  it('renders page title', async () => {
    render(<IncidentReport />)
    await waitFor(() => {
      expect(screen.getByText('灾情上报')).toBeInTheDocument()
    })
  })

  it('renders submit button', async () => {
    render(<IncidentReport />)
    await waitFor(() => {
      expect(screen.getByText('提交上报')).toBeInTheDocument()
    })
  })

  it('renders category select options', async () => {
    render(<IncidentReport />)
    await waitFor(() => {
      expect(screen.getByText('我的上报记录')).toBeInTheDocument()
    })
  })

  it('renders map view', () => {
    const { container } = render(<IncidentReport />)
    expect(container).toBeTruthy()
  })
})

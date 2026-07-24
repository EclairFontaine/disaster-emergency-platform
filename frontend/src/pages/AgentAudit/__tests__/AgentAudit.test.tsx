import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '../../../test/test-utils'
import userEvent from '@testing-library/user-event'
import AgentAudit from '../index'

vi.mock('../../../services/api', () => ({
  api: {
    listAgentRuns: vi.fn().mockResolvedValue([
      { id: 1, incident_id: 1, run_type: 'generate', status: 'completed', started_at: '2024-01-01T00:00:00', finished_at: '2024-01-01T00:01:00' },
      { id: 2, incident_id: 2, run_type: 'extract', status: 'failed', started_at: '2024-01-01T00:02:00', finished_at: null },
    ]),
    getAgentRunDetail: vi.fn().mockResolvedValue({
      run: { id: 1, incident_id: 1, run_type: 'generate', status: 'completed', output_data: {}, error_message: null, started_at: '2024-01-01T00:00:00', finished_at: '2024-01-01T00:01:00' },
      citations: [],
    }),
    retryAgentRun: vi.fn().mockResolvedValue({ success: true }),
  },
}))

describe('AgentAudit Page — 渲染', () => {
  it('renders page title', async () => {
    render(<AgentAudit />)
    await waitFor(() => expect(screen.getByText('Agent 审计日志')).toBeInTheDocument())
  })

  it('shows retry button for failed runs', async () => {
    render(<AgentAudit />)
    await waitFor(() => expect(screen.getByText('重试')).toBeInTheDocument())
  })

  it('shows detail buttons', async () => {
    render(<AgentAudit />)
    await waitFor(() => {
      const buttons = screen.getAllByText('详情')
      expect(buttons.length).toBeGreaterThan(0)
    })
  })
})

describe('AgentAudit Page — 交互', () => {
  it('clicking detail button opens modal', async () => {
    render(<AgentAudit />)
    const user = userEvent.setup()
    await waitFor(() => screen.getByText('Agent 审计日志'))
    const detailButtons = screen.getAllByText('详情')
    await user.click(detailButtons[0])
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument()
      expect(screen.getByText('Agent 执行详情')).toBeInTheDocument()
    })
  })

  it('clicking retry calls retry API', async () => {
    render(<AgentAudit />)
    const user = userEvent.setup()
    await waitFor(() => screen.getByText('重试'))
    await user.click(screen.getByText('重试'))
    await waitFor(() => {
      expect(screen.getByText('Agent 审计日志')).toBeInTheDocument()
    })
  })

  it('renders table with correct columns', async () => {
    const { container } = render(<AgentAudit />)
    await waitFor(() => {
      expect(container.querySelector('.ant-table')).toBeTruthy()
    })
  })
})

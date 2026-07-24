import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '../../../test/test-utils'
import userEvent from '@testing-library/user-event'
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

describe('IncidentReport Page — 渲染', () => {
  it('renders page title', async () => {
    render(<IncidentReport />)
    await waitFor(() => expect(screen.getByText('灾情上报')).toBeInTheDocument())
  })

  it('renders submit button', async () => {
    render(<IncidentReport />)
    await waitFor(() => expect(screen.getByText('提交上报')).toBeInTheDocument())
  })

  it('renders upload button', async () => {
    render(<IncidentReport />)
    await waitFor(() => expect(screen.getByText('选择图片')).toBeInTheDocument())
  })
})

describe('IncidentReport Page — 交互', () => {
  it('allows filling title field', async () => {
    render(<IncidentReport />)
    await waitFor(() => screen.getByPlaceholderText('简要描述灾情'))
    const input = screen.getByPlaceholderText('简要描述灾情')
    await userEvent.setup().type(input, '昆明地震')
    expect(input).toHaveValue('昆明地震')
  })

  it('allows filling description field', async () => {
    render(<IncidentReport />)
    await waitFor(() => screen.getByPlaceholderText('请详细描述灾情情况'))
    const textarea = screen.getByPlaceholderText('请详细描述灾情情况')
    await userEvent.setup().type(textarea, '发生强烈地震')
    expect(textarea).toHaveValue('发生强烈地震')
  })

  it('shows form validation on empty submit', async () => {
    render(<IncidentReport />)
    const user = userEvent.setup()
    await waitFor(() => screen.getByText('提交上报'))
    await user.click(screen.getByText('提交上报'))
    await waitFor(() => {
      expect(screen.getByText('请输入标题')).toBeInTheDocument()
    })
  })

  it('renders category select with options', async () => {
    const { container } = render(<IncidentReport />)
    await waitFor(() => {
      expect(screen.getByText('我的上报记录')).toBeInTheDocument()
      expect(container.querySelector('.ant-select')).toBeTruthy()
    })
  })
})

import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor, within } from '../../../test/test-utils'
import userEvent from '@testing-library/user-event'
import KnowledgeBase from '../index'

vi.mock('../../../services/api', () => ({
  api: {
    listPlans: vi.fn().mockResolvedValue([
      { id: 1, title: '云南地震预案', content: '内容', generated_by: 'manual', incident_id: null, created_at: '2024-01-01' },
    ]),
    createPlan: vi.fn().mockResolvedValue({}),
    updatePlan: vi.fn().mockResolvedValue({}),
    deletePlan: vi.fn().mockResolvedValue({}),
    searchPlans: vi.fn().mockResolvedValue([]),
  },
}))

describe('KnowledgeBase Page — 渲染', () => {
  it('renders page title', async () => {
    render(<KnowledgeBase />)
    await waitFor(() => expect(screen.getByText('知识库管理')).toBeInTheDocument())
  })

  it('renders add plan button', async () => {
    render(<KnowledgeBase />)
    await waitFor(() => {
      const buttons = screen.getAllByText('添加预案')
      expect(buttons.length).toBeGreaterThan(0)
    })
  })

  it('renders search input', async () => {
    render(<KnowledgeBase />)
    await waitFor(() => expect(screen.getByPlaceholderText('搜索预案...')).toBeInTheDocument())
  })
})

describe('KnowledgeBase Page — 交互', () => {
  it('opens add plan modal on button click', async () => {
    render(<KnowledgeBase />)
    const user = userEvent.setup()
    await waitFor(() => {
      const buttons = screen.getAllByText('添加预案')
      expect(buttons.length).toBeGreaterThan(0)
    })
    const addButton = screen.getAllByText('添加预案')[0]
    await user.click(addButton)
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })
  })

  it('allows typing in search input', async () => {
    render(<KnowledgeBase />)
    await waitFor(() => expect(screen.getByPlaceholderText('搜索预案...')).toBeInTheDocument())
    const input = screen.getByPlaceholderText('搜索预案...')
    await userEvent.setup().type(input, '地震')
    expect(input).toHaveValue('地震')
  })

  it('displays plan data in table', async () => {
    render(<KnowledgeBase />)
    await waitFor(() => {
      expect(screen.getByText('云南地震预案')).toBeInTheDocument()
    })
  })
})

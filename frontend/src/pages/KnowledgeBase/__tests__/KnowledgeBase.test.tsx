import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '../../../test/test-utils'
import KnowledgeBase from '../index'

vi.mock('../../../services/api', () => ({
  api: {
    listPlans: vi.fn().mockResolvedValue([]),
    createPlan: vi.fn().mockResolvedValue({}),
    updatePlan: vi.fn().mockResolvedValue({}),
    deletePlan: vi.fn().mockResolvedValue({}),
    searchPlans: vi.fn().mockResolvedValue([]),
  },
}))

describe('KnowledgeBase Page', () => {
  it('renders page title', async () => {
    render(<KnowledgeBase />)
    await waitFor(() => {
      expect(screen.getByText('知识库管理')).toBeInTheDocument()
    })
  })

  it('renders add plan button', async () => {
    render(<KnowledgeBase />)
    await waitFor(() => {
      expect(screen.getByText('添加预案')).toBeInTheDocument()
    })
  })

  it('renders search input', async () => {
    render(<KnowledgeBase />)
    await waitFor(() => {
      expect(screen.getByPlaceholderText('搜索预案...')).toBeInTheDocument()
    })
  })

  it('renders table columns', async () => {
    const { container } = render(<KnowledgeBase />)
    await waitFor(() => {
      expect(container.querySelector('.ant-table')).toBeTruthy()
    })
  })
})

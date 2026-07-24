import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '../../../test/test-utils'
import PlanWorkbench from '../index'

vi.mock('../../../services/api', () => ({
  api: {
    listIncidents: vi.fn().mockResolvedValue([
      { id: 1, title: '测试灾情', status: 'confirmed' },
    ]),
    listPlans: vi.fn().mockResolvedValue([]),
    generatePlan: vi.fn().mockResolvedValue({ agent_run_id: 1 }),
    getAgentRunDetail: vi.fn().mockResolvedValue({
      run: { output_data: { plan_id: 1, plan_content: '# 测试方案', source_refs: [], auto_dispatches: [] }, status: 'completed' },
      citations: [],
    }),
    getPlan: vi.fn().mockResolvedValue({}),
    updatePlan: vi.fn().mockResolvedValue({}),
    reviewPlan: vi.fn().mockResolvedValue({}),
    updateDispatchStatus: vi.fn().mockResolvedValue({}),
  },
}))

describe('PlanWorkbench Page', () => {
  it('renders page title', async () => {
    render(<PlanWorkbench />)
    await waitFor(() => {
      expect(screen.getByText('应急方案生成')).toBeInTheDocument()
    })
  })

  it('renders incident selector', async () => {
    render(<PlanWorkbench />)
    await waitFor(() => {
      expect(screen.getByText('AI 生成方案')).toBeInTheDocument()
    })
  })

  it('renders history plan section', async () => {
    render(<PlanWorkbench />)
    await waitFor(() => {
      expect(screen.getByText('历史方案')).toBeInTheDocument()
    })
  })

  it('renders empty placeholder when no plan selected', async () => {
    render(<PlanWorkbench />)
    await waitFor(() => {
      expect(screen.getByText('选择灾情后点击「AI 生成方案」')).toBeInTheDocument()
    })
  })
})

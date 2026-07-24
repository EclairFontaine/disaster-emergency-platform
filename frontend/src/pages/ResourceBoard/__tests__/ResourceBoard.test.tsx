import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '../../../test/test-utils'
import ResourceBoard from '../index'

vi.mock('../../../services/api', () => ({
  api: {
    listResources: vi.fn().mockResolvedValue([]),
    listDispatchOrders: vi.fn().mockResolvedValue([]),
    listIncidents: vi.fn().mockResolvedValue([]),
    createResource: vi.fn().mockResolvedValue({}),
    lockResource: vi.fn().mockResolvedValue({ success: true }),
    createDispatchOrder: vi.fn().mockResolvedValue({}),
    updateDispatchStatus: vi.fn().mockResolvedValue({}),
  },
}))

describe('ResourceBoard Page', () => {
  it('renders step guide', async () => {
    render(<ResourceBoard />)
    await waitFor(() => {
      expect(screen.getByText('选择资源')).toBeInTheDocument()
      expect(screen.getByText('锁定资源')).toBeInTheDocument()
      expect(screen.getByText('创建调度')).toBeInTheDocument()
      expect(screen.getByText('释放回收')).toBeInTheDocument()
    })
  })

  it('renders resource panel', async () => {
    render(<ResourceBoard />)
    await waitFor(() => {
      expect(screen.getByText('资源看板')).toBeInTheDocument()
    })
  })

  it('renders dispatch management section', async () => {
    render(<ResourceBoard />)
    await waitFor(() => {
      expect(screen.getByText('调度管理')).toBeInTheDocument()
    })
  })

  it('renders add resource button', async () => {
    render(<ResourceBoard />)
    await waitFor(() => {
      expect(screen.getByText('添加资源')).toBeInTheDocument()
    })
  })

  it('renders new dispatch button', async () => {
    render(<ResourceBoard />)
    await waitFor(() => {
      const buttons = screen.getAllByText('新建调度单')
      expect(buttons.length).toBeGreaterThan(0)
    })
  })
})

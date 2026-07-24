import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor, within } from '../../../test/test-utils'
import userEvent from '@testing-library/user-event'
import ResourceBoard from '../index'

vi.mock('../../../services/api', () => ({
  api: {
    listResources: vi.fn().mockResolvedValue([
      { id: 1, type: 'personnel', name: '消防队', quantity: 100, available_qty: 90, locked_qty: 10, latitude: 25.04, longitude: 102.68, status: 'idle' },
    ]),
    listDispatchOrders: vi.fn().mockResolvedValue([]),
    listIncidents: vi.fn().mockResolvedValue([
      { id: 1, title: '地震灾情' },
    ]),
    createResource: vi.fn().mockResolvedValue({}),
    lockResource: vi.fn().mockResolvedValue({ success: true }),
    createDispatchOrder: vi.fn().mockResolvedValue({}),
    updateDispatchStatus: vi.fn().mockResolvedValue({}),
  },
}))

describe('ResourceBoard Page — 渲染', () => {
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
    await waitFor(() => expect(screen.getByText('资源看板')).toBeInTheDocument())
  })

  it('renders dispatch section', async () => {
    render(<ResourceBoard />)
    await waitFor(() => expect(screen.getByText('调度管理')).toBeInTheDocument())
  })
})

describe('ResourceBoard Page — 交互', () => {
  it('opens add resource modal', async () => {
    render(<ResourceBoard />)
    const user = userEvent.setup()
    await waitFor(() => screen.getByText('添加资源'))
    await user.click(screen.getByText('添加资源'))
    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument()
    })
  })

  it('add resource modal has name field', async () => {
    render(<ResourceBoard />)
    const user = userEvent.setup()
    await waitFor(() => screen.getByText('添加资源'))
    await user.click(screen.getByText('添加资源'))
    await waitFor(() => {
      const dialog = screen.getByRole('dialog')
      const nameLabels = within(dialog).getAllByText('名称')
      expect(nameLabels.length).toBeGreaterThan(0)
    })
  })

  it('opens new dispatch modal', async () => {
    render(<ResourceBoard />)
    const user = userEvent.setup()
    await waitFor(() => screen.getByText('新建调度单'))
    await user.click(screen.getByText('新建调度单'))
    await waitFor(() => {
      const dialogs = screen.getAllByRole('dialog')
      expect(dialogs.length).toBeGreaterThan(0)
    })
  })

  it('shows resource data in table', async () => {
    render(<ResourceBoard />)
    await waitFor(() => {
      expect(screen.getByText('消防队')).toBeInTheDocument()
    })
  })
})

import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '../../../test/test-utils'
import UserManage from '../index'

vi.mock('../../../services/api', () => ({
  api: {
    listUsers: vi.fn().mockResolvedValue([
      { id: 1, username: 'admin', real_name: '管理员', phone: '13800000001', role: { name: 'admin' }, is_active: true, created_at: '2024-01-01' },
      { id: 2, username: 'reporter1', real_name: '张三', phone: '13800000002', role: { name: 'info_reporter' }, is_active: true, created_at: '2024-01-02' },
    ]),
    createUser: vi.fn().mockResolvedValue({}),
    updateUser: vi.fn().mockResolvedValue({}),
    deleteUser: vi.fn().mockResolvedValue({}),
  },
}))

describe('UserManage Page', () => {
  it('renders page title', async () => {
    render(<UserManage />)
    await waitFor(() => {
      expect(screen.getByText('用户管理')).toBeInTheDocument()
    })
  })

  it('renders add user button', async () => {
    render(<UserManage />)
    await waitFor(() => {
      expect(screen.getByText('添加用户')).toBeInTheDocument()
    })
  })

  it('renders user records in table', async () => {
    const { container } = render(<UserManage />)
    await waitFor(() => {
      expect(container.querySelector('.ant-table')).toBeTruthy()
    })
  })

  it('shows admin user in table', async () => {
    render(<UserManage />)
    await waitFor(() => {
      expect(screen.getByText('管理员')).toBeInTheDocument()
    })
  })

  it('shows reporter user in table', async () => {
    render(<UserManage />)
    await waitFor(() => {
      expect(screen.getByText('张三')).toBeInTheDocument()
    })
  })
})

import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '../../../test/test-utils'
import userEvent from '@testing-library/user-event'
import Login from '../index'

const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return { ...actual, useNavigate: () => mockNavigate }
})

vi.mock('../../../services/api', () => ({
  api: {
    login: vi.fn().mockResolvedValue({
      access_token: 'test-token',
      token_type: 'bearer',
      user: { id: 1, username: 'admin', real_name: '管理员', role: { name: 'admin' } },
    }),
  },
}))

vi.mock('../../../store', () => ({
  useAppStore: (selector: any) => {
    const state = {
      user: null,
      setAuth: vi.fn(),
    }
    return selector(state)
  },
}))

describe('Login Page — 渲染', () => {
  it('renders login form', () => {
    render(<Login />)
    expect(screen.getByText('云南自然灾害应急协同决策平台')).toBeInTheDocument()
  })

  it('renders username input', () => {
    render(<Login />)
    expect(screen.getByPlaceholderText('用户名')).toBeInTheDocument()
  })

  it('renders password input', () => {
    render(<Login />)
    expect(screen.getByPlaceholderText('密码')).toBeInTheDocument()
  })

  it('renders login button', () => {
    render(<Login />)
    expect(screen.getByRole('button', { name: /登.*录/ })).toBeInTheDocument()
  })

  it('shows default account hint', () => {
    render(<Login />)
    expect(screen.getByText('默认管理员: admin / admin123')).toBeInTheDocument()
  })
})

describe('Login Page — 交互', () => {
  it('allows typing username', async () => {
    render(<Login />)
    const input = screen.getByPlaceholderText('用户名')
    await userEvent.setup().type(input, 'admin')
    expect(input).toHaveValue('admin')
  })

  it('allows typing password', async () => {
    render(<Login />)
    const input = screen.getByPlaceholderText('密码')
    await userEvent.setup().type(input, 'admin123')
    expect(input).toHaveValue('admin123')
  })

  it('calls login API on form submit', async () => {
    render(<Login />)
    const user = userEvent.setup()
    await user.type(screen.getByPlaceholderText('用户名'), 'admin')
    await user.type(screen.getByPlaceholderText('密码'), 'admin123')
    await user.click(screen.getByRole('button', { name: /登.*录/ }))
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard')
    })
  })

  it('shows validation error on empty submit', async () => {
    render(<Login />)
    const user = userEvent.setup()
    await user.click(screen.getByRole('button', { name: /登.*录/ }))
    await waitFor(() => {
      expect(screen.getByText('请输入用户名')).toBeInTheDocument()
    })
  })
})

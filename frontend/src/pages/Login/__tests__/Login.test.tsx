import { describe, it, expect } from 'vitest'
import { render, screen } from '../../../test/test-utils'
import Login from '../index'

describe('Login Page', () => {
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

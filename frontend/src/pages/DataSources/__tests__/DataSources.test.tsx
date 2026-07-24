import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '../../../test/test-utils'
import DataSources from '../index'

vi.mock('../../../services/api', () => ({
  api: {
    listDatasources: vi.fn().mockResolvedValue([]),
    createDatasource: vi.fn().mockResolvedValue({}),
    updateDatasource: vi.fn().mockResolvedValue({}),
    deleteDatasource: vi.fn().mockResolvedValue({}),
  },
}))

describe('DataSources Page', () => {
  it('renders page title', async () => {
    render(<DataSources />)
    await waitFor(() => {
      expect(screen.getByText('数据源管理')).toBeInTheDocument()
    })
  })

  it('renders add datasource button', async () => {
    render(<DataSources />)
    await waitFor(() => {
      expect(screen.getByText('添加数据源')).toBeInTheDocument()
    })
  })

  it('renders table', async () => {
    const { container } = render(<DataSources />)
    await waitFor(() => {
      expect(container.querySelector('.ant-table')).toBeTruthy()
    })
  })
})

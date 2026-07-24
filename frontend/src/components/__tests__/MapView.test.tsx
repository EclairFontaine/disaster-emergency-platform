import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '../../test/test-utils'
import MapView from '../MapView'

describe('MapView Component', () => {
  it('renders loading state', () => {
    render(<MapView />)
    expect(screen.getByText(/地图加载中|加载/i)).toBeTruthy()
  })

  it('renders with empty incidents and resources', () => {
    render(<MapView incidents={[]} resources={[]} />)
    expect(screen.getByText(/地图加载中|加载/i)).toBeTruthy()
  })
})

import '@testing-library/jest-dom'

Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
})

// Suppress React Router v7 future flag warnings
const originalConsoleError = console.error
console.error = (...args: any[]) => {
  const msg = args[0]?.toString?.() || ''
  if (msg.includes('React Router Future Flag')) return
  originalConsoleError(...args)
}

// Suppress unhandled Axios rejections during component teardown in jsdom
process.on('unhandledRejection', (reason: any) => {
  if (reason?.code === 'ERR_NETWORK' || reason?.config?.url?.includes('/api/')) return
  throw reason
})

import { create } from 'zustand'

interface User {
  id: number
  username: string
  real_name?: string
  phone?: string
  role_id: number
  role?: { id: number; name: string; description?: string }
  is_active: boolean
  created_at?: string
}

interface AppState {
  user: User | null
  token: string | null
  setAuth: (token: string, user: User) => void
  logout: () => void
  isAuthenticated: () => boolean
  hasRole: (roleName: string) => boolean
  notifications: Notification[]
  pushNotification: (n: Notification) => void
  clearNotifications: () => void
}

interface Notification {
  id: number
  event: string
  message: string
  time: number
}

export const useAppStore = create<AppState>((set, get) => ({
  user: null,
  token: null,
  notifications: [],
  setAuth: (token, user) => set({ token, user }),
  logout: () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    set({ token: null, user: null })
  },
  isAuthenticated: () => !!get().token,
  hasRole: (roleName) => get().user?.role?.name === roleName,
  pushNotification: (n) => set((s) => ({ notifications: [n, ...s.notifications].slice(0, 50) })),
  clearNotifications: () => set({ notifications: [] }),
}))

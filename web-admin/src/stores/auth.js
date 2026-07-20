import { defineStore } from 'pinia'
import { api } from '@/api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    refresh: localStorage.getItem('refresh') || '',
    user: JSON.parse(localStorage.getItem('user') || 'null')
  }),
  getters: {
    isLoggedIn: (s) => !!s.token,
    isAdmin: (s) => s.user?.role === 'admin'
  },
  actions: {
    setTokens(access, refresh) {
      this.token = access
      this.refresh = refresh
      localStorage.setItem('token', access)
      localStorage.setItem('refresh', refresh)
    },
    setUser(user) {
      this.user = user
      localStorage.setItem('user', JSON.stringify(user))
    },
    async login(username, password) {
      const data = await api.auth.login(username, password)
      this.setTokens(data.access_token, data.refresh_token)
      const me = await api.auth.me()
      this.setUser(me)
      return me
    },
    async refreshUser() {
      if (!this.isLoggedIn) return null
      try {
        const me = await api.auth.me()
        this.setUser(me)
        return me
      } catch {
        this.logout()
        return null
      }
    },
    logout() {
      this.token = ''
      this.refresh = ''
      this.user = null
      localStorage.removeItem('token')
      localStorage.removeItem('refresh')
      localStorage.removeItem('user')
    }
  }
})

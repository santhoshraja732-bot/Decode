import { defineStore } from 'pinia'
import api from '../api/axios'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: JSON.parse(localStorage.getItem('user') || 'null'),
    token: localStorage.getItem('access_token') || null,
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
    isAdmin: (state) => state.user && state.user.role === 'admin',
  },
  actions: {
    setSession(token, user) {
      this.token = token
      this.user = user
      localStorage.setItem('access_token', token)
      localStorage.setItem('user', JSON.stringify(user))
    },
    async login(username, password) {
      const form = new URLSearchParams()
      form.append('username', username)
      form.append('password', password)
      const { data } = await api.post('/auth/login', form, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })
      this.setSession(data.access_token, data.user)
      return data.user
    },
    async register(username, email, password) {
      const { data } = await api.post('/auth/register', { username, email, password })
      this.setSession(data.access_token, data.user)
      return data.user
    },
    async refreshMe() {
      const { data } = await api.get('/users/me')
      this.user = data
      localStorage.setItem('user', JSON.stringify(data))
      return data
    },
    logout() {
      this.user = null
      this.token = null
      localStorage.removeItem('access_token')
      localStorage.removeItem('user')
    },
  },
})

import { defineStore } from 'pinia'
import api from '../api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('car_token') || '',
    user: JSON.parse(localStorage.getItem('car_user') || 'null')
  }),
  getters: {
    isLogin: (s) => !!s.token
  },
  actions: {
    async login(username, password) {
      const data = await api.post('/auth/login', { username, password })
      this._set(data)
    },
    async register(username, password, display_name) {
      const data = await api.post('/auth/register', { username, password, display_name })
      this._set(data)
    },
    _set(data) {
      this.token = data.token
      this.user = data.user
      localStorage.setItem('car_token', data.token)
      localStorage.setItem('car_user', JSON.stringify(data.user))
    },
    logout() {
      this.token = ''
      this.user = null
      localStorage.removeItem('car_token')
      localStorage.removeItem('car_user')
    }
  }
})

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authApi from '../api/auth'
import { setToken, removeToken, getToken } from '../auth/token'
import { setRole, removeRole, getRole } from '../auth/guards'
import type { User, LoginParams } from '../types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(getToken())

  const isLoggedIn = computed(() => !!token.value)
  const role = computed(() => user.value?.role ?? getRole())

  async function login(params: LoginParams) {
    const res = await authApi.login(params)
    const { access_token, user: u } = res.data
    setToken(access_token)
    setRole(u.role)
    token.value = access_token
    user.value = u
  }

  async function fetchMe() {
    if (!token.value) return
    try {
      const res = await authApi.getMe()
      user.value = res.data
    } catch {
      // token 失效
      token.value = null
      removeToken()
      removeRole()
    }
  }

  async function logout() {
    try {
      await authApi.logout()
    } finally {
      token.value = null
      user.value = null
      removeToken()
      removeRole()
    }
  }

  return { user, token, isLoggedIn, role, login, fetchMe, logout }
})

import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login as apiLogin, getMe, getMyPermissions, type LoginData, type UserInfo } from '@/api/user'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref<UserInfo | null>(null)
  const permissions = ref<string[]>([])

  const isTokenExpired = (tok: string): boolean => {
    if (!tok) return true
    const parts = tok.split('.')
    if (parts.length !== 3) return true
    try {
      const payload = JSON.parse(decodeURIComponent(escape(atob(parts[1].replace(/-/g, '+').replace(/_/g, '/')))))
      const exp = Number(payload.exp || 0)
      const now = Math.floor(Date.now() / 1000)
      return !exp || now >= exp
    } catch {
      return true
    }
  }

  const login = async (data: LoginData): Promise<{ success: boolean; message?: string }> => {
    try {
      const res = await apiLogin(data)
      token.value = res.access_token
      localStorage.setItem('token', res.access_token)
      await fetchUser()
      return { success: true }
    } catch (error: any) {
      const status = error?.response?.status
      if (status === 401) {
        return { success: false, message: '用户名或密码错误' }
      }
      const msg = error?.response?.data?.detail || '登录失败'
      return { success: false, message: msg }
    }
  }

  const fetchUser = async () => {
    if (!token.value || isTokenExpired(token.value)) { logout(); return }
    try {
      const res = await getMe()
      user.value = res
      try {
        permissions.value = await getMyPermissions()
      } catch {}
    } catch (error) {
      console.error('Fetch user failed:', error)
      logout()
    }
  }

  const logout = () => {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  return { token, user, permissions, login, fetchUser, logout }
})

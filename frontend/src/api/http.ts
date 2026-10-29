import axios from 'axios'

import router from '../router'
import { useAuthStore } from '../stores/auth'

const http = axios.create()

http.interceptors.request.use((config) => {
  const auth = useAuthStore()
  if (auth.accessToken) {
    config.headers.Authorization = `Bearer ${auth.accessToken}`
  }
  return config
})

let refreshing: Promise<string> | null = null

http.interceptors.response.use(
  (response) => response,
  async (error) => {
    const auth = useAuthStore()
    const original = error.config
    const url: string = original?.url ?? ''
    const skip =
      error.response?.status !== 401 ||
      original?._retry ||
      url.includes('/api/auth/login') ||
      url.includes('/api/auth/refresh') ||
      url.includes('/api/auth/register') ||
      !auth.refreshToken
    if (skip || !original) {
      return Promise.reject(error)
    }
    original._retry = true
    try {
      if (!refreshing) {
        const pending = axios
          .post('/api/auth/refresh', { refresh_token: auth.refreshToken })
          .then((response) => {
            auth.setSession(response.data)
            return response.data.access_token as string
          })
          .finally(() => {
            refreshing = null
          })
        refreshing = pending
      }
      const token = await refreshing
      original.headers.Authorization = `Bearer ${token}`
      return http(original)
    } catch (refreshError) {
      auth.clear()
      await router.push('/login')
      return Promise.reject(refreshError)
    }
  },
)

export function errorDetail(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') {
      return detail
    }
    if (Array.isArray(detail)) {
      return '请检查输入'
    }
  }
  return '请求失败'
}

export default http

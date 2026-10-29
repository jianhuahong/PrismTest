import { computed, ref } from 'vue'
import { defineStore } from 'pinia'

interface TokenPair {
  access_token: string
  refresh_token: string
}

interface UserProfile {
  username: string
  role: string
}

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref(localStorage.getItem('access_token') ?? '')
  const refreshToken = ref(localStorage.getItem('refresh_token') ?? '')
  const username = ref(localStorage.getItem('username') ?? '')
  const role = ref(localStorage.getItem('role') ?? '')
  const isLoggedIn = computed(() => accessToken.value.length > 0)

  function setSession(tokens: TokenPair, user?: UserProfile) {
    accessToken.value = tokens.access_token
    refreshToken.value = tokens.refresh_token
    localStorage.setItem('access_token', tokens.access_token)
    localStorage.setItem('refresh_token', tokens.refresh_token)
    if (user) {
      username.value = user.username
      role.value = user.role
      localStorage.setItem('username', user.username)
      localStorage.setItem('role', user.role)
    }
  }

  function clear() {
    accessToken.value = ''
    refreshToken.value = ''
    username.value = ''
    role.value = ''
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('username')
    localStorage.removeItem('role')
  }

  return { accessToken, refreshToken, username, role, isLoggedIn, setSession, clear }
})

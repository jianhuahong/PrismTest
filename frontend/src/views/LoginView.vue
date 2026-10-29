<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import http, { errorDetail } from '../api/http'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const health = ref('检查中')
const form = reactive({ username: '', password: '' })

onMounted(async () => {
  try {
    const response = await http.get('/health')
    health.value = response.data.status === 'ok' ? '后端正常' : '后端异常'
  } catch {
    health.value = '后端未连接'
  }
})

async function submit() {
  loading.value = true
  try {
    const response = await http.post('/api/auth/login', form)
    auth.setSession(response.data)
    const me = await http.get('/api/auth/me')
    auth.setSession(response.data, me.data)
    await router.push('/')
  } catch (error) {
    ElMessage.error(errorDetail(error))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page">
    <el-card>
      <h1>登录 Prism</h1>
      <p class="hint">{{ health }}</p>
      <el-form label-position="top" @submit.prevent="submit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" autocomplete="username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password autocomplete="current-password" />
        </el-form-item>
        <el-button type="primary" native-type="submit" :loading="loading">登录</el-button>
        <el-button link @click="router.push('/register')">注册</el-button>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
h1 {
  margin: 0 0 8px;
  font-size: 24px;
}
.hint {
  margin: 0 0 16px;
  color: #909399;
}
</style>

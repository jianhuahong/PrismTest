<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import http, { errorDetail } from '../api/http'
import { roleLabel } from '../roles'
import { useAuthStore } from '../stores/auth'

interface Project {
  id: number
  name: string
  key: string
  my_role: string
  can_write: boolean
}

const router = useRouter()
const auth = useAuthStore()
const projects = ref<Project[]>([])
const loading = ref(false)
const creating = ref(false)
const dialog = ref(false)
const form = reactive({ name: '', key: '' })

async function load() {
  loading.value = true
  try {
    const response = await http.get<Project[]>('/api/projects')
    projects.value = response.data
  } catch (error) {
    ElMessage.error(errorDetail(error))
  } finally {
    loading.value = false
  }
}

async function createProject() {
  creating.value = true
  try {
    await http.post('/api/projects', form)
    dialog.value = false
    form.name = ''
    form.key = ''
    await load()
  } catch (error) {
    ElMessage.error(errorDetail(error))
  } finally {
    creating.value = false
  }
}

function openProject(row: Project) {
  void router.push(`/projects/${row.id}`)
}

function logout() {
  const refresh = auth.refreshToken
  auth.clear()
  void http.post('/api/auth/logout', { refresh_token: refresh }).catch(() => undefined)
  void router.push('/login')
}

onMounted(load)
</script>

<template>
  <div class="page">
    <div class="toolbar">
      <h1>项目</h1>
      <div>
        <span class="who">{{ auth.username }}（{{ roleLabel[auth.role] ?? auth.role }}）</span>
        <el-button type="primary" @click="dialog = true">新建项目</el-button>
        <el-button @click="logout">退出</el-button>
      </div>
    </div>
    <el-table v-loading="loading" :data="projects" @row-click="openProject">
      <el-table-column prop="name" label="名称" />
      <el-table-column prop="key" label="标识" />
      <el-table-column label="我的角色">
        <template #default="{ row }">{{ roleLabel[row.my_role] ?? row.my_role }}</template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialog" title="新建项目" width="420px">
      <el-form label-position="top" @submit.prevent="createProject">
        <el-form-item label="名称">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="标识">
          <el-input v-model="form.key" placeholder="小写字母开头，如 demo-api" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="createProject">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
h1 {
  margin: 0;
  font-size: 24px;
}
.who {
  margin-right: 12px;
  color: #606266;
}
</style>

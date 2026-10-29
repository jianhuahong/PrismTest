<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import http, { errorDetail } from '../api/http'
import { roleLabel } from '../roles'

interface Project {
  id: number
  name: string
  key: string
  my_role: string
  can_write: boolean
}

interface Member {
  user_id: number
  username: string
  role: string
}

const route = useRoute()
const router = useRouter()
const project = ref<Project | null>(null)
const members = ref<Member[]>([])
const name = ref('')
const saving = ref(false)
const adding = ref(false)
const loadError = ref('')
const memberForm = reactive({ username: '', role: 'readonly' })

const projectId = computed(() => route.params.id)
const canManageMembers = computed(
  () => project.value?.my_role === 'admin' || project.value?.my_role === 'owner',
)

async function load() {
  loadError.value = ''
  try {
    const [projectResponse, memberResponse] = await Promise.all([
      http.get<Project>(`/api/projects/${projectId.value}`),
      http.get<Member[]>(`/api/projects/${projectId.value}/members`),
    ])
    project.value = projectResponse.data
    name.value = projectResponse.data.name
    members.value = memberResponse.data
  } catch (error) {
    project.value = null
    loadError.value = errorDetail(error)
    ElMessage.error(loadError.value)
  }
}

async function rename() {
  saving.value = true
  try {
    const response = await http.patch<Project>(`/api/projects/${projectId.value}`, { name: name.value })
    project.value = response.data
    ElMessage.success('已保存')
  } catch (error) {
    ElMessage.error(errorDetail(error))
  } finally {
    saving.value = false
  }
}

async function addMember() {
  adding.value = true
  try {
    await http.post(`/api/projects/${projectId.value}/members`, memberForm)
    memberForm.username = ''
    memberForm.role = 'readonly'
    await load()
  } catch (error) {
    ElMessage.error(errorDetail(error))
  } finally {
    adding.value = false
  }
}

onMounted(load)
</script>

<template>
  <div class="page" v-if="loadError">
    <el-button link @click="router.push('/')">返回项目列表</el-button>
    <el-alert class="card-gap" :title="loadError" type="error" show-icon :closable="false" />
  </div>
  <div class="page" v-else-if="project">
    <el-button link @click="router.push('/')">返回项目列表</el-button>
    <h1>{{ project.name }}</h1>
    <p class="meta">标识 {{ project.key }} · 我的角色 {{ roleLabel[project.my_role] ?? project.my_role }}</p>

    <el-card>
      <template #header>项目名称</template>
      <el-form inline @submit.prevent="rename">
        <el-input v-model="name" :disabled="!project.can_write" style="width: 280px" />
        <el-button
          type="primary"
          native-type="submit"
          :disabled="!project.can_write"
          :loading="saving"
        >
          保存
        </el-button>
      </el-form>
      <p v-if="!project.can_write" class="hint">只读成员不能修改。</p>
    </el-card>

    <el-card class="card-gap">
      <template #header>成员</template>
      <el-table :data="members">
        <el-table-column prop="username" label="用户名" />
        <el-table-column label="角色">
          <template #default="{ row }">{{ roleLabel[row.role] ?? row.role }}</template>
        </el-table-column>
      </el-table>
      <el-form v-if="canManageMembers" class="add" inline @submit.prevent="addMember">
        <el-input v-model="memberForm.username" placeholder="用户名" style="width: 180px" />
        <el-select v-model="memberForm.role" style="width: 140px">
          <el-option label="负责人" value="owner" />
          <el-option label="成员" value="member" />
          <el-option label="只读" value="readonly" />
        </el-select>
        <el-button type="primary" native-type="submit" :loading="adding">添加</el-button>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
h1 {
  margin: 8px 0;
  font-size: 24px;
}
.meta,
.hint {
  color: #909399;
}
.add {
  margin-top: 16px;
}
</style>

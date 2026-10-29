import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '../stores/auth'
import LoginView from '../views/LoginView.vue'
import ProjectDetailView from '../views/ProjectDetailView.vue'
import ProjectListView from '../views/ProjectListView.vue'
import RegisterView from '../views/RegisterView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: LoginView },
    { path: '/register', component: RegisterView },
    { path: '/', component: ProjectListView, meta: { auth: true } },
    { path: '/projects/:id', component: ProjectDetailView, meta: { auth: true } },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.auth && !auth.isLoggedIn) {
    return '/login'
  }
  if ((to.path === '/login' || to.path === '/register') && auth.isLoggedIn) {
    return '/'
  }
  return true
})

export default router

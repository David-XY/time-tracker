// src/router.ts
import { createRouter, createWebHistory } from 'vue-router'
import Backlog from './pages/ProjectBacklog.vue'
import Issue from './pages/IssueDetail.vue'
import TimeLog from './pages/TimeLog.vue'
import Reports from './pages/Reports.vue'
import Login from './pages/Login.vue'
import { api } from './api'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: Login },
    { path: '/', component: Backlog },
    { path: '/issue/:id', component: Issue },
    { path: '/timelog', component: TimeLog },
    { path: '/reports', component: Reports },
  ]
})

let checked = false
router.beforeEach(async (to, from, next) => {
  if (to.path === '/login') return next()
  if (!checked) {
    try {
      const res = await api.me()
      if (!res.user) return next('/login')
    } catch {
      return next('/login')
    }
    checked = true
  }
  next()
})

export default router

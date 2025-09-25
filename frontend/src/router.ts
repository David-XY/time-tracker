import { createRouter, createWebHistory } from 'vue-router'
import Backlog from './pages/ProjectBacklog.vue'
import Issue from './pages/IssueDetail.vue'
import TimeLog from './pages/TimeLog.vue'
import Reports from './pages/Reports.vue'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: Backlog },
    { path: '/issue/:id', component: Issue },
    { path: '/timelog', component: TimeLog },
    { path: '/reports', component: Reports },
  ]
})

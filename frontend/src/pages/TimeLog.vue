<template>
  <section>
    <div style="display:flex; gap:0.5rem; align-items:center; margin-bottom: 1rem;">
      <label>Week starting:</label>
      <input type="date" v-model="weekStart" />
      <label>User:</label>
      <select v-model.number="userId">
        <option :value="0">All</option>
        <option v-for="u in users" :key="u.id" :value="u.id">{{ u.username }}</option>
      </select>
      <label>Project:</label>
      <select v-model.number="projectId">
        <option :value="0">All</option>
        <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
      </select>
    </div>
    <table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse; width:100%">
      <thead><tr><th>Date</th><th>User</th><th>Issue</th><th>Minutes</th><th>Notes</th></tr></thead>
      <tbody>
        <tr v-for="t in entries" :key="t.id">
          <td>{{ t.date }}</td>
          <td>{{ t.user }}</td>
          <td>{{ t.issue_title }}</td>
          <td>{{ t.duration_minutes }}</td>
          <td>{{ t.notes }}</td>
        </tr>
      </tbody>
    </table>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { api } from '../api'

const weekStart = ref<string>(getMonday(new Date()).toISOString().slice(0,10))
const users = ref<any[]>([])
const projects = ref<any[]>([])
const userId = ref<number>(0)
const projectId = ref<number>(0)
const entries = ref<any[]>([])

function getMonday(d: Date) {
  const day = d.getDay() || 7
  const monday = new Date(d)
  if (day !== 1) monday.setDate(d.getDate() - day + 1)
  monday.setHours(0,0,0,0)
  return monday
}

async function load() {
  const [us, ps] = await Promise.all([api.users(), api.projects()])
  users.value = us; projects.value = ps;
  await loadEntries()
}
async function loadEntries(){
  const params:any = { week_start: weekStart.value }
  if (userId.value) params.user_id = userId.value
  if (projectId.value) params.project_id = projectId.value
  entries.value = await api.timeEntries(params)
}
onMounted(load)
watch([weekStart, userId, projectId], loadEntries)
</script>

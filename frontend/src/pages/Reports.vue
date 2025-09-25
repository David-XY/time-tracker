<template>
  <section>
    <div style="display:flex; gap:0.5rem; align-items:center; margin-bottom:1rem">
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
      <button @click="downloadPdf">Download PDF</button>
    </div>
    <canvas ref="canvas"></canvas>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { api } from '../api'
import { Chart, BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend } from 'chart.js'
Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend)

const canvas = ref<HTMLCanvasElement | null>(null)
const weekStart = ref<string>(getMonday(new Date()).toISOString().slice(0,10))
const users = ref<any[]>([])
const projects = ref<any[]>([])
const userId = ref<number>(0)
const projectId = ref<number>(0)
let chart: Chart | null = null

function getMonday(d: Date) {
  const day = d.getDay() || 7
  const monday = new Date(d)
  if (day !== 1) monday.setDate(d.getDate() - day + 1)
  monday.setHours(0,0,0,0)
  return monday
}

function randomColor() {
  const r = Math.floor(Math.random() * 200)
  const g = Math.floor(Math.random() * 200)
  const b = Math.floor(Math.random() * 200)
  return `rgba(${r}, ${g}, ${b}, 0.7)`
}

async function draw() {
  const params:any = { week_start: weekStart.value }
  if (userId.value) params.user_id = userId.value
  if (projectId.value) params.project_id = projectId.value
  const data = await api.reportWeek(params)

  // assign distinct colors
  data.datasets = data.datasets.map((ds:any) => ({
    ...ds,
    backgroundColor: randomColor()
  }))

  const ctx = canvas.value!.getContext('2d')!
  if (chart) chart.destroy()
  chart = new Chart(ctx, {
    type: 'bar',
    data,
    options: {
      responsive: true,
      scales: {
        x: { stacked: false },  // grouped bars
        y: { stacked: false }
      }
    }
  })
}

function downloadPdf(){
  const params:any = { week_start: weekStart.value }
  if (userId.value) params.user_id = userId.value
  if (projectId.value) params.project_id = projectId.value
  const url = api.reportPdfUrl(params)
  window.open(url, '_blank')
}

onMounted(async ()=>{
  const [us, ps] = await Promise.all([api.users(), api.projects()])
  users.value = us; projects.value = ps;
  await draw()
})
watch([weekStart, userId, projectId], draw)
</script>

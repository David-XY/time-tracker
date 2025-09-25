<template>
  <section>
    <div style="display:flex; gap:0.5rem; align-items:center; margin-bottom: 1rem;">
      <label>Project:</label>
      <select v-model.number="projectId">
        <option :value="0">All</option>
        <option v-for="p in projects" :key="p.id" :value="p.id">{{ p.name }}</option>
      </select>
      <input v-model="qLabel" placeholder="Filter label" style="width:10rem" />
      <input v-model="qAssignee" placeholder="Assignee" style="width:10rem" />
    </div>

    <ul style="list-style:none; padding:0; display:grid; gap:0.5rem">
      <li v-for="i in issues" :key="i.id" style="border:1px solid #ddd; padding:0.75rem; border-radius:8px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <div style="font-weight:600">{{ i.title }}</div>
            <small>Issue #{{ i.github_number }} — <a :href="i.url" target="_blank">GitHub</a> — {{ i.state }}</small><br/>
            <small v-if="i.assignee">Assignee: {{ i.assignee }}</small><br/>
            <small v-if="i.labels?.length">Labels: {{ i.labels.join(', ') }}</small>
          </div>
          <div style="display:flex; gap:0.5rem; align-items:center;">
            <button @click="start(i.id)">Start</button>
            <button @click="stop()">Stop</button>
            <router-link :to="`/issue/${i.id}`">Open</router-link>
          </div>
        </div>
      </li>
    </ul>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { api } from '../api'

const projects = ref<any[]>([])
const issues = ref<any[]>([])
const projectId = ref<number>(0)
const qLabel = ref<string>('')
const qAssignee = ref<string>('')

async function load() {
  projects.value = await api.projects()
  await loadIssues()
}
async function loadIssues() {
  const params:any = {}
  if (projectId.value) params.project_id = projectId.value
  if (qLabel.value) params.label = qLabel.value
  if (qAssignee.value) params.assignee = qAssignee.value
  issues.value = await api.issues(params)
}
function start(id:number){ api.startTimer(id).then(loadIssues).catch(alert) }
function stop(){ api.stopTimer().then(loadIssues).catch(err=>alert(err)) }

onMounted(load)
watch([projectId, qLabel, qAssignee], loadIssues)
</script>

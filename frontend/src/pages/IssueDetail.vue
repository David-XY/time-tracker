<template>
  <section v-if="issue">
    <h2 style="margin-bottom:0.25rem">{{ issue.title }}</h2>
    <p><small>Issue #{{ issue.github_number }} — <a :href="issue.url" target="_blank">GitHub</a> — {{ issue.state }}</small></p>
    <p v-if="issue.assignee"><small>Assignee: {{ issue.assignee }}</small></p>
    <p v-if="issue.labels?.length"><small>Labels: {{ issue.labels.join(', ') }}</small></p>

    <div style="display:flex; gap:0.75rem; margin:1rem 0;">
      <button @click="start">Start Timer</button>
      <button @click="stop">Stop Timer</button>
    </div>

    <form @submit.prevent="addManual">
      <label>Manual add (minutes):</label>
      <input v-model.number="minutes" type="number" min="1" required style="width:8rem" />
      <label>Date:</label>
      <input v-model="date" type="date" />
      <input v-model="notes" placeholder="Notes (optional)" style="width:16rem" />
      <button type="submit">Add</button>
    </form>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from '../api'
import { useRoute } from 'vue-router'

const route = useRoute()
const id = Number(route.params.id)
const issue = ref<any>(null)
const minutes = ref<number>(30)
const date = ref<string>(new Date().toISOString().slice(0,10))
const notes = ref<string>('')

async function load() { issue.value = await api.issue(id) }
async function start() { await api.startTimer(id); alert('Started timer'); }
async function stop() { await api.stopTimer(); alert('Stopped timer'); }
async function addManual(){
  await api.addTime(id, { duration_minutes: minutes.value, date: date.value, notes: notes.value })
  minutes.value = 30; notes.value = ''
  alert('Time added')
}
onMounted(load)
</script>

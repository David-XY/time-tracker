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
      <li
        v-for="i in issues"
        :key="i.id"
        style="border:1px solid #ddd; padding:0.75rem; border-radius:8px;"
      >
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <div style="font-weight:600">{{ i.title }}</div>
            <small>
              Issue #{{ i.github_number }} —
              <a :href="i.url" target="_blank">GitHub</a> — {{ i.state }}
            </small><br/>
            <small v-if="i.assignee">Assignee: {{ i.assignee }}</small><br/>
            <small v-if="i.labels?.length">Labels: {{ i.labels.join(', ') }}</small>
          </div>
          <div style="display:flex; gap:0.5rem; align-items:center;">
            <button
              :disabled="loadingIssueId === i.id"
              @click="toggleTimer(i)"
            >
              <span v-if="loadingIssueId === i.id">⏳</span>
              <span v-else-if="activeIssueId === i.id">⏹ Stop</span>
              <span v-else>▶ Start</span>
            </button>
          </div>
        </div>

        <!-- Manual time entry form -->
        <form
          @submit.prevent="addManual(i)"
          style="margin-top:0.5rem; display:flex; gap:0.5rem; align-items:center; flex-wrap:wrap;"
        >
          <input
            v-model="manualDuration[i.id]"
            placeholder="Duration (e.g. 1h 30m, 90m)"
            style="width:12rem"
          />
          <input
            v-model="manualDate[i.id]"
            type="date"
          />
          <input
            v-model="manualNotes[i.id]"
            placeholder="Notes"
            style="flex:1; min-width:10rem"
          />
          <button type="submit">Add</button>
        </form>
      </li>
    </ul>
  </section>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { api } from '../api'

const emit = defineEmits<{
  (e: 'timer-changed'): void
}>()

const projects = ref<any[]>([])
const issues = ref<any[]>([])
const projectId = ref<number>(0)
const qLabel = ref<string>('')
const qAssignee = ref<string>('')

const activeIssueId = ref<number | null>(null)
const loadingIssueId = ref<number | null>(null)

// Manual entry state per issue
const manualDuration = ref<{ [key: number]: string }>({})
const manualDate = ref<{ [key: number]: string }>({})
const manualNotes = ref<{ [key: number]: string }>({})

async function load() {
  projects.value = await api.projects()
  await loadIssues()
  const status = await api.timerStatus().catch(() => null)
  activeIssueId.value = status?.issue_id || null
}

async function loadIssues() {
  const params: any = {}
  if (projectId.value) params.project_id = projectId.value
  if (qLabel.value) params.label = qLabel.value
  if (qAssignee.value) params.assignee = qAssignee.value
  issues.value = await api.issues(params)

  // initialize manual form state for each issue
  for (const i of issues.value) {
    if (!(i.id in manualDuration.value)) manualDuration.value[i.id] = ''
    if (!(i.id in manualDate.value)) manualDate.value[i.id] = new Date().toISOString().slice(0, 10)
    if (!(i.id in manualNotes.value)) manualNotes.value[i.id] = ''
  }
}

async function toggleTimer(issue: any) {
  loadingIssueId.value = issue.id
  try {
    if (activeIssueId.value === issue.id) {
      await api.stopTimer()
      activeIssueId.value = null
    } else {
      await api.startTimer(issue.id)
      activeIssueId.value = issue.id
    }
    emit('timer-changed') // notify parent (App.vue) so header updates immediately
  } catch (err) {
    alert(err)
  } finally {
    loadingIssueId.value = null
  }
}

function parseDuration(input: string): number {
  if (!input) return 0
  input = input.trim().toLowerCase()

  const hourMatch = input.match(/(\d+)\s*h/)
  const minMatch = input.match(/(\d+)\s*m/)

  let total = 0
  if (hourMatch) total += parseInt(hourMatch[1], 10) * 60
  if (minMatch) total += parseInt(minMatch[1], 10)

  // If only digits given → treat as minutes
  if (!hourMatch && !minMatch && /^\d+$/.test(input)) {
    total = parseInt(input, 10)
  }

  return total
}

async function addManual(issue: any) {
  const totalMinutes = parseDuration(manualDuration.value[issue.id] || '')

  if (totalMinutes <= 0) {
    alert('Please enter a valid duration (e.g. "1h 30m", "90m")')
    return
  }

  const d = manualDate.value[issue.id] || new Date().toISOString().slice(0, 10)
  const notes = manualNotes.value[issue.id] || ''

  await api.addTime(issue.id, { duration_minutes: totalMinutes, date: d, notes })

  // reset form
  manualDuration.value[issue.id] = ''
  manualNotes.value[issue.id] = ''
  manualDate.value[issue.id] = new Date().toISOString().slice(0, 10)

  alert(`Added ${totalMinutes} minutes`)
}

onMounted(load)
watch([projectId, qLabel, qAssignee], loadIssues)
</script>

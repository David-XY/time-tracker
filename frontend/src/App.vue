<template>
  <div style="max-width:1000px;margin:2rem auto;padding:1rem">
    <header style="display:flex;gap:1rem;align-items:center;justify-content:space-between">
      <h1>Time Tracker</h1>
      <div style="display:flex;gap:1rem;align-items:center">
        <nav style="display:flex;gap:0.75rem">
          <router-link to="/">Backlog</router-link>
          <router-link to="/timelog">Time Log</router-link>
          <router-link to="/reports">Reports</router-link>
        </nav>
        <span v-if="me">👤 {{ me.username }}</span>
        <a :href="loginHref" v-else>Login with GitHub</a>
        <span v-if="timer?.running" style="font-size:0.9rem;">
          ⏱ {{ timer.issue_title }} • {{ pretty(timer.elapsed_seconds) }}
        </span>
      </div>
    </header>
    <router-view @timer-changed="refreshTimer" />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { api } from './api'

const me = ref<any>(null)
const timer = ref<any>(null)
const loginHref = `https://${location.hostname.replace('app.', '')}/auth/github/login`

function pretty(s: number){
  const m = Math.floor(s/60), sec = s%60
  return `${m}m ${sec}s`
}

async function refreshTimer() {
  try {
    const t = await api.timerStatus()
    timer.value = t
  } catch {
    timer.value = null
  }
}

async function load(){
  me.value = (await api.me()).user
  await refreshTimer()
}

onMounted(() => {
  load()
  setInterval(() => {
    if (timer.value?.running) {
      timer.value.elapsed_seconds += 1
    }
  }, 1000)
})
</script>

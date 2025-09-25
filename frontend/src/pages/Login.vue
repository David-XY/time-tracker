<template>
  <section style="text-align:center; margin-top:5rem;">
    <h2>Welcome to Time Tracker</h2>
    <p>You must log in with GitHub to continue.</p>
    <a :href="loginHref">
      <button>Login with GitHub</button>
    </a>
  </section>
</template>

<script setup lang="ts">
const loginHref = `https://${location.hostname.replace('app.', '')}/auth/github/login`
</script>

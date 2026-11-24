<script setup>
import { onBeforeUnmount, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppShell from './components/common/AppShell.vue'
import { logout, store, toast } from './store'

const route = useRoute()
const router = useRouter()

function expired() {
  logout()
  toast('Session ended. Please log in again.', 'warning')
  router.push('/login')
}
onMounted(() => window.addEventListener('auth-expired', expired))
onBeforeUnmount(() => window.removeEventListener('auth-expired', expired))
</script>

<template>
  <AppShell v-if="store.user && route.meta.role">
    <router-view :key="route.fullPath" />
  </AppShell>
  <router-view v-else />

  <div class="toasts" aria-live="polite">
    <div v-for="t in store.toasts" :key="t.id" class="toast" :class="t.type">{{ t.message }}</div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { get, post } from '../../api'
import { logout, store, toast } from '../../store'

const route = useRoute()
const router = useRouter()
const menuOpen = ref(false)
const bellOpen = ref(false)
const notes = ref({ items: [], unread: 0 })
let timer = null
let lastTopId = null

const NAV = {
  admin: [
    ['/admin', 'Dashboard'],
    ['/admin/treks', 'Treks'],
    ['/admin/staff', 'Trekking Staff'],
    ['/admin/users', 'Users (Trekkers)'],
    ['/admin/bookings', 'Bookings'],
    ['/admin/reports', 'Reports']
  ],
  staff: [['/staff', 'Dashboard']],
  user: [
    ['/dashboard', 'Dashboard'],
    ['/browse', 'Browse Treks'],
    ['/bookings', 'My Bookings'],
    ['/history', 'History'],
    ['/profile', 'Profile']
  ]
}

const links = computed(() => NAV[store.user.role] || [])
const roleLabel = computed(
  () => ({ admin: 'Administrator', staff: 'Trekking Staff', user: 'Trekker' })[store.user.role]
)

async function poll() {
  try {
    const data = await get('/notifications')
    const top = data.items
    if (lastTopId !== null && top && top.id > lastTopId && !top.is_read) {
      toast(top.message, top.kind === 'info' ? 'info' : top.kind)
    }
    lastTopId = top ? top.id : 0
    notes.value = data
  } catch {}
}

async function toggleBell() {
  bellOpen.value = !bellOpen.value
  if (!bellOpen.value && notes.value.unread) {
    await post('/notifications/read')
    poll()
  }
}

function leave() {
  logout()
  router.push('/login')
}

onMounted(() => {
  poll()
  timer = setInterval(poll, 5000)
})

onBeforeUnmount(() => clearInterval(timer))
</script>

<template>
  <div class="shell">
    <div class="scrim" :class="{ show: menuOpen }" @click="menuOpen = false"></div>

    <aside class="sidebar" :class="{ open: menuOpen }">
      <div class="brand">TrekHub</div>
      <nav class="nav" @click="menuOpen = false">
        <router-link
          v-for="[to, label] in links"
          :key="to"
          :to="to"
          :class="{
            active:
              route.path.startsWith(to) &&
              ((to !== '/admin' && to !== '/staff') || route.path === to)
          }"
        >
          {{ label }}
        </router-link>
      </nav>
      <div class="side-foot">
        <div><b>{{ store.user.name }}</b></div>
        <div>{{ roleLabel }}</div>
        <button
          class="btn ghost sm mt"
          style="color: #fff; border-color: rgba(255, 255, 255, 0.3)"
          @click="leave"
        >
          Logout
        </button>
      </div>
    </aside>

    <div class="main">
      <header class="topbar">
        <button class="icon-btn hamburger" aria-label="Open menu" @click="menuOpen = true">
          Menu
        </button>
        <span class="title grow">Trekking Management Application</span>
        <div style="position: relative">
          <button class="icon-btn" aria-label="Notifications" @click="toggleBell">
            Notifications
            <span v-if="notes.unread" class="bell-badge">{{ notes.unread }}</span>
          </button>
          <div v-if="bellOpen" class="dropdown">
            <div class="dd-head">
              <span>Notifications</span>
              <a href="#" @click.prevent="toggleBell">Close</a>
            </div>
            <div class="dd-list">
              <div v-if="!notes.items.length" class="empty">You're all caught up.</div>
              <div
                v-for="n in notes.items"
                :key="n.id"
                class="dd-item"
                :class="{ unread: !n.is_read }"
              >
                {{ n.message }}<small>{{ n.created_at }}</small>
              </div>
            </div>
          </div>
        </div>
      </header>
      <main class="content"><slot /></main>
    </div>
  </div>
</template>

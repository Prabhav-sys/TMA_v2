<script setup>
import { onMounted, ref, watch } from 'vue'
import { get, qs } from '../../api'
import { toast } from '../../store'

const rows = ref([])
const loading = ref(true)
const q = ref('')

async function load() {
  loading.value = true
  try {
    rows.value = await get('/admin/bookings' + qs({ q: q.value }))
  } catch (e) {
    toast(e.message, 'error')
  } finally {
    loading.value = false
  }
}

let timer
watch(q, () => {
  clearTimeout(timer)
  timer = setTimeout(load, 250)
})

onMounted(load)
</script>

<template>
  <div class="page-head">
    <h1>Bookings</h1>
  </div>

  <div class="card flush">
    <div class="card-head">
      <input
        v-model="q"
        class="input"
        style="max-width: 320px"
        type="search"
        placeholder="Search by user or trek..."
        aria-label="Search bookings"
      />
    </div>

    <p v-if="loading" class="empty">Loading bookings...</p>

    <div v-else class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>User</th>
            <th>Trek</th>
            <th>Location</th>
            <th>Trek Dates</th>
            <th>Booked On</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="b in rows" :key="b.id">
            <td>{{ b.id }}</td>
            <td>
              <b>{{ b.user_name }}</b>
              <div class="small muted">{{ b.user_email }}</div>
            </td>
            <td>{{ b.trek_name }}</td>
            <td>{{ b.location }}</td>
            <td>{{ b.start_date }} to {{ b.end_date }}</td>
            <td>{{ b.booking_date }}</td>
            <td><span class="badge" :class="b.status">{{ b.status }}</span></td>
          </tr>
          <tr v-if="!rows.length">
            <td colspan="7" class="empty">No bookings found.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

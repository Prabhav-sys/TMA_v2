<script setup>
import { onMounted, ref } from 'vue'
import { get, post } from '../../api'
import { toast } from '../../store'

const rows = ref([])
const loading = ref(true)

async function load() {
  try {
    rows.value = await get('/bookings')
  } catch (e) {
    toast(e.message, 'error')
  } finally {
    loading.value = false
  }
}

onMounted(load)

async function cancel(b) {
  if (!confirm(`Cancel your booking for ${b.trek_name}?`)) return
  try {
    await post(`/bookings/${b.id}/cancel`)
    toast('Booking cancelled', 'success')
    load()
  } catch (e) {
    toast(e.message, 'error')
  }
}
</script>

<template>
  <div class="page-head">
    <div>
      <h1>My Bookings</h1>
      <p>Track the status of every trek you booked.</p>
    </div>
    <router-link to="/browse" class="btn">Book another trek</router-link>
  </div>

  <div class="card flush">
    <p v-if="loading" class="empty">Loading bookings...</p>
    <div v-else class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Trek</th>
            <th>Trek Dates</th>
            <th>Booked On</th>
            <th>Trek Status</th>
            <th>Booking Status</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="b in rows" :key="b.id">
            <td>
              <router-link :to="`/treks/${b.trek_id}`"><b>{{ b.trek_name }}</b></router-link>
              <div class="small muted">{{ b.location }}</div>
            </td>
            <td>{{ b.start_date }} to {{ b.end_date }}</td>
            <td>{{ b.booking_date }}</td>
            <td><span class="badge" :class="b.trek_status">{{ b.trek_status }}</span></td>
            <td><span class="badge" :class="b.status">{{ b.status }}</span></td>
            <td>
              <button
                v-if="b.status === 'Booked' && !['Ongoing', 'Completed'].includes(b.trek_status)"
                class="btn sm danger ghost"
                @click="cancel(b)"
              >
                Cancel
              </button>
            </td>
          </tr>
          <tr v-if="!rows.length">
            <td colspan="6" class="empty">No bookings yet. Find your first trek!</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { get } from '../../api'
import StatCard from '../common/StatCard.vue'

const s = ref(null)
const error = ref('')

onMounted(async () => {
  try {
    s.value = await get('/admin/stats')
  } catch (e) {
    error.value = e.message
  }
})
</script>

<template>
  <div class="page-head">
    <div>
      <h1>Admin Dashboard</h1>
      <p>System summary and recent booking activity.</p>
    </div>
  </div>

  <div v-if="error" class="error-box">{{ error }}</div>
  <p v-else-if="!s" class="muted">Loading dashboard...</p>

  <template v-else>
    <div class="row mb">
      <StatCard label="Total Treks" :value="s.total_treks" />
      <StatCard label="Total Users (Trekkers)" :value="s.total_users" />
      <StatCard label="Total Trekking Staff" :value="s.total_staff" />
      <StatCard label="Total Bookings" :value="s.total_bookings" />
      <StatCard label="Active Bookings" :value="s.active_bookings" />
      <StatCard label="Completed Treks" :value="s.completed_treks" />
    </div>

    <div class="card flush">
      <div class="card-head">
        <h3>Recent Bookings</h3>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Booking</th>
              <th>User</th>
              <th>Trek</th>
              <th>Date</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="b in s.recent_bookings" :key="b.id">
              <td>#{{ b.id }}</td>
              <td>{{ b.user_name }}</td>
              <td>{{ b.trek_name }}</td>
              <td>{{ b.booking_date }}</td>
              <td><span class="badge" :class="b.status">{{ b.status }}</span></td>
            </tr>
            <tr v-if="!s.recent_bookings.length">
              <td colspan="5" class="empty">No bookings yet.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </template>
</template>

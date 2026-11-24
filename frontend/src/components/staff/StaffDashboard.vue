<script setup>
import { onMounted, ref } from 'vue'
import { get } from '../../api'
import { store } from '../../store'
import StatCard from '../common/StatCard.vue'

const d = ref(null)
const error = ref('')

onMounted(async () => {
  try {
    d.value = await get('/staff/dashboard')
  } catch (e) {
    error.value = e.message
  }
})
</script>

<template>
  <div class="page-head">
    <div>
      <h1>Staff Dashboard</h1>
      <p>Hello {{ store.user.name }}, here are the treks you lead.</p>
    </div>
  </div>

  <div v-if="error" class="error-box">{{ error }}</div>
  <p v-else-if="!d" class="muted">Loading dashboard...</p>

  <template v-else>
    <div class="row mb">
      <StatCard label="Assigned Treks" :value="d.assigned" />
      <StatCard label="Total Participants" :value="d.total_participants" />
      <StatCard label="Ongoing Treks" :value="d.ongoing" />
    </div>

    <div class="card flush">
      <div class="card-head">
        <h3>My Assigned Treks</h3>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Trek</th>
              <th>Dates</th>
              <th>Participants</th>
              <th>Slots</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in d.treks" :key="t.id">
              <td>
                <b>{{ t.name }}</b>
                <div class="small muted">{{ t.location }}</div>
              </td>
              <td>{{ t.start_date }} to {{ t.end_date }}</td>
              <td>{{ t.registered }}</td>
              <td>{{ t.available_slots }} left of {{ t.total_slots }}</td>
              <td><span class="badge" :class="t.status">{{ t.status }}</span></td>
              <td>
                <router-link class="btn sm" :to="`/staff/treks/${t.id}`">Manage</router-link>
              </td>
            </tr>
            <tr v-if="!d.treks.length">
              <td colspan="6" class="empty">
                No treks assigned to you yet. The admin will assign treks.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </template>
</template>

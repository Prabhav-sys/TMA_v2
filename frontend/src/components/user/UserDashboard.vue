<script setup>
import { onMounted, ref } from 'vue'
import { get } from '../../api'
import { store, toast } from '../../store'
import StatCard from '../common/StatCard.vue'

const dash = ref(null)
const treks = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const [d, t] = await Promise.all([get('/dashboard'), get('/treks?status=Open')])
    dash.value = d
    treks.value = t.filter((x) => x.available_slots > 0).slice(0, 5)
  } catch (e) {
    toast(e.message, 'error')
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="page-head">
    <div>
      <h1>Welcome, {{ store.user.name.split(' ')[0] }}!</h1>
      <p>Overview of your bookings and available treks.</p>
    </div>
  </div>

  <p v-if="loading" class="muted">Loading...</p>

  <template v-else>
    <div class="row mb">
      <StatCard label="Upcoming treks" :value="dash.booked" />
      <StatCard label="Completed treks" :value="dash.completed" />
      <StatCard label="Cancelled" :value="dash.cancelled" />
    </div>

    <div class="card flush mb">
      <div class="card-head">
        <h3>Available Treks</h3>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Trek Name</th>
              <th>Location</th>
              <th>Difficulty</th>
              <th>Start Date</th>
              <th>Slots Left</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in treks" :key="t.id">
              <td><b>{{ t.name }}</b></td>
              <td>{{ t.location }}</td>
              <td>{{ t.difficulty }}</td>
              <td>{{ t.start_date }}</td>
              <td>{{ t.available_slots }} / {{ t.total_slots }}</td>
              <td>
                <router-link :to="`/treks/${t.id}`" class="btn sm">View &amp; Book</router-link>
              </td>
            </tr>
            <tr v-if="!treks.length">
              <td colspan="6" class="empty">No treks are open for booking right now.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="card flush">
      <div class="card-head">
        <h3>My Upcoming Bookings</h3>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Trek</th>
              <th>Location</th>
              <th>Dates</th>
              <th>Trek Status</th>
              <th>Booking Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="b in dash.upcoming" :key="b.id">
              <td><b>{{ b.trek_name }}</b></td>
              <td>{{ b.location }}</td>
              <td>{{ b.start_date }} to {{ b.end_date }}</td>
              <td><span class="badge" :class="b.trek_status">{{ b.trek_status }}</span></td>
              <td><span class="badge" :class="b.status">{{ b.status }}</span></td>
            </tr>
            <tr v-if="!dash.upcoming.length">
              <td colspan="5" class="empty">You haven't booked any trek yet.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </template>
</template>

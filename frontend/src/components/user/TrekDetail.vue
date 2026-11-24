<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { get, post } from '../../api'
import { toast } from '../../store'

const route = useRoute()
const router = useRouter()
const trek = ref(null)
const mine = ref(null)
const error = ref('')
const confirming = ref(false)
const busy = ref(false)

const canBook = computed(
  () => trek.value && trek.value.status === 'Open' && trek.value.available_slots > 0 && !mine.value
)

const blocker = computed(() => {
  if (!trek.value) return ''
  if (mine.value) return 'You have already booked this trek.'
  if (trek.value.status !== 'Open') return `Booking closed (Status: ${trek.value.status}).`
  if (trek.value.available_slots === 0) return 'Sorry, this trek is full.'
  return ''
})

async function load() {
  try {
    trek.value = await get(`/treks/${route.params.id}`)
    const all = await get('/bookings')
    mine.value = all.find((b) => b.trek_id === trek.value.id && b.status === 'Booked') || null
  } catch (e) {
    error.value = e.message
  }
}

onMounted(load)

async function confirmBooking() {
  busy.value = true
  try {
    await post(`/treks/${trek.value.id}/book`)
    toast('Booking confirmed!', 'success')
    confirming.value = false
    router.push('/bookings')
  } catch (e) {
    toast(e.message, 'error')
    confirming.value = false
    load()
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <router-link to="/browse" class="small">&larr; Back to treks</router-link>

  <div v-if="error" class="error-box mt">{{ error }}</div>
  <p v-else-if="!trek" class="muted mt">Loading trek details...</p>

  <div v-else class="card mt">
    <div class="mb">
      <h1 style="margin-bottom: 0.2rem">{{ trek.name }}</h1>
      <p class="muted" style="margin: 0">Location: {{ trek.location }}</p>
    </div>

    <div class="row mb">
      <span class="badge" :class="trek.difficulty">{{ trek.difficulty }}</span>
      <span class="badge" :class="trek.status">{{ trek.status }}</span>
      <span class="badge" :class="trek.available_slots > 0 ? 'green' : 'red'">
        {{ trek.available_slots }} of {{ trek.total_slots }} slots left
      </span>
    </div>

    <div class="table-wrap mb">
      <table>
        <tbody>
          <tr>
            <th style="width: 180px">Duration</th>
            <td>{{ trek.duration_days }} days</td>
          </tr>
          <tr>
            <th>Dates</th>
            <td>{{ trek.start_date }} to {{ trek.end_date }}</td>
          </tr>
          <tr v-if="trek.altitude_m">
            <th>Max Altitude</th>
            <td>{{ trek.altitude_m }} m</td>
          </tr>
          <tr>
            <th>Trek Leader</th>
            <td>{{ trek.staff_name || 'To be announced' }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <h3>About this trek</h3>
    <p>{{ trek.description || 'Details coming soon.' }}</p>

    <h3>Instructions</h3>
    <p>{{ trek.instructions || 'Carry ID proof, water, and comfortable trekking shoes.' }}</p>

    <div v-if="!confirming" class="row mt">
      <button class="btn" :disabled="!canBook" @click="confirming = true">Book this trek</button>
      <span v-if="blocker" class="muted small">{{ blocker }}</span>
    </div>

    <!-- Simple Inline Booking Confirmation Box -->
    <div v-else class="card mt" style="background: #faf6ec">
      <h3>Confirm Booking</h3>
      <p>
        Do you want to book <b>{{ trek.name }}</b> starting on <b>{{ trek.start_date }}</b>?
      </p>
      <div class="row">
        <button class="btn ghost" :disabled="busy" @click="confirming = false">Cancel</button>
        <button class="btn" :disabled="busy" @click="confirmBooking">
          {{ busy ? 'Booking...' : 'Confirm & Book' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { get, post, put } from '../../api'
import { toast } from '../../store'

const route = useRoute()
const id = route.params.id
const trek = ref(null)
const people = ref([])
const slots = ref(0)
const status = ref('Open')
const error = ref('')

const locked = computed(() => trek.value && ['Ongoing', 'Completed'].includes(trek.value.status))
const active = computed(() => people.value.filter((p) => p.status !== 'Cancelled'))

async function load() {
  try {
    const d = await get(`/staff/treks/${id}`)
    trek.value = d.trek
    people.value = d.participants
    slots.value = d.trek.total_slots
    status.value = ['Open', 'Closed'].includes(d.trek.status) ? d.trek.status : 'Open'
  } catch (e) {
    error.value = e.message
  }
}

onMounted(load)

async function act(fn, okMsg) {
  try {
    await fn()
    toast(okMsg, 'success')
    load()
  } catch (e) {
    toast(e.message, 'error')
  }
}

const update = () =>
  act(() => put(`/staff/treks/${id}`, { total_slots: slots.value, status: status.value }), 'Trek updated')
const start = () =>
  confirm('Mark this trek as started?') && act(() => post(`/staff/treks/${id}/start`), 'Trek marked as started')
const complete = () =>
  confirm('Mark this trek as completed? Booked participants move to their history.') &&
  act(() => post(`/staff/treks/${id}/complete`), 'Trek marked as completed')
const remove = (p) =>
  confirm(`Remove ${p.user_name} from this trek?`) &&
  act(() => post(`/staff/treks/${id}/participants/${p.id}/remove`), 'Participant removed')
</script>

<template>
  <router-link to="/staff" class="small">&larr; Back to My Treks</router-link>

  <div v-if="error" class="error-box mt">{{ error }}</div>
  <p v-else-if="!trek" class="muted mt">Loading trek...</p>

  <template v-else>
    <div class="page-head mt">
      <div>
        <h1>{{ trek.name }}</h1>
        <p>{{ trek.location }} · <span class="badge" :class="trek.status">{{ trek.status }}</span></p>
      </div>
    </div>

    <!-- Simple Trek Details Table -->
    <div class="card flush mb">
      <div class="card-head">
        <h3>Trek Details</h3>
      </div>
      <div class="table-wrap">
        <table>
          <tbody>
            <tr>
              <th style="width: 180px">Difficulty</th>
              <td><span class="badge" :class="trek.difficulty">{{ trek.difficulty }}</span></td>
            </tr>
            <tr>
              <th>Duration</th>
              <td>{{ trek.duration_days }} days</td>
            </tr>
            <tr>
              <th>Dates</th>
              <td>{{ trek.start_date }} to {{ trek.end_date }}</td>
            </tr>
            <tr>
              <th>Slots</th>
              <td>{{ trek.available_slots }} available of {{ trek.total_slots }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Manage Trek Form -->
    <form class="card mb" @submit.prevent="update">
      <h3>Manage Trek</h3>
      <p v-if="locked" class="info-box">
        This trek is {{ trek.status.toLowerCase() }}, so slots and status are locked.
      </p>

      <fieldset :disabled="locked" style="border: 0; padding: 0; margin: 0">
        <div class="field">
          <label for="sl">Total Slots (booked: {{ trek.registered }})</label>
          <input
            id="sl"
            v-model.number="slots"
            class="input"
            type="number"
            :min="Math.max(trek.registered, 1)"
            required
          />
        </div>
        <div class="field">
          <label for="st">Booking Status</label>
          <select id="st" v-model="status" class="input">
            <option>Open</option>
            <option>Closed</option>
          </select>
        </div>
        <button class="btn">Update Trek</button>
      </fieldset>

      <div class="row mt">
        <button
          type="button"
          class="btn ghost"
          :disabled="!['Approved', 'Open', 'Closed'].includes(trek.status)"
          @click="start"
        >
          Mark Started
        </button>
        <button
          type="button"
          class="btn ok ghost"
          :disabled="['Pending', 'Completed'].includes(trek.status)"
          @click="complete"
        >
          Mark Completed
        </button>
      </div>
    </form>

    <!-- Participants Table -->
    <div class="card flush">
      <div class="card-head">
        <h3>Participants ({{ active.length }})</h3>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>#</th>
              <th>Name</th>
              <th>Email</th>
              <th>Contact</th>
              <th>Booked On</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(p, i) in people" :key="p.id">
              <td>{{ i + 1 }}</td>
              <td><b>{{ p.user_name }}</b></td>
              <td>{{ p.user_email }}</td>
              <td>{{ p.user_contact || '—' }}</td>
              <td>{{ p.booking_date }}</td>
              <td><span class="badge" :class="p.status">{{ p.status }}</span></td>
              <td>
                <button
                  v-if="p.status === 'Booked' && !locked"
                  class="btn sm danger ghost"
                  @click="remove(p)"
                >
                  Remove
                </button>
              </td>
            </tr>
            <tr v-if="!people.length">
              <td colspan="7" class="empty">No one has booked yet.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </template>
</template>

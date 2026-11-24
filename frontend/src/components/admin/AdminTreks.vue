<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import { del, get, post, put, qs } from '../../api'
import { toast } from '../../store'

const treks = ref([])
const staff = ref([])
const loading = ref(true)
const q = ref('')
const status = ref('')
const showForm = ref(false)
const editingId = ref(null)
const error = ref('')

const blank = () => ({
  name: '',
  location: '',
  difficulty: 'Moderate',
  duration_days: 5,
  total_slots: 15,
  start_date: '',
  status: 'Approved',
  staff_id: ''
})
const f = reactive(blank())

const STATUSES = ['Pending', 'Approved', 'Open', 'Closed', 'Ongoing', 'Completed']

async function load() {
  loading.value = true
  try {
    const [t, s] = await Promise.all([
      get('/admin/treks' + qs({ q: q.value, status: status.value })),
      get('/admin/staff')
    ])
    treks.value = Array.isArray(t) ? t : []
    staff.value = Array.isArray(s) ? s.filter((x) => x.status === 'active') : []
  } catch (e) {
    toast(e.message, 'error')
  } finally {
    loading.value = false
  }
}

let timer
watch([q, status], () => {
  clearTimeout(timer)
  timer = setTimeout(load, 250)
})

onMounted(load)

function openNew() {
  Object.assign(f, blank())
  editingId.value = null
  error.value = ''
  showForm.value = true
}

function openEdit(t) {
  Object.assign(f, blank(), {
    name: t.name,
    location: t.location,
    difficulty: t.difficulty,
    duration_days: t.duration_days,
    total_slots: t.total_slots,
    start_date: t.start_date,
    status: t.status,
    staff_id: t.staff_id || ''
  })
  editingId.value = t.id
  error.value = ''
  showForm.value = true
}

async function save() {
  error.value = ''
  try {
    const body = { ...f, staff_id: f.staff_id || null }
    if (editingId.value) await put(`/admin/treks/${editingId.value}`, body)
    else await post('/admin/treks', body)
    toast(editingId.value ? 'Trek updated' : 'Trek created', 'success')
    showForm.value = false
    load()
  } catch (e) {
    error.value = e.message
  }
}

async function remove(t) {
  if (!confirm(`Remove "${t.name}"?`)) return
  try {
    await del(`/admin/treks/${t.id}`)
    toast('Trek removed', 'success')
    load()
  } catch (e) {
    toast(e.message, 'error')
  }
}

async function assign(t, staffId) {
  try {
    await put(`/admin/treks/${t.id}/assign`, { staff_id: staffId || null })
    toast('Staff assignment saved', 'success')
    load()
  } catch (e) {
    toast(e.message, 'error')
  }
}

async function setStatus(t, s) {
  try {
    await put(`/admin/treks/${t.id}`, { status: s })
    toast(`${t.name} is now ${s}`, 'success')
    load()
  } catch (e) {
    toast(e.message, 'error')
  }
}
</script>

<template>
  <div class="page-head">
    <div>
      <h1>Treks</h1>
      <p>Create routes, approve them and assign staff.</p>
    </div>
    <button v-if="!showForm" class="btn" @click="openNew">+ Add New Trek</button>
  </div>

  <!-- Minimal Add / Edit Trek Form -->
  <div v-if="showForm" class="card mb">
    <h3>{{ editingId ? 'Edit Trek' : 'Add New Trek' }}</h3>
    <div v-if="error" class="error-box" role="alert">{{ error }}</div>

    <form @submit.prevent="save">
      <div class="field">
        <label for="tn">Trek Name</label>
        <input id="tn" v-model="f.name" class="input" required minlength="3" />
      </div>

      <div class="field">
        <label for="tl">Location</label>
        <input id="tl" v-model="f.location" class="input" required />
      </div>

      <div class="field">
        <label for="td">Difficulty</label>
        <select id="td" v-model="f.difficulty" class="input">
          <option>Easy</option>
          <option>Moderate</option>
          <option>Hard</option>
        </select>
      </div>

      <div class="field">
        <label for="tdu">Duration (days)</label>
        <input id="tdu" v-model.number="f.duration_days" class="input" type="number" min="1" max="60" required />
      </div>

      <div class="field">
        <label for="ts">Start Date</label>
        <input id="ts" v-model="f.start_date" class="input" type="date" required />
      </div>

      <div class="field">
        <label for="tsl">Total Slots</label>
        <input id="tsl" v-model.number="f.total_slots" class="input" type="number" min="1" required />
      </div>

      <div class="field">
        <label for="tst">Status</label>
        <select id="tst" v-model="f.status" class="input">
          <option v-for="s in STATUSES" :key="s">{{ s }}</option>
        </select>
      </div>

      <div class="field">
        <label for="tsf">Assigned Staff</label>
        <select id="tsf" v-model="f.staff_id" class="input">
          <option value="">Unassigned</option>
          <option v-for="s in staff" :key="s.id" :value="s.id">{{ s.name }}</option>
        </select>
      </div>

      <div class="row">
        <button type="button" class="btn ghost" @click="showForm = false">Cancel</button>
        <button class="btn">{{ editingId ? 'Save Changes' : 'Create Trek' }}</button>
      </div>
    </form>
  </div>

  <!-- Treks Table -->
  <div class="card flush">
    <div class="card-head">
      <input
        v-model="q"
        class="input grow"
        style="max-width: 320px"
        type="search"
        placeholder="Search treks by name or location..."
        aria-label="Search treks"
      />
      <select v-model="status" class="input" style="width: auto" aria-label="Filter by status">
        <option value="">All statuses</option>
        <option v-for="s in STATUSES" :key="s">{{ s }}</option>
      </select>
    </div>

    <p v-if="loading" class="empty">Loading treks...</p>

    <div v-else class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Trek</th>
            <th>Location</th>
            <th>Difficulty</th>
            <th>Days</th>
            <th>Slots</th>
            <th>Start</th>
            <th>Staff</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in treks" :key="t.id">
            <td>{{ t.id }}</td>
            <td><b>{{ t.name }}</b></td>
            <td>{{ t.location }}</td>
            <td><span class="badge" :class="t.difficulty">{{ t.difficulty }}</span></td>
            <td>{{ t.duration_days }}</td>
            <td>{{ t.available_slots }}/{{ t.total_slots }}</td>
            <td>{{ t.start_date }}</td>
            <td>
              <select
                class="input"
                style="min-width: 130px; padding: 0.3rem"
                :value="t.staff_id || ''"
                :aria-label="`Assign staff to ${t.name}`"
                @change="assign(t, $event.target.value)"
              >
                <option value="">Unassigned</option>
                <option v-for="s in staff" :key="s.id" :value="s.id">{{ s.name }}</option>
              </select>
            </td>
            <td><span class="badge" :class="t.status">{{ t.status }}</span></td>
            <td>
              <div class="actions">
                <button v-if="t.status === 'Pending'" class="btn sm ok ghost" @click="setStatus(t, 'Approved')">
                  Approve
                </button>
                <button class="btn sm ghost" @click="openEdit(t)">Edit</button>
                <button class="btn sm danger ghost" @click="remove(t)">Delete</button>
              </div>
            </td>
          </tr>
          <tr v-if="!treks.length">
            <td colspan="10" class="empty">No treks found.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

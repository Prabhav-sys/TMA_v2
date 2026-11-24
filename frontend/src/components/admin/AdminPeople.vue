<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { del, get, post, put, qs } from '../../api'
import { toast } from '../../store'

const props = defineProps({ kind: String })
const isStaff = computed(() => props.kind === 'staff')
const rows = ref([])
const loading = ref(true)
const q = ref('')
const showForm = ref(false)
const editingId = ref(null)
const error = ref('')

const blank = () => ({
  name: '',
  email: '',
  password: ''
})
const f = reactive(blank())

async function load() {
  loading.value = true
  try {
    const data = await get(`/admin/${props.kind}` + qs({ q: q.value }))
    rows.value = Array.isArray(data) ? data : []
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

async function setStatus(u, status) {
  const verb = { blacklisted: 'blacklist', inactive: 'deactivate', active: 'reactivate' }[status]
  if (!confirm(`Do you want to ${verb} ${u.name}?`)) return
  try {
    await put(`/admin/users/${u.id}/status`, { status })
    toast(`${u.name} is now ${status}`, 'success')
    load()
  } catch (e) {
    toast(e.message, 'error')
  }
}

function openNew() {
  Object.assign(f, blank())
  editingId.value = null
  error.value = ''
  showForm.value = true
}

function openEdit(u) {
  Object.assign(f, { name: u.name, email: u.email, password: '' })
  editingId.value = u.id
  error.value = ''
  showForm.value = true
}

async function save() {
  error.value = ''
  try {
    if (editingId.value) await put(`/admin/staff/${editingId.value}`, f)
    else await post('/admin/staff', f)
    toast(editingId.value ? 'Staff updated' : 'Staff created', 'success')
    showForm.value = false
    load()
  } catch (e) {
    error.value = e.message
  }
}

async function remove(u) {
  if (!confirm(`Delete ${u.name}? Their treks will become unassigned.`)) return
  try {
    await del(`/admin/staff/${u.id}`)
    toast('Staff removed', 'success')
    load()
  } catch (e) {
    toast(e.message, 'error')
  }
}
</script>

<template>
  <div class="page-head">
    <div>
      <h1>{{ isStaff ? 'Trekking Staff' : 'Users (Trekkers)' }}</h1>
      <p>
        {{
          isStaff
            ? 'Create staff accounts and manage their access.'
            : 'Blacklisted users cannot log in or book treks.'
        }}
      </p>
    </div>
    <button v-if="isStaff && !showForm" type="button" class="btn" @click="openNew">
      + Add Trekking Staff
    </button>
  </div>

  <div v-if="isStaff && showForm" class="card mb">
    <h3>{{ editingId ? 'Edit Trekking Staff' : 'Create New Trekking Staff' }}</h3>
    <div v-if="error" class="error-box" role="alert">{{ error }}</div>

    <form @submit.prevent="save">
      <div class="field">
        <label for="sn">Full Name</label>
        <input id="sn" v-model="f.name" class="input" required minlength="2" />
      </div>

      <div class="field">
        <label for="se">Email Address</label>
        <input id="se" v-model="f.email" class="input" type="email" required :disabled="!!editingId" />
      </div>

      <div class="field">
        <label for="sp">{{ editingId ? 'New Password (optional)' : 'Password' }}</label>
        <input id="sp" v-model="f.password" class="input" type="password" :required="!editingId" />
      </div>

      <p class="muted small">Share the email and password with the staff member so they can log in.</p>

      <div class="row">
        <button type="button" class="btn ghost" @click="showForm = false">Cancel</button>
        <button class="btn">{{ editingId ? 'Save Changes' : 'Create Staff' }}</button>
      </div>
    </form>
  </div>

  <div class="card flush">
    <div class="card-head">
      <input
        v-model="q"
        class="input"
        style="max-width: 320px"
        type="search"
        :placeholder="`Search ${isStaff ? 'staff' : 'users'} by name or email...`"
        aria-label="Search"
      />
    </div>

    <p v-if="loading" class="empty">Loading...</p>

    <div v-else class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Email</th>
            <th v-if="isStaff">Assigned Treks</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in rows" :key="u.id">
            <td>{{ isStaff ? 'T' : 'U' }}{{ String(u.id).padStart(3, '0') }}</td>
            <td><b>{{ u.name }}</b></td>
            <td>{{ u.email }}</td>
            <td v-if="isStaff" class="small">{{ (u.assigned_treks || []).join(', ') || '—' }}</td>
            <td><span class="badge" :class="u.status">{{ u.status }}</span></td>
            <td>
              <div class="actions">
                <button v-if="isStaff" type="button" class="btn sm ghost" @click="openEdit(u)">Edit</button>
                <button v-if="u.status !== 'blacklisted'" type="button" class="btn sm danger ghost" @click="setStatus(u, 'blacklisted')">Blacklist</button>
                <button v-if="u.status === 'active'" type="button" class="btn sm ghost" @click="setStatus(u, 'inactive')">Deactivate</button>
                <button v-if="u.status !== 'active'" type="button" class="btn sm ok ghost" @click="setStatus(u, 'active')">Whitelist</button>
                <button v-if="isStaff" type="button" class="btn sm danger ghost" @click="remove(u)">Delete</button>
              </div>
            </td>
          </tr>
          <tr v-if="!rows.length">
            <td :colspan="isStaff ? 6 : 5" class="empty">Nobody found.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

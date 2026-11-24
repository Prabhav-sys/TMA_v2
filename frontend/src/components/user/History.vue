<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { api, get, post } from '../../api'
import { toast } from '../../store'

const rows = ref([])
const jobs = ref([])
const loading = ref(true)
const starting = ref(false)
let timer = null

async function loadJobs() {
  jobs.value = await get('/exports')
  if (!jobs.value.some((j) => j.status === 'Pending')) {
    clearInterval(timer)
    timer = null
  }
}

async function load() {
  try {
    ;[rows.value] = await Promise.all([get('/history'), loadJobs()])
  } catch (e) {
    toast(e.message, 'error')
  } finally {
    loading.value = false
  }
}

onMounted(load)
onBeforeUnmount(() => clearInterval(timer))

async function startExport() {
  starting.value = true
  try {
    const r = await post('/export')
    toast(r.message, 'info')
    await loadJobs()
    if (!timer) timer = setInterval(loadJobs, 2000)
  } catch (e) {
    toast(e.message, 'error')
  } finally {
    starting.value = false
  }
}

async function download(job) {
  try {
    const res = await api(`/exports/${job.id}/download`, { raw: true })
    const url = URL.createObjectURL(await res.blob())
    const a = Object.assign(document.createElement('a'), {
      href: url,
      download: `trekking_history_${job.id}.csv`
    })
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    toast(e.message, 'error')
  }
}
</script>

<template>
  <div class="page-head">
    <div>
      <h1>Trekking History</h1>
      <p>History shows all your completed and cancelled treks.</p>
    </div>
    <button class="btn" :disabled="starting" @click="startExport">
      {{ starting ? 'Starting...' : 'Export Booking History (CSV)' }}
    </button>
  </div>

  <div v-if="jobs.length" class="card mb">
    <h3>Your Exports</h3>
    <div
      v-for="j in jobs"
      :key="j.id"
      class="row between"
      style="padding: 0.4rem 0; border-bottom: 1px solid #efe9db"
    >
      <span>Export #{{ j.id }} <span class="muted small">· {{ j.created_at }}</span></span>
      <span class="row">
        <span class="badge" :class="j.status">{{ j.status === 'Pending' ? 'Preparing...' : j.status }}</span>
        <button v-if="j.status === 'Done'" class="btn sm" @click="download(j)">Download</button>
      </span>
    </div>
  </div>

  <div class="card flush">
    <p v-if="loading" class="empty">Loading history...</p>
    <div v-else class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Trek</th>
            <th>Location</th>
            <th>Trek Dates</th>
            <th>Completed On</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="b in rows" :key="b.id">
            <td><b>{{ b.trek_name }}</b></td>
            <td>{{ b.location }}</td>
            <td>{{ b.start_date }} to {{ b.end_date }}</td>
            <td>{{ b.completed_on || '—' }}</td>
            <td><span class="badge" :class="b.status">{{ b.status }}</span></td>
          </tr>
          <tr v-if="!rows.length">
            <td colspan="5" class="empty">
              Nothing here yet. Completed and cancelled treks will appear in this list.
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

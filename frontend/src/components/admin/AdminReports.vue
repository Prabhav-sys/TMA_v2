<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { get, post, qs } from '../../api'
import { toast } from '../../store'
import ChartCanvas from '../common/ChartCanvas.vue'

const analytics = ref(null)
const now = new Date()
const month = ref(`${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`)
const report = ref(null)
const sending = ref(false)

const ym = computed(() => month.value.split('-').map(Number))

const reportRows = computed(() => {
  if (!report.value) return []
  return Object.entries(report.value)
    .filter(([, val]) => typeof val === 'number' || typeof val === 'string')
    .filter(([key]) => !['html', 'year', 'month', 'month_name'].includes(key))
    .map(([key, val]) => ({
      label: key.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()),
      value: val
    }))
})

async function loadReport() {
  try {
    report.value = await get('/admin/report/preview' + qs({ year: ym.value, month: ym.value }))
  } catch (e) {
    toast(e.message, 'error')
  }
}

async function sendReport() {
  sending.value = true
  try {
    const res = await post('/admin/report/send', { year: ym.value, month: ym.value })
    toast(res.message, 'success')
  } catch (e) {
    toast(e.message, 'error')
  } finally {
    sending.value = false
  }
}

watch(month, loadReport)

onMounted(async () => {
  try {
    analytics.value = await get('/admin/analytics')
  } catch (e) {
    toast(e.message, 'error')
  }
  loadReport()
})
</script>

<template>
  <div class="page-head">
    <div>
      <h1>Reports &amp; Statistics</h1>
      <p>Overview of trek bookings and monthly activity.</p>
    </div>
  </div>

  <p v-if="!analytics" class="muted">Loading report data...</p>

  <template v-else>
    <!-- Chart 1: Popular Treks -->
    <div class="card mb">
      <h3>Popular Treks</h3>
      <ChartCanvas
        v-if="analytics.popular_treks.length"
        type="bar"
        label="Bookings"
        :labels="analytics.popular_treks.map((x) => x.name)"
        :values="analytics.popular_treks.map((x) => x.bookings)"
      />
      <p v-else class="muted">No bookings yet.</p>
    </div>

    <!-- Chart 2: Treks by Status -->
    <div class="card mb">
      <h3>Treks by Status</h3>
      <ChartCanvas
        v-if="analytics.trek_status.length"
        type="pie"
        :labels="analytics.trek_status.map((x) => x.status)"
        :values="analytics.trek_status.map((x) => x.count)"
      />
      <p v-else class="muted">No treks available.</p>
    </div>

    <!-- Monthly Report Section -->
    <div class="card">
      <div class="row between mb">
        <div>
          <h3>Monthly Activity Report</h3>
          <p class="muted small">Select a month to view or send the report via email.</p>
        </div>
        <div class="row">
          <input v-model="month" type="month" class="input" style="width: auto" />
          <button class="btn" :disabled="sending" @click="sendReport">
            {{ sending ? 'Sending...' : 'Send Report Email' }}
          </button>
        </div>
      </div>

      <div v-if="reportRows.length" class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Metric</th>
              <th>Value</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in reportRows" :key="row.label">
              <td>{{ row.label }}</td>
              <td>{{ row.value }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else-if="report" class="muted">No activity recorded for this month.</p>
    </div>
  </template>
</template>

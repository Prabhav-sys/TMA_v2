<script setup>
import { onMounted, reactive, ref, watch } from 'vue'
import { get, qs } from '../../api'
import { toast } from '../../store'

const treks = ref([])
const loading = ref(true)
const f = reactive({ q: '', difficulty: '' })

async function load() {
  loading.value = true
  try {
    treks.value = await get('/treks' + qs({ q: f.q, difficulty: f.difficulty }))
  } catch (e) {
    toast(e.message, 'error')
  } finally {
    loading.value = false
  }
}

let timer
watch(f, () => {
  clearTimeout(timer)
  timer = setTimeout(load, 250)
})

onMounted(load)
</script>

<template>
  <div class="page-head">
    <div>
      <h1>Browse Treks</h1>
      <p>Search and filter available treks.</p>
    </div>
  </div>

  <div class="card mb">
    <div class="row">
      <div class="grow">
        <label for="fq">Search</label>
        <input id="fq" v-model="f.q" class="input" type="search" placeholder="Search treks..." />
      </div>
      <div>
        <label for="fd">Difficulty</label>
        <select id="fd" v-model="f.difficulty" class="input">
          <option value="">All</option>
          <option>Easy</option>
          <option>Moderate</option>
          <option>Hard</option>
        </select>
      </div>
    </div>
  </div>

  <p v-if="loading" class="muted">Loading treks...</p>

  <div v-else-if="treks.length" class="card flush">
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Trek Name</th>
            <th>Location</th>
            <th>Difficulty</th>
            <th>Duration</th>
            <th>Start Date</th>
            <th>Slots Left</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in treks" :key="t.id">
            <td><b>{{ t.name }}</b></td>
            <td>{{ t.location }}</td>
            <td><span class="badge" :class="t.difficulty">{{ t.difficulty }}</span></td>
            <td>{{ t.duration_days }} days</td>
            <td>{{ t.start_date }}</td>
            <td>{{ t.available_slots }} / {{ t.total_slots }}</td>
            <td>
              <router-link :to="`/treks/${t.id}`" class="btn sm">View &amp; Book</router-link>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <div v-else class="card empty">No treks match your filters.</div>
</template>

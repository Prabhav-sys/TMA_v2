<script setup>
import { reactive, ref } from 'vue'
import { put } from '../api'
import { store, toast, updateUser } from '../store'

const f = reactive({ name: store.user.name, contact: store.user.contact || '' })
const error = ref('')
const busy = ref(false)

async function save() {
  error.value = ''
  busy.value = true
  try {
    const data = await put('/auth/me', { name: f.name, contact: f.contact })
    updateUser(data.user)
    toast('Profile updated', 'success')
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="page-head">
    <div>
      <h1>My Profile</h1>
      <p>Update your details.</p>
    </div>
  </div>
  <form class="card" style="max-width: 640px" @submit.prevent="save">
    <div v-if="error" class="error-box" role="alert">{{ error }}</div>
    <div class="form">
      <div class="field">
        <label for="pn">Full name</label>
        <input id="pn" v-model="f.name" class="input" required minlength="2" />
      </div>
      <div class="field">
        <label for="pe">Email (cannot be changed)</label>
        <input id="pe" :value="store.user.email" class="input" disabled />
      </div>
      <div class="field">
        <label for="pc">Contact number</label>
        <input id="pc" v-model="f.contact" class="input" type="tel" />
      </div>
      <div class="field">
        <label>Role</label>
        <input :value="store.user.role" class="input" disabled style="text-transform: capitalize" />
      </div>
    </div>
    <button class="btn" :disabled="busy">{{ busy ? 'Saving…' : 'Save changes' }}</button>
  </form>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { post } from '../api'
import { toast } from '../store'

const router = useRouter()
const f = reactive({ name: '', email: '', password: '' })
const error = ref('')
const busy = ref(false)

async function submit() {
  error.value = ''
  busy.value = true
  try {
    await post('/auth/register', { name: f.name, email: f.email, password: f.password })
    toast('Account created. Please log in.', 'success')
    router.push('/login')
  } catch (e) {
    error.value = e.message
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="auth">
    <section class="auth-side">
      <form class="auth-card card" @submit.prevent="submit">
        <h2>Create User Account</h2>
        <p class="muted">Register as a Trekker</p>
        <div v-if="error" class="error-box" role="alert">{{ error }}</div>
        <div class="field"><label for="n">Full name</label><input id="n" v-model="f.name" class="input" required /></div>
        <div class="field"><label for="e">Email address</label><input id="e" v-model="f.email" class="input" type="email" required /></div>
        <div class="field"><label for="p">Password</label><input id="p" v-model="f.password" class="input" type="password" required /></div>
        <button class="btn block" :disabled="busy">{{ busy ? 'Creating…' : 'Register' }}</button>
        <p class="center small mt">Already have an account? <router-link to="/login">Login here</router-link></p>
      </form>
    </section>
  </div>
</template>

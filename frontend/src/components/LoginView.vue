<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { post } from '../api'
import { homeFor, setSession, toast } from '../store'

const router = useRouter()
const role = ref('user')
const email = ref('')
const password = ref('')
const error = ref('')
const busy = ref(false)
const roles = [
  ['admin', 'Admin'],
  ['staff', 'Trekking Staff'],
  ['user', 'User (Trekker)']
]

async function submit() {
  error.value = ''
  busy.value = true
  try {
    const data = await post('/auth/login', {
      email: email.value,
      password: password.value,
      role: role.value
    })
    setSession(data.token, data.user)
    toast(`Welcome back, ${data.user.name.split(' ')[0]}!`, 'success')
    router.push(homeFor(data.user.role))
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
        <h2>Login</h2>

        <div class="role-pick" role="radiogroup" aria-label="Login as">
          <button
            v-for="[key, label] in roles"
            :key="key"
            type="button"
            :class="{ on: role === key }"
            @click="role = key"
          >
            {{ label }}
          </button>
        </div>

        <div v-if="error" class="error-box" role="alert">{{ error }}</div>

        <div class="field">
          <label for="email">Email address</label>
          <input id="email" v-model="email" class="input" type="email" required />
        </div>

        <div class="field">
          <label for="pw">Password</label>
          <input id="pw" v-model="password" class="input" type="password" required />
        </div>

        <button class="btn block" :disabled="busy">{{ busy ? 'Signing in…' : 'Login' }}</button>

        <p class="center small mt">
          Don't have an account? <router-link to="/register">Register as User (Trekker)</router-link>
        </p>
      </form>
    </section>
  </div>
</template>

import { reactive } from 'vue'

export const store = reactive({
  user: JSON.parse(localStorage.getItem('user') || 'null'),
  toasts: [],
})

export function setSession(token, user) {
  localStorage.setItem('token', token)
  localStorage.setItem('user', JSON.stringify(user))
  store.user = user
}

export function updateUser(user) {
  localStorage.setItem('user', JSON.stringify(user))
  store.user = user
}

export function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  store.user = null
}

let nextId = 1
export function toast(message, type = 'info') {
  const id = nextId++
  store.toasts.push({ id, message, type })
  setTimeout(() => (store.toasts = store.toasts.filter((t) => t.id !== id)), 4200)
}

export const homeFor = (role) => ({ admin: '/admin', staff: '/staff', user: '/dashboard' })[role] || '/login'

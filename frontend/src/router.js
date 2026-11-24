import { createRouter, createWebHistory } from 'vue-router'
import { homeFor, store } from './store'

const routes = [
  { path: '/', redirect: () => (store.user ? homeFor(store.user.role) : '/login') },
  { path: '/login', component: () => import('./components/LoginView.vue') },
  { path: '/register', component: () => import('./components/RegisterView.vue') },

  { path: '/admin', component: () => import('./components/admin/AdminDashboard.vue'), meta: { role: 'admin' } },
  { path: '/admin/treks', component: () => import('./components/admin/AdminTreks.vue'), meta: { role: 'admin' } },
  { path: '/admin/staff', component: () => import('./components/admin/AdminPeople.vue'), props: { kind: 'staff' }, meta: { role: 'admin' } },
  { path: '/admin/users', component: () => import('./components/admin/AdminPeople.vue'), props: { kind: 'users' }, meta: { role: 'admin' } },
  { path: '/admin/bookings', component: () => import('./components/admin/AdminBookings.vue'), meta: { role: 'admin' } },
  { path: '/admin/reports', component: () => import('./components/admin/AdminReports.vue'), meta: { role: 'admin' } },

  { path: '/staff', component: () => import('./components/staff/StaffDashboard.vue'), meta: { role: 'staff' } },
  { path: '/staff/treks/:id', component: () => import('./components/staff/StaffTrek.vue'), meta: { role: 'staff' } },

  { path: '/dashboard', component: () => import('./components/user/UserDashboard.vue'), meta: { role: 'user' } },
  { path: '/browse', component: () => import('./components/user/BrowseTreks.vue'), meta: { role: 'user' } },
  { path: '/treks/:id', component: () => import('./components/user/TrekDetail.vue'), meta: { role: 'user' } },
  { path: '/bookings', component: () => import('./components/user/MyBookings.vue'), meta: { role: 'user' } },
  { path: '/history', component: () => import('./components/user/History.vue'), meta: { role: 'user' } },
  { path: '/profile', component: () => import('./components/Profile.vue'), meta: { role: 'user' } },

  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  const need = to.meta.role
  if (!need) return store.user && (to.path === '/login' || to.path === '/register') ? homeFor(store.user.role) : true
  if (!store.user) return '/login'
  if (need !== '*' && need !== store.user.role) return homeFor(store.user.role)
  return true
})

export default router

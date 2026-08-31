import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../store/auth'

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', name: 'login', component: () => import('../views/LoginView.vue'), meta: { guestOnly: true } },
  { path: '/register', name: 'register', component: () => import('../views/RegisterView.vue'), meta: { guestOnly: true } },
  { path: '/dashboard', name: 'dashboard', component: () => import('../views/UserDashboard.vue'), meta: { requiresAuth: true } },
  { path: '/admin', name: 'admin', component: () => import('../views/AdminDashboard.vue'), meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/risk-monitor', name: 'risk-monitor', component: () => import('../views/RiskMonitorView.vue'), meta: { requiresAuth: true, requiresAdmin: true, hideNav: true } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return next({ name: 'login' })
  }
  if (to.meta.requiresAdmin && !auth.isAdmin) {
    return next({ name: 'dashboard' })
  }
  if (to.meta.guestOnly && auth.isAuthenticated) {
    return next({ name: auth.isAdmin ? 'admin' : 'dashboard' })
  }
  next()
})

export default router

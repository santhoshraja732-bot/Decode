<template>
  <nav class="navbar">
    <div class="navbar-inner">
      <div class="nav-side"></div>
      <div class="brand">
        <img src="/logo-v2.png" alt="DecodersPay" class="logo-mark" /> DecodersPay
      </div>
      <div class="links nav-side" v-if="auth.isAuthenticated">
        <router-link v-if="!auth.isAdmin" to="/dashboard">Dashboard</router-link>
        <router-link v-if="auth.isAdmin" to="/admin">Admin Console</router-link>
        <div class="user-chip">
          <span class="avatar">{{ initials }}</span>
          <span class="user-meta">
            <span class="user-name">{{ auth.user?.username }}</span>
            <span class="user-role">{{ auth.user?.role }}</span>
          </span>
        </div>
        <button class="btn-secondary btn-sm" @click="logout">Logout</button>
      </div>
      <div class="nav-side" v-else></div>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'

const auth = useAuthStore()
const router = useRouter()

const initials = computed(() => (auth.user?.username || '?').slice(0, 2).toUpperCase())

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.navbar {
  position: sticky;
  top: 0;
  z-index: 40;
  border-bottom: 1px solid var(--glass-border);
  background: rgba(10, 13, 16, 0.5);
  backdrop-filter: blur(22px) saturate(160%);
  -webkit-backdrop-filter: blur(22px) saturate(160%);
}
.navbar-inner {
  max-width: 1180px;
  margin: 0 auto;
  padding: 14px 24px;
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 16px;
}
.nav-side { display: flex; align-items: center; }
.nav-side.links { justify-content: flex-end; }
.brand {
  font-weight: 800;
  font-size: 17px;
  letter-spacing: -0.01em;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  white-space: nowrap;
}
.logo-mark {
  width: 30px;
  height: 30px;
  object-fit: contain;
  flex-shrink: 0;
}
.links {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
}
.links a {
  color: var(--text-dim);
  text-decoration: none;
  padding: 8px 12px;
  border-radius: 7px;
  font-weight: 600;
  transition: color 0.15s ease, background 0.15s ease;
}
.links a:hover { color: var(--text); background: var(--bg-panel); }
.links a.router-link-active {
  color: var(--accent);
  background: var(--accent-soft);
}
.user-chip {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 4px 10px 4px 4px;
  margin: 0 4px 0 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid var(--glass-border);
}
.avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: var(--bg-inset);
  border: 1px solid var(--border-soft);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 10.5px;
  font-weight: 700;
  color: var(--accent);
  flex-shrink: 0;
}
.user-meta {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}
.user-name { font-size: 12.5px; font-weight: 600; color: var(--text); }
.user-role { font-size: 10.5px; color: var(--text-faint); text-transform: capitalize; }

@media (max-width: 720px) {
  .user-meta { display: none; }
  .links { gap: 2px; }
}
</style>

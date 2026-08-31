<template>
  <div class="auth-wrap">
    <div class="auth-shell">
      <div class="auth-side">
        <img src="/logo-v2.png" alt="DecodersPay" class="logo-mark-lg" />
        <h1>DecodersPay</h1>
        <p class="muted">Secure Digital Transaction &amp; Fraud Prevention Platform</p>
        <ul class="auth-features">
          <li><span class="feat-dot"></span> Real-time rule-based risk scoring</li>
          <li><span class="feat-dot"></span> OTP-verified transfers</li>
          <li><span class="feat-dot"></span> Live admin risk monitor</li>
        </ul>
      </div>

      <div class="card auth-card">
        <div class="brand-lg mobile-only"><img src="/logo-v2.png" alt="DecodersPay" class="logo-mark-sm" /> DecodersPay</div>
        <h2 class="auth-title">Welcome back</h2>
        <p class="muted auth-sub">Sign in to your simulated account</p>

        <label>Username</label>
        <input v-model="username" @keyup.enter="submit" placeholder="e.g. admin" autofocus />

        <label>Password</label>
        <input v-model="password" type="password" @keyup.enter="submit" placeholder="••••••••" />

        <div v-if="error" class="error-box">{{ error }}</div>

        <button class="btn-primary mt-24" style="width:100%" :disabled="loading" @click="submit">
          {{ loading ? 'Signing in...' : 'Sign In' }}
        </button>

        <p class="muted mt-16" style="font-size:13px">
          No account? <router-link to="/register">Register here</router-link>
        </p>
        <div class="demo-hint">
          Demo admin: <span class="mono">admin / Admin@123</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../store/auth'

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

const auth = useAuthStore()
const router = useRouter()

async function submit() {
  error.value = ''
  loading.value = true
  try {
    const user = await auth.login(username.value, password.value)
    router.push(user.role === 'admin' ? '/admin' : '/dashboard')
  } catch (e) {
    error.value = e.response?.data?.detail || 'Login failed.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-wrap {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background:
    radial-gradient(900px 500px at 10% 0%, rgba(53, 224, 122, 0.08), transparent 60%),
    radial-gradient(700px 500px at 100% 100%, rgba(76, 195, 240, 0.06), transparent 55%),
    var(--bg);
}
.auth-shell {
  display: flex;
  align-items: center;
  gap: 56px;
  max-width: 880px;
  width: 100%;
}
.auth-side { flex: 1; padding-right: 8px; display: flex; flex-direction: column; align-items: center; text-align: center; }
.logo-mark-lg {
  width: 88px;
  height: 88px;
  object-fit: contain;
  filter: drop-shadow(0 8px 20px rgba(53, 224, 122, 0.35));
  margin-bottom: 18px;
}
.auth-side h1 { font-size: 30px; margin: 0 0 8px; letter-spacing: -0.02em; }
.auth-side p.muted { font-size: 14px; max-width: 320px; }
.auth-features {
  list-style: none;
  padding: 0;
  margin: 28px 0 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  font-size: 13.5px;
  color: var(--text-dim);
}
.auth-features li { display: flex; align-items: center; gap: 10px; }
.feat-dot {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--accent); flex-shrink: 0;
  box-shadow: 0 0 0 3px var(--accent-soft);
}

.auth-card { width: 100%; max-width: 380px; flex-shrink: 0; }
.auth-title { font-size: 20px; margin: 4px 0 2px; }
.auth-sub { font-size: 13px; margin-top: 0; }
.mobile-only { display: none; }
.brand-lg { font-size: 18px; font-weight: 700; display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 18px; }
.logo-mark-sm {
  width: 26px; height: 26px;
  object-fit: contain;
}
.demo-hint {
  margin-top: 14px;
  font-size: 11.5px;
  color: var(--text-faint);
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid var(--glass-border);
  border-radius: 7px;
  padding: 8px 10px;
}

@media (max-width: 760px) {
  .auth-side { display: none; }
  .mobile-only { display: flex; }
  .auth-shell { justify-content: center; }
}
</style>

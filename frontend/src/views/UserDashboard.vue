<template>
  <div class="page">
    <div class="grid grid-3">
      <div class="card stat-card hoverable">
        <div class="stat-label">Simulated Balance</div>
        <div class="stat-value">₹{{ auth.user?.balance?.toFixed(2) }}</div>
      </div>
      <div class="card stat-card hoverable">
        <div class="stat-label">Your Account Number</div>
        <div class="stat-value mono" style="font-size:18px">{{ auth.user?.account_number }}</div>
      </div>
      <div class="card stat-card hoverable">
        <div class="stat-label">Account Status</div>
        <div class="stat-value" :style="{color: auth.user?.is_blocked ? 'var(--danger)' : 'var(--accent)'}">
          {{ auth.user?.is_blocked ? 'Blocked' : 'Active' }}
        </div>
      </div>
    </div>

    <div class="card mt-24">
      <h3 style="margin-top:0">New Simulated Transaction</h3>
      <div class="grid grid-2">
        <div>
          <label>Receiver Account</label>
          <input
            v-model="form.receiver_account"
            list="account-directory"
            placeholder="Type an account number, or pick a suggestion"
            @change="onReceiverSelect"
          />
          <datalist id="account-directory">
            <option v-for="d in directory" :key="d.account_number" :value="d.account_number">
              {{ d.username }}
            </option>
          </datalist>
        </div>
        <div>
          <label>Receiver Name</label>
          <input v-model="form.receiver_name" placeholder="e.g. Jane Doe" />
        </div>
        <div>
          <label>Amount (INR)</label>
          <input v-model.number="form.amount" type="number" min="1" placeholder="0.00" />
        </div>
        <div>
          <label>Simulated Device ID</label>
          <input v-model="form.device_id" placeholder="e.g. laptop-chrome-01" />
        </div>
      </div>
      <div v-if="createError" class="error-box">{{ createError }}</div>
      <div v-if="lastResult" class="success-box">
        Transaction {{ lastResult.id.slice(0,8) }}… finished with status
        <strong>{{ lastResult.status.replace('_',' ') }}</strong> (risk score {{ lastResult.risk_score }}).
        <div v-if="lastResult.flag_reasons">{{ lastResult.flag_reasons }}</div>
      </div>

      <button class="btn-primary mt-16" :disabled="submitting || !canSubmit" @click="startTransaction">
        {{ submitting ? 'Processing...' : 'Send & Verify with OTP' }}
      </button>
    </div>

    <RulesPanel />

    <div class="card mt-24">
      <div class="flex-between">
        <h3 style="margin:0">Your Transaction History</h3>
        <button class="btn-secondary btn-sm" @click="loadTransactions">Refresh</button>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Date</th><th>Receiver</th><th>Amount</th><th>Status</th><th>Risk</th><th>Reasons</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in transactions" :key="t.id">
              <td>{{ formatDateTime(t.created_at) }}</td>
              <td>{{ t.receiver_name || t.receiver_account }}</td>
              <td>₹{{ t.amount.toFixed(2) }}</td>
              <td><StatusBadge :status="t.status" /></td>
              <td>{{ t.risk_score }}</td>
              <td class="muted wrap" style="max-width:260px">{{ t.flag_reasons }}</td>
            </tr>
            <tr v-if="!transactions.length">
              <td colspan="6" class="muted">No transactions yet.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <OtpModal
      v-if="pendingTxn"
      :transaction-id="pendingTxn.transaction_id"
      :amount="`₹${form.amount}`"
      :receiver="form.receiver_name || form.receiver_account"
      :initial-debug-otp="pendingTxn.debug_otp"
      :expires-in-seconds="pendingTxn.expires_in_seconds"
      @close="pendingTxn = null"
      @verified="onVerified"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../api/axios'
import { useAuthStore } from '../store/auth'
import StatusBadge from '../components/StatusBadge.vue'
import OtpModal from '../components/OtpModal.vue'
import RulesPanel from '../components/RulesPanel.vue'
import { formatDateTime } from '../utils/datetime'

const auth = useAuthStore()

const form = ref({ receiver_account: '', receiver_name: '', amount: null, device_id: 'web-browser-01' })
const submitting = ref(false)
const createError = ref('')
const pendingTxn = ref(null)
const lastResult = ref(null)
const transactions = ref([])
const directory = ref([])

const canSubmit = computed(() => form.value.receiver_account && form.value.amount > 0)

async function loadDirectory() {
  const { data } = await api.get('/users/directory')
  directory.value = data
}

function onReceiverSelect() {
  const match = directory.value.find((d) => d.account_number === form.value.receiver_account)
  if (match && !form.value.receiver_name) {
    form.value.receiver_name = match.username
  }
}

async function startTransaction() {
  createError.value = ''
  lastResult.value = null
  submitting.value = true
  try {
    const { data } = await api.post('/transactions/', form.value)
    pendingTxn.value = data
  } catch (e) {
    createError.value = e.response?.data?.detail || 'Could not start transaction.'
  } finally {
    submitting.value = false
  }
}

async function onVerified(txn) {
  pendingTxn.value = null
  lastResult.value = txn
  form.value = { receiver_account: '', receiver_name: '', amount: null, device_id: form.value.device_id }
  await auth.refreshMe()
  await loadTransactions()
}

async function loadTransactions() {
  const { data } = await api.get('/transactions/')
  transactions.value = data
}

onMounted(() => {
  loadTransactions()
  loadDirectory()
  auth.refreshMe()
})
</script>

<template>
  <div class="card">
    <div class="flex-between">
      <h3 style="margin:0">Transaction Monitoring</h3>
      <div style="display:flex; gap:8px; align-items:center">
        <select v-model="statusFilter" @change="load">
          <option value="">All statuses</option>
          <option v-for="s in statuses" :key="s" :value="s">{{ s.replace('_',' ') }}</option>
        </select>
        <button class="btn-secondary btn-sm" @click="load">Refresh</button>
      </div>
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Date</th><th>Sender</th><th>Receiver</th><th>Amount</th><th>Status</th><th>Risk</th><th>Reasons</th><th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in transactions" :key="t.id">
            <td>{{ formatDateTime(t.created_at) }}</td>
            <td class="mono" style="font-size:12px">{{ t.sender_id.slice(0,8) }}…</td>
            <td>{{ t.receiver_name || t.receiver_account }}</td>
            <td>₹{{ t.amount.toFixed(2) }}</td>
            <td><StatusBadge :status="t.status" /></td>
            <td>{{ t.risk_score }}</td>
            <td class="muted wrap" style="max-width:220px; font-size:12px">{{ t.flag_reasons }}</td>
            <td>
              <div v-if="['flagged','held','blocked'].includes(t.status)" style="display:flex; gap:6px">
                <button class="btn-primary btn-sm" @click="decide(t, 'approve')">Approve</button>
                <button class="btn-danger btn-sm" @click="decide(t, 'reject')">Reject</button>
              </div>
            </td>
          </tr>
          <tr v-if="!transactions.length"><td colspan="8" class="muted">No transactions found.</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api/axios'
import StatusBadge from '../StatusBadge.vue'
import { formatDateTime } from '../../utils/datetime'

const transactions = ref([])
const statusFilter = ref('')
const statuses = ['pending_otp', 'processing', 'completed', 'flagged', 'held', 'blocked', 'rejected', 'failed']

async function load() {
  const params = statusFilter.value ? { status: statusFilter.value } : {}
  const { data } = await api.get('/admin/transactions', { params })
  transactions.value = data
}

async function decide(t, decision) {
  await api.post(`/admin/transactions/${t.id}/decision`, { decision })
  await load()
}

onMounted(load)
defineExpose({ load })
</script>

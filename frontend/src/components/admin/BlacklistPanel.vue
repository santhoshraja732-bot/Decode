<template>
  <div class="card">
    <div class="flex-between">
      <h3 style="margin:0">Blacklisted Receiver Accounts</h3>
      <button class="btn-secondary btn-sm" @click="load">Refresh</button>
    </div>

    <div class="grid grid-3 mt-16">
      <input v-model="newAccount" placeholder="Account number to blacklist" />
      <input v-model="newReason" placeholder="Reason (optional)" />
      <button class="btn-primary" @click="add">Add to Blacklist</button>
    </div>

    <div v-if="error" class="error-box">{{ error }}</div>

    <div class="table-wrap">
      <table>
        <thead><tr><th>Account #</th><th>Reason</th><th>Added</th><th>Action</th></tr></thead>
        <tbody>
          <tr v-for="b in entries" :key="b.id">
            <td class="mono">{{ b.account_number }}</td>
            <td>{{ b.reason }}</td>
            <td>{{ formatDateTime(b.created_at) }}</td>
            <td><button class="btn-danger btn-sm" @click="remove(b)">Remove</button></td>
          </tr>
          <tr v-if="!entries.length"><td colspan="4" class="muted">No blacklisted accounts.</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api/axios'
import { formatDateTime } from '../../utils/datetime'

const entries = ref([])
const newAccount = ref('')
const newReason = ref('')
const error = ref('')

async function load() {
  const { data } = await api.get('/admin/blacklist')
  entries.value = data
}

async function add() {
  error.value = ''
  if (!newAccount.value) return
  try {
    await api.post('/admin/blacklist', null, { params: { account_number: newAccount.value, reason: newReason.value } })
    newAccount.value = ''
    newReason.value = ''
    await load()
  } catch (e) {
    error.value = e.response?.data?.detail || 'Could not add entry.'
  }
}

async function remove(b) {
  await api.delete(`/admin/blacklist/${b.id}`)
  await load()
}

onMounted(load)
defineExpose({ load })
</script>

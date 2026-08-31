<template>
  <div class="card">
    <div class="flex-between">
      <h3 style="margin:0">Audit Log</h3>
      <button class="btn-secondary btn-sm" @click="load">Refresh</button>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr><th>Time</th><th>Actor</th><th>Action</th><th>Target</th><th>Details</th></tr>
        </thead>
        <tbody>
          <tr v-for="l in logs" :key="l.id">
            <td>{{ formatDateTime(l.timestamp) }}</td>
            <td>{{ l.actor_username || 'system' }}</td>
            <td class="mono" style="font-size:12px">{{ l.action }}</td>
            <td class="muted" style="font-size:12px">{{ l.target_type }}{{ l.target_id ? ' · ' + l.target_id.slice(0,8) + '…' : '' }}</td>
            <td class="wrap" style="max-width:320px; font-size:12px">{{ l.details }}</td>
          </tr>
          <tr v-if="!logs.length"><td colspan="5" class="muted">No audit entries yet.</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api/axios'
import { formatDateTime } from '../../utils/datetime'

const logs = ref([])

async function load() {
  const { data } = await api.get('/admin/audit-logs')
  logs.value = data
}

onMounted(load)
defineExpose({ load })
</script>

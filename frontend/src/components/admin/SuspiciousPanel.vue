<template>
  <div class="card">
    <div class="flex-between">
      <h3 style="margin:0">Suspicious Activity</h3>
      <div style="display:flex; gap:8px; align-items:center">
        <select v-model="resolvedFilter" @change="load">
          <option value="">All</option>
          <option value="false">Unresolved</option>
          <option value="true">Resolved</option>
        </select>
        <button class="btn-secondary btn-sm" @click="load">Refresh</button>
      </div>
    </div>

    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Date</th><th>Rule</th><th>Description</th><th>Severity</th><th>Resolved</th><th>Action</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in activities" :key="a.id">
            <td>{{ formatDateTime(a.created_at) }}</td>
            <td class="mono" style="font-size:12px">{{ a.rule_triggered }}</td>
            <td class="wrap" style="max-width:320px">{{ a.description }}</td>
            <td><span class="badge" :class="`badge-${a.severity}`">{{ a.severity }}</span></td>
            <td>{{ a.resolved ? 'Yes' : 'No' }}</td>
            <td>
              <button v-if="!a.resolved" class="btn-secondary btn-sm" @click="resolve(a)">Mark Resolved</button>
            </td>
          </tr>
          <tr v-if="!activities.length"><td colspan="6" class="muted">No suspicious activity recorded.</td></tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api/axios'
import { formatDateTime } from '../../utils/datetime'

const activities = ref([])
const resolvedFilter = ref('')

async function load() {
  const params = {}
  if (resolvedFilter.value !== '') params.resolved = resolvedFilter.value
  const { data } = await api.get('/admin/suspicious-activities', { params })
  activities.value = data
}

async function resolve(a) {
  const note = window.prompt('Resolution note (optional):', '') || ''
  await api.post(`/admin/suspicious-activities/${a.id}/resolve`, { resolution_note: note })
  await load()
}

onMounted(load)
defineExpose({ load })
</script>

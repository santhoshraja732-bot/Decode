<template>
  <div class="card">
    <div class="flex-between">
      <h3 style="margin:0">User Management</h3>
      <button class="btn-secondary btn-sm" @click="load">Refresh</button>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr><th>Username</th><th>Email</th><th>Role</th><th>Balance</th><th>Account #</th><th>Status</th><th>Action</th></tr>
        </thead>
        <tbody>
          <tr v-for="u in users" :key="u.id">
            <td>{{ u.username }}</td>
            <td>{{ u.email }}</td>
            <td>{{ u.role }}</td>
            <td>₹{{ u.balance.toFixed(2) }}</td>
            <td class="mono" style="font-size:12px">{{ u.account_number }}</td>
            <td>
              <span class="badge" :class="u.is_blocked ? 'badge-blocked' : 'badge-completed'">
                {{ u.is_blocked ? 'Blocked' : 'Active' }}
              </span>
            </td>
            <td>
              <button v-if="u.role !== 'admin'" class="btn-sm" :class="u.is_blocked ? 'btn-primary' : 'btn-danger'" @click="toggle(u)">
                {{ u.is_blocked ? 'Unblock' : 'Block' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../../api/axios'

const users = ref([])

async function load() {
  const { data } = await api.get('/admin/users')
  users.value = data
}

async function toggle(u) {
  await api.post(`/admin/users/${u.id}/status`, { is_blocked: !u.is_blocked })
  await load()
}

onMounted(load)
defineExpose({ load })
</script>

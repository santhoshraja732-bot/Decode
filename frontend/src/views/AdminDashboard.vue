<template>
  <div class="page">
    <div class="flex-between">
      <h2 style="margin-top:0">Admin Console</h2>
      <button class="btn-primary" @click="openRiskMonitor">Open Risk Level Monitor ↗</button>
    </div>
    <StatsOverview v-if="stats" :stats="stats" />

    <div class="tabs mt-24">
      <button class="tab-btn" :class="{active: tab==='transactions'}" @click="tab='transactions'">Transactions</button>
      <button class="tab-btn" :class="{active: tab==='suspicious'}" @click="tab='suspicious'">Suspicious Activity</button>
      <button class="tab-btn" :class="{active: tab==='audit'}" @click="tab='audit'">Audit Log</button>
      <button class="tab-btn" :class="{active: tab==='users'}" @click="tab='users'">Users</button>
      <button class="tab-btn" :class="{active: tab==='blacklist'}" @click="tab='blacklist'">Blacklist</button>
    </div>

    <TransactionsPanel v-show="tab==='transactions'" />
    <SuspiciousPanel v-show="tab==='suspicious'" />
    <AuditLogPanel v-show="tab==='audit'" />
    <UsersPanel v-show="tab==='users'" />
    <BlacklistPanel v-show="tab==='blacklist'" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api/axios'
import StatsOverview from '../components/admin/StatsOverview.vue'
import TransactionsPanel from '../components/admin/TransactionsPanel.vue'
import SuspiciousPanel from '../components/admin/SuspiciousPanel.vue'
import AuditLogPanel from '../components/admin/AuditLogPanel.vue'
import UsersPanel from '../components/admin/UsersPanel.vue'
import BlacklistPanel from '../components/admin/BlacklistPanel.vue'

const tab = ref('transactions')
const stats = ref(null)

async function loadStats() {
  const { data } = await api.get('/admin/stats')
  stats.value = data
}

onMounted(loadStats)

function openRiskMonitor() {
  window.open(
    '/risk-monitor',
    'DecodersPay Risk Monitor',
    'width=980,height=760,menubar=no,toolbar=no,location=no,status=no'
  )
}
</script>

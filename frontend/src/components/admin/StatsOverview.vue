<template>
  <div class="grid grid-4">
    <div class="card stat-card hoverable">
      <div class="stat-label">Total Users</div>
      <div class="stat-value">{{ stats.total_users }}</div>
    </div>
    <div class="card stat-card hoverable">
      <div class="stat-label">Total Transactions</div>
      <div class="stat-value">{{ stats.total_transactions }}</div>
    </div>
    <div class="card stat-card hoverable">
      <div class="stat-label">Flagged / Held</div>
      <div class="stat-value" style="color:var(--warning)">{{ stats.flagged_transactions + stats.held_transactions }}</div>
    </div>
    <div class="card stat-card hoverable">
      <div class="stat-label">Blocked</div>
      <div class="stat-value" style="color:var(--danger)">{{ stats.blocked_transactions }}</div>
    </div>
    <div class="card stat-card hoverable">
      <div class="stat-label">Completed</div>
      <div class="stat-value" style="color:var(--accent)">{{ stats.completed_transactions }}</div>
    </div>
    <div class="card stat-card hoverable">
      <div class="stat-label">Suspicious Activity Logs</div>
      <div class="stat-value">{{ stats.total_suspicious_activities }}</div>
    </div>
    <div class="card stat-card hoverable">
      <div class="stat-label">Unresolved Alerts</div>
      <div class="stat-value" style="color:var(--warning)">{{ stats.unresolved_suspicious_activities }}</div>
    </div>
  </div>
</template>

<script setup>
defineProps({ stats: { type: Object, required: true } })
</script>

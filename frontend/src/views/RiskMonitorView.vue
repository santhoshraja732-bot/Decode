<template>
  <div class="risk-page">
    <div class="risk-header">
      <div class="flex-between">
        <div>
          <div class="brand-sm"><img src="/logo-v2.png" alt="DecodersPay" class="dot" /> DecodersPay</div>
          <h2 style="margin:4px 0 0">Risk Level Monitor</h2>
        </div>
        <div class="live-indicator">
          <span class="pulse" :class="{ off: !autoRefresh }"></span>
          {{ autoRefresh ? 'Live' : 'Paused' }}
          <button class="btn-secondary btn-sm" style="margin-left:12px" @click="autoRefresh = !autoRefresh">
            {{ autoRefresh ? 'Pause' : 'Resume' }}
          </button>
          <button class="btn-secondary btn-sm" style="margin-left:8px" @click="loadAll">Refresh now</button>
        </div>
      </div>
      <p class="muted" style="font-size:12px;margin:6px 0 0">
        Last updated: {{ lastUpdated ? lastUpdated.toLocaleTimeString() : '—' }}
      </p>
    </div>

    <div class="grid grid-4 mt-16">
      <div class="card risk-card risk-low">
        <div class="stat-label">Low Risk Alerts</div>
        <div class="stat-value">{{ severityCounts.low }}</div>
      </div>
      <div class="card risk-card risk-medium">
        <div class="stat-label">Medium Risk Alerts</div>
        <div class="stat-value">{{ severityCounts.medium }}</div>
      </div>
      <div class="card risk-card risk-high">
        <div class="stat-label">High Risk Alerts</div>
        <div class="stat-value">{{ severityCounts.high }}</div>
      </div>
      <div class="card risk-card risk-critical">
        <div class="stat-label">Critical Risk Alerts</div>
        <div class="stat-value">{{ severityCounts.critical }}</div>
      </div>
    </div>

    <div class="grid grid-3 mt-24">
      <div class="card">
        <div class="flex-between">
          <h3 style="margin:0">🚩 Flagged</h3>
          <span class="badge badge-flagged">{{ flagged.length }}</span>
        </div>
        <p class="muted" style="font-size:12px">Allowed through, but watched.</p>
        <div v-for="t in flagged" :key="t.id" class="risk-row">
          <div class="flex-between">
            <span class="mono" style="font-size:12px">₹{{ t.amount.toFixed(2) }}</span>
            <span class="mono" style="font-size:11px;color:var(--text-dim)">score {{ t.risk_score }}</span>
          </div>
          <div class="muted" style="font-size:11px;margin-top:4px">{{ t.flag_reasons || 'No reasons logged' }}</div>
        </div>
        <div v-if="!flagged.length" class="muted" style="font-size:12px">Nothing flagged right now.</div>
      </div>

      <div class="card">
        <div class="flex-between">
          <h3 style="margin:0">⏸ Held</h3>
          <span class="badge badge-held">{{ held.length }}</span>
        </div>
        <p class="muted" style="font-size:12px">Waiting on admin review.</p>
        <div v-for="t in held" :key="t.id" class="risk-row">
          <div class="flex-between">
            <span class="mono" style="font-size:12px">₹{{ t.amount.toFixed(2) }}</span>
            <span class="mono" style="font-size:11px;color:var(--text-dim)">score {{ t.risk_score }}</span>
          </div>
          <div class="muted" style="font-size:11px;margin-top:4px">{{ t.flag_reasons || 'No reasons logged' }}</div>
        </div>
        <div v-if="!held.length" class="muted" style="font-size:12px">Nothing held right now.</div>
      </div>

      <div class="card">
        <div class="flex-between">
          <h3 style="margin:0">⛔ Blocked</h3>
          <span class="badge badge-blocked">{{ blocked.length }}</span>
        </div>
        <p class="muted" style="font-size:12px">Auto-blocked by a rule.</p>
        <div v-for="t in blocked" :key="t.id" class="risk-row">
          <div class="flex-between">
            <span class="mono" style="font-size:12px">₹{{ t.amount.toFixed(2) }}</span>
            <span class="mono" style="font-size:11px;color:var(--text-dim)">score {{ t.risk_score }}</span>
          </div>
          <div class="muted" style="font-size:11px;margin-top:4px">{{ t.flag_reasons || 'No reasons logged' }}</div>
        </div>
        <div v-if="!blocked.length" class="muted" style="font-size:12px">Nothing blocked right now.</div>
      </div>
    </div>

    <div class="card mt-24">
      <h3 style="margin-top:0">Predefined Rules Active</h3>
      <p class="muted" style="font-size:12px">
        Every transaction is scored automatically. Score ≥ 80 → <strong style="color:var(--danger)">Blocked</strong>,
        score ≥ 50 → <strong style="color:var(--warning)">Held</strong> for review,
        score ≥ 25 → <strong style="color:var(--info)">Flagged</strong> and watched,
        otherwise completed. Rules include: critical/high transaction amount, blacklisted receiver,
        transaction velocity, fan-out to many receivers, spending spikes vs. average, new/unknown device,
        and self-transfers.
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import api from '../api/axios'

const flagged = ref([])
const held = ref([])
const blocked = ref([])
const severityCounts = ref({ low: 0, medium: 0, high: 0, critical: 0 })
const lastUpdated = ref(null)
const autoRefresh = ref(true)
let timer = null

async function loadAll() {
  try {
    const [f, h, b, sa] = await Promise.all([
      api.get('/admin/transactions', { params: { status: 'flagged' } }),
      api.get('/admin/transactions', { params: { status: 'held' } }),
      api.get('/admin/transactions', { params: { status: 'blocked' } }),
      api.get('/admin/suspicious-activities', { params: { resolved: false } }),
    ])
    flagged.value = f.data
    held.value = h.data
    blocked.value = b.data

    const counts = { low: 0, medium: 0, high: 0, critical: 0 }
    for (const a of sa.data) {
      if (counts[a.severity] !== undefined) counts[a.severity]++
    }
    severityCounts.value = counts
    lastUpdated.value = new Date()
  } catch (e) {
    // silently retry on next tick; this is a monitoring view
  }
}

onMounted(() => {
  loadAll()
  timer = setInterval(() => {
    if (autoRefresh.value) loadAll()
  }, 5000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.risk-page {
  max-width: 1180px;
  margin: 0 auto;
  padding: 24px 20px 60px;
}
.risk-header {
  padding-bottom: 8px;
  border-bottom: 1px solid var(--border);
}
.brand-sm {
  font-weight: 700;
  font-size: 14px;
  color: var(--text-dim);
  display: flex;
  align-items: center;
  gap: 6px;
}
.dot {
  width: 18px;
  height: 18px;
  object-fit: contain;
  display: inline-block;
}
.live-indicator {
  display: flex;
  align-items: center;
  font-size: 13px;
  color: var(--text-dim);
}
.pulse {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--accent);
  margin-right: 6px;
  animation: pulse 1.4s infinite;
}
.pulse.off {
  background: var(--text-dim);
  animation: none;
}
@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(53,224,122,0.6); }
  70% { box-shadow: 0 0 0 8px rgba(53,224,122,0); }
  100% { box-shadow: 0 0 0 0 rgba(53,224,122,0); }
}
.risk-card { border-left: 3px solid transparent; transition: transform 0.18s ease, border-color 0.18s ease; }
.risk-card:hover { transform: translateY(-1px); }
.risk-low { border-left-color: var(--info); }
.risk-medium { border-left-color: var(--warning); }
.risk-high { border-left-color: #f97316; }
.risk-critical { border-left-color: var(--danger); }
.risk-row {
  padding: 10px 0;
  border-bottom: 1px solid var(--border-soft);
  transition: background 0.12s ease;
}
.risk-row:last-child { border-bottom: none; }
</style>

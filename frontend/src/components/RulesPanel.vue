<template>
  <div class="card mt-24">
    <button class="rules-toggle" @click="open = !open">
      <span class="flex-between" style="width:100%">
        <span class="rules-title">📋 Rules we monitor</span>
        <span class="chevron" :class="{ up: open }">⌄</span>
      </span>
    </button>

    <div v-show="open" class="mt-16">
      <div v-for="r in rules" :key="r.code" class="rule-row">
        <span class="badge" :class="`badge-${r.severity}`">{{ severityLabel(r.severity) }}</span>
        <div class="rule-text">
          <strong>{{ r.name }}.</strong> {{ r.description }}
        </div>
      </div>

      <p class="muted rule-footer">
        Decision logic: any critical flag, or 2+ high flags → auto-blocked. 1 high flag → OTP, then
        held for admin review. All other transactions → OTP, then completed. Every transfer requires
        a one-time verification code.
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const open = ref(true)

// Mirrors backend/app/fraud_rules.py — kept here as a readable reference
// for admins and users; the backend is the actual source of truth.
const rules = [
  {
    code: 'BLACKLISTED_RECEIVER',
    name: 'Blocked account',
    severity: 'critical',
    description: 'Sender or recipient account is currently blocked.',
  },
  {
    code: 'CRITICAL_AMOUNT',
    name: 'High-value transfer',
    severity: 'high',
    description: 'Amount exceeds the high-value threshold of ₹20,000.',
  },
  {
    code: 'FAN_OUT',
    name: 'Possible structuring',
    severity: 'high',
    description: 'Two or more transfers just under the high-value threshold from the same sender within 30 minutes.',
  },
  {
    code: 'VELOCITY',
    name: 'High velocity',
    severity: 'high',
    description: 'Three or more transfers from the same sender within 10 minutes.',
  },
  {
    code: 'AMOUNT_SPIKE',
    name: 'Balance drain',
    severity: 'medium',
    description: "Transfer would remove more than 80% of the sender's balance.",
  },
  {
    code: 'NEW_DEVICE',
    name: 'New recipient, large amount',
    severity: 'medium',
    description: 'First-ever transfer to this recipient, for over ₹1,000.',
  },
  {
    code: 'SELF_TRANSFER',
    name: 'Off-hours activity',
    severity: 'low',
    description: 'Initiated between 12am and 5am local time.',
  },
]

function severityLabel(sev) {
  return sev.charAt(0).toUpperCase() + sev.slice(1)
}
</script>

<style scoped>
.rules-toggle {
  background: transparent;
  border: none;
  padding: 0;
  width: 100%;
  text-align: left;
  color: var(--text);
}
.rules-title {
  font-weight: 700;
  font-size: 15px;
}
.chevron {
  color: var(--text-dim);
  font-size: 18px;
  transition: transform 0.15s ease;
}
.chevron.up { transform: rotate(180deg); }

.rule-row {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 10px 0;
  border-bottom: 1px solid var(--border);
}
.rule-row:last-of-type { border-bottom: none; }
.rule-row .badge { flex-shrink: 0; margin-top: 2px; }
.rule-text {
  font-size: 13px;
  color: var(--text-dim);
  line-height: 1.5;
}
.rule-text strong { color: var(--text); }

.rule-footer {
  font-size: 12px;
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid var(--border);
  line-height: 1.6;
}
</style>

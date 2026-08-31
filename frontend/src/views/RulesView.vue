<template>
  <div class="page">
    <h2 style="margin-top:0">Fraud Detection Rules</h2>
    <p class="muted" style="font-size:13px">
      Every transaction is scored automatically the moment its OTP is verified. Based on the total
      score, DecodersPay decides whether to complete, flag, hold, or block it.
    </p>

    <div class="card mt-16">
      <h3 style="margin-top:0">How the score becomes a decision</h3>
      <div class="table-wrap">
        <table>
          <thead>
            <tr><th>Risk score</th><th>Outcome</th><th>Meaning</th></tr>
          </thead>
          <tbody>
            <tr>
              <td class="mono">0 – 24</td>
              <td><span class="badge badge-completed">Completed</span></td>
              <td>Transaction goes through normally.</td>
            </tr>
            <tr>
              <td class="mono">25 – 49</td>
              <td><span class="badge badge-flagged">Flagged</span></td>
              <td>Allowed through, but marked for admin review.</td>
            </tr>
            <tr>
              <td class="mono">50 – 79</td>
              <td><span class="badge badge-held">Held</span></td>
              <td>Money is not moved until an admin approves it.</td>
            </tr>
            <tr>
              <td class="mono">80 – 100</td>
              <td><span class="badge badge-blocked">Blocked</span></td>
              <td>Automatically stopped; funds never leave the sender's balance.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="grid grid-2 mt-24">
      <div class="card hoverable" v-for="r in rules" :key="r.code">
        <div class="flex-between">
          <h3 style="margin:0">{{ r.name }}</h3>
          <span class="badge" :class="`badge-${r.severity}`">+{{ r.points }} pts</span>
        </div>
        <p class="muted" style="font-size:13px;margin-top:8px">{{ r.description }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

// Mirrors backend/app/fraud_rules.py — kept here as a readable reference
// for admins and users; the backend is the actual source of truth.
const rules = ref([
  {
    code: 'CRITICAL_AMOUNT',
    name: 'Critical Amount',
    points: 60,
    severity: 'critical',
    description: 'Triggers when the transaction amount is ₹20,000 or more.',
  },
  {
    code: 'HIGH_AMOUNT',
    name: 'High Amount',
    points: 25,
    severity: 'high',
    description: 'Triggers when the transaction amount is ₹5,000 or more (but under the critical threshold).',
  },
  {
    code: 'BLACKLISTED_RECEIVER',
    name: 'Blacklisted Receiver',
    points: 100,
    severity: 'critical',
    description: 'Triggers when the receiving account has been placed on the admin blacklist.',
  },
  {
    code: 'VELOCITY',
    name: 'Transaction Velocity',
    points: 30,
    severity: 'high',
    description: 'Triggers when a user sends 3 or more transactions within a 10-minute window.',
  },
  {
    code: 'FAN_OUT',
    name: 'Fan-Out',
    points: 25,
    severity: 'medium',
    description: 'Triggers when a user sends money to 5 or more distinct accounts within 30 minutes.',
  },
  {
    code: 'AMOUNT_SPIKE',
    name: 'Amount Spike',
    points: 20,
    severity: 'medium',
    description: "Triggers when an amount is 5x or more the sender's recent average completed transaction.",
  },
  {
    code: 'NEW_DEVICE',
    name: 'New Device',
    points: 20,
    severity: 'medium',
    description: 'Triggers when a transaction over ₹1,000 comes from a device not seen before for that user.',
  },
  {
    code: 'SELF_TRANSFER',
    name: 'Self Transfer',
    points: 15,
    severity: 'low',
    description: "Triggers when the sender's and receiver's account numbers are identical.",
  },
])
</script>

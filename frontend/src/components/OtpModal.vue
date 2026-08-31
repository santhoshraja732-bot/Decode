<template>
  <Teleport to="body">
    <div class="modal-backdrop" @click.self="$emit('close')">
      <div class="modal-box">
        <h3>Verify Transaction</h3>
        <p class="muted" style="font-size:13px">
          Enter the one-time code to authorize this transfer of
          <strong>{{ amount }}</strong> to <strong>{{ receiver }}</strong>.
        </p>

        <div v-if="debugOtp" class="success-box">
          Simulation mode: no real SMS/email is sent. Your OTP is
          <span class="mono"><strong>{{ debugOtp }}</strong></span>.
        </div>

        <label>6-digit OTP code</label>
        <input v-model="code" maxlength="6" placeholder="••••••" @keyup.enter="submit" />

        <div class="muted mt-16" style="font-size:12px">
          Code expires in {{ secondsLeft }}s
          <button class="btn-secondary btn-sm" style="margin-left:10px" :disabled="resending" @click="resend">
            {{ resending ? 'Sending...' : 'Resend code' }}
          </button>
        </div>

        <div v-if="error" class="error-box">{{ error }}</div>

        <div class="flex-between mt-24">
          <button class="btn-secondary" @click="$emit('close')">Cancel</button>
          <button class="btn-primary" :disabled="verifying || code.length !== 6" @click="submit">
            {{ verifying ? 'Verifying...' : 'Verify & Submit' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import api from '../api/axios'

const props = defineProps({
  transactionId: { type: String, required: true },
  amount: { type: [String, Number], required: true },
  receiver: { type: String, required: true },
  initialDebugOtp: { type: String, default: '' },
  expiresInSeconds: { type: Number, default: 120 },
})
const emit = defineEmits(['close', 'verified'])

const code = ref('')
const error = ref('')
const verifying = ref(false)
const resending = ref(false)
const debugOtp = ref(props.initialDebugOtp)
const secondsLeft = ref(props.expiresInSeconds)

let timer = null
onMounted(() => {
  timer = setInterval(() => {
    if (secondsLeft.value > 0) secondsLeft.value -= 1
  }, 1000)
})
onUnmounted(() => clearInterval(timer))

async function submit() {
  error.value = ''
  verifying.value = true
  try {
    const { data } = await api.post('/transactions/verify-otp', {
      transaction_id: props.transactionId,
      code: code.value,
    })
    emit('verified', data)
  } catch (e) {
    error.value = e.response?.data?.detail || 'Verification failed.'
  } finally {
    verifying.value = false
  }
}

async function resend() {
  error.value = ''
  resending.value = true
  try {
    const { data } = await api.post(`/transactions/${props.transactionId}/resend-otp`)
    debugOtp.value = data.debug_otp
    secondsLeft.value = data.expires_in_seconds
    code.value = ''
  } catch (e) {
    error.value = e.response?.data?.detail || 'Could not resend code.'
  } finally {
    resending.value = false
  }
}
</script>

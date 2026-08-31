<template>
  <span class="badge" :class="`badge-${status}`">{{ label }}</span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({ status: { type: String, required: true } })
const label = computed(() => props.status.replace(/_/g, ' '))
</script>

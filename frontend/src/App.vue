<template>
  <Navbar v-if="showNav" />
  <router-view />
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Navbar from './components/Navbar.vue'

const route = useRoute()
const showNav = computed(() => !route.meta.guestOnly && !route.meta.hideNav)
</script>

<template>
  <v-app>
    <NavBar v-if="auth.isAuthenticated" />
    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

<script setup>
  import { onMounted } from 'vue'
  import NavBar from '@/components/NavBar.vue'
  import { useAuthStore } from '@/stores/auth'

  const auth = useAuthStore()

  onMounted(() => {
    auth.init()
  })
</script>

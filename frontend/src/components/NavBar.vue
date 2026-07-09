<template>
  <v-app-bar color="primary" flat>
    <v-app-bar-title>Detecciones y Reconocimiento</v-app-bar-title>

    <template v-if="auth.isAuthenticated">
      <v-btn
        v-if="auth.isOperator"
        :to="{ name: 'detections' }"
        variant="text"
      >
        Detecciones
      </v-btn>
      <v-btn :to="{ name: 'search' }" variant="text">
        Búsqueda
      </v-btn>
      <v-btn
        v-if="auth.isOperator"
        :to="{ name: 'persons' }"
        variant="text"
      >
        Personas
      </v-btn>
      <v-btn
        v-if="auth.isOperator"
        :to="{ name: 'recognition' }"
        variant="text"
      >
        Reconocimiento
      </v-btn>

      <v-divider vertical class="mx-2" />

      <v-chip class="mr-2" color="secondary" size="small">
        {{ auth.user?.preferred_username }} ({{ auth.user?.roles?.find(r => ['admin','operator','viewer'].includes(r)) }})
      </v-chip>

      <v-btn icon @click="handleLogout">
        <v-icon>mdi-logout</v-icon>
      </v-btn>
    </template>
  </v-app-bar>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

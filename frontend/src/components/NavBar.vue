<template>
  <v-app-bar flat border="b" color="surface">
    <v-app-bar-title>
      <span class="text-primary font-weight-bold">SOA</span>
      <span class="text-medium-emphasis ml-1 text-body-2">· Sistema de Detección y Reconocimiento</span>
    </v-app-bar-title>

    <template v-if="auth.isAuthenticated">
      <v-btn
        v-if="auth.isOperator"
        :to="{ name: 'detections' }"
        variant="text"
        size="small"
        prepend-icon="mdi-camera"
        :active="route.name === 'detections'"
      >
        Detecciones
      </v-btn>
      <v-btn
        :to="{ name: 'search' }"
        variant="text"
        size="small"
        prepend-icon="mdi-magnify"
        :active="route.name === 'search'"
      >
        Búsqueda
      </v-btn>
      <v-btn
        v-if="auth.isOperator"
        :to="{ name: 'persons' }"
        variant="text"
        size="small"
        prepend-icon="mdi-account-group"
        :active="route.name === 'persons'"
      >
        Personas
      </v-btn>
      <v-btn
        v-if="auth.isOperator"
        :to="{ name: 'recognition' }"
        variant="text"
        size="small"
        prepend-icon="mdi-face-recognition"
        :active="route.name === 'recognition'"
      >
        Reconocimiento
      </v-btn>

      <v-divider vertical class="mx-2 my-3" />

      <v-chip
        size="small"
        variant="tonal"
        :color="roleColor"
        class="mr-2 text-caption"
        prepend-icon="mdi-shield-account"
      >
        {{ auth.user?.preferred_username }}
        <span class="ml-1 opacity-60">
          {{ auth.user?.roles?.find(r => ['admin','operator','viewer'].includes(r)) }}
        </span>
      </v-chip>

      <v-btn icon variant="text" size="small" @click="handleLogout">
        <v-icon size="18">mdi-logout</v-icon>
        <v-tooltip activator="parent">Cerrar sesión</v-tooltip>
      </v-btn>
    </template>
  </v-app-bar>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const roleColor = computed(() => {
  const role = auth.user?.roles?.find(r => ['admin','operator','viewer'].includes(r))
  if (role === 'admin') return 'error'
  if (role === 'operator') return 'primary'
  return 'secondary'
})

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

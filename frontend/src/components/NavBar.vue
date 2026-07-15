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
      <v-btn
        :to="{ name: 'rps' }"
        variant="text"
        size="small"
        prepend-icon="mdi-hand-back-right-outline"
        :active="route.name === 'rps'"
      >
        Piedra, Papel o Tijera
      </v-btn>
      <v-btn
        v-if="auth.isAdmin"
        :to="{ name: 'users' }"
        variant="text"
        size="small"
        prepend-icon="mdi-account-cog"
        :active="route.name === 'users'"
      >
        Usuarios
      </v-btn>
      <v-btn
        :to="{ name: 'profile' }"
        variant="text"
        size="small"
        prepend-icon="mdi-account-circle-outline"
        :active="route.name === 'profile'"
      >
        Mi Perfil
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
          {{ topRole }}
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

// Orden de prioridad (mayor a menor jerarquía): el primero que el usuario tenga es el que se muestra.
const topRole = computed(() => ['admin', 'operator', 'viewer'].find(r => auth.user?.roles?.includes(r)))

const roleColor = computed(() => {
  if (topRole.value === 'admin') return 'error'
  if (topRole.value === 'operator') return 'primary'
  return 'secondary'
})

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>

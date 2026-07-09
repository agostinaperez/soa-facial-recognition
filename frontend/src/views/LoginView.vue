<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="4">

        <div class="text-center mb-6">
          <v-icon size="48" color="primary" class="mb-3">mdi-shield-lock</v-icon>
          <div class="text-h5 font-weight-bold">Iniciar Sesión</div>
          <div class="text-h8 font-weight">-</div>
          <div class="text-h8 font-weight">Sistema de Detección y Reconocimiento</div>
        </div>

        <v-card flat border color="surface-variant" class="pa-2">
          <v-card-text>
            <v-text-field
              v-model="username"
              label="Usuario"
              prepend-inner-icon="mdi-account-outline"
              variant="outlined"
              density="comfortable"
              class="mb-3"
              autofocus
              @keyup.enter="handleLogin"
            />
            <v-text-field
              v-model="password"
              label="Contraseña"
              prepend-inner-icon="mdi-lock-outline"
              type="password"
              variant="outlined"
              density="comfortable"
              @keyup.enter="handleLogin"
            />
            <v-alert
              v-if="error"
              type="error"
              variant="tonal"
              density="compact"
              class="mt-3"
              :text="error"
            />
          </v-card-text>
          <v-card-actions class="px-4 pb-4">
            <v-btn
              block
              color="primary"
              size="large"
              variant="flat"
              :loading="loading"
              @click="handleLogin"
            >
              Ingresar
            </v-btn>
          </v-card-actions>
        </v-card>

      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    router.push('/detections')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

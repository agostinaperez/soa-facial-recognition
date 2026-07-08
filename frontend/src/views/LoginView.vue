<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="4">
        <v-card class="pa-4">
          <v-card-title class="text-h5 mb-4">Iniciar sesión</v-card-title>
          <v-card-text>
            <v-text-field
              v-model="username"
              label="Usuario"
              prepend-inner-icon="mdi-account"
              variant="outlined"
              class="mb-3"
            />
            <v-text-field
              v-model="password"
              label="Contraseña"
              prepend-inner-icon="mdi-lock"
              type="password"
              variant="outlined"
              class="mb-3"
            />
            <v-alert v-if="error" type="error" class="mb-3">{{ error }}</v-alert>
          </v-card-text>
          <v-card-actions>
            <v-btn
              block
              color="primary"
              size="large"
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

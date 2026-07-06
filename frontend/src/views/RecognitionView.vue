<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h2 class="text-h5 mb-4">Reconocimiento facial</h2>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="5">
        <v-card class="pa-4">
          <v-card-title>Configuración</v-card-title>
          <v-card-text>
            <v-file-input
              v-model="image"
              label="Imagen"
              accept="image/*"
              variant="outlined"
              prepend-icon="mdi-face-recognition"
              class="mb-3"
              :clearable="false"
            />
            <v-text-field
              v-model="threshold"
              label="Umbral de confianza (0 a 1)"
              variant="outlined"
              type="number"
              step="0.1"
              min="0"
              max="1"
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
              :disabled="!image"
              @click="handleRecognition"
            >
              Reconocer
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <v-col cols="12" md="7" v-if="result !== null">
        <v-card class="pa-4">
          <v-card-title>Resultado</v-card-title>
          <v-card-text>
            <template v-if="result.personId">
              <v-alert type="success" class="mb-3">Persona identificada</v-alert>
              <p class="mb-1"><strong>Nombre:</strong> {{ result.nombre }} {{ result.apellido }}</p>
              <p class="mb-1"><strong>ID:</strong> {{ result.personId }}</p>
              <p class="mb-1">
                <strong>Confianza:</strong> {{ (result.confidence * 100).toFixed(1) }}%
              </p>
            </template>
            <template v-else>
              <v-alert type="warning" class="mb-3">No se identificó ninguna persona</v-alert>
              <p class="mb-1">
                <strong>Confianza máxima alcanzada:</strong> {{ (result.confidence * 100).toFixed(1) }}%
              </p>
              <p class="text-caption text-grey">
                El resultado no superó el umbral de {{ threshold }}.
              </p>
            </template>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import { api } from '@/services/api'

const image = ref(null)
const threshold = ref(0.8)
const loading = ref(false)
const error = ref('')
const result = ref(null)

async function handleRecognition() {
  error.value = ''
  result.value = null
  loading.value = true
  try {
    const file = Array.isArray(image.value) ? image.value[0] : image.value

    const base64 = await new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result.split(',')[1])
      reader.onerror = reject
      reader.readAsDataURL(file)
    })

    const response = await api.post('/face-recognition', {
      image: base64,
      threshold: parseFloat(threshold.value),
    })
    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.detail || 'Error al procesar el reconocimiento')
    }
    result.value = await response.json()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

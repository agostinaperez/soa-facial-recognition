<template>
  <v-container class="py-6">
    <div class="text-h6 font-weight-bold mb-1">Reconocimiento facial</div>
    <div class="text-medium-emphasis text-body-2 mb-5">Identificá una persona a partir de una imagen</div>

    <v-row>
      <v-col cols="12" md="5">
        <v-card flat border color="surface-variant">
          <v-card-text class="pa-5">
            <div class="text-caption text-medium-emphasis text-uppercase mb-2">Imagen</div>
            <v-file-input
              v-model="image"
              accept="image/*"
              variant="outlined"
              density="comfortable"
              prepend-icon=""
              prepend-inner-icon="mdi-face-recognition"
              :clearable="false"
              placeholder="Seleccioná un archivo"
              class="mb-4"
            />

            <div style="color: #8b949e; font-size: 12px; text-transform: uppercase; margin-bottom: 4px;">
              Umbral de confianza
            </div>
            <div class="d-flex align-center gap-3 mb-4">
              <v-slider
                v-model="threshold"
                :min="0"
                :max="1"
                :step="0.05"
                color="primary"
                hide-details
                class="flex-grow-1"
              />
              <span class="text-body-2 font-weight-medium" style="min-width: 36px; color: #e6edf3">{{ threshold }}</span>
            </div>

            <v-alert v-if="error" type="error" variant="tonal" density="compact" :text="error" />
          </v-card-text>
          <v-card-actions class="px-5 pb-5">
            <v-btn
              block
              color="primary"
              variant="flat"
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
        <v-card flat border :color="result.personId ? 'surface-variant' : 'surface-variant'">
          <v-card-text class="pa-5">
            <template v-if="result.personId">
              <div class="d-flex align-center mb-4">
                <v-icon color="success" size="20" class="mr-2">mdi-check-circle</v-icon>
                <span class="text-body-2 font-weight-medium text-success">Persona identificada</span>
              </div>
              <div class="d-flex align-center mb-5">
                <v-avatar color="primary" size="48" class="mr-4">
                  <span class="text-body-1 font-weight-bold">
                    {{ result.nombre[0] }}{{ result.apellido[0] }}
                  </span>
                </v-avatar>
                <div>
                  <div class="text-h6 font-weight-bold">{{ result.nombre }} {{ result.apellido }}</div>
                  <div class="font-mono text-caption text-medium-emphasis">{{ result.personId }}</div>
                </div>
              </div>
              <div class="text-caption text-medium-emphasis mb-2">Confianza</div>
              <div class="d-flex align-center gap-3">
                <v-progress-linear
                  :model-value="result.confidence * 100"
                  color="success"
                  bg-color="surface"
                  height="8"
                  rounded
                  class="flex-grow-1"
                />
                <span class="text-body-2 font-weight-bold text-success" style="min-width: 44px">
                  {{ (result.confidence * 100).toFixed(1) }}%
                </span>
              </div>
            </template>

            <template v-else>
              <div class="d-flex align-center mb-4">
                <v-icon color="warning" size="20" class="mr-2">mdi-alert-circle-outline</v-icon>
                <span class="text-body-2 font-weight-medium text-warning">No se identificó ninguna persona</span>
              </div>
              <div class="text-caption text-medium-emphasis mb-2">Confianza máxima alcanzada</div>
              <div class="d-flex align-center gap-3">
                <v-progress-linear
                  :model-value="result.confidence * 100"
                  color="warning"
                  bg-color="surface"
                  height="8"
                  rounded
                  class="flex-grow-1"
                />
                <span class="text-body-2 font-weight-bold text-warning" style="min-width: 44px">
                  {{ (result.confidence * 100).toFixed(1) }}%
                </span>
              </div>
              <div class="text-caption text-medium-emphasis mt-3">
                El resultado no superó el umbral de {{ threshold }}.
              </div>
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

<style scoped>
.font-mono {
  font-family: 'Courier New', Courier, monospace;
}
</style>

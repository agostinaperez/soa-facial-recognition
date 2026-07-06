<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h2 class="text-h5 mb-4">Nueva detección</h2>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="6">
        <v-card class="pa-4">
          <v-card-title>Configuración</v-card-title>
          <v-card-text>
            <v-select
              v-model="selectedModel"
              :items="models"
              label="Modelo"
              variant="outlined"
              class="mb-3"
              :loading="loadingModels"
            />
            <v-file-input
            v-model="image"
            label="Imagen"
            accept="image/*"
            variant="outlined"
            prepend-icon="mdi-camera"
            class="mb-3"
            :clearable="false"
            />
            <v-text-field
            v-model="lat"
            label="Latitud"
            variant="outlined"
            class="mb-3"
            />
            <v-text-field
            v-model="lon"
            label="Longitud"
            variant="outlined"
            class="mb-3"
            />
            <v-alert v-if="error" type="error" class="mb-3">{{ error }}</v-alert>
            <v-alert v-if="success" type="success" class="mb-3">{{ success }}</v-alert>
          </v-card-text>
          <v-card-actions>
            <v-btn
              block
              color="primary"
              size="large"
              :loading="loading"
              :disabled="!selectedModel || !image || !lat || !lon"
              @click="handleSubmit"
            >
              Enviar
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <v-col cols="12" md="6" v-if="result">
        <v-card class="pa-4">
          <v-card-title>Resultado</v-card-title>
          <v-card-text>
            <p class="mb-2"><strong>Frame ID:</strong> {{ result.frame_id }}</p>
            <p class="mb-2"><strong>Estado:</strong> {{ result.message }}</p>
            <v-divider class="my-3" />
            <p class="text-caption text-grey">
              Las detecciones se procesan en segundo plano. Podés consultar el resultado en Búsqueda usando el Frame ID.
            </p>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/services/api'

const models = ref([])
const selectedModel = ref(null)
const image = ref(null)
const lat = ref('')
const lon = ref('')
const loading = ref(false)
const loadingModels = ref(false)
const error = ref('')
const success = ref('')
const result = ref(null)

onMounted(async () => {
  loadingModels.value = true
  try {
    const response = await api.get('/models')
    models.value = await response.json()
  } catch (e) {
    error.value = 'No se pudieron cargar los modelos'
  } finally {
    loadingModels.value = false
  }
})

async function handleSubmit() {
  error.value = ''
  success.value = ''
  loading.value = true

  try {
    const formData = new FormData()
    const file = Array.isArray(image.value) ? image.value[0] : image.value
    formData.append('file', file)
    formData.append('model_id', selectedModel.value)
    formData.append('latitude', lat.value)
    formData.append('longitude', lon.value)

    const response = await api.postForm('/detections', formData)

    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.detail || 'Error al enviar la detección')
    }

    result.value = await response.json()
    success.value = 'Imagen enviada correctamente'
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

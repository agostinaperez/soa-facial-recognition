<template>
  <v-container class="py-6">
    <div class="text-h6 font-weight-bold mb-1">Nueva detección</div>
    <div class="text-medium-emphasis text-body-2 mb-5"></div>

    <v-row>
      <v-col cols="12" md="6">
        <v-card flat border color="surface-variant">
          <v-card-text class="pa-5">

            <div class="text-caption text-medium-emphasis mb-1 text-uppercase letter-spacing-wide">Modelo</div>
            <v-select
              v-model="selectedModel"
              :items="models"
              variant="outlined"
              density="comfortable"
              class="mb-4"
              :loading="loadingModels"
              placeholder="Seleccioná un modelo"
            />

            <div class="text-caption text-medium-emphasis mb-1 text-uppercase letter-spacing-wide">Imagen</div>
            <v-file-input
              v-model="image"
              accept="image/*"
              variant="outlined"
              density="comfortable"
              prepend-icon=""
              prepend-inner-icon="mdi-image-outline"
              class="mb-4"
              :clearable="false"
              placeholder="Seleccioná un archivo"
            />

            <v-row dense class="mb-4">
              <v-col>
                <div class="text-caption text-medium-emphasis mb-1 text-uppercase">Latitud</div>
                <v-text-field v-model="lat" variant="outlined" density="comfortable" placeholder="Latitud" />
              </v-col>
              <v-col>
                <div class="text-caption text-medium-emphasis mb-1 text-uppercase">Longitud</div>
                <v-text-field v-model="lon" variant="outlined" density="comfortable" placeholder="Longitud" />
              </v-col>
            </v-row>

            <v-divider class="mb-4" />
            <div class="d-flex align-center justify-space-between mb-3">
              <div class="text-caption text-medium-emphasis text-uppercase">Metadata adicional</div>
              <v-btn
                variant="tonal"
                size="small"
                class="mb-3"
                prepend-icon="mdi-plus"
                style="color: #e6edf3"
                @click="addEntry"
              >
                Agregar campo
              </v-btn>
            </div>
            <v-row v-for="(entry, index) in metadataEntries" :key="index" dense class="mb-1">
              <v-col cols="5">
                <v-text-field v-model="entry.key" label="Clave" variant="outlined" density="compact" />
              </v-col>
              <v-col cols="5">
                <v-text-field v-model="entry.value" label="Valor" variant="outlined" density="compact" />
              </v-col>
              <v-col cols="2" class="d-flex align-center">
                <v-btn icon variant="text" color="error" size="small" @click="removeEntry(index)">
                  <v-icon size="16">mdi-close</v-icon>
                </v-btn>
              </v-col>
            </v-row>

            <v-alert v-if="error" type="error" variant="tonal" density="compact" class="mt-3" :text="error" />
            <v-alert v-if="success" type="success" variant="tonal" density="compact" class="mt-3" :text="success" />
          </v-card-text>

          <v-card-actions class="px-5 pb-5">
            <v-btn
              block
              color="primary"
              variant="flat"
              size="large"
              :loading="loading"
              :disabled="!selectedModel || !image || !lat || !lon"
              @click="handleSubmit"
            >
              Enviar fotograma
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <v-col cols="12" md="6" v-if="result">
        <v-card flat border color="surface-variant">
          <v-card-text class="pa-5">
            <div class="d-flex align-center mb-4">
              <v-icon color="success" class="mr-2">mdi-check-circle-outline</v-icon>
              <span class="text-body-2 font-weight-medium">Fotograma recibido</span>
            </div>
            <div class="text-caption text-medium-emphasis mb-1">Frame ID</div>
            <div class="text-body-2 font-mono mb-4 pa-2 rounded" style="background: rgba(255,255,255,0.05)">
              {{ result.frame_id }}
            </div>
            <div class="text-caption text-medium-emphasis mb-1">Estado</div>
            <div class="text-body-2 mb-4">{{ result.message }}</div>
            <v-alert type="info" variant="tonal" density="compact">
              Las detecciones se procesan en segundo plano. Consultá el resultado en Búsqueda usando el Frame ID.
            </v-alert>
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
const metadataEntries = ref([])
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
  } catch {
    error.value = 'No se pudieron cargar los modelos'
  } finally {
    loadingModels.value = false
  }
})

function addEntry() { metadataEntries.value.push({ key: '', value: '' }) }
function removeEntry(index) { metadataEntries.value.splice(index, 1) }
function buildMetadata() {
  const obj = {}
  for (const entry of metadataEntries.value) {
    if (entry.key.trim()) obj[entry.key.trim()] = entry.value
  }
  return obj
}

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
    formData.append('extra_metadata', JSON.stringify(buildMetadata()))
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

<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h2 class="text-h5 mb-4">Búsqueda de fotogramas</h2>
      </v-col>
    </v-row>

    <v-row>
      <v-col cols="12" md="4">
        <v-card class="pa-4">
          <v-card-title>Filtros</v-card-title>
          <v-card-text>
            <v-text-field
              v-model="minLat"
              label="Latitud mínima"
              variant="outlined"
              class="mb-3"
            />
            <v-text-field
              v-model="maxLat"
              label="Latitud máxima"
              variant="outlined"
              class="mb-3"
            />
            <v-text-field
              v-model="minLon"
              label="Longitud mínima"
              variant="outlined"
              class="mb-3"
            />
            <v-text-field
              v-model="maxLon"
              label="Longitud máxima"
              variant="outlined"
              class="mb-3"
            />
            <v-text-field
              v-model="detectedClass"
              label="Clase detectada"
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
              @click="handleSearch"
            >
              Buscar
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <v-col cols="12" md="8">
        <v-card class="pa-4" v-if="results.length > 0">
          <v-card-title>Resultados ({{ results.length }})</v-card-title>
          <v-card-text>
            <v-expansion-panels>
              <v-expansion-panel
                v-for="frame in results"
                :key="frame.frameId"
              >
                <v-expansion-panel-title>
                  <span class="text-caption">{{ frame.frameId }}</span>
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <v-img
                    :src="frame.imageURL"
                    :headers="{ Authorization: `Bearer ${auth.token}` }"
                    max-height="300"
                    class="mb-3"
                    cover
                  />
                  <p class="mb-1"><strong>Metadata:</strong></p>
                  <pre class="text-caption mb-3">{{ JSON.stringify(frame.metadata, null, 2) }}</pre>
                  <p class="mb-1"><strong>Detecciones ({{ frame.detections.length }}):</strong></p>
                  <v-chip
                    v-for="det in frame.detections"
                    :key="det.id"
                    class="mr-2 mb-2"
                    size="small"
                  >
                    {{ det.class_name }} ({{ (det.confidence * 100).toFixed(1) }}%)
                  </v-chip>
                </v-expansion-panel-text>
              </v-expansion-panel>
            </v-expansion-panels>
          </v-card-text>
        </v-card>

        <v-card class="pa-4" v-else-if="searched && results.length === 0">
          <v-card-text class="text-grey">
            No se encontraron fotogramas con los filtros indicados.
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import { api } from '@/services/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const minLat = ref('')
const maxLat = ref('')
const minLon = ref('')
const maxLon = ref('')
const detectedClass = ref('')

const loading = ref(false)
const error = ref('')
const results = ref([])
const searched = ref(false)

async function handleSearch() {
  error.value = ''
  loading.value = true
  searched.value = false

  try {
    const params = new URLSearchParams()
    if (minLat.value) params.append('min_lat', minLat.value)
    if (maxLat.value) params.append('max_lat', maxLat.value)
    if (minLon.value) params.append('min_lon', minLon.value)
    if (maxLon.value) params.append('max_lon', maxLon.value)
    if (detectedClass.value) params.append('detected_class', detectedClass.value)

    const response = await api.get(`/frames/search?${params.toString()}`)
    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.detail || 'Error al buscar fotogramas')
    }
    results.value = await response.json()
    searched.value = true
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

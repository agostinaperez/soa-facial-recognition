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
            <v-text-field v-model="minLat" label="Latitud mínima" variant="outlined" class="mb-3" />
            <v-text-field v-model="maxLat" label="Latitud máxima" variant="outlined" class="mb-3" />
            <v-text-field v-model="minLon" label="Longitud mínima" variant="outlined" class="mb-3" />
            <v-text-field v-model="maxLon" label="Longitud máxima" variant="outlined" class="mb-3" />
            <v-text-field v-model="detectedClass" label="Clase detectada" variant="outlined" class="mb-3" />

            <v-divider class="mb-3" />
            <p class="text-body-2 mb-2">Filtrar por metadata</p>
            <v-row
              v-for="(entry, index) in metadataFilters"
              :key="index"
              dense
              class="mb-1"
            >
              <v-col cols="5">
                <v-text-field
                  v-model="entry.key"
                  label="Clave"
                  variant="outlined"
                  density="compact"
                />
              </v-col>
              <v-col cols="5">
                <v-text-field
                  v-model="entry.value"
                  label="Valor"
                  variant="outlined"
                  density="compact"
                />
              </v-col>
              <v-col cols="2" class="d-flex align-center">
                <v-btn icon variant="text" color="error" size="small" @click="removeFilter(index)">
                  <v-icon>mdi-close</v-icon>
                </v-btn>
              </v-col>
            </v-row>
            <v-btn variant="tonal" size="small" class="mb-3" prepend-icon="mdi-plus" @click="addFilter">
              Agregar filtro
            </v-btn>

            <v-alert v-if="error" type="error" class="mb-3">{{ error }}</v-alert>
          </v-card-text>
          <v-card-actions>
            <v-btn block color="primary" size="large" :loading="loading" @click="handleSearch">
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
              <v-expansion-panel v-for="frame in results" :key="frame.frameId">
                <v-expansion-panel-title>
                  <span class="text-caption">{{ frame.frameId }}</span>
                </v-expansion-panel-title>
                <v-expansion-panel-text>
                  <v-row>
                    <v-col cols="12" md="4">
                      <v-img
                        :src="frame._imgSrc || ''"
                        height="180"
                        cover
                        rounded="lg"
                      />
                    </v-col>

                    <v-col cols="12" md="8">
                      <p class="mb-2"><strong>Metadata:</strong></p>
                      <template v-if="frame.metadata && Object.keys(frame.metadata).length > 0">
                        <v-chip
                          v-for="(value, key) in frame.metadata"
                          :key="key"
                          class="mr-2 mb-2"
                          size="small"
                          color="primary"
                          variant="tonal"
                        >
                          <strong>{{ key }}:</strong>&nbsp;{{ value }}
                        </v-chip>
                      </template>
                      <p v-else class="text-caption text-grey mb-3">Sin metadata adicional</p>

                      <p class="mt-3 mb-2"><strong>Detecciones ({{ frame.detections.length }}):</strong></p>
                      <v-chip
                        v-for="det in frame.detections"
                        :key="det.id"
                        class="mr-2 mb-2"
                        size="small"
                        color="secondary"
                        variant="tonal"
                      >
                        {{ det.class_name }} ({{ (det.confidence * 100).toFixed(1) }}%)
                      </v-chip>
                    </v-col>
                  </v-row>
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

        <v-card class="pa-4" v-else-if="loading">
          <v-card-text class="d-flex justify-center">
            <v-progress-circular indeterminate color="primary" />
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/services/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const minLat = ref('')
const maxLat = ref('')
const minLon = ref('')
const maxLon = ref('')
const detectedClass = ref('')
const metadataFilters = ref([])

const loading = ref(false)
const error = ref('')
const results = ref([])
const searched = ref(false)

onMounted(() => handleSearch())

function addFilter() {
  metadataFilters.value.push({ key: '', value: '' })
}

function removeFilter(index) {
  metadataFilters.value.splice(index, 1)
}

async function loadImage(frame) {
  try {
    const response = await api.get(`/frames/${frame.frameId}?thumbnail=true`)
    if (!response.ok) return
    const blob = await response.blob()
    frame._imgSrc = URL.createObjectURL(blob)
  } catch {
    // si falla simplemente no muestra imagen
  }
}

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

    for (const entry of metadataFilters.value) {
      if (entry.key.trim() && entry.value.trim()) {
        params.append('metadata_key', entry.key.trim())
        params.append('metadata_value', entry.value.trim())
      }
    }

    const response = await api.get(`/frames/search?${params.toString()}`)
    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.detail || 'Error al buscar fotogramas')
    }
    const data = await response.json()
    results.value = data
    searched.value = true

    // carga las imágenes en paralelo con el token
    data.forEach(frame => loadImage(frame))
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

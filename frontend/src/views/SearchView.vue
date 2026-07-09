<template>
  <v-container class="py-6">
    <div class="text-h6 font-weight-bold mb-1">Búsqueda de fotogramas</div>
    <div class="text-medium-emphasis text-body-2 mb-5">Filtrá por ubicación, clases detectadas y metadata</div>

    <v-row>
      <v-col cols="12" md="4">
        <v-card flat border color="surface-variant">
          <v-card-text class="pa-5">
            <div class="text-caption text-medium-emphasis text-uppercase mb-3">Rango de coordenadas</div>
            <v-row dense class="mb-1">
              <v-col><v-text-field v-model="minLat" label="Lat mínima" variant="outlined" density="compact" /></v-col>
              <v-col><v-text-field v-model="maxLat" label="Lat máxima" variant="outlined" density="compact" /></v-col>
            </v-row>
            <v-row dense class="mb-4">
              <v-col><v-text-field v-model="minLon" label="Lon mínima" variant="outlined" density="compact" /></v-col>
              <v-col><v-text-field v-model="maxLon" label="Lon máxima" variant="outlined" density="compact" /></v-col>
            </v-row>

            <div class="text-caption text-medium-emphasis text-uppercase mb-2">Clase detectada</div>
            <v-text-field
              v-model="detectedClass"
              variant="outlined"
              density="comfortable"
              placeholder="ej: person, car"
              prepend-inner-icon="mdi-tag-outline"
              class="mb-4"
            />

            <v-divider class="mb-4" />
            <div class="d-flex align-center justify-space-between mb-3">
              <div class="text-caption text-medium-emphasis text-uppercase">Filtros de metadata</div>
              <v-btn variant="tonal" size="x-small" class="mb-3" prepend-icon="mdi-plus" style="color: #e6edf3" @click="addFilter">Agregar Campo</v-btn>
            </div>
            <v-row v-for="(entry, index) in metadataFilters" :key="index" dense class="mb-1">
              <v-col cols="5"><v-text-field v-model="entry.key" label="Clave" variant="outlined" density="compact" /></v-col>
              <v-col cols="5"><v-text-field v-model="entry.value" label="Valor" variant="outlined" density="compact" /></v-col>
              <v-col cols="2" class="d-flex align-center">
                <v-btn icon variant="text" color="error" size="small" @click="removeFilter(index)">
                  <v-icon size="16">mdi-close</v-icon>
                </v-btn>
              </v-col>
            </v-row>

            <v-alert v-if="error" type="error" variant="tonal" density="compact" class="mt-3" :text="error" />
          </v-card-text>
          <v-card-actions class="px-5 pb-5">
            <v-btn block color="primary" variant="flat" size="large" :loading="loading" @click="handleSearch">
              Buscar
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <v-col cols="12" md="8">
        <div v-if="loading" class="d-flex justify-center align-center" style="height: 200px">
          <v-progress-circular indeterminate color="primary" />
        </div>

        <template v-else-if="results.length > 0">
          <div class="text-caption text-medium-emphasis mb-3">
            {{ results.length }} resultado{{ results.length !== 1 ? 's' : '' }}
          </div>
          <v-expansion-panels variant="accordion" class="border rounded">
            <v-expansion-panel
              v-for="frame in results"
              :key="frame.frameId"
              color="surface-variant"
            >
              <v-expansion-panel-title>
                <div class="d-flex align-center gap-3">
                  <v-icon size="16" color="primary" class="mr-2">mdi-image-outline</v-icon>
                  <span class="font-mono text-caption">{{ frame.frameId }}</span>
                  <v-chip
                    v-if="frame.detections.length"
                    size="x-small"
                    color="secondary"
                    variant="tonal"
                    class="ml-2"
                  >
                    {{ frame.detections.length }} det.
                  </v-chip>
                </div>
              </v-expansion-panel-title>
              <v-expansion-panel-text>
                <v-row>
                  <v-col cols="12" md="4">
                    <div
                      class="rounded overflow-hidden"
                      style="height: 160px; background: rgba(255,255,255,0.04); display:flex; align-items:center; justify-content:center"
                    >
                      <img
                        v-if="frame._imgSrc"
                        :src="frame._imgSrc"
                        style="width:100%; height:100%; object-fit:cover"
                      />
                      <v-icon v-else size="32" color="medium-emphasis">mdi-image-off-outline</v-icon>
                    </div>
                  </v-col>
                  <v-col cols="12" md="8">
                    <div class="text-caption text-medium-emphasis mb-2">Metadata</div>
                    <template v-if="frame.metadata && Object.keys(frame.metadata).length">
                      <v-chip
                        v-for="(value, key) in frame.metadata"
                        :key="key"
                        size="small"
                        color="primary"
                        variant="tonal"
                        class="mr-1 mb-1"
                      >
                        {{ key }}: {{ value }}
                      </v-chip>
                    </template>
                    <p v-else class="text-caption text-medium-emphasis">Sin metadata adicional</p>

                    <div class="text-caption text-medium-emphasis mt-3 mb-2">Detecciones</div>
                    <v-chip
                      v-for="det in frame.detections"
                      :key="det.id"
                      size="small"
                      color="secondary"
                      variant="tonal"
                      class="mr-1 mb-1"
                    >
                      {{ det.class_name }} · {{ (det.confidence * 100).toFixed(0) }}%
                    </v-chip>
                  </v-col>
                </v-row>
              </v-expansion-panel-text>
            </v-expansion-panel>
          </v-expansion-panels>
        </template>

        <v-card v-else-if="searched" flat border color="surface-variant" class="pa-6 text-center">
          <v-icon size="40" color="medium-emphasis" class="mb-3">mdi-image-search-outline</v-icon>
          <div class="text-body-2 text-medium-emphasis">No se encontraron fotogramas con esos filtros.</div>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/services/api'

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

function addFilter() { metadataFilters.value.push({ key: '', value: '' }) }
function removeFilter(index) { metadataFilters.value.splice(index, 1) }

async function loadImage(frame) {
  try {
    const response = await api.get(`/frames/${frame.frameId}?thumbnail=true`)
    if (!response.ok) return
    const blob = await response.blob()
    frame._imgSrc = URL.createObjectURL(blob)
  } catch { /* silencioso */ }
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
    data.forEach(frame => loadImage(frame))
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h2 class="text-h5 mb-4">Gestión de personas</h2>
      </v-col>
    </v-row>

    <v-row>
      <!-- Crear persona -->
      <v-col cols="12" md="5">
        <v-card class="pa-4">
          <v-card-title>Nueva persona</v-card-title>
          <v-card-text>
            <v-text-field
              v-model="nombre"
              label="Nombre"
              variant="outlined"
              class="mb-3"
            />
            <v-text-field
              v-model="apellido"
              label="Apellido"
              variant="outlined"
              class="mb-3"
            />
            <v-text-field
              v-model="email"
              label="Email"
              variant="outlined"
              class="mb-3"
            />
            <v-alert v-if="createError" type="error" class="mb-3">{{ createError }}</v-alert>
            <v-alert v-if="createSuccess" type="success" class="mb-3">{{ createSuccess }}</v-alert>
          </v-card-text>
          <v-card-actions>
            <v-btn
              block
              color="primary"
              size="large"
              :loading="loadingCreate"
              :disabled="!nombre || !apellido || !email"
              @click="handleCreate"
            >
              Crear
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <!-- Buscar persona y cargar embeddings -->
      <v-col cols="12" md="7">
        <v-card class="pa-4">
          <v-card-title>Buscar persona por ID</v-card-title>
          <v-card-text>
            <v-text-field
              v-model="searchId"
              label="Person ID"
              variant="outlined"
              class="mb-3"
            />
            <v-alert v-if="searchError" type="error" class="mb-3">{{ searchError }}</v-alert>
          </v-card-text>
          <v-card-actions>
            <v-btn
              block
              color="primary"
              size="large"
              :loading="loadingSearch"
              :disabled="!searchId"
              @click="handleSearch"
            >
              Buscar
            </v-btn>
          </v-card-actions>

          <!-- Resultado de búsqueda -->
          <template v-if="person">
            <v-divider class="my-3" />
            <v-card-text>
              <p class="mb-1"><strong>Nombre:</strong> {{ person.nombre }} {{ person.apellido }}</p>
              <p class="mb-1"><strong>Email:</strong> {{ person.email }}</p>
              <p class="mb-3"><strong>ID:</strong> {{ person.personId }}</p>

              <v-divider class="mb-3" />
              <p class="mb-2"><strong>Cargar imágenes para embeddings</strong></p>

              <v-file-input
                v-model="embeddingFiles"
                label="Imágenes"
                accept="image/*"
                variant="outlined"
                prepend-icon="mdi-face-recognition"
                multiple
                class="mb-3"
                :clearable="false"
              />
              <v-alert v-if="embeddingError" type="error" class="mb-3">{{ embeddingError }}</v-alert>
              <v-alert v-if="embeddingSuccess" type="success" class="mb-3">{{ embeddingSuccess }}</v-alert>
            </v-card-text>
            <v-card-actions>
              <v-btn
                block
                color="secondary"
                size="large"
                :loading="loadingEmbedding"
                :disabled="!embeddingFiles || embeddingFiles.length === 0"
                @click="handleEmbeddings"
              >
                Generar embeddings
              </v-btn>
            </v-card-actions>
          </template>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'
import { api } from '@/services/api'

// --- Crear persona ---
const nombre = ref('')
const apellido = ref('')
const email = ref('')
const loadingCreate = ref(false)
const createError = ref('')
const createSuccess = ref('')

async function handleCreate() {
  createError.value = ''
  createSuccess.value = ''
  loadingCreate.value = true
  try {
    const response = await api.post('/persons', {
      nombre: nombre.value,
      apellido: apellido.value,
      email: email.value,
    })
    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.detail || 'Error al crear la persona')
    }
    const data = await response.json()
    createSuccess.value = `Persona creada con ID: ${data.personId}`
    nombre.value = ''
    apellido.value = ''
    email.value = ''
  } catch (e) {
    createError.value = e.message
  } finally {
    loadingCreate.value = false
  }
}

// --- Buscar persona ---
const searchId = ref('')
const person = ref(null)
const loadingSearch = ref(false)
const searchError = ref('')

async function handleSearch() {
  searchError.value = ''
  person.value = null
  loadingSearch.value = true
  try {
    const response = await api.get(`/persons/${searchId.value}`)
    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.detail || 'Persona no encontrada')
    }
    person.value = await response.json()
  } catch (e) {
    searchError.value = e.message
  } finally {
    loadingSearch.value = false
  }
}

// --- Embeddings ---
const embeddingFiles = ref([])
const loadingEmbedding = ref(false)
const embeddingError = ref('')
const embeddingSuccess = ref('')

async function handleEmbeddings() {
  embeddingError.value = ''
  embeddingSuccess.value = ''
  loadingEmbedding.value = true
  try {
    // El backend espera las imágenes como array de strings base64
    const toBase64 = (file) =>
      new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => resolve(reader.result.split(',')[1])
        reader.onerror = reject
        reader.readAsDataURL(file)
      })

    const files = Array.isArray(embeddingFiles.value)
      ? embeddingFiles.value
      : [embeddingFiles.value]

    const images = await Promise.all(files.map(toBase64))

    const response = await api.post(`/persons/${person.value.personId}/embeddings`, { images })
    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.detail || 'Error al generar embeddings')
    }
    const data = await response.json()
    embeddingSuccess.value = data.message
    embeddingFiles.value = []
  } catch (e) {
    embeddingError.value = e.message
  } finally {
    loadingEmbedding.value = false
  }
}
</script>

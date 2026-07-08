<template>
  <v-container>
    <v-row>
      <v-col cols="12">
        <h2 class="text-h5 mb-4">Gestión de personas</h2>
      </v-col>
    </v-row>

    <v-row>
      <!-- Lista de personas -->
      <v-col cols="12" md="7">
        <v-card class="pa-4">
          <v-card-title class="d-flex justify-space-between align-center">
            Personas registradas
            <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreateDialog">
              Nueva persona
            </v-btn>
          </v-card-title>
          <v-card-text>
            <v-alert v-if="listError" type="error" class="mb-3">{{ listError }}</v-alert>
            <v-progress-circular v-if="loadingList" indeterminate color="primary" class="d-flex mx-auto" />
            <v-table v-else-if="persons.length > 0">
              <thead>
                <tr>
                  <th>Nombre</th>
                  <th>Apellido</th>
                  <th>Email</th>
                  <th>Acciones</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="p in persons"
                  :key="p.personId"
                  @click="selectPerson(p)"
                  :class="{
                    'bg-blue-lighten-5': selectedPerson?.personId === p.personId
                  }"
                  style="cursor:pointer; transition: background-color .2s;"
                >
                  <td>{{ p.nombre }}</td>
                  <td>{{ p.apellido }}</td>
                  <td>{{ p.email }}</td>
                  <td>
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      color="primary"
                      @click="openEmbeddingDialog(p)"
                    >
                      <v-icon>mdi-face-recognition</v-icon>
                      <v-tooltip activator="parent">Cargar embeddings</v-tooltip>
                    </v-btn>
                    <v-btn
                      icon
                      variant="text"
                      size="small"
                      color="warning"
                      @click="openEditDialog(p)"
                    >
                      <v-icon>mdi-pencil</v-icon>
                      <v-tooltip activator="parent">Editar</v-tooltip>
                    </v-btn>
                    <v-btn
                      v-if="auth.isAdmin"
                      icon
                      variant="text"
                      size="small"
                      color="error"
                      @click="openDeleteDialog(p)"
                    >
                      <v-icon>mdi-delete</v-icon>
                      <v-tooltip activator="parent">Eliminar</v-tooltip>
                    </v-btn>
                  </td>
                </tr>
              </tbody>
            </v-table>
            <p v-else class="text-grey text-caption">No hay personas registradas.</p>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- Panel de detalle -->
      <v-col cols="12" md="5">
        <v-card class="pa-4">

          <template v-if="selectedPerson">

            <v-card-title class="d-flex justify-space-between align-center">
              Detalle

              <v-btn
                variant="text"
                size="small"
                prepend-icon="mdi-close"
                @click="selectedPerson = null"
              >
                Cerrar
              </v-btn>
            </v-card-title>

            <v-card-text>
              <p class="mb-1"><strong>ID:</strong> {{ selectedPerson.personId }}</p>
              <p class="mb-1"><strong>Nombre:</strong> {{ selectedPerson.nombre }} {{ selectedPerson.apellido }}</p>
              <p class="mb-1"><strong>Email:</strong> {{ selectedPerson.email }}</p>

              <template v-if="selectedPerson.extra && Object.keys(selectedPerson.extra).length > 0">
                <v-divider class="my-3" />

                <p class="mb-2"><strong>Información adicional</strong></p>

                <v-chip
                  v-for="(value, key) in selectedPerson.extra"
                  :key="key"
                  class="mr-2 mb-2"
                  color="primary"
                  variant="tonal"
                >
                  {{ key }}: {{ value }}
                </v-chip>

              </template>

            </v-card-text>

          </template>

          <template v-else>

            <div class="text-center py-10">

              <v-icon
                size="70"
                color="grey-lighten-1"
                class="mb-4"
              >
                mdi-account-search
              </v-icon>

              <div class="text-h6 mb-2">
                Ninguna persona seleccionada
              </div>

              <div class="text-grey">
                Seleccioná una persona de la lista para ver sus datos.
              </div>

            </div>

          </template>

        </v-card>
      </v-col>
    </v-row>

    <!-- crear / editar persona -->
    <v-dialog v-model="personDialog" max-width="500">
      <v-card>
        <v-card-title>{{ editingPerson ? 'Editar persona' : 'Nueva persona' }}</v-card-title>
        <v-card-text>
          <v-text-field v-model="form.nombre" label="Nombre" variant="outlined" class="mb-3" />
          <v-text-field v-model="form.apellido" label="Apellido" variant="outlined" class="mb-3" />
          <v-text-field v-model="form.email" label="Email" variant="outlined" class="mb-3" />
          <v-alert v-if="formError" type="error" class="mb-3">{{ formError }}</v-alert>
          <v-alert v-if="formSuccess" type="success" class="mb-3">{{ formSuccess }}</v-alert>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="personDialog = false">Cancelar</v-btn>
          <v-btn
            color="primary"
            :loading="loadingForm"
            :disabled="!form.nombre || !form.apellido || !form.email"
            @click="handleSavePerson"
          >
            {{ editingPerson ? 'Guardar cambios' : 'Crear' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- confirmar eliminación -->
    <v-dialog v-model="deleteDialog" max-width="400">
      <v-card>
        <v-card-title>Eliminar persona</v-card-title>
        <v-card-text>
          ¿Confirmas que querés eliminar a <strong>{{ personToDelete?.nombre }} {{ personToDelete?.apellido }}</strong>?
          Esta acción no se puede deshacer.
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="deleteDialog = false">Cancelar</v-btn>
          <v-btn color="error" :loading="loadingDelete" @click="handleDelete">Eliminar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- cargar embeddings -->
    <v-dialog v-model="embeddingDialog" max-width="500">
      <v-card>
        <v-card-title>Cargar embeddings — {{ embeddingTarget?.nombre }} {{ embeddingTarget?.apellido }}</v-card-title>
        <v-card-text>
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
          <v-spacer />
          <v-btn variant="text" @click="embeddingDialog = false">Cancelar</v-btn>
          <v-btn
            color="secondary"
            :loading="loadingEmbedding"
            :disabled="!embeddingFiles || embeddingFiles.length === 0"
            @click="handleEmbeddings"
          >
            Generar embeddings
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { api } from '@/services/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

// --- Lista ---
const persons = ref([])
const loadingList = ref(false)
const listError = ref('')
const selectedPerson = ref(null)

async function loadPersons() {
  loadingList.value = true
  listError.value = ''
  try {
    const response = await api.get('/persons')
    if (!response.ok) throw new Error('Error al cargar personas')
    persons.value = await response.json()
  } catch (e) {
    listError.value = e.message
  } finally {
    loadingList.value = false
  }
}


function selectPerson(person) {
  if (selectedPerson.value?.personId === person.personId) {
    selectedPerson.value = null
  } else {
    selectedPerson.value = person
  }
}

onMounted(loadPersons)

// --- Crear / Editar ---
const personDialog = ref(false)
const editingPerson = ref(null)
const form = ref({ nombre: '', apellido: '', email: '' })
const loadingForm = ref(false)
const formError = ref('')
const formSuccess = ref('')

function openCreateDialog() {
  editingPerson.value = null
  form.value = { nombre: '', apellido: '', email: '' }
  formError.value = ''
  formSuccess.value = ''
  personDialog.value = true
}

function openEditDialog(person) {
  editingPerson.value = person
  form.value = { nombre: person.nombre, apellido: person.apellido, email: person.email }
  formError.value = ''
  formSuccess.value = ''
  selectedPerson.value = person
  personDialog.value = true
}

async function handleSavePerson() {
  formError.value = ''
  formSuccess.value = ''
  loadingForm.value = true
  try {
    let response
    if (editingPerson.value) {
      response = await api.put(`/persons/${editingPerson.value.personId}`, form.value)
    } else {
      response = await api.post('/persons', form.value)
    }
    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.detail || 'Error al guardar')
    }
    const data = await response.json()
    formSuccess.value = editingPerson.value ? 'Persona actualizada' : `Persona creada con ID: ${data.personId}`
    await loadPersons()
    if (editingPerson.value) selectedPerson.value = data
    if (!editingPerson.value) setTimeout(() => { personDialog.value = false }, 1000)
  } catch (e) {
    formError.value = e.message
  } finally {
    loadingForm.value = false
  }
}

// --- Eliminar ---
const deleteDialog = ref(false)
const personToDelete = ref(null)
const loadingDelete = ref(false)

function openDeleteDialog(person) {
  personToDelete.value = person
  deleteDialog.value = true
}

async function handleDelete() {
  loadingDelete.value = true
  try {
    const response = await api.delete(`/persons/${personToDelete.value.personId}`)
    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.detail || 'Error al eliminar')
    }
    deleteDialog.value = false
    if (selectedPerson.value?.personId === personToDelete.value.personId) {
      selectedPerson.value = null
    }
    await loadPersons()
  } catch (e) {
    listError.value = e.message
  } finally {
    loadingDelete.value = false
  }
}

// --- Embeddings ---
const embeddingDialog = ref(false)
const embeddingTarget = ref(null)
const embeddingFiles = ref([])
const loadingEmbedding = ref(false)
const embeddingError = ref('')
const embeddingSuccess = ref('')

function openEmbeddingDialog(person) {
  embeddingTarget.value = person
  embeddingFiles.value = []
  embeddingError.value = ''
  embeddingSuccess.value = ''
  embeddingDialog.value = true
}

async function handleEmbeddings() {
  embeddingError.value = ''
  embeddingSuccess.value = ''
  loadingEmbedding.value = true
  try {
    const toBase64 = (file) =>
      new Promise((resolve, reject) => {
        const reader = new FileReader()
        reader.onload = () => resolve(reader.result.split(',')[1])
        reader.onerror = reject
        reader.readAsDataURL(file)
      })

    const files = Array.isArray(embeddingFiles.value) ? embeddingFiles.value : [embeddingFiles.value]
    const images = await Promise.all(files.map(toBase64))

    const response = await api.post(`/persons/${embeddingTarget.value.personId}/embeddings`, { images })
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

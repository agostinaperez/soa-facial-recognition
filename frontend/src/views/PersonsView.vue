<template>
  <v-container class="py-6">
    <div class="text-h6 font-weight-bold mb-1">Personas registradas</div>
    <div class="text-medium-emphasis text-body-2 mb-5"></div>

    <v-row>
      <v-col cols="12" md="7">
        <v-card flat border color="surface-variant">
          <v-card-text class="pa-0">
            <div class="d-flex align-center justify-space-between pa-4">
              <div class="text-caption text-medium-emphasis text-uppercase">
                {{ persons.length }} persona{{ persons.length !== 1 ? 's' : '' }}
              </div>
              <v-btn color="primary" variant="flat" size="small" prepend-icon="mdi-plus" @click="openCreateDialog">
                Nueva persona
              </v-btn>
            </div>

            <v-alert v-if="listError" type="error" variant="tonal" density="compact" class="mx-4 mb-3" :text="listError" />
            <v-progress-linear v-if="loadingList" indeterminate color="primary" />

            <v-table v-if="persons.length > 0" density="comfortable">
              <thead>
                <tr>
                  <th class="text-caption text-medium-emphasis">Nombre</th>
                  <th class="text-caption text-medium-emphasis">Email</th>
                  <th class="text-caption text-medium-emphasis text-right">Acciones</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="p in persons"
                  :key="p.personId"
                  @click="selectPerson(p)"
                  :class="{ 'selected-row': selectedPerson?.personId === p.personId }"
                  style="cursor: pointer"
                >
                  <td>
                    <div class="font-weight-medium">{{ p.nombre }} {{ p.apellido }}</div>
                  </td>
                  <td class="text-medium-emphasis text-body-2">{{ p.email }}</td>
                  <td class="text-right">
                    <v-btn icon variant="text" size="small" color="info" @click.stop="openEmbeddingDialog(p)">
                      <v-icon size="16">mdi-face-recognition</v-icon>
                      <v-tooltip activator="parent">Cargar embeddings</v-tooltip>
                    </v-btn>
                    <v-btn icon variant="text" size="small" color="primary" @click.stop="openEditDialog(p)">
                      <v-icon size="16">mdi-pencil-outline</v-icon>
                      <v-tooltip activator="parent">Editar</v-tooltip>
                    </v-btn>
                    <v-btn v-if="auth.isAdmin" icon variant="text" size="small" color="error" @click.stop="openDeleteDialog(p)">
                      <v-icon size="16">mdi-delete-outline</v-icon>
                      <v-tooltip activator="parent">Eliminar</v-tooltip>
                    </v-btn>
                  </td>
                </tr>
              </tbody>
            </v-table>

            <div v-else-if="!loadingList" class="text-center pa-8 text-medium-emphasis text-body-2">
              No hay personas registradas.
            </div>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="5">
        <v-card flat border color="surface-variant" style="min-height: 200px">
          <template v-if="selectedPerson">
            <v-card-text class="pa-5">
              <div class="d-flex align-center justify-space-between mb-4">
                <div class="text-caption text-medium-emphasis text-uppercase">Detalle</div>
                <v-btn variant="text" size="x-small" icon @click="selectedPerson = null">
                  <v-icon size="16">mdi-close</v-icon>
                </v-btn>
              </div>

              <div class="d-flex align-center mb-4">
                <v-avatar color="primary" size="40" class="mr-3">
                  <span class="text-body-2 font-weight-bold">
                    {{ selectedPerson.nombre[0] }}{{ selectedPerson.apellido[0] }}
                  </span>
                </v-avatar>
                <div>
                  <div class="font-weight-medium">{{ selectedPerson.nombre }} {{ selectedPerson.apellido }}</div>
                  <div class="text-caption text-medium-emphasis">{{ selectedPerson.email }}</div>
                </div>
              </div>

              <div class="text-caption text-medium-emphasis mb-1">ID</div>
              <div class="font-mono text-caption pa-2 rounded mb-4" style="background: rgba(255,255,255,0.05)">
                {{ selectedPerson.personId }}
              </div>

              <template v-if="selectedPerson.extra && Object.keys(selectedPerson.extra).length">
                <v-divider class="mb-3" />
                <div class="text-caption text-medium-emphasis mb-2">Info adicional</div>
                <v-chip
                  v-for="(value, key) in selectedPerson.extra"
                  :key="key"
                  size="small"
                  color="primary"
                  variant="tonal"
                  class="mr-1 mb-1"
                >
                  {{ key }}: {{ value }}
                </v-chip>
              </template>
            </v-card-text>
          </template>
          <template v-else>
            <div class="d-flex flex-column align-center justify-center pa-8" style="min-height: 200px">
              <v-icon size="40" color="medium-emphasis" class="mb-3">mdi-account-search-outline</v-icon>
              <div class="text-body-2 text-medium-emphasis">Seleccioná una persona</div>
            </div>
          </template>
        </v-card>
      </v-col>
    </v-row>

    <!-- Crear / Editar -->
    <v-dialog v-model="personDialog" max-width="480">
      <v-card color="surface">
        <v-card-title class="pa-5 pb-2 text-body-1 font-weight-bold">
          {{ editingPerson ? 'Editar persona' : 'Nueva persona' }}
        </v-card-title>
        <v-card-text class="pa-5">
          <v-text-field v-model="form.nombre" label="Nombre" variant="outlined" density="comfortable" class="mb-3" />
          <v-text-field v-model="form.apellido" label="Apellido" variant="outlined" density="comfortable" class="mb-3" />
          <v-text-field v-model="form.email" label="Email" variant="outlined" density="comfortable" />
          <v-alert v-if="formError" type="error" variant="tonal" density="compact" class="mt-3" :text="formError" />
          <v-alert v-if="formSuccess" type="success" variant="tonal" density="compact" class="mt-3" :text="formSuccess" />
        </v-card-text>
        <v-card-actions class="pa-5 pt-0">
          <v-spacer />
          <v-btn variant="text" size="small" @click="personDialog = false">Cancelar</v-btn>
          <v-btn
            color="primary"
            variant="flat"
            size="small"
            :loading="loadingForm"
            :disabled="!form.nombre || !form.apellido || !form.email"
            @click="handleSavePerson"
          >
            {{ editingPerson ? 'Guardar' : 'Crear' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Eliminar -->
    <v-dialog v-model="deleteDialog" max-width="400">
      <v-card color="surface">
        <v-card-title class="pa-5 pb-2 text-body-1 font-weight-bold">Eliminar persona</v-card-title>
        <v-card-text class="pa-5">
          ¿Eliminás a <strong>{{ personToDelete?.nombre }} {{ personToDelete?.apellido }}</strong>?
          Esta acción no se puede deshacer.
        </v-card-text>
        <v-card-actions class="pa-5 pt-0">
          <v-spacer />
          <v-btn variant="text" size="small" @click="deleteDialog = false">Cancelar</v-btn>
          <v-btn color="error" variant="flat" size="small" :loading="loadingDelete" @click="handleDelete">Eliminar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Embeddings -->
    <v-dialog v-model="embeddingDialog" max-width="480">
      <v-card color="surface">
        <v-card-title class="pa-5 pb-2 text-body-1 font-weight-bold">
          Cargar embeddings
        </v-card-title>
        <v-card-subtitle class="px-5 pb-2 text-medium-emphasis">
          {{ embeddingTarget?.nombre }} {{ embeddingTarget?.apellido }}
        </v-card-subtitle>
        <v-card-text class="pa-5">
          <v-file-input
            v-model="embeddingFiles"
            label="Imágenes faciales"
            accept="image/*"
            variant="outlined"
            density="comfortable"
            prepend-icon=""
            prepend-inner-icon="mdi-face-recognition"
            multiple
            :clearable="false"
          />
          <v-alert v-if="embeddingError" type="error" variant="tonal" density="compact" class="mt-3" :text="embeddingError" />
          <v-alert v-if="embeddingSuccess" type="success" variant="tonal" density="compact" class="mt-3" :text="embeddingSuccess" />
        </v-card-text>
        <v-card-actions class="pa-5 pt-0">
          <v-spacer />
          <v-btn variant="text" size="small" @click="embeddingDialog = false">Cancelar</v-btn>
          <v-btn
            color="secondary"
            variant="flat"
            size="small"
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
  selectedPerson.value = selectedPerson.value?.personId === person.personId ? null : person
}

onMounted(loadPersons)

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
    formSuccess.value = editingPerson.value ? 'Persona actualizada' : `Persona creada`
    await loadPersons()
    if (editingPerson.value) selectedPerson.value = data
    if (!editingPerson.value) setTimeout(() => { personDialog.value = false }, 800)
  } catch (e) {
    formError.value = e.message
  } finally {
    loadingForm.value = false
  }
}

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
    if (selectedPerson.value?.personId === personToDelete.value.personId) selectedPerson.value = null
    await loadPersons()
  } catch (e) {
    listError.value = e.message
  } finally {
    loadingDelete.value = false
  }
}

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
    const toBase64 = (file) => new Promise((resolve, reject) => {
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

<style scoped>
.selected-row {
  background: rgba(56, 139, 253, 0.08) !important;
}
.font-mono {
  font-family: 'Courier New', Courier, monospace;
}
</style>

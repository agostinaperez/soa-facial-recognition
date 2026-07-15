<template>
  <v-container class="py-6">
    <div class="text-h6 font-weight-bold mb-1">Usuarios</div>
    <div class="text-medium-emphasis text-body-2 mb-5">
      Alta de usuarios del sistema (usuario/contraseña + persona para reconocimiento facial)
    </div>

    <v-card flat border color="surface-variant">
      <v-card-text class="pa-0">
        <div class="d-flex align-center justify-space-between pa-4">
          <div class="text-caption text-medium-emphasis text-uppercase">
            {{ users.length }} usuario{{ users.length !== 1 ? 's' : '' }}
          </div>
          <v-btn color="primary" variant="flat" size="small" prepend-icon="mdi-plus" @click="openCreateDialog">
            Nuevo usuario
          </v-btn>
        </div>

        <v-alert v-if="listError" type="error" variant="tonal" density="compact" class="mx-4 mb-3" :text="listError" />
        <v-progress-linear v-if="loadingList" indeterminate color="primary" />

        <v-table v-if="users.length > 0" density="comfortable">
          <thead>
            <tr>
              <th class="text-caption text-medium-emphasis">Usuario</th>
              <th class="text-caption text-medium-emphasis">Email</th>
              <th class="text-caption text-medium-emphasis">Roles</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="u in users" :key="u.id">
              <td class="font-weight-medium">{{ u.username }}</td>
              <td class="text-medium-emphasis text-body-2">{{ u.email }}</td>
              <td>
                <v-chip
                  v-for="r in u.roles"
                  :key="r"
                  size="small"
                  variant="tonal"
                  class="mr-1"
                >
                  {{ r }}
                </v-chip>
              </td>
            </tr>
          </tbody>
        </v-table>

        <div v-else-if="!loadingList" class="text-center pa-8 text-medium-emphasis text-body-2">
          No hay usuarios registrados.
        </div>
      </v-card-text>
    </v-card>

    <v-dialog v-model="createDialog" max-width="480">
      <v-card color="surface">
        <v-card-title class="pa-5 pb-2 text-body-1 font-weight-bold">Nuevo usuario</v-card-title>
        <v-card-text class="pa-5">
          <v-text-field v-model="form.username" label="Usuario" variant="outlined" density="comfortable" class="mb-3" />
          <v-text-field v-model="form.email" label="Email" variant="outlined" density="comfortable" class="mb-3" />
          <v-text-field v-model="form.password" label="Contraseña" type="password" variant="outlined" density="comfortable" class="mb-3" />
          <v-text-field v-model="form.nombre" label="Nombre" variant="outlined" density="comfortable" class="mb-3" />
          <v-text-field v-model="form.apellido" label="Apellido" variant="outlined" density="comfortable" class="mb-3" />
          <v-select
            v-model="form.roles"
            :items="['admin', 'operator', 'viewer']"
            label="Rol"
            variant="outlined"
            density="comfortable"
            multiple
            chips
          />
          <v-alert v-if="formError" type="error" variant="tonal" density="compact" class="mt-3" :text="formError" />
          <v-alert v-if="formSuccess" type="success" variant="tonal" density="compact" class="mt-3" :text="formSuccess" />
        </v-card-text>
        <v-card-actions class="pa-5 pt-0">
          <v-spacer />
          <v-btn variant="text" size="small" @click="createDialog = false">Cancelar</v-btn>
          <v-btn
            color="primary"
            variant="flat"
            size="small"
            :loading="loadingForm"
            :disabled="!formValid"
            @click="handleCreate"
          >
            Crear
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { api } from '@/services/api'

const users = ref([])
const loadingList = ref(false)
const listError = ref('')

async function loadUsers() {
  loadingList.value = true
  listError.value = ''
  try {
    const response = await api.get('/auth/users')
    if (!response.ok) throw new Error('Error al cargar usuarios')
    users.value = await response.json()
  } catch (e) {
    listError.value = e.message
  } finally {
    loadingList.value = false
  }
}

onMounted(loadUsers)

const createDialog = ref(false)
const form = ref({ username: '', email: '', password: '', nombre: '', apellido: '', roles: ['viewer'] })
const loadingForm = ref(false)
const formError = ref('')
const formSuccess = ref('')

const formValid = computed(() =>
  form.value.username && form.value.email && form.value.password &&
  form.value.nombre && form.value.apellido && form.value.roles.length > 0
)

function openCreateDialog() {
  form.value = { username: '', email: '', password: '', nombre: '', apellido: '', roles: ['viewer'] }
  formError.value = ''
  formSuccess.value = ''
  createDialog.value = true
}

async function handleCreate() {
  formError.value = ''
  formSuccess.value = ''
  loadingForm.value = true
  try {
    const response = await api.post('/auth/users', form.value)
    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.detail || 'Error al crear el usuario')
    }
    formSuccess.value = 'Usuario creado correctamente'
    await loadUsers()
    setTimeout(() => { createDialog.value = false }, 800)
  } catch (e) {
    formError.value = e.message
  } finally {
    loadingForm.value = false
  }
}
</script>

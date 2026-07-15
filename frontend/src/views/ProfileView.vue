<template>
  <v-container class="py-6">
    <div class="text-h6 font-weight-bold mb-1">Mi Perfil</div>
    <div class="text-medium-emphasis text-body-2 mb-5">
      Gestioná tu vínculo con reconocimiento facial y tus fotos de rostro
    </div>

    <v-row>
      <v-col cols="12" md="7">
        <v-card flat border color="surface-variant">
          <v-card-text class="pa-5">
            <div class="text-caption text-medium-emphasis text-uppercase mb-2">Cuenta</div>
            <div class="font-weight-medium mb-1">{{ auth.user?.preferred_username }}</div>
            <div class="text-body-2 text-medium-emphasis mb-4">{{ auth.user?.email }}</div>

            <v-progress-linear v-if="loadingMe" indeterminate color="primary" class="mb-4" />

            <template v-if="linkedPerson">
              <v-alert type="success" variant="tonal" density="compact" class="mb-4">
                Tu cuenta está vinculada a <strong>{{ linkedPerson.nombre }} {{ linkedPerson.apellido }}</strong>.
                Ya podés iniciar sesión con reconocimiento facial una vez que subas al menos una foto.
              </v-alert>

              <div class="text-caption text-medium-emphasis text-uppercase mb-2">Cámara</div>

              <div v-if="stage === 'idle'" class="d-flex flex-column align-center py-6">
                <v-icon size="40" color="medium-emphasis" class="mb-3">mdi-camera-outline</v-icon>
                <div class="text-body-2 text-medium-emphasis mb-2 text-center">
                  Activá la cámara para sacarte fotos de tu rostro
                </div>
              </div>

              <div v-show="stage === 'camera' || stage === 'preview'">
                <video
                  v-show="stage === 'camera'"
                  ref="videoRef"
                  autoplay
                  playsinline
                  muted
                  class="profile-media"
                />
                <img v-if="stage === 'preview' && capturedImage" :src="capturedImage" class="profile-media" />
              </div>
              <canvas ref="canvasRef" style="display: none" />

              <div class="d-flex mt-3" style="gap: 8px">
                <v-btn v-if="stage === 'idle'" color="primary" variant="flat" @click="startCamera">
                  Activar cámara
                </v-btn>
                <v-btn v-if="stage === 'camera'" color="primary" variant="flat" @click="takePhoto">
                  Tomar foto
                </v-btn>
                <template v-if="stage === 'preview'">
                  <v-btn variant="tonal" @click="retake">Volver a sacar foto</v-btn>
                  <v-btn color="secondary" variant="flat" @click="addToPending">Agregar a la lista</v-btn>
                </template>
              </div>

              <template v-if="pendingPhotos.length">
                <div class="text-caption text-medium-emphasis text-uppercase mt-4 mb-2">
                  {{ pendingPhotos.length }} foto{{ pendingPhotos.length !== 1 ? 's' : '' }} lista{{ pendingPhotos.length !== 1 ? 's' : '' }} para subir
                </div>
                <div class="d-flex flex-wrap mb-3" style="gap: 8px">
                  <div v-for="(p, i) in pendingPhotos" :key="i" class="pending-thumb">
                    <img :src="p.preview" />
                    <v-btn icon size="x-small" variant="flat" color="error" class="pending-thumb-remove" @click="removePending(i)">
                      <v-icon size="14">mdi-close</v-icon>
                    </v-btn>
                  </div>
                </div>
              </template>

              <v-divider class="my-4" />

              <v-file-input
                v-model="embeddingFiles"
                label="O subí fotos desde tu dispositivo"
                accept="image/*"
                variant="outlined"
                density="comfortable"
                prepend-icon=""
                prepend-inner-icon="mdi-image-outline"
                multiple
                :clearable="false"
              />

              <v-alert v-if="embeddingError" type="error" variant="tonal" density="compact" class="mt-3" :text="embeddingError" />
              <v-alert v-if="embeddingSuccess" type="success" variant="tonal" density="compact" class="mt-3" :text="embeddingSuccess" />

              <v-btn
                block
                color="primary"
                variant="flat"
                class="mt-4"
                :loading="loadingEmbedding"
                :disabled="pendingPhotos.length === 0 && (!embeddingFiles || embeddingFiles.length === 0)"
                @click="handleUpload"
              >
                Subir fotos
              </v-btn>
            </template>

            <template v-else-if="!loadingMe">
              <v-alert type="info" variant="tonal" density="compact" class="mb-4">
                Todavía no vinculaste tu cuenta con un registro facial.
              </v-alert>
              <v-alert v-if="linkError" type="error" variant="tonal" density="compact" class="mb-4" :text="linkError" />
              <v-btn color="primary" variant="flat" :loading="loadingLink" @click="handleLink">
                Vincular mi cuenta
              </v-btn>
            </template>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { nextTick, onMounted, onUnmounted, ref } from 'vue'
import { api } from '@/services/api'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()

const loadingMe = ref(false)
const linkedPerson = ref(null)

async function loadMe() {
  loadingMe.value = true
  try {
    await auth.fetchUser()
    linkedPerson.value = auth.user?.linked_person || null
  } finally {
    loadingMe.value = false
  }
}

onMounted(loadMe)

const loadingLink = ref(false)
const linkError = ref('')

async function handleLink() {
  linkError.value = ''
  loadingLink.value = true
  try {
    const response = await api.post('/auth/link-keycloak', {})
    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.detail || 'No se pudo vincular tu cuenta')
    }
    await loadMe()
  } catch (e) {
    linkError.value = e.message
  } finally {
    loadingLink.value = false
  }
}

const videoRef = ref(null)
const canvasRef = ref(null)
let stream = null

const stage = ref('idle') // idle | camera | preview
const capturedImage = ref('')
const pendingPhotos = ref([]) // [{ base64, preview }]

async function startCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true })
    stage.value = 'camera'
    await nextTick()
    if (videoRef.value) {
      videoRef.value.srcObject = stream
    }
  } catch (e) {
    embeddingError.value = 'No se pudo acceder a la cámara. Revisá los permisos del navegador.'
  }
}

function takePhoto() {
  const video = videoRef.value
  const canvas = canvasRef.value
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight
  canvas.getContext('2d').drawImage(video, 0, 0)
  capturedImage.value = canvas.toDataURL('image/jpeg')
  stage.value = 'preview'
}

function retake() {
  capturedImage.value = ''
  stage.value = 'camera'
}

function addToPending() {
  pendingPhotos.value.push({
    base64: capturedImage.value.split(',')[1],
    preview: capturedImage.value
  })
  capturedImage.value = ''
  stage.value = 'camera'
}

function removePending(index) {
  pendingPhotos.value.splice(index, 1)
}

function stopCamera() {
  if (stream) {
    stream.getTracks().forEach((t) => t.stop())
    stream = null
  }
}

onUnmounted(stopCamera)

const embeddingFiles = ref([])
const loadingEmbedding = ref(false)
const embeddingError = ref('')
const embeddingSuccess = ref('')

async function handleUpload() {
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
    const files = Array.isArray(embeddingFiles.value) ? embeddingFiles.value : [embeddingFiles.value].filter(Boolean)
    const fromFiles = await Promise.all(files.map(toBase64))
    const images = [...pendingPhotos.value.map((p) => p.base64), ...fromFiles]

    const response = await api.post(`/persons/${linkedPerson.value.personId}/embeddings`, { images })
    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.detail || 'Error al subir las fotos')
    }
    const data = await response.json()
    embeddingSuccess.value = data.message
    pendingPhotos.value = []
    embeddingFiles.value = []
  } catch (e) {
    embeddingError.value = e.message
  } finally {
    loadingEmbedding.value = false
  }
}
</script>

<style scoped>
.profile-media {
  width: 100%;
  max-height: 300px;
  object-fit: cover;
  border-radius: 8px;
  background: #000;
}
.pending-thumb {
  position: relative;
  width: 64px;
  height: 64px;
}
.pending-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 6px;
}
.pending-thumb-remove {
  position: absolute;
  top: -6px;
  right: -6px;
}
</style>

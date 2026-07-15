<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="4">

        <div class="text-center mb-6">
          <v-icon size="48" color="primary" class="mb-3">mdi-shield-lock</v-icon>
          <div class="text-h5 font-weight-bold">Iniciar Sesión</div>
          <div class="text-h8 font-weight">-</div>
          <div class="text-h8 font-weight">Sistema de Detección y Reconocimiento</div>
        </div>

        <v-btn-toggle
          v-model="mode"
          mandatory
          color="primary"
          variant="outlined"
          divided
          class="d-flex mb-4"
        >
          <v-btn value="password" class="flex-grow-1">
            <v-icon start size="18">mdi-account-outline</v-icon>
            Usuario y contraseña
          </v-btn>
          <v-btn value="face" class="flex-grow-1">
            <v-icon start size="18">mdi-face-recognition</v-icon>
            Reconocimiento facial
          </v-btn>
        </v-btn-toggle>

        <v-card v-if="mode === 'password'" flat border color="surface-variant" class="pa-2">
          <v-card-text>
            <v-text-field
              v-model="username"
              label="Usuario"
              prepend-inner-icon="mdi-account-outline"
              variant="outlined"
              density="comfortable"
              class="mb-3"
              autofocus
              @keyup.enter="handleLogin"
            />
            <v-text-field
              v-model="password"
              label="Contraseña"
              prepend-inner-icon="mdi-lock-outline"
              type="password"
              variant="outlined"
              density="comfortable"
              @keyup.enter="handleLogin"
            />
            <v-alert
              v-if="error"
              type="error"
              variant="tonal"
              density="compact"
              class="mt-3"
              :text="error"
            />
          </v-card-text>
          <v-card-actions class="px-4 pb-4">
            <v-btn
              block
              color="primary"
              size="large"
              variant="flat"
              :loading="loading"
              @click="handleLogin"
            >
              Ingresar
            </v-btn>
          </v-card-actions>
        </v-card>

        <v-card v-else flat border color="surface-variant" class="pa-2">
          <v-card-text>
            <div v-if="stage === 'idle'" class="d-flex flex-column align-center py-6">
              <v-icon size="40" color="medium-emphasis" class="mb-3">mdi-camera-outline</v-icon>
              <div class="text-body-2 text-medium-emphasis mb-2 text-center">
                Activá la cámara para iniciar sesión con tu rostro
              </div>
            </div>

            <div v-show="stage === 'camera' || stage === 'preview' || stage === 'loading'">
              <video
                v-show="stage === 'camera'"
                ref="videoRef"
                autoplay
                playsinline
                muted
                class="face-login-media"
              />
              <img v-if="stage !== 'camera' && capturedImage" :src="capturedImage" class="face-login-media" />
            </div>
            <canvas ref="canvasRef" style="display: none" />

            <v-alert v-if="error" type="error" variant="tonal" density="compact" :text="error" class="mt-4" />
          </v-card-text>
          <v-card-actions class="px-4 pb-4">
            <v-btn v-if="stage === 'idle'" block color="primary" variant="flat" size="large" @click="startCamera">
              Activar cámara
            </v-btn>
            <v-btn v-else-if="stage === 'camera'" block color="primary" variant="flat" size="large" @click="takePhoto">
              Tomar foto
            </v-btn>
            <template v-else-if="stage === 'preview'">
              <v-btn variant="tonal" @click="retake">Volver a sacar foto</v-btn>
              <v-spacer />
              <v-btn color="primary" variant="flat" @click="handleFaceLogin">Ingresar</v-btn>
            </template>
            <v-btn v-else-if="stage === 'loading'" block color="primary" variant="flat" size="large" loading disabled>
              Verificando rostro...
            </v-btn>
          </v-card-actions>
        </v-card>

      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { nextTick, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const mode = ref('password')

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    router.push('/detections')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}

const videoRef = ref(null)
const canvasRef = ref(null)
let stream = null

const stage = ref('idle') // idle | camera | preview | loading
const capturedImage = ref('')

async function startCamera() {
  error.value = ''
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: true })
    stage.value = 'camera'
    await nextTick()
    if (videoRef.value) {
      videoRef.value.srcObject = stream
    }
  } catch (e) {
    error.value = 'No se pudo acceder a la cámara. Revisá los permisos del navegador.'
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
  error.value = ''
  stage.value = 'camera'
}

async function handleFaceLogin() {
  error.value = ''
  stage.value = 'loading'
  try {
    const base64 = capturedImage.value.split(',')[1]
    await auth.loginWithFace(base64)
    stopCamera()
    router.push('/detections')
  } catch (e) {
    error.value = e.message
    stage.value = 'preview'
  }
}

function stopCamera() {
  if (stream) {
    stream.getTracks().forEach((t) => t.stop())
    stream = null
  }
}

watch(mode, (value) => {
  error.value = ''
  if (value === 'password') {
    stopCamera()
    stage.value = 'idle'
    capturedImage.value = ''
  }
})

onUnmounted(stopCamera)
</script>

<style scoped>
.face-login-media {
  width: 100%;
  max-height: 280px;
  object-fit: cover;
  border-radius: 8px;
  background: #000;
}
</style>

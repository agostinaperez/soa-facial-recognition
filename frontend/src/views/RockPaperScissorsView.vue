<template>
  <v-container class="py-6">
    <div class="text-h6 font-weight-bold mb-1">Piedra, Papel o Tijera</div>
    <div class="text-medium-emphasis text-body-2 mb-5">Sacate una foto haciendo un gesto y jugá contra la PC</div>

    <v-row>
      <v-col cols="12" md="5">
        <v-card flat border color="surface-variant">
          <v-card-text class="pa-5">
            <div class="text-caption text-medium-emphasis text-uppercase mb-2">Cámara</div>

            <div v-if="stage === 'idle'" class="d-flex flex-column align-center py-8">
              <v-icon size="48" color="medium-emphasis" class="mb-3">mdi-camera-outline</v-icon>
              <div class="text-body-2 text-medium-emphasis mb-4 text-center">
                Activá la cámara para sacarte una foto de tu gesto
              </div>
            </div>

            <div v-show="stage === 'camera' || stage === 'preview' || stage === 'loading'">
              <video
                v-show="stage === 'camera'"
                ref="videoRef"
                autoplay
                playsinline
                muted
                class="rps-media"
              />
              <img v-if="stage !== 'camera' && capturedImage" :src="capturedImage" class="rps-media" />
            </div>
            <canvas ref="canvasRef" style="display: none" />

            <v-alert v-if="error" type="error" variant="tonal" density="compact" :text="error" class="mt-4" />
          </v-card-text>
          <v-card-actions class="px-5 pb-5">
            <v-btn v-if="stage === 'idle'" block color="primary" variant="flat" size="large" @click="startCamera">
              Activar cámara
            </v-btn>
            <v-btn v-else-if="stage === 'camera'" block color="primary" variant="flat" size="large" @click="takePhoto">
              Tomar foto
            </v-btn>
            <template v-else-if="stage === 'preview'">
              <v-btn variant="tonal" @click="retake">Volver a sacar foto</v-btn>
              <v-spacer />
              <v-btn color="primary" variant="flat" @click="play">Jugar</v-btn>
            </template>
            <v-btn v-else-if="stage === 'loading'" block color="primary" variant="flat" size="large" loading disabled>
              Jugando...
            </v-btn>
            <v-btn v-else-if="stage === 'result'" block color="primary" variant="flat" size="large" @click="playAgain">
              Jugar de nuevo
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>

      <v-col cols="12" md="7" v-if="result !== null">
        <v-card flat border color="surface-variant">
          <v-card-text class="pa-5">
            <div class="d-flex align-center mb-4">
              <v-icon :color="resultColor" size="20" class="mr-2">{{ resultIcon }}</v-icon>
              <span class="text-body-2 font-weight-medium" :class="`text-${resultColor}`">{{ resultLabel }}</span>
            </div>

            <v-row class="mb-4">
              <v-col cols="6">
                <div class="text-caption text-medium-emphasis mb-1">Tu jugada</div>
                <div class="text-h6 font-weight-bold">{{ translateGesture(result.gesture) }}</div>
              </v-col>
              <v-col cols="6">
                <div class="text-caption text-medium-emphasis mb-1">Jugada de la PC</div>
                <div class="text-h6 font-weight-bold">{{ translateGesture(result.computer_choice) }}</div>
              </v-col>
            </v-row>

            <div class="text-caption text-medium-emphasis mb-2">Confianza de detección</div>
            <div class="d-flex align-center gap-3">
              <v-progress-linear
                :model-value="result.confidence * 100"
                :color="resultColor"
                bg-color="surface"
                height="8"
                rounded
                class="flex-grow-1"
              />
              <span class="text-body-2 font-weight-bold" :class="`text-${resultColor}`" style="min-width: 44px">
                {{ (result.confidence * 100).toFixed(1) }}%
              </span>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { computed, nextTick, onUnmounted, ref } from 'vue'
import { api } from '@/services/api'

const videoRef = ref(null)
const canvasRef = ref(null)
let stream = null

const stage = ref('idle') // idle | camera | preview | loading | result
const capturedImage = ref('')
const error = ref('')
const result = ref(null)

const GESTURE_LABELS = { Rock: 'Piedra', Paper: 'Papel', Scissors: 'Tijera' }
function translateGesture(g) {
  return GESTURE_LABELS[g] || g
}

const RESULT_META = {
  win: { color: 'success', icon: 'mdi-trophy', label: 'Ganaste' },
  lose: { color: 'error', icon: 'mdi-emoticon-sad-outline', label: 'Perdiste' },
  tie: { color: 'warning', icon: 'mdi-handshake-outline', label: 'Empate' },
}
const resultColor = computed(() => RESULT_META[result.value?.result]?.color || 'medium-emphasis')
const resultIcon = computed(() => RESULT_META[result.value?.result]?.icon || 'mdi-help-circle-outline')
const resultLabel = computed(() => RESULT_META[result.value?.result]?.label || '')

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

async function play() {
  error.value = ''
  stage.value = 'loading'
  try {
    const base64 = capturedImage.value.split(',')[1]
    const response = await api.post('/rps/play', { image: base64 })
    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.detail || 'Error al procesar la jugada')
    }
    result.value = await response.json()
    stage.value = 'result'
  } catch (e) {
    error.value = e.message
    stage.value = 'preview'
  }
}

function playAgain() {
  result.value = null
  capturedImage.value = ''
  error.value = ''
  stage.value = stream ? 'camera' : 'idle'
}

function stopCamera() {
  if (stream) {
    stream.getTracks().forEach((t) => t.stop())
    stream = null
  }
}

onUnmounted(stopCamera)
</script>

<style scoped>
.rps-media {
  width: 100%;
  max-height: 320px;
  object-fit: cover;
  border-radius: 8px;
  background: #000;
}
</style>

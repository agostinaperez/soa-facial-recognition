import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/LoginView.vue')
  },
  {
    path: '/',
    redirect: '/detections'
  },
  {
    path: '/detections',
    name: 'detections',
    component: () => import('@/views/DetectionView.vue'),
    meta: { requiresAuth: true, requiresOperator: true }
  },
  {
    path: '/search',
    name: 'search',
    component: () => import('@/views/SearchView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/persons',
    name: 'persons',
    component: () => import('@/views/PersonsView.vue'),
    meta: { requiresAuth: true, requiresOperator: true }
  },
  {
    path: '/recognition',
    name: 'recognition',
    component: () => import('@/views/RecognitionView.vue'),
    meta: { requiresAuth: true, requiresOperator: true }
  },
  {
    path: '/rps',
    name: 'rps',
    component: () => import('@/views/RockPaperScissorsView.vue'),
    meta: { requiresAuth: true }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from) => {
  const auth = useAuthStore()

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return '/login'
  }

  if (to.meta.requiresOperator && !auth.isOperator) {
    return '/search'
  }

  if (to.name === 'login' && auth.isAuthenticated) {
    return '/detections'
  }
})

export default router

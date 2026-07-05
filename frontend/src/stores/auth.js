import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const KEYCLOAK_URL = import.meta.env.VITE_KEYCLOAK_URL
const REALM = import.meta.env.VITE_KEYCLOAK_REALM
const CLIENT_ID = import.meta.env.VITE_KEYCLOAK_CLIENT_ID
const CLIENT_SECRET = import.meta.env.VITE_KEYCLOAK_CLIENT_SECRET

export const useAuthStore = defineStore('auth', () => {
    const token = ref(localStorage.getItem('token') || null)
    const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))

    const isAuthenticated = computed(() => !!token.value)
    const roles = computed(() => user.value?.roles || [])
    const isAdmin = computed(() => roles.value.includes('admin'))
    const isOperator = computed(() => roles.value.includes('admin') || roles.value.includes('operator'))
    const isViewer = computed(() => roles.value.includes('admin') || roles.value.includes('operator') || roles.value.includes('viewer'))

    async function login(username, password) {
        const response = await fetch(
        `${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/token`,
        {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({
            grant_type: 'password',
            client_id: CLIENT_ID,
            client_secret: CLIENT_SECRET,
            username,
            password
            })
        }
        )

        if (!response.ok) {
        throw new Error('Usuario o contraseña incorrectos')
        }

        const data = await response.json()
        token.value = data.access_token
        localStorage.setItem('token', data.access_token)

        await fetchUser()
    }

    async function fetchUser() {
        const response = await fetch(`${import.meta.env.VITE_API_URL}/auth/me`, {
            headers: { Authorization: `Bearer ${token.value}` }
        })

        if (!response.ok) {
            logout()
            throw new Error('No se pudo obtener el usuario')
        }

        const data = await response.json()
        user.value = data
        localStorage.setItem('user', JSON.stringify(user.value))
    }

    function logout() {
        token.value = null
        user.value = null
        localStorage.removeItem('token')
        localStorage.removeItem('user')
    }

    function isTokenExpired() {
        if (!token.value) return true
        try {
            const payload = JSON.parse(atob(token.value.split('.')[1]))
            return payload.exp * 1000 < Date.now()
        } catch {
            return true
        }
    }

    async function init() {
        if (token.value && isTokenExpired()) {
            logout()
        }
    }

    return { token, user, isAuthenticated, roles, isAdmin, isOperator, isViewer, login, logout, fetchUser, init }

})

import { useAuthStore } from '@/stores/auth'

const BASE_URL = import.meta.env.VITE_API_URL

async function request(method, path, body = null, isFormData = false) {
  const auth = useAuthStore()

  const headers = {
    Authorization: `Bearer ${auth.token}`
  }
  if (!isFormData) {
    headers['Content-Type'] = 'application/json'
  }

  const options = { method, headers }
  if (body) {
    options.body = isFormData ? body : JSON.stringify(body)
  }

  const response = await fetch(`${BASE_URL}${path}`, options)

  if (response.status === 401) {
    auth.logout()
    window.location.href = '/login'
    throw new Error('Sesión expirada')
  }

  return response
}

export const api = {
  get: (path) => request('GET', path),
  post: (path, body) => request('POST', path, body),
  postForm: (path, formData) => request('POST', path, formData, true),
  put: (path, body) => request('PUT', path, body),
  delete: (path) => request('DELETE', path),
}

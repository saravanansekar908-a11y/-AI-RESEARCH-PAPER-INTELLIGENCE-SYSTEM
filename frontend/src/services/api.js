import axios from 'axios'

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || '' })
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('research_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export const apiError = (error) => error?.response?.data?.detail || error?.message || 'Something went wrong. Please try again.'
export default api


import axios from 'axios'

// API Configuration
// Priority: Environment variable > Azure Web App
const API_BASE_URL = import.meta.env.VITE_API_URL ||
  'https://petinsure360-backend.azurewebsites.net/api' // Azure Web App deployment

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor for logging
api.interceptors.request.use(
  config => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  response => {
    console.log(`API Response: ${response.status}`, response.data)
    return response
  },
  error => {
    console.error('API Error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export default api

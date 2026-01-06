import axios from 'axios'

// API Configuration
// Priority: Environment variable > Azure Web App
const API_BASE_URL = import.meta.env.VITE_API_URL ||
  'https://petinsure360-backend.azurewebsites.net' // Azure Web App deployment

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

export default api

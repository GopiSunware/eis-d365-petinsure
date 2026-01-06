import { io } from 'socket.io-client'

// WebSocket Configuration
// Uses same base as API but without /api suffix
const API_BASE_URL = import.meta.env.VITE_API_URL ||
  'https://petinsure360-backend.azurewebsites.net'

// Remove /api suffix if present for WebSocket connection
const WS_URL = API_BASE_URL.replace(/\/api$/, '')

// Create Socket.IO client
const socket = io(WS_URL, {
  autoConnect: false,  // Don't connect automatically
  reconnection: true,
  reconnectionAttempts: 5,
  reconnectionDelay: 1000,
  timeout: 10000,
  transports: ['websocket', 'polling']
})

// Connection status
let isConnected = false

// Event handlers registry
const eventHandlers = new Map()

// Connect to WebSocket
export const connectSocket = () => {
  if (!isConnected) {
    socket.connect()
    console.log('Connecting to WebSocket:', WS_URL)
  }
}

// Disconnect from WebSocket
export const disconnectSocket = () => {
  if (isConnected) {
    socket.disconnect()
    console.log('Disconnected from WebSocket')
  }
}

// Subscribe to an event
export const subscribeToEvent = (event, handler) => {
  if (!eventHandlers.has(event)) {
    eventHandlers.set(event, new Set())
  }
  eventHandlers.get(event).add(handler)
  socket.on(event, handler)

  // Return unsubscribe function
  return () => {
    eventHandlers.get(event)?.delete(handler)
    socket.off(event, handler)
  }
}

// Socket event listeners
socket.on('connect', () => {
  isConnected = true
  console.log('WebSocket connected:', socket.id)
})

socket.on('disconnect', (reason) => {
  isConnected = false
  console.log('WebSocket disconnected:', reason)
})

socket.on('connect_error', (error) => {
  console.warn('WebSocket connection error:', error.message)
})

socket.on('connected', (data) => {
  console.log('Server welcome:', data.message)
})

// Real-time event types for BI Dashboard
export const BI_EVENTS = {
  CUSTOMER_CREATED: 'customer_created',
  PET_ADDED: 'pet_added',
  POLICY_CREATED: 'policy_created',
  CLAIM_SUBMITTED: 'claim_submitted',
  CLAIM_STATUS_UPDATE: 'claim_status_update'
}

// Get connection status
export const getConnectionStatus = () => ({
  isConnected,
  socketId: socket.id,
  url: WS_URL
})

export default socket

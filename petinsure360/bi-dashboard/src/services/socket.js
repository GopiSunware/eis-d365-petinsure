/**
 * WebSocket Service for BI Dashboard
 * Native WebSocket implementation (replaces Socket.IO)
 * Uses API Gateway WebSocket API
 */

// WebSocket URL from environment variable
const WS_URL = import.meta.env.VITE_SOCKET_URL || 'ws://localhost:3002/ws';

// WebSocket instance
let ws = null;
let isConnected = false;
let reconnectAttempts = 0;
let reconnectTimeout = null;

// Event handlers registry
const eventHandlers = new Map();

// Connect to WebSocket
export const connectSocket = () => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    console.log('WebSocket already connected');
    return;
  }

  try {
    ws = new WebSocket(WS_URL);
    console.log('Connecting to WebSocket:', WS_URL);

    ws.onopen = () => {
      isConnected = true;
      reconnectAttempts = 0;
      console.log('WebSocket connected');

      // Trigger connect event handlers
      triggerEvent('connect', {});
    };

    ws.onclose = () => {
      isConnected = false;
      console.log('WebSocket disconnected');

      // Trigger disconnect event handlers
      triggerEvent('disconnect', {});

      // Attempt reconnection
      reconnectAttempts++;
      const backoffTime = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
      console.log(`Reconnecting in ${backoffTime/1000}s...`);
      reconnectTimeout = setTimeout(connectSocket, backoffTime);
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        const { type, data } = message;

        // Trigger event handlers for this message type
        triggerEvent(type, data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

  } catch (error) {
    console.error('Error creating WebSocket:', error);
  }
};

// Disconnect from WebSocket
export const disconnectSocket = () => {
  if (reconnectTimeout) {
    clearTimeout(reconnectTimeout);
    reconnectTimeout = null;
  }

  if (ws) {
    ws.close();
    ws = null;
  }

  isConnected = false;
  console.log('Disconnected from WebSocket');
};

// Subscribe to an event
export const subscribeToEvent = (event, handler) => {
  if (!eventHandlers.has(event)) {
    eventHandlers.set(event, new Set());
  }
  eventHandlers.get(event).add(handler);

  // Return unsubscribe function
  return () => {
    eventHandlers.get(event)?.delete(handler);
  };
};

// Trigger event handlers
const triggerEvent = (event, data) => {
  const handlers = eventHandlers.get(event) || new Set();
  handlers.forEach(handler => {
    try {
      handler(data);
    } catch (error) {
      console.error(`Error in event handler for ${event}:`, error);
    }
  });
};

// Real-time event types for BI Dashboard
export const BI_EVENTS = {
  CUSTOMER_CREATED: 'customer_created',
  PET_ADDED: 'pet_added',
  POLICY_CREATED: 'policy_created',
  CLAIM_SUBMITTED: 'claim_submitted',
  CLAIM_STATUS_UPDATE: 'claim_status_update'
};

// Get connection status
export const getConnectionStatus = () => ({
  isConnected,
  url: WS_URL
});

// Send message
export const sendMessage = (action, data = {}) => {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ action, ...data }));
  } else {
    console.warn('WebSocket is not connected. Cannot send message.');
  }
};

export default {
  connectSocket,
  disconnectSocket,
  subscribeToEvent,
  getConnectionStatus,
  sendMessage,
  BI_EVENTS
};

import { useEffect, useRef, useState } from 'react';

/**
 * Custom hook for managing WebSocket connections
 * Replaces Socket.IO with native WebSocket
 */
export function useWebSocket(url) {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef(null);
  const eventHandlers = useRef(new Map());
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);

  const connect = () => {
    try {
      const ws = new WebSocket(url);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        reconnectAttempts.current = 0;

        // Trigger 'connect' event handlers
        const connectHandlers = eventHandlers.current.get('connect') || [];
        connectHandlers.forEach(handler => handler());
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        wsRef.current = null;

        // Trigger 'disconnect' event handlers
        const disconnectHandlers = eventHandlers.current.get('disconnect') || [];
        disconnectHandlers.forEach(handler => handler());

        // Attempt reconnection with exponential backoff
        reconnectAttempts.current++;
        const backoffTime = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
        console.log(`Reconnecting in ${backoffTime/1000}s...`);
        reconnectTimeoutRef.current = setTimeout(connect, backoffTime);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log('Received WebSocket message:', message);

          // Message format: { type: 'event_name', data: {...} }
          const { type, data } = message;

          // Trigger event handlers for this message type
          const handlers = eventHandlers.current.get(type) || [];
          handlers.forEach(handler => handler(data));
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Error creating WebSocket:', error);
    }
  };

  const disconnect = () => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  };

  const on = (eventName, handler) => {
    const handlers = eventHandlers.current.get(eventName) || [];
    handlers.push(handler);
    eventHandlers.current.set(eventName, handlers);
  };

  const off = (eventName, handler) => {
    if (!handler) {
      // Remove all handlers for this event
      eventHandlers.current.delete(eventName);
    } else {
      // Remove specific handler
      const handlers = eventHandlers.current.get(eventName) || [];
      const filtered = handlers.filter(h => h !== handler);
      if (filtered.length > 0) {
        eventHandlers.current.set(eventName, filtered);
      } else {
        eventHandlers.current.delete(eventName);
      }
    }
  };

  const send = (action, data = {}) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ action, ...data }));
    } else {
      console.warn('WebSocket is not connected. Cannot send message.');
    }
  };

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, []);

  return {
    isConnected,
    connect,
    disconnect,
    on,
    off,
    send
  };
}

/**
 * Chat API Service
 * Uses the shared Claims Data API for chat functionality
 */

// Chat API uses the shared claims data API
const CHAT_API_BASE = import.meta.env.VITE_CLAIMS_API_URL || 'http://localhost:8000';

export const chatApi = {
  // Get available AI chat providers
  async getChatProviders() {
    const response = await fetch(`${CHAT_API_BASE}/api/chat/providers`);
    if (!response.ok) {
      throw new Error('Failed to fetch chat providers');
    }
    return response.json();
  },

  // Check if chat is available
  async getChatStatus() {
    const response = await fetch(`${CHAT_API_BASE}/api/chat/status`);
    if (!response.ok) {
      throw new Error('Failed to fetch chat status');
    }
    return response.json();
  },

  // Send chat message with optional screenshot and context
  async sendChatMessage(provider, messages, screenshot = null, appContext = null) {
    // Debug logging - show what's being sent
    console.group('🚀 Chat API Request');
    console.log('Provider:', provider);
    console.log('Messages:', messages);
    console.log('App Context:', appContext);
    if (screenshot) {
      const sizeKB = Math.round((screenshot.length * 3 / 4) / 1024);
      console.log(`Screenshot: ✅ Included (${sizeKB}KB)`);
      // Store globally for easy access
      window.__lastChatScreenshot = screenshot;
      console.log('📷 To view screenshot, run in console: window.open(window.__lastChatScreenshot)');
    } else {
      console.log('Screenshot: ❌ Not captured');
    }
    console.groupEnd();

    const response = await fetch(`${CHAT_API_BASE}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        provider,
        messages,
        screenshot,
        appContext
      })
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.message || error.detail || 'Failed to send chat message');
    }

    return response.json();
  }
};

export default chatApi;

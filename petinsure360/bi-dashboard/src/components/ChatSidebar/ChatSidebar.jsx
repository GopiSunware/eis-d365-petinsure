import { useState, useEffect, useRef, useCallback } from 'react';
import { chatApi } from '../../services/chatApi';
import { buildChatContext } from '../../services/chatContext';
import { useScreenshot } from '../../hooks/useScreenshot';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import ProviderSelector from './ProviderSelector';
import TokenUsage from './TokenUsage';

// Dynamic greeting based on user status and role
const getInitialMessage = (customerData, recentActivity, portalType = 'customer') => {
  const timeOfDay = new Date().getHours();
  let greeting = timeOfDay < 12 ? 'Good morning' : timeOfDay < 17 ? 'Good afternoon' : 'Good evening';

  // BI Dashboard / Analyst greeting
  if (portalType === 'bi-dashboard' || customerData?.role === 'analyst') {
    const name = customerData?.first_name || 'Analyst';
    let content = `${greeting}, ${name}! 👋 Welcome to **PetInsure360 BI Analytics Dashboard**.\n\n`;

    // Add unique recent activity (deduplicated)
    if (recentActivity && recentActivity.length > 0) {
      const uniqueActivity = [...new Set(recentActivity)].slice(0, 3);
      if (uniqueActivity.length > 0) {
        content += `**Recent Activity:**\n`;
        uniqueActivity.forEach(activity => {
          content += `• ${activity}\n`;
        });
        content += '\n';
      }
    }

    content += `I can help you with:\n`;
    content += `• 📊 Analyzing claims trends and KPIs\n`;
    content += `• 👥 Customer 360 insights\n`;
    content += `• ⚠️ Risk analysis and fraud detection\n`;
    content += `• 🔄 Pipeline monitoring (Rule Engine vs Agent)\n`;
    content += `• ⚙️ AI model configuration\n\n`;
    content += `What would you like to explore?`;
    return { role: 'assistant', content };
  }

  // EIS Admin Portal greeting
  if (portalType === 'eis-admin' || customerData?.role === 'admin') {
    const name = customerData?.first_name || 'Admin';
    let content = `${greeting}, ${name}! 👋 Welcome to **EIS Admin Portal**.\n\n`;

    content += `I can help you with:\n`;
    content += `• ⚙️ System configurations and settings\n`;
    content += `• 💰 Cost monitoring and optimization\n`;
    content += `• 📋 Audit logs and compliance\n`;
    content += `• 🔧 Service health and diagnostics\n`;
    content += `• 👤 User and role management\n\n`;
    content += `What would you like to manage?`;
    return { role: 'assistant', content };
  }

  // Customer Portal - logged in user
  if (customerData) {
    const name = customerData.first_name || customerData.full_name?.split(' ')[0] || 'there';
    let content = `${greeting}, ${name}! 👋 Welcome back to PetInsure360.\n\n`;

    // Add unique recent activity
    if (recentActivity && recentActivity.length > 0) {
      const uniqueActivity = [...new Set(recentActivity)].slice(0, 3);
      if (uniqueActivity.length > 0) {
        content += `**Recent Activity:**\n`;
        uniqueActivity.forEach(activity => {
          content += `• ${activity}\n`;
        });
        content += '\n';
      }
    }

    // Add offers for customers only
    content += `**Current Offers:**\n`;
    content += `• 🎉 Multi-pet discount: Save 5% on additional pets\n`;
    content += `• 💰 Annual payment: Get 10% off\n\n`;

    content += `How can I help you today? I can assist with quotes, claims, policy questions, or share our coverage plans!`;
    return { role: 'assistant', content };
  }

  // Not logged in - Customer Portal
  return {
    role: 'assistant',
    content: `${greeting}! 👋 Welcome to PetInsure360.\n\nI'm your AI assistant and I can help you:\n• Get a personalized insurance quote\n• Learn about our coverage plans\n• Answer questions about pet insurance\n\n**Special Offers:**\n• 🐾 Multi-pet discount: 5% off for 2+ pets\n• 🎖️ Military/Veteran discount: 5% off\n• 🏠 Shelter adoption discount: 5% off\n\nTo access all features, please **Register** or **Sign In**.\n\nWhat would you like to know?`
  };
};

const MIN_WIDTH = 320;
const MAX_WIDTH = 1200;
// Default to 20% of screen width
const getDefaultWidth = () => Math.max(MIN_WIDTH, Math.min(MAX_WIDTH, Math.floor(window.innerWidth * 0.20)));

export default function ChatSidebar({
  isOpen,
  onClose,
  onWidthChange,
  currentPage = 'dashboard',
  customerData = null,
  petData = null,
  claimData = null,
  recentActivity = [],
  portalType = 'customer' // 'customer', 'bi-dashboard', 'eis-admin'
}) {
  const [messages, setMessages] = useState(() => [getInitialMessage(customerData, recentActivity, portalType)]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [aiProvider, setAiProvider] = useState(null);
  const [aiProviders, setAiProviders] = useState(null);
  const [tokenUsage, setTokenUsage] = useState({ total: 0, cost: 0, history: [] });
  const [sidebarWidth, setSidebarWidth] = useState(getDefaultWidth);
  const [isResizing, setIsResizing] = useState(false);

  const messagesEndRef = useRef(null);
  const sidebarRef = useRef(null);
  const { captureScreenshot, isCapturing } = useScreenshot();

  // Handle resize drag
  const handleMouseDown = useCallback((e) => {
    e.preventDefault();
    setIsResizing(true);
  }, []);

  // Notify parent of width changes
  useEffect(() => {
    onWidthChange?.(sidebarWidth);
  }, [sidebarWidth, onWidthChange]);

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!isResizing) return;
      const newWidth = window.innerWidth - e.clientX;
      setSidebarWidth(Math.min(MAX_WIDTH, Math.max(MIN_WIDTH, newWidth)));
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'ew-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing]);

  // Fetch available AI providers on mount
  useEffect(() => {
    async function fetchProviders() {
      try {
        const data = await chatApi.getChatProviders();
        setAiProviders(data);
        // Set default provider
        if (data.default) {
          setAiProvider(data.default);
        }
      } catch (err) {
        console.error('Failed to fetch AI providers:', err);
        setError('Chat service unavailable');
      }
    }
    fetchProviders();
  }, []);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Handle sending a message
  const handleSend = async (content) => {
    if (!content.trim() || loading) return;

    // Add user message to chat
    const userMessage = { role: 'user', content };
    setMessages(prev => [...prev, userMessage]);
    setLoading(true);
    setError(null);

    try {
      // Capture screenshot of main content
      const screenshot = await captureScreenshot('main-content');

      // Build context from current app state
      const appContext = buildChatContext({
        currentPage,
        customerData,
        petData,
        claimData
      });

      // Prepare messages for API (exclude initial greeting and error messages)
      const apiMessages = messages
        .filter((msg, i) => i > 0 && !msg.isError) // Skip initial message and errors
        .concat(userMessage)
        .map(m => ({ role: m.role, content: m.content }));

      // Send to API
      const response = await chatApi.sendChatMessage(
        aiProvider,
        apiMessages,
        screenshot,
        appContext
      );

      // Add assistant response
      const assistantMessage = {
        role: 'assistant',
        content: response.response.content,
        provider: response.response.provider,
        model: response.response.model
      };
      setMessages(prev => [...prev, assistantMessage]);

      // Update token usage
      if (response.usage) {
        setTokenUsage(prev => ({
          total: prev.total + response.usage.totalTokens,
          cost: prev.cost + (response.estimatedCost || 0),
          history: [...prev.history, {
            tokens: response.usage.totalTokens,
            cost: response.estimatedCost || 0
          }]
        }));
      }

    } catch (err) {
      console.error('Chat error:', err);
      setError(err.message || 'Failed to get response');
      // Add error message to chat
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Sorry, I encountered an error: ${err.message}. Please try again.`,
        isError: true
      }]);
    } finally {
      setLoading(false);
    }
  };

  // Clear chat history
  const handleClear = () => {
    setMessages([getInitialMessage(customerData, recentActivity, portalType)]);
    setTokenUsage({ total: 0, cost: 0, history: [] });
    setError(null);
  };

  // Update greeting when customer data changes
  useEffect(() => {
    if (messages.length === 1) {
      setMessages([getInitialMessage(customerData, recentActivity, portalType)]);
    }
  }, [customerData, portalType]);

  const hasNoProviders = !aiProviders?.enabled?.length;

  return (
    <div
      id="chat-sidebar"
      ref={sidebarRef}
      className={`chat-sidebar fixed right-0 top-0 h-full bg-white shadow-2xl z-40 flex flex-col
        ${isResizing ? '' : 'transition-transform duration-300 ease-in-out'}
        ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}
      style={{ width: `${sidebarWidth}px` }}
    >
      {/* Resize handle */}
      <div
        onMouseDown={handleMouseDown}
        className={`absolute left-0 top-0 h-full w-1 cursor-ew-resize
          hover:bg-emerald-500 transition-colors z-10
          ${isResizing ? 'bg-emerald-500' : 'bg-transparent hover:bg-emerald-300'}`}
        title="Drag to resize"
      />

      {/* Header */}
      <div className="flex-shrink-0 bg-gradient-to-r from-emerald-600 to-emerald-700 text-white p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="text-xl">🐾</span>
            <h2 className="font-semibold">Pet Insurance Assistant</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-white/20 rounded transition-colors"
            title="Close chat"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Provider selector */}
        {aiProviders && (
          <ProviderSelector
            providers={aiProviders}
            selected={aiProvider}
            onChange={setAiProvider}
          />
        )}
      </div>

      {/* Messages area */}
      <div className="flex-grow overflow-y-auto p-4 space-y-4 bg-gray-50">
        {hasNoProviders ? (
          <div className="text-center py-8">
            <div className="text-4xl mb-3">⚠️</div>
            <p className="text-gray-600 mb-2">No AI providers configured</p>
            <p className="text-sm text-gray-500">
              Add OPENAI_API_KEY or ANTHROPIC_API_KEY to backend/.env
            </p>
          </div>
        ) : (
          <>
            {messages.map((msg, index) => (
              <ChatMessage key={index} message={msg} />
            ))}

            {/* Loading indicator */}
            {loading && (
              <div className="flex items-center gap-2 text-gray-500">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                  <span className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                  <span className="w-2 h-2 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                </div>
                <span className="text-sm">
                  {isCapturing ? 'Capturing screen...' : 'Thinking...'}
                </span>
              </div>
            )}

            {/* Error display */}
            {error && !loading && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-600">
                {error}
              </div>
            )}

            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input area */}
      {!hasNoProviders && (
        <div className="flex-shrink-0 border-t border-gray-200 p-4 bg-white">
          <ChatInput
            onSend={handleSend}
            disabled={loading || hasNoProviders}
            placeholder={loading ? 'Waiting for response...' : 'Ask about your pet insurance...'}
          />

          {/* Clear button */}
          {messages.length > 1 && (
            <button
              onClick={handleClear}
              className="mt-2 text-xs text-gray-400 hover:text-gray-600 transition-colors"
            >
              Clear conversation
            </button>
          )}
        </div>
      )}

      {/* Token usage footer */}
      {tokenUsage.total > 0 && (
        <TokenUsage usage={tokenUsage} />
      )}
    </div>
  );
}

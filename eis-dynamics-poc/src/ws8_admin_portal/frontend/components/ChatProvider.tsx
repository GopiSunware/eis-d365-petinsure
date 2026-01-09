'use client';

import { useState, useCallback, useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { ChatSidebar } from './ChatSidebar';
import { ChatToggle } from './ChatToggle';

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [chatOpen, setChatOpen] = useState(true); // Open by default
  const [chatWidth, setChatWidth] = useState(384); // Default, will be updated on mount
  const pathname = usePathname();

  // Set width to 20% of screen on mount (client-side only)
  useEffect(() => {
    setChatWidth(Math.max(320, Math.floor(window.innerWidth * 0.20)));
  }, []);

  // Get current page name for chat context
  const getCurrentPage = useCallback(() => {
    if (pathname === '/') return 'dashboard';
    if (pathname === '/costs') return 'costs';
    if (pathname === '/ai-config') return 'ai-config';
    if (pathname === '/claims-rules') return 'claims-rules';
    if (pathname === '/policy-config') return 'policy-config';
    if (pathname === '/rating-config') return 'rating-config';
    if (pathname === '/audit') return 'audit';
    if (pathname === '/users') return 'users';
    if (pathname?.startsWith('/approvals')) return 'approvals';
    return 'dashboard';
  }, [pathname]);

  return (
    <>
      <div
        id="main-content"
        className="flex-1 overflow-y-auto p-6 transition-all duration-300"
        style={{ marginRight: chatOpen ? `${chatWidth}px` : '0px' }}
      >
        {children}
      </div>

      {/* Chat Sidebar */}
      <ChatSidebar
        isOpen={chatOpen}
        onClose={() => setChatOpen(false)}
        onWidthChange={setChatWidth}
        currentPage={getCurrentPage()}
      />

      {/* Chat Toggle Button */}
      <ChatToggle onClick={() => setChatOpen(true)} isOpen={chatOpen} />
    </>
  );
}

export default ChatProvider;

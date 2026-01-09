'use client';

import { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { ChatSidebar } from './ChatSidebar';
import ChatToggle from './ChatToggle';

interface ChatContextType {
  isOpen: boolean;
  openChat: () => void;
  closeChat: () => void;
  toggleChat: () => void;
  setClaimContext: (claimId: string | null, claimData?: Record<string, unknown> | null) => void;
  setPageContext: (page: string) => void;
  setPipelineStatus: (status: Record<string, unknown> | null) => void;
}

const ChatContext = createContext<ChatContextType | null>(null);

export function useChat() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
}

interface ChatProviderProps {
  children: ReactNode;
}

export function ChatProvider({ children }: ChatProviderProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [sidebarWidth, setSidebarWidth] = useState(384);
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [claimId, setClaimId] = useState<string | null>(null);
  const [claimData, setClaimData] = useState<Record<string, unknown> | null>(null);
  const [pipelineStatus, setPipelineStatus] = useState<Record<string, unknown> | null>(null);

  const openChat = useCallback(() => setIsOpen(true), []);
  const closeChat = useCallback(() => setIsOpen(false), []);
  const toggleChat = useCallback(() => setIsOpen(prev => !prev), []);

  const setClaimContext = useCallback((id: string | null, data?: Record<string, unknown> | null) => {
    setClaimId(id);
    setClaimData(data || null);
  }, []);

  const setPageContext = useCallback((page: string) => {
    setCurrentPage(page);
  }, []);

  const handleWidthChange = useCallback((width: number) => {
    setSidebarWidth(width);
  }, []);

  return (
    <ChatContext.Provider
      value={{
        isOpen,
        openChat,
        closeChat,
        toggleChat,
        setClaimContext,
        setPageContext,
        setPipelineStatus
      }}
    >
      <div
        className="transition-all duration-300"
        style={{ marginRight: isOpen ? `${sidebarWidth}px` : '0px' }}
      >
        {children}
      </div>

      <ChatSidebar
        isOpen={isOpen}
        onClose={closeChat}
        onWidthChange={handleWidthChange}
        currentPage={currentPage}
        claimId={claimId}
        claimData={claimData}
        pipelineStatus={pipelineStatus}
      />

      <ChatToggle onClick={toggleChat} isOpen={isOpen} />
    </ChatContext.Provider>
  );
}

export default ChatProvider;

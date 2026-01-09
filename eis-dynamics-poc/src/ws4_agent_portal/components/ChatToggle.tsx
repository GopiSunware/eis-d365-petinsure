'use client';

import { MessageCircle } from 'lucide-react';

interface ChatToggleProps {
  onClick: () => void;
  isOpen: boolean;
}

export function ChatToggle({ onClick, isOpen }: ChatToggleProps) {
  if (isOpen) return null;

  return (
    <button
      onClick={onClick}
      className="fixed bottom-6 right-6 z-30 bg-indigo-600 hover:bg-indigo-700 text-white
        rounded-full p-4 shadow-lg transition-all duration-300 hover:scale-105
        flex items-center gap-2 group"
      title="Open AI Assistant"
    >
      <MessageCircle className="w-6 h-6" />
      <span className="max-w-0 overflow-hidden group-hover:max-w-xs transition-all duration-300 whitespace-nowrap">
        Ask AI
      </span>
    </button>
  );
}

export default ChatToggle;

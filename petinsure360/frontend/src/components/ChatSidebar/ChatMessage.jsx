import React from 'react';

// Simple markdown parser for common patterns
function parseMarkdown(text) {
  if (!text) return text;

  // Split by code blocks first to protect them
  const parts = text.split(/(```[\s\S]*?```|`[^`]+`)/g);

  return parts.map((part, i) => {
    // Code block
    if (part.startsWith('```')) {
      const code = part.slice(3, -3).replace(/^\w+\n/, ''); // Remove language identifier
      return (
        <pre key={i} className="bg-gray-100 rounded p-2 my-2 overflow-x-auto text-xs font-mono">
          {code}
        </pre>
      );
    }
    // Inline code
    if (part.startsWith('`') && part.endsWith('`')) {
      return (
        <code key={i} className="bg-gray-100 px-1 rounded text-sm font-mono">
          {part.slice(1, -1)}
        </code>
      );
    }

    // Parse bold, italic, and bullet points in regular text
    let content = part;

    // Bold **text**
    content = content.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // Bullet points
    content = content.replace(/^[•\-\*]\s+/gm, '• ');

    return (
      <span
        key={i}
        dangerouslySetInnerHTML={{ __html: content }}
      />
    );
  });
}

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user';
  const isError = message.isError;

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] rounded-2xl px-4 py-2 ${
          isUser
            ? 'bg-emerald-600 text-white rounded-br-md'
            : isError
            ? 'bg-red-50 text-red-700 border border-red-200 rounded-bl-md'
            : 'bg-white text-gray-800 shadow-sm border border-gray-100 rounded-bl-md'
        }`}
      >
        {/* Message content */}
        <div className="text-sm whitespace-pre-wrap break-words">
          {isUser ? message.content : parseMarkdown(message.content)}
        </div>

        {/* Model info for assistant messages */}
        {!isUser && message.model && (
          <div className="mt-1 text-xs opacity-50">
            {message.provider === 'openai' ? 'GPT-4o' : 'Claude'}
          </div>
        )}
      </div>
    </div>
  );
}

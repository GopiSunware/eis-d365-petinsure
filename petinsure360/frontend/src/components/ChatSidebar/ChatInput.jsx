import { useState, useRef, useEffect, useCallback } from 'react';

// Check for Web Speech API support
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
const hasSpeechSupport = !!SpeechRecognition;

export default function ChatInput({ onSend, disabled, placeholder }) {
  const [value, setValue] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [speechError, setSpeechError] = useState(null);
  const textareaRef = useRef(null);
  const recognitionRef = useRef(null);

  // Initialize speech recognition
  useEffect(() => {
    if (!hasSpeechSupport) return;

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map(result => result[0].transcript)
        .join('');
      setValue(transcript);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      setIsListening(false);
      if (event.error === 'not-allowed') {
        setSpeechError('Microphone access denied');
      } else if (event.error === 'no-speech') {
        setSpeechError('No speech detected');
      } else {
        setSpeechError(`Error: ${event.error}`);
      }
      // Clear error after 3 seconds
      setTimeout(() => setSpeechError(null), 3000);
    };

    recognitionRef.current = recognition;

    return () => {
      recognition.abort();
    };
  }, []);

  // Toggle speech recognition
  const toggleListening = useCallback(() => {
    if (!recognitionRef.current) return;

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      setSpeechError(null);
      recognitionRef.current.start();
      setIsListening(true);
    }
  }, [isListening]);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }
  }, [value]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (value.trim() && !disabled) {
      onSend(value.trim());
      setValue('');
    }
  };

  const handleKeyDown = (e) => {
    // Submit on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="space-y-2">
      {/* Error message */}
      {speechError && (
        <div className="text-xs text-red-500 px-1">
          {speechError}
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex gap-2">
        <div className="flex-grow relative">
          <textarea
            ref={textareaRef}
            value={value}
            onChange={(e) => setValue(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled || isListening}
            placeholder={isListening ? 'Listening...' : placeholder}
            rows={1}
            className={`w-full resize-none rounded-lg border px-3 py-2 text-sm
              focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent
              disabled:bg-gray-100 disabled:text-gray-500
              ${isListening ? 'border-red-400 bg-red-50' : 'border-gray-300'}`}
            style={{ maxHeight: '120px' }}
          />
        </div>

        {/* Microphone button */}
        {hasSpeechSupport && (
          <button
            type="button"
            onClick={toggleListening}
            disabled={disabled}
            className={`flex-shrink-0 rounded-lg px-3 py-2 transition-colors
              ${isListening
                ? 'bg-red-500 hover:bg-red-600 text-white animate-pulse'
                : 'bg-gray-100 hover:bg-gray-200 text-gray-600'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            title={isListening ? 'Stop listening' : 'Voice input'}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              {isListening ? (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              )}
            </svg>
          </button>
        )}

        {/* Send button */}
        <button
          type="submit"
          disabled={disabled || !value.trim()}
          className="flex-shrink-0 bg-emerald-600 text-white rounded-lg px-4 py-2
            hover:bg-emerald-700 disabled:bg-gray-300 disabled:cursor-not-allowed
            transition-colors"
          title="Send message"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
          </svg>
        </button>
      </form>
    </div>
  );
}

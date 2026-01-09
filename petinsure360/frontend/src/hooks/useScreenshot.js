import { useCallback, useState } from 'react';
import html2canvas from 'html2canvas';

/**
 * Hook for capturing screenshots of DOM elements
 * Returns base64 JPEG suitable for sending to AI vision APIs
 */
export function useScreenshot() {
  const [isCapturing, setIsCapturing] = useState(false);

  const captureScreenshot = useCallback(async (elementId = 'main-content') => {
    const element = document.getElementById(elementId);
    if (!element) {
      console.warn(`Element with id "${elementId}" not found`);
      return null;
    }

    setIsCapturing(true);

    try {
      const canvas = await html2canvas(element, {
        scale: 1,                // Full resolution for better text readability
        useCORS: true,           // Allow cross-origin images
        logging: false,          // Disable console logs
        backgroundColor: '#ffffff',
        // Ignore certain elements
        ignoreElements: (el) => {
          // Ignore the chat sidebar itself to avoid recursion
          return el.id === 'chat-sidebar' || el.classList.contains('chat-sidebar');
        }
      });

      // Convert to JPEG with 70% quality for smaller file size
      const dataUrl = canvas.toDataURL('image/jpeg', 0.7);

      // Log size for debugging
      const sizeKB = Math.round((dataUrl.length * 3/4) / 1024);
      console.log(`Screenshot captured: ${canvas.width}x${canvas.height}, ~${sizeKB}KB`);

      // Log the actual image to console for debugging
      console.log('%c📸 Screenshot Preview:', 'font-size: 14px; font-weight: bold; color: #059669;');
      console.log('📷 To view screenshot, run: window.open(window.__lastChatScreenshot)');

      return dataUrl;
    } catch (error) {
      console.error('Screenshot capture error:', error);
      return null;
    } finally {
      setIsCapturing(false);
    }
  }, []);

  return { captureScreenshot, isCapturing };
}

export default useScreenshot;

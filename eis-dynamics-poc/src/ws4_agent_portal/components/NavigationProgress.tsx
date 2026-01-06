"use client";

import { useEffect, useState, useRef } from "react";
import { usePathname, useSearchParams } from "next/navigation";

export function NavigationProgress() {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [progress, setProgress] = useState(0);
  const [visible, setVisible] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const prevPathRef = useRef(pathname);

  // Reset on route change complete
  useEffect(() => {
    if (prevPathRef.current !== pathname) {
      // Route changed - complete the bar
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      setProgress(100);
      setTimeout(() => {
        setVisible(false);
        setProgress(0);
      }, 400);
      prevPathRef.current = pathname;
    }
  }, [pathname, searchParams]);

  // Intercept link clicks to show loading
  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      const link = target.closest("a");

      if (link && link.href && !link.target) {
        try {
          const url = new URL(link.href);
          if (url.origin === window.location.origin && url.pathname !== pathname) {
            // Clear any existing interval
            if (intervalRef.current) {
              clearInterval(intervalRef.current);
            }

            // Start progress
            setVisible(true);
            setProgress(10);

            // Animate progress
            let currentProgress = 10;
            intervalRef.current = setInterval(() => {
              currentProgress += Math.random() * 10 + 5;
              if (currentProgress >= 90) {
                currentProgress = 90;
                if (intervalRef.current) {
                  clearInterval(intervalRef.current);
                }
              }
              setProgress(currentProgress);
            }, 150);
          }
        } catch (e) {
          // Invalid URL, ignore
        }
      }
    };

    document.addEventListener("click", handleClick, true);
    return () => {
      document.removeEventListener("click", handleClick, true);
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [pathname]);

  if (!visible && progress === 0) return null;

  return (
    <div className="fixed top-0 left-0 right-0 z-[9999] pointer-events-none">
      <div className="h-1 bg-primary-100">
        <div
          className="h-full bg-gradient-to-r from-primary-500 via-primary-600 to-primary-500 transition-all ease-out relative overflow-hidden"
          style={{
            width: `${progress}%`,
            transitionDuration: progress === 100 ? '200ms' : '300ms'
          }}
        >
          {/* Animated shine effect */}
          <div
            className="absolute inset-0 w-full"
            style={{
              background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent)',
              animation: 'shimmer 1s infinite',
            }}
          />
          {/* Glow at the end */}
          <div
            className="absolute right-0 top-0 h-full w-20"
            style={{
              background: 'linear-gradient(to left, rgba(59, 130, 246, 0.8), transparent)',
              boxShadow: '0 0 20px 5px rgba(59, 130, 246, 0.5)',
            }}
          />
        </div>
      </div>
    </div>
  );
}

import { useEffect, useState } from 'react';

interface ToastProps {
  message: string;
  isVisible: boolean;
  onClose: () => void;
  duration?: number;
}

export function Toast({ message, isVisible, onClose, duration = 5000 }: ToastProps) {
  const [progress, setProgress] = useState(100);

  useEffect(() => {
    if (!isVisible) return;

    const startTime = Date.now();
    const interval = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const remaining = Math.max(0, 100 - (elapsed / duration) * 100);
      setProgress(remaining);

      if (remaining <= 0) {
        clearInterval(interval);
        onClose();
      }
    }, 50);

    return () => clearInterval(interval);
  }, [isVisible, duration, onClose]);

  if (!isVisible) return null;

  return (
    <div className="fixed top-4 left-1/2 transform -translate-x-1/2 z-50 pointer-events-none">
      <div className="bg-red-600 text-white px-6 py-4 rounded-lg shadow-lg max-w-md pointer-events-auto">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">{message}</span>
          <button
            onClick={onClose}
            className="ml-4 text-red-200 hover:text-white"
          >
            ✕
          </button>
        </div>
        <div className="mt-2 h-1 bg-red-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-white transition-all duration-50 ease-linear"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>
    </div>
  );
}

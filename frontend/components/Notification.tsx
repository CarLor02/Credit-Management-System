'use client';

import { useEffect } from 'react';
import { Notification as NotificationProps, NotificationType } from '@/contexts/NotificationContext';

interface Props {
  notification: NotificationProps;
  onClose: (id: string) => void;
}

const ICONS: Record<NotificationType, string> = {
  success: 'ri-checkbox-circle-fill',
  error: 'ri-close-circle-fill',
  warning: 'ri-error-warning-fill',
  info: 'ri-information-fill',
};

const COLORS: Record<NotificationType, { bg: string; text: string; border: string }> = {
  success: { bg: 'bg-green-50', text: 'text-green-800', border: 'border-green-200' },
  error: { bg: 'bg-red-50', text: 'text-red-800', border: 'border-red-200' },
  warning: { bg: 'bg-yellow-50', text: 'text-yellow-800', border: 'border-yellow-200' },
  info: { bg: 'bg-blue-50', text: 'text-blue-800', border: 'border-blue-200' },
};

export default function Notification({ notification, onClose }: Props) {
  const { id, message, type, duration = 3000 } = notification;

  useEffect(() => {
    const timer = setTimeout(() => {
      onClose(id);
    }, duration);

    return () => clearTimeout(timer);
  }, [id, duration, onClose]);

  const handleClose = () => {
    onClose(id);
  };

  const icon = ICONS[type];
  const color = COLORS[type];

  return (
    <div
      className={`flex items-start w-full max-w-sm p-4 rounded-lg shadow-lg border ${color.bg} ${color.border} animate-slideInUp`}
      role="alert"
    >
      <div className="flex-shrink-0">
        <i className={`${icon} ${color.text} text-xl`}></i>
      </div>
      <div className="ml-3 mr-4 flex-1">
        <p className={`text-sm font-medium ${color.text}`}>{message}</p>
      </div>
      <button
        onClick={handleClose}
        className={`-mx-1.5 -my-1.5 ml-auto inline-flex h-8 w-8 items-center justify-center rounded-lg p-1.5 ${color.text} hover:bg-white hover:shadow-md hover:border hover:border-gray-300 transition-all duration-200 ease-in-out`}
        aria-label="Close"
      >
        <span className="sr-only">Close</span>
        <i className="ri-close-line text-lg"></i>
      </button>
    </div>
  );
}

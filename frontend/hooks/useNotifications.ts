import { useState, useCallback, useRef } from 'react';
import { Notification } from '../types';

export function useNotifications() {
    const [activeToasts, setActiveToasts] = useState<Notification[]>([]);
    const [notificationHistory, setNotificationHistory] = useState<Notification[]>([]);
    const notificationIdCounter = useRef(0);

    const addNotification = useCallback((text: string, type: 'info' | 'error', duration: number = 5000) => {
        const id = notificationIdCounter.current++;
        const newNotification: Notification = { id, text, type };

        setNotificationHistory(prev => [newNotification, ...prev].slice(0, 50));
        setActiveToasts(prev => [...prev, newNotification]);

        setTimeout(() => {
            setActiveToasts(prev => prev.filter(n => n.id !== id));
        }, duration);
    }, []);

    const removeActiveToast = (id: number) => {
        setActiveToasts(prev => prev.filter(toast => toast.id !== id));
    };

    const clearNotificationHistory = () => {
        setNotificationHistory([]);
    };

    return {
        addNotification,
        activeToasts,
        removeActiveToast,
        notificationHistory,
        clearNotificationHistory
    };
}
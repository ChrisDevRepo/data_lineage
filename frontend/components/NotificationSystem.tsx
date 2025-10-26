import React, { useState, useEffect, useRef } from 'react';
import { Notification } from '../types';

// --- Individual Toast Component ---
const Toast = ({ notification, onDismiss }: { notification: Notification; onDismiss: (id: number) => void; }) => {
    const [isVisible, setIsVisible] = useState(false);
    useEffect(() => {
        setIsVisible(true);
    }, []);

    const bgColor = notification.type === 'error' ? 'bg-red-500' : 'bg-blue-500';
    const icon = notification.type === 'error' ? (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
    ) : (
        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
    );

    return (
        <div className={`flex items-center ${bgColor} text-white text-sm font-bold px-4 py-3 rounded-lg shadow-lg transition-all duration-300 transform ${isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-full'}`}>
            {icon}
            <span className="mx-3 flex-1">{notification.text}</span>
            <button onClick={() => onDismiss(notification.id)} className="p-1 rounded-full hover:bg-black/20">
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>
        </div>
    );
};

// --- Toast Container ---
export const NotificationContainer = ({ activeToasts, onDismissToast }: { activeToasts: Notification[]; onDismissToast: (id: number) => void; }) => (
    <div className="fixed top-24 right-4 z-50 pointer-events-none w-80 flex flex-col items-end gap-3">
        {activeToasts.map(toast => (
            <div key={toast.id} className="pointer-events-auto">
                <Toast notification={toast} onDismiss={onDismissToast} />
            </div>
        ))}
    </div>
);

// --- Notification History Panel ---
const HistoryIcon = () => <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5"><path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 0 0 5.454-1.31A8.967 8.967 0 0 1 18 9.75V9A6 6 0 0 0 6 9v.75a8.967 8.967 0 0 1-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 0 1-5.714 0m5.714 0a3 3 0 1 1-5.714 0" /></svg>;

export const NotificationHistory = ({ history, onClearHistory }: { history: Notification[]; onClearHistory: () => void; }) => {
    const [isHistoryOpen, setIsHistoryOpen] = useState(false);
    const historyRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (historyRef.current && !historyRef.current.contains(event.target as Node)) {
                setIsHistoryOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    return (
        <div className="relative" ref={historyRef}>
            <button onClick={() => setIsHistoryOpen(p => !p)} className="h-10 w-10 flex items-center justify-center bg-gray-200 hover:bg-gray-300 rounded-lg text-gray-800" title="Notification History">
                <HistoryIcon />
                {history.length > 0 && (
                    <span className="absolute -top-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-red-500 text-xs font-bold text-white">{history.length}</span>
                )}
            </button>
            {isHistoryOpen && (
                <div className="absolute top-full mt-2 right-0 w-80 bg-white rounded-lg shadow-xl border border-gray-200 z-30">
                    <div className="flex justify-between items-center p-3 border-b">
                        <h3 className="font-bold text-gray-800">History</h3>
                        {history.length > 0 && <button onClick={onClearHistory} className="text-sm text-blue-600 hover:underline">Clear</button>}
                    </div>
                    <div className="max-h-80 overflow-y-auto p-2">
                        {history.length > 0 ? (
                            history.map(item => (
                                <div key={item.id} className={`p-2 my-1 rounded-md text-sm ${item.type === 'error' ? 'bg-red-50 text-red-800' : 'bg-blue-50 text-blue-800'}`}>
                                    {item.text}
                                </div>
                            ))
                        ) : (
                            <p className="p-4 text-center text-sm text-gray-500">No recent notifications.</p>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

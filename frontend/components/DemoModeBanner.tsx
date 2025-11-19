import React from 'react';

/**
 * Demo Mode Banner - Visual indicator that the app is running in demo mode
 *
 * Appears at the top of the screen when RUN_MODE=demo
 * Orange background with informational message
 * No dismiss option (demo mode is system-wide setting)
 */
export const DemoModeBanner: React.FC = () => {
  return (
    <div className="px-4 py-3 bg-orange-100 border-b border-orange-400 flex items-center gap-3">
      {/* Icon */}
      <svg
        className="w-5 h-5 text-orange-600 flex-shrink-0"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>

      {/* Message */}
      <div className="flex flex-col flex-1">
        <div className="text-sm font-semibold text-orange-900">
          🎪 Demo Mode Active
        </div>
        <div className="text-xs text-orange-700">
          You are viewing sample data. Data import is disabled in demo mode. To enable imports, set <span className="font-mono bg-orange-200 px-1 rounded">RUN_MODE=production</span> in .env and restart the server.
        </div>
      </div>
    </div>
  );
};

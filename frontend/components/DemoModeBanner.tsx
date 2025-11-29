import React from 'react';

/**
 * Demo Mode Indicator - Small badge displayed next to the logo when RUN_MODE=demo
 *
 * Styled similarly to the Trace Mode indicator for visual consistency
 */
export const DemoModeIndicator: React.FC = () => {
  return (
    <span
      className="text-sm font-semibold text-amber-700 px-3 py-1 bg-amber-50 rounded-md border border-amber-300"
    >
      Demo Mode Active
    </span>
  );
};

// Keep DemoModeBanner as an alias for backwards compatibility
export const DemoModeBanner = DemoModeIndicator;

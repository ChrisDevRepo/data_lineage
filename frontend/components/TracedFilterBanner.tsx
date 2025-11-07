import React from 'react';
import { Button } from './ui/Button';

interface TracedFilterBannerProps {
  startNodeName: string;
  upstreamLevels: number;
  downstreamLevels: number;
  totalNodes: number;
  onReset: () => void;
}

/**
 * Visual indicator showing user is in "traced filtered mode"
 * Appears between toolbar and graph after "End Trace" is clicked
 *
 * Best practice: Amber/orange color for filtering state (not error, not success - informational)
 * Dismissible with Reset View button or X
 */
export const TracedFilterBanner: React.FC<TracedFilterBannerProps> = ({
  startNodeName,
  upstreamLevels,
  downstreamLevels,
  totalNodes,
  onReset
}) => {
  return (
    <div className="px-4 py-3 bg-amber-50 border-b border-amber-300 flex items-center justify-between">
      <div className="flex items-center gap-3">
        {/* Icon */}
        <svg
          className="w-5 h-5 text-amber-600 flex-shrink-0"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
          />
        </svg>

        {/* Message */}
        <div className="flex flex-col">
          <div className="text-sm font-semibold text-amber-900">
            🔍 Trace Filter Active
          </div>
          <div className="text-xs text-amber-700">
            Showing <span className="font-bold">{totalNodes} nodes</span> from{' '}
            <span className="font-mono text-amber-800">"{startNodeName}"</span>
            {' '}({upstreamLevels} levels up / {downstreamLevels} levels down)
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2">
        <Button
          onClick={onReset}
          variant="secondary"
          className="h-8 px-3 text-xs bg-white hover:bg-amber-100 border-amber-300"
        >
          Reset View
        </Button>

        {/* X button */}
        <button
          onClick={onReset}
          className="w-8 h-8 flex items-center justify-center hover:bg-amber-100 text-amber-700 hover:text-amber-900 rounded transition-colors"
          title="Reset View (clear trace filter)"
        >
          <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
};

import React from 'react';

interface SkeletonGraphProps {
  progress: number;
  stage: string;
}

export const SkeletonGraph: React.FC<SkeletonGraphProps> = ({ progress, stage }) => {
  return (
    <div className="w-screen h-screen flex flex-col font-sans">
      {/* Header Skeleton */}
      <header className="flex-shrink-0 z-20">
        <div className="flex items-center justify-between px-4 py-2 bg-white shadow-sm">
          <div className="flex items-center gap-3">
            <div className="h-10 w-32 bg-gray-200 rounded animate-pulse"></div>
          </div>
        </div>
        <div className="h-1 bg-gradient-to-r from-blue-500 via-teal-400 to-orange-400"></div>
      </header>

      <main className="flex-grow p-4 relative bg-gray-100 overflow-hidden">
        <div className="w-full h-full bg-white rounded-lg shadow-md flex flex-col">
          {/* Toolbar Skeleton */}
          <div className="flex-shrink-0 border-b border-gray-200 p-3 bg-gray-50">
            <div className="flex flex-wrap items-center gap-2">
              <div className="h-9 w-48 bg-gray-200 rounded animate-pulse"></div>
              <div className="h-9 w-32 bg-gray-200 rounded animate-pulse"></div>
              <div className="h-9 w-32 bg-gray-200 rounded animate-pulse"></div>
              <div className="h-9 w-24 bg-gray-200 rounded animate-pulse"></div>
            </div>
          </div>

          {/* Graph Area Skeleton with Loading Indicator */}
          <div className="flex-grow relative bg-gray-50 flex items-center justify-center">
            {/* Skeleton Nodes */}
            <div className="absolute inset-0 opacity-20">
              <div className="absolute top-1/4 left-1/4 w-32 h-20 bg-blue-300 rounded animate-pulse"></div>
              <div className="absolute top-1/3 left-1/2 w-32 h-20 bg-green-300 rounded animate-pulse"></div>
              <div className="absolute top-1/2 left-1/3 w-32 h-20 bg-purple-300 rounded animate-pulse"></div>
              <div className="absolute top-2/3 left-2/3 w-32 h-20 bg-orange-300 rounded animate-pulse"></div>
            </div>

            {/* Loading Progress Overlay */}
            <div className="z-10 text-center max-w-md px-6">
              {/* Animated spinner */}
              <div className="inline-block animate-spin rounded-full h-16 w-16 border-b-4 border-blue-600 mb-4"></div>

              {/* Main message */}
              <h2 className="text-gray-800 text-xl font-bold mb-2">Loading Lineage Data</h2>

              {/* Dynamic status message */}
              <p className="text-gray-600 text-sm mb-3">
                {stage}
              </p>

              {/* Dynamic progress indicator */}
              <div className="w-full bg-gray-200 rounded-full h-2 mb-2 overflow-hidden">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                ></div>
              </div>

              {/* Progress percentage */}
              <p className="text-gray-500 text-xs">
                {progress}% complete
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

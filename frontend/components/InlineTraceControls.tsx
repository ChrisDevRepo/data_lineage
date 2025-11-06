import React, { useState, useEffect } from 'react';
import { DataNode } from '../types';
import { Button } from './ui/Button';

interface InlineTraceControlsProps {
  startNodeId: string;
  startNodeName: string;
  allData: DataNode[];
  onApply: (config: {
    startNodeId: string;
    upstreamLevels: number;
    downstreamLevels: number;
  }) => void;
  onEnd: () => void;
}

export const InlineTraceControls: React.FC<InlineTraceControlsProps> = ({
  startNodeId,
  startNodeName,
  allData,
  onApply,
  onEnd
}) => {
  const [startSearch, setStartSearch] = useState(startNodeName);
  const [selectedNodeId, setSelectedNodeId] = useState(startNodeId);
  const [suggestions, setSuggestions] = useState<DataNode[]>([]);
  const [upstream, setUpstream] = useState(3);
  const [isUpstreamAll, setIsUpstreamAll] = useState(false);
  const [downstream, setDownstream] = useState(3);
  const [isDownstreamAll, setIsDownstreamAll] = useState(false);

  // Update when start node changes
  useEffect(() => {
    setStartSearch(startNodeName);
    setSelectedNodeId(startNodeId);
  }, [startNodeId, startNodeName]);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setStartSearch(value);
    if (value.trim()) {
      setSuggestions(
        allData.filter(n => n.name.toLowerCase().includes(value.toLowerCase())).slice(0, 5)
      );
    } else {
      setSuggestions([]);
    }
  };

  const selectNode = (node: DataNode) => {
    setSelectedNodeId(node.id);
    setStartSearch(node.name);
    setSuggestions([]);
  };

  const handleApply = () => {
    onApply({
      startNodeId: selectedNodeId,
      upstreamLevels: isUpstreamAll ? Number.MAX_SAFE_INTEGER : upstream,
      downstreamLevels: isDownstreamAll ? Number.MAX_SAFE_INTEGER : downstream
    });
  };

  return (
    <div className="bg-blue-50 border-b border-blue-200 px-4 py-3">
      <div className="flex items-center gap-4 flex-wrap">
        {/* Start Node Input */}
        <div className="relative flex-shrink-0" style={{ width: '280px' }}>
          <label className="text-xs font-medium text-gray-700 mb-1 block">Start Node</label>
          <input
            type="text"
            value={startSearch}
            onChange={handleSearchChange}
            placeholder="Search for node..."
            className="w-full h-9 px-3 bg-white border border-gray-300 rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {suggestions.length > 0 && (
            <div className="absolute top-full mt-1 w-full bg-white border border-gray-300 rounded shadow-lg z-50 max-h-48 overflow-y-auto">
              {suggestions.map(node => (
                <button
                  key={node.id}
                  onClick={() => selectNode(node)}
                  className="w-full px-3 py-2 text-left text-sm hover:bg-blue-50 flex flex-col gap-0.5"
                >
                  <span className="font-medium text-gray-800">{node.name}</span>
                  <span className="text-xs text-gray-500">{node.schema} • {node.object_type}</span>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Upstream Levels */}
        <div className="flex items-end gap-2">
          <div>
            <label className="text-xs font-medium text-gray-700 mb-1 block">Upstream</label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                min="0"
                max="99"
                value={upstream}
                onChange={(e) => {
                  setUpstream(parseInt(e.target.value) || 0);
                  setIsUpstreamAll(false);
                }}
                disabled={isUpstreamAll}
                className="w-16 h-9 px-2 bg-white border border-gray-300 rounded text-sm text-center focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-500"
              />
              <button
                onClick={() => setIsUpstreamAll(!isUpstreamAll)}
                className={`h-9 px-3 rounded text-sm font-medium transition-colors ${
                  isUpstreamAll
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                }`}
              >
                All
              </button>
            </div>
          </div>
        </div>

        {/* Downstream Levels */}
        <div className="flex items-end gap-2">
          <div>
            <label className="text-xs font-medium text-gray-700 mb-1 block">Downstream</label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                min="0"
                max="99"
                value={downstream}
                onChange={(e) => {
                  setDownstream(parseInt(e.target.value) || 0);
                  setIsDownstreamAll(false);
                }}
                disabled={isDownstreamAll}
                className="w-16 h-9 px-2 bg-white border border-gray-300 rounded text-sm text-center focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100 disabled:text-gray-500"
              />
              <button
                onClick={() => setIsDownstreamAll(!isDownstreamAll)}
                className={`h-9 px-3 rounded text-sm font-medium transition-colors ${
                  isDownstreamAll
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50'
                }`}
              >
                All
              </button>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-end gap-2 ml-auto">
          <Button
            onClick={handleApply}
            variant="primary"
            className="h-9 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded text-sm font-medium transition-colors"
          >
            Apply Trace
          </Button>
          <Button
            onClick={onEnd}
            variant="secondary"
            className="h-9 px-4 bg-white hover:bg-gray-50 text-gray-700 border border-gray-300 rounded text-sm font-medium transition-colors"
          >
            End Tracing
          </Button>
        </div>
      </div>
    </div>
  );
};

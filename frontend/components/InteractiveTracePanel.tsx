import React, { useState, useEffect } from 'react';
import { DataNode, TraceConfig } from '../types';
import { Button } from './ui/Button';
import { Select } from './ui/Select';
import { Checkbox } from './ui/Checkbox';

type InteractiveTracePanelProps = {
    isOpen: boolean;
    onClose: () => void;
    onApply: (config: Omit<TraceConfig, 'rawExclusionPatterns'>) => void;
    availableSchemas: string[];
    inheritedSchemaFilter: Set<string>;
    availableTypes: string[];
    inheritedTypeFilter: Set<string>;
    allData: DataNode[];
    addNotification: (text: string, type: 'info' | 'error') => void;
};

// OPTIMIZATION: Memoize to prevent unnecessary re-renders
export const InteractiveTracePanel = React.memo(({ isOpen, onClose, onApply, availableSchemas, inheritedSchemaFilter, availableTypes, inheritedTypeFilter, allData, addNotification }: InteractiveTracePanelProps) => {
    const [traceMode, setTraceMode] = useState<'levels' | 'path'>('levels'); // 'levels' = level-based, 'path' = start-to-end path
    const [startNodeSearch, setStartNodeSearch] = useState('');
    const [startSuggestions, setStartSuggestions] = useState<DataNode[]>([]);
    const [selectedNode, setSelectedNode] = useState<DataNode | null>(null);
    const [endNodeSearch, setEndNodeSearch] = useState('');
    const [endSuggestions, setEndSuggestions] = useState<DataNode[]>([]);
    const [selectedEndNode, setSelectedEndNode] = useState<DataNode | null>(null);
    const [upstream, setUpstream] = useState(3);
    const [isUpstreamAll, setIsUpstreamAll] = useState(false);
    const [downstream, setDownstream] = useState(3);
    const [isDownstreamAll, setIsDownstreamAll] = useState(false);
    const [includedSchemas, setIncludedSchemas] = useState(new Set(availableSchemas));
    const [includedTypes, setIncludedTypes] = useState(new Set(availableTypes));
    const [exclusions, setExclusions] = useState("*_TMP;*_BAK");

    // Inherit schema and type filters from detail mode when opening trace mode
    useEffect(() => {
        if (isOpen) {
            // Use inherited schema filter from detail mode
            setIncludedSchemas(new Set(inheritedSchemaFilter));
            // Use inherited type filter from detail mode
            setIncludedTypes(new Set(inheritedTypeFilter));
        }
    }, [isOpen, inheritedSchemaFilter, inheritedTypeFilter]);

    const handleStartSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        setStartNodeSearch(value);
        if (value) {
            setStartSuggestions(allData.filter(n => n.name.toLowerCase().includes(value.toLowerCase())).slice(0, 5));
        } else {
            setStartSuggestions([]);
            setSelectedNode(null);
        }
    };

    const selectStartNode = (node: DataNode) => {
        setSelectedNode(node);
        setStartNodeSearch(node.name);
        setStartSuggestions([]);
    };

    const handleEndSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        setEndNodeSearch(value);
        if (value) {
            setEndSuggestions(allData.filter(n => n.name.toLowerCase().includes(value.toLowerCase())).slice(0, 5));
        } else {
            setEndSuggestions([]);
            setSelectedEndNode(null);
        }
    };

    const selectEndNode = (node: DataNode) => {
        setSelectedEndNode(node);
        setEndNodeSearch(node.name);
        setEndSuggestions([]);
    };

    const handleApplyClick = () => {
        if (!selectedNode) {
            addNotification('Please select a valid start node.', 'error');
            return;
        }
        if (traceMode === 'path' && !selectedEndNode) {
            addNotification('Please select a valid end node for path tracing.', 'error');
            return;
        }
        if (traceMode === 'path' && selectedNode.id === selectedEndNode?.id) {
            addNotification('Start and end nodes must be different.', 'error');
            return;
        }
        onApply({
            startNodeId: selectedNode.id,
            endNodeId: traceMode === 'path' ? selectedEndNode?.id : null,
            upstreamLevels: isUpstreamAll ? Number.MAX_SAFE_INTEGER : upstream,
            downstreamLevels: isDownstreamAll ? Number.MAX_SAFE_INTEGER : downstream,
            includedSchemas: includedSchemas,
            includedTypes: includedTypes,
            exclusionPatterns: exclusions.split(';').map(p => p.trim()).filter(p => p !== ''),
        });
    };

    const handleReset = () => {
        setTraceMode('levels');
        setSelectedNode(null);
        setStartNodeSearch('');
        setStartSuggestions([]);
        setSelectedEndNode(null);
        setEndNodeSearch('');
        setEndSuggestions([]);
        setUpstream(3);
        setDownstream(3);
        setIsUpstreamAll(false);
        setIsDownstreamAll(false);
        setIncludedSchemas(new Set(availableSchemas));
        setIncludedTypes(new Set(availableTypes));
        setExclusions("*_TMP;*_BAK");
    };

    return (
        <div className={`absolute top-0 right-0 h-full bg-white shadow-2xl z-20 w-80 transform transition-transform duration-300 ease-in-out ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}>
            <div className="flex flex-col h-full">
                {/* Header with logo and colorful accent */}
                <header className="flex-shrink-0">
                    <div className="flex items-center justify-between px-4 py-2.5">
                        <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-green-500 to-green-600 flex items-center justify-center flex-shrink-0">
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5 text-white">
                                    <path strokeLinecap="round" strokeLinejoin="round" d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M12 18.75H4.5a2.25 2.25 0 0 1-2.25-2.25V9m12.841 9.091L16.5 19.5m-1.409-1.409c.407-.407.659-.97.659-1.591v-9a2.25 2.25 0 0 0-2.25-2.25h-9c-.621 0-1.184.252-1.591.659m12.182 12.182L2.909 5.909M1.5 4.5l1.409 1.409" />
                                </svg>
                            </div>
                            <h2 className="text-lg font-bold text-gray-800">Interactive Trace</h2>
                        </div>
                        <button
                            onClick={onClose}
                            className="w-9 h-9 flex items-center justify-center hover:bg-gray-100 text-gray-600 rounded transition-colors flex-shrink-0"
                            title="Close panel"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
                            </svg>
                        </button>
                    </div>
                    <div className="h-1 bg-gradient-to-r from-green-500 via-teal-400 to-blue-500"></div>
                </header>

                {/* Main content */}
                <main className="flex-grow overflow-y-auto px-4 py-4 space-y-5 text-sm">
                    {/* Trace Mode */}
                    <div>
                        <label className="block mb-1.5 text-xs font-semibold text-gray-700 uppercase tracking-wide">Trace Mode</label>
                        <Select value={traceMode} onChange={(e) => setTraceMode(e.target.value as 'levels' | 'path')} fullWidth>
                            <option value="levels">By Levels</option>
                            <option value="path">Path Between Nodes</option>
                        </Select>
                        <p className="text-xs text-gray-500 mt-1">
                            {traceMode === 'levels' ? 'Trace upstream/downstream by depth' : 'Find shortest path between two nodes'}
                        </p>
                    </div>

                    {/* Start Node */}
                    <div className="relative">
                        <label className="block mb-1.5 text-xs font-semibold text-gray-700 uppercase tracking-wide">Start Node</label>
                        <input
                            type="text"
                            placeholder="Search for node..."
                            value={startNodeSearch}
                            onChange={handleStartSearchChange}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                        />
                        {startSuggestions.length > 0 && (
                            <div className="absolute top-full mt-1 w-full bg-white border border-gray-200 rounded-md shadow-lg z-30 max-h-40 overflow-y-auto">
                                {startSuggestions.map(node => (
                                    <div
                                        key={node.id}
                                        onMouseDown={() => selectStartNode(node)}
                                        className="px-3 py-2 hover:bg-green-50 cursor-pointer text-sm border-b last:border-b-0"
                                    >
                                        <div className="font-medium text-gray-800">{node.name}</div>
                                        <div className="text-xs text-gray-500">{node.schema} • {node.object_type}</div>
                                    </div>
                                ))}
                            </div>
                        )}
                        {selectedNode && (
                            <div className="mt-2 px-3 py-2 bg-green-50 border border-green-200 rounded-md">
                                <div className="text-xs font-medium text-green-800">{selectedNode.name}</div>
                                <div className="text-xs text-green-600">{selectedNode.schema}</div>
                            </div>
                        )}
                    </div>

                    {/* End Node (Path mode only) */}
                    {traceMode === 'path' && (
                        <div className="relative">
                            <label className="block mb-1.5 text-xs font-semibold text-gray-700 uppercase tracking-wide">End Node</label>
                            <input
                                type="text"
                                placeholder="Search for node..."
                                value={endNodeSearch}
                                onChange={handleEndSearchChange}
                                className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent"
                            />
                            {endSuggestions.length > 0 && (
                                <div className="absolute top-full mt-1 w-full bg-white border border-gray-200 rounded-md shadow-lg z-30 max-h-40 overflow-y-auto">
                                    {endSuggestions.map(node => (
                                        <div
                                            key={node.id}
                                            onMouseDown={() => selectEndNode(node)}
                                            className="px-3 py-2 hover:bg-green-50 cursor-pointer text-sm border-b last:border-b-0"
                                        >
                                            <div className="font-medium text-gray-800">{node.name}</div>
                                            <div className="text-xs text-gray-500">{node.schema} • {node.object_type}</div>
                                        </div>
                                    ))}
                                </div>
                            )}
                            {selectedEndNode && (
                                <div className="mt-2 px-3 py-2 bg-green-50 border border-green-200 rounded-md">
                                    <div className="text-xs font-medium text-green-800">{selectedEndNode.name}</div>
                                    <div className="text-xs text-green-600">{selectedEndNode.schema}</div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Trace Levels (Levels mode only) */}
                    {traceMode === 'levels' && (
                        <div>
                            <label className="block mb-1.5 text-xs font-semibold text-gray-700 uppercase tracking-wide">Trace Depth</label>
                            <div className="space-y-3 bg-gray-50 border border-gray-200 rounded-md p-3">
                                <div className="flex items-center justify-between gap-2">
                                    <label className="text-xs text-gray-600 font-medium min-w-[80px]">Upstream</label>
                                    <div className="flex items-center gap-2">
                                        <input
                                            type="number"
                                            min="0"
                                            max="99"
                                            value={upstream}
                                            onChange={e => setUpstream(parseInt(e.target.value, 10))}
                                            disabled={isUpstreamAll}
                                            className="w-16 px-2 py-1 border border-gray-300 rounded-md disabled:bg-gray-100 disabled:opacity-70 text-center text-sm"
                                        />
                                        <Button
                                            onClick={() => setIsUpstreamAll(p => !p)}
                                            variant={isUpstreamAll ? 'primary' : 'secondary'}
                                            size="sm"
                                            className="w-12 text-xs"
                                        >
                                            {isUpstreamAll ? 'All' : 'All'}
                                        </Button>
                                    </div>
                                </div>
                                <div className="flex items-center justify-between gap-2">
                                    <label className="text-xs text-gray-600 font-medium min-w-[80px]">Downstream</label>
                                    <div className="flex items-center gap-2">
                                        <input
                                            type="number"
                                            min="0"
                                            max="99"
                                            value={downstream}
                                            onChange={e => setDownstream(parseInt(e.target.value, 10))}
                                            disabled={isDownstreamAll}
                                            className="w-16 px-2 py-1 border border-gray-300 rounded-md disabled:bg-gray-100 disabled:opacity-70 text-center text-sm"
                                        />
                                        <Button
                                            onClick={() => setIsDownstreamAll(p => !p)}
                                            variant={isDownstreamAll ? 'primary' : 'secondary'}
                                            size="sm"
                                            className="w-12 text-xs"
                                        >
                                            {isDownstreamAll ? 'All' : 'All'}
                                        </Button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Divider */}
                    <div className="border-t border-gray-200"></div>

                    {/* Included Schemas */}
                    <div>
                        <label className="block mb-1.5 text-xs font-semibold text-gray-700 uppercase tracking-wide">
                            Schemas ({includedSchemas.size}/{availableSchemas.length})
                        </label>
                        <div className="max-h-32 overflow-y-auto border border-gray-200 rounded-md p-2 space-y-1 bg-white">
                            {availableSchemas.map(s => (
                                <Checkbox
                                    key={s}
                                    checked={includedSchemas.has(s)}
                                    onChange={() => {
                                        const newSet = new Set(includedSchemas);
                                        if (newSet.has(s)) newSet.delete(s);
                                        else newSet.add(s);
                                        setIncludedSchemas(newSet);
                                    }}
                                    label={s}
                                />
                            ))}
                        </div>
                    </div>

                    {/* Included Types */}
                    <div>
                        <label className="block mb-1.5 text-xs font-semibold text-gray-700 uppercase tracking-wide">
                            Types ({includedTypes.size}/{availableTypes.length})
                        </label>
                        <div className="max-h-32 overflow-y-auto border border-gray-200 rounded-md p-2 space-y-1 bg-white">
                            {availableTypes.map(t => (
                                <Checkbox
                                    key={t}
                                    checked={includedTypes.has(t)}
                                    onChange={() => {
                                        const newSet = new Set(includedTypes);
                                        if (newSet.has(t)) newSet.delete(t);
                                        else newSet.add(t);
                                        setIncludedTypes(newSet);
                                    }}
                                    label={t}
                                />
                            ))}
                        </div>
                    </div>

                    {/* Exclusion Patterns */}
                    <div>
                        <label htmlFor="exclusions-input" className="block mb-1.5 text-xs font-semibold text-gray-700 uppercase tracking-wide">
                            Exclusion Patterns
                        </label>
                        <input
                            type="text"
                            id="exclusions-input"
                            value={exclusions}
                            onChange={e => setExclusions(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md font-mono text-xs focus:outline-none focus:ring-2 focus:ring-green-500"
                            placeholder="*_TMP;*_BAK"
                        />
                        <p className="text-xs text-gray-500 mt-1">Separate with semicolons (;)</p>
                    </div>
                </main>

                {/* Footer */}
                <footer className="flex-shrink-0 px-4 py-3 border-t border-gray-200 bg-gray-50 flex justify-end gap-2">
                    <Button onClick={handleReset} variant="secondary" size="md">
                        Reset
                    </Button>
                    <Button onClick={handleApplyClick} variant="primary" size="md">
                        Apply Trace
                    </Button>
                </footer>
            </div>
        </div>
    );
});

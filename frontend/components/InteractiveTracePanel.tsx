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

export const InteractiveTracePanel = ({ isOpen, onClose, onApply, availableSchemas, inheritedSchemaFilter, availableTypes, inheritedTypeFilter, allData, addNotification }: InteractiveTracePanelProps) => {
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
                <header className="flex items-center justify-between p-4 border-b">
                    <h2 className="text-xl font-bold">Interactive Trace</h2>
                    <Button onClick={onClose} variant="icon">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor" className="w-6 h-6"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" /></svg>
                    </Button>
                </header>
                <main className="flex-grow p-4 overflow-y-auto space-y-6 text-sm">
                    <div>
                        <label className="font-semibold block mb-1">1. Trace Mode</label>
                        <Select value={traceMode} onChange={(e) => setTraceMode(e.target.value as 'levels' | 'path')} fullWidth>
                            <option value="levels">By Levels (upstream/downstream)</option>
                            <option value="path">Path Between Nodes</option>
                        </Select>
                    </div>
                    <div className="relative">
                        <label className="font-semibold block mb-1">2. Start Node</label>
                        <input type="text" placeholder="Search for start node..." value={startNodeSearch} onChange={handleStartSearchChange} className="w-full p-2 border rounded-md" />
                        {startSuggestions.length > 0 && (
                            <div className="absolute top-full mt-1 w-full bg-white border rounded-md shadow-lg z-30">
                                {startSuggestions.map(node => <div key={node.id} onMouseDown={() => selectStartNode(node)} className="p-2 hover:bg-blue-100 cursor-pointer">{node.name}</div>)}
                            </div>
                        )}
                    </div>
                    {traceMode === 'path' && (
                        <div className="relative">
                            <label className="font-semibold block mb-1">3. End Node</label>
                            <input type="text" placeholder="Search for end node..." value={endNodeSearch} onChange={handleEndSearchChange} className="w-full p-2 border rounded-md" />
                            {endSuggestions.length > 0 && (
                                <div className="absolute top-full mt-1 w-full bg-white border rounded-md shadow-lg z-30">
                                    {endSuggestions.map(node => <div key={node.id} onMouseDown={() => selectEndNode(node)} className="p-2 hover:bg-blue-100 cursor-pointer">{node.name}</div>)}
                                </div>
                            )}
                        </div>
                    )}
                    {traceMode === 'levels' && (
                    <div>
                        <label className="font-semibold block mb-2">3. Trace Levels</label>
                        <div className="space-y-3">
                            <div className="flex items-center justify-between">
                                <label className="font-medium text-gray-700">Ancestors (upstream)</label>
                                <div className="flex items-center gap-2">
                                    <input type="number" min="0" max="99" value={upstream} onChange={e => setUpstream(parseInt(e.target.value, 10))} disabled={isUpstreamAll} className="w-16 p-1 border rounded-md disabled:bg-gray-100 disabled:opacity-70 text-center" />
                                    <Button
                                        onClick={() => setIsUpstreamAll(p => !p)}
                                        variant={isUpstreamAll ? 'primary' : 'secondary'}
                                        size="sm"
                                        className="w-14"
                                    >
                                        {isUpstreamAll ? 'Limited' : 'All'}
                                    </Button>
                                </div>
                            </div>
                            <div className="flex items-center justify-between">
                                <label className="font-medium text-gray-700">Descendants (downstream)</label>
                                <div className="flex items-center gap-2">
                                    <input type="number" min="0" max="99" value={downstream} onChange={e => setDownstream(parseInt(e.target.value, 10))} disabled={isDownstreamAll} className="w-16 p-1 border rounded-md disabled:bg-gray-100 disabled:opacity-70 text-center" />
                                    <Button
                                        onClick={() => setIsDownstreamAll(p => !p)}
                                        variant={isDownstreamAll ? 'primary' : 'secondary'}
                                        size="sm"
                                        className="w-14"
                                    >
                                        {isDownstreamAll ? 'Limited' : 'All'}
                                    </Button>
                                </div>
                            </div>
                        </div>
                    </div>
                    )}
                    <div>
                        <label className="font-semibold block mb-1">{traceMode === 'path' ? '4' : '4'}. Included Schemas ({includedSchemas.size}/{availableSchemas.length})</label>
                        <div className="max-h-32 overflow-y-auto border rounded-md p-2 space-y-1">
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
                    <div>
                        <label className="font-semibold block mb-1">5. Included Types ({includedTypes.size}/{availableTypes.length})</label>
                        <div className="max-h-32 overflow-y-auto border rounded-md p-2 space-y-1">
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
                    <div>
                        <label htmlFor="exclusions-input" className="font-semibold block mb-1">6. Exclusion Patterns</label>
                        <input type="text" id="exclusions-input" value={exclusions} onChange={e => setExclusions(e.target.value)} className="w-full p-2 border rounded-md font-mono text-xs" placeholder="e.g. *_TMP;*_BAK" />
                        <p className="text-xs text-gray-500 mt-1">Separate patterns with a semicolon (;).</p>
                    </div>
                </main>
                <footer className="p-4 border-t flex justify-end gap-2">
                    <Button onClick={handleReset} variant="secondary">Reset</Button>
                    <Button onClick={handleApplyClick} variant="primary">Apply Trace</Button>
                </footer>
            </div>
        </div>
    );
};

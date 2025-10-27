import React, { useState, useEffect } from 'react';
import { DataNode, TraceConfig } from '../types';

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
    const [startNodeSearch, setStartNodeSearch] = useState('');
    const [suggestions, setSuggestions] = useState<DataNode[]>([]);
    const [selectedNode, setSelectedNode] = useState<DataNode | null>(null);
    const [upstream, setUpstream] = useState(3);
    const [isUpstreamAll, setIsUpstreamAll] = useState(false);
    const [downstream, setDownstream] = useState(3);
    const [isDownstreamAll, setIsDownstreamAll] = useState(false);
    const [includedSchemas, setIncludedSchemas] = useState(new Set(availableSchemas));
    const [includedTypes, setIncludedTypes] = useState(new Set(availableTypes));
    const [exclusions, setExclusions] = useState("_TEMP_*;STG_*");

    // Inherit schema and type filters from detail mode when opening trace mode
    useEffect(() => {
        if (isOpen) {
            // Use inherited schema filter from detail mode
            setIncludedSchemas(new Set(inheritedSchemaFilter));
            // Use inherited type filter from detail mode
            setIncludedTypes(new Set(inheritedTypeFilter));
        }
    }, [isOpen, inheritedSchemaFilter, inheritedTypeFilter]);

    const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        setStartNodeSearch(value);
        if (value) {
            setSuggestions(allData.filter(n => n.name.toLowerCase().includes(value.toLowerCase())).slice(0, 5));
        } else {
            setSuggestions([]);
            setSelectedNode(null);
        }
    };
    
    const selectNode = (node: DataNode) => {
        setSelectedNode(node);
        setStartNodeSearch(node.name);
        setSuggestions([]);
    };

    const handleApplyClick = () => {
        if (!selectedNode) {
            addNotification('Please select a valid start node.', 'error');
            return;
        }
        onApply({
            startNodeId: selectedNode.id,
            upstreamLevels: isUpstreamAll ? Number.MAX_SAFE_INTEGER : upstream,
            downstreamLevels: isDownstreamAll ? Number.MAX_SAFE_INTEGER : downstream,
            includedSchemas: includedSchemas,
            includedTypes: includedTypes,
            exclusionPatterns: exclusions.split(';').map(p => p.trim()).filter(p => p !== ''),
        });
    };

    const handleReset = () => {
        setSelectedNode(null);
        setStartNodeSearch('');
        setSuggestions([]);
        setUpstream(3);
        setDownstream(3);
        setIsUpstreamAll(false);
        setIsDownstreamAll(false);
        setIncludedSchemas(new Set(availableSchemas));
        setIncludedTypes(new Set(availableTypes));
        setExclusions("_TEMP_*;STG_*");
    };

    return (
        <div className={`absolute top-0 right-0 h-full bg-white shadow-2xl z-20 w-80 transform transition-transform duration-300 ease-in-out ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}>
            <div className="flex flex-col h-full">
                <header className="flex items-center justify-between p-4 border-b">
                    <h2 className="text-xl font-bold">Interactive Trace</h2>
                    <button onClick={onClose} className="p-1 rounded-full hover:bg-gray-200">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor" className="w-6 h-6"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" /></svg>
                    </button>
                </header>
                <main className="flex-grow p-4 overflow-y-auto space-y-6 text-sm">
                    <div className="relative">
                        <label className="font-semibold block mb-1">1. Start Node</label>
                        <input type="text" placeholder="Search for a node..." value={startNodeSearch} onChange={handleSearchChange} className="w-full p-2 border rounded-md" />
                        {suggestions.length > 0 && (
                            <div className="absolute top-full mt-1 w-full bg-white border rounded-md shadow-lg z-30">
                                {suggestions.map(node => <div key={node.id} onMouseDown={() => selectNode(node)} className="p-2 hover:bg-blue-100 cursor-pointer">{node.name}</div>)}
                            </div>
                        )}
                    </div>
                    <div>
                        <label className="font-semibold block mb-2">2. Trace Levels</label>
                        <div className="space-y-3">
                            <div className="flex items-center justify-between">
                                <label className="font-medium text-gray-700">Ancestors (upstream)</label>
                                <div className="flex items-center gap-2">
                                    <input type="number" min="0" max="99" value={upstream} onChange={e => setUpstream(parseInt(e.target.value, 10))} disabled={isUpstreamAll} className="w-16 p-1 border rounded-md disabled:bg-gray-100 disabled:opacity-70 text-center" />
                                    <button onClick={() => setIsUpstreamAll(p => !p)} className={`w-14 px-2 py-1 text-xs font-semibold rounded-md transition-colors ${isUpstreamAll ? 'bg-blue-600 text-white' : 'bg-gray-200 hover:bg-gray-300'}`}>
                                        {isUpstreamAll ? 'Limited' : 'All'}
                                    </button>
                                </div>
                            </div>
                            <div className="flex items-center justify-between">
                                <label className="font-medium text-gray-700">Descendants (downstream)</label>
                                <div className="flex items-center gap-2">
                                    <input type="number" min="0" max="99" value={downstream} onChange={e => setDownstream(parseInt(e.target.value, 10))} disabled={isDownstreamAll} className="w-16 p-1 border rounded-md disabled:bg-gray-100 disabled:opacity-70 text-center" />
                                    <button onClick={() => setIsDownstreamAll(p => !p)} className={`w-14 px-2 py-1 text-xs font-semibold rounded-md transition-colors ${isDownstreamAll ? 'bg-blue-600 text-white' : 'bg-gray-200 hover:bg-gray-300'}`}>
                                        {isDownstreamAll ? 'Limited' : 'All'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                    <div>
                        <label className="font-semibold block mb-1">3. Included Schemas ({includedSchemas.size}/{availableSchemas.length})</label>
                        <div className="max-h-32 overflow-y-auto border rounded-md p-2 space-y-1">
                            {availableSchemas.map(s => <label key={s} className="flex items-center gap-2 cursor-pointer"><input type="checkbox" checked={includedSchemas.has(s)} onChange={() => { const newSet = new Set(includedSchemas); if (newSet.has(s)) newSet.delete(s); else newSet.add(s); setIncludedSchemas(newSet); }} />{s}</label>)}
                        </div>
                    </div>
                    <div>
                        <label className="font-semibold block mb-1">4. Included Types ({includedTypes.size}/{availableTypes.length})</label>
                        <div className="max-h-32 overflow-y-auto border rounded-md p-2 space-y-1">
                            {availableTypes.map(t => <label key={t} className="flex items-center gap-2 cursor-pointer"><input type="checkbox" checked={includedTypes.has(t)} onChange={() => { const newSet = new Set(includedTypes); if (newSet.has(t)) newSet.delete(t); else newSet.add(t); setIncludedTypes(newSet); }} />{t}</label>)}
                        </div>
                    </div>
                    <div>
                        <label htmlFor="exclusions-input" className="font-semibold block mb-1">5. Exclusion Patterns</label>
                        <input type="text" id="exclusions-input" value={exclusions} onChange={e => setExclusions(e.target.value)} className="w-full p-2 border rounded-md font-mono text-xs" placeholder="e.g. _TEMP_*;STG_*" />
                        <p className="text-xs text-gray-500 mt-1">Separate patterns with a semicolon (;).</p>
                    </div>
                </main>
                <footer className="p-4 border-t flex justify-end gap-2">
                    <button onClick={handleReset} className="h-10 px-4 bg-gray-200 hover:bg-gray-300 font-semibold rounded-lg text-sm">Reset</button>
                    <button onClick={handleApplyClick} className="h-10 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg text-sm">Apply Trace</button>
                </footer>
            </div>
        </div>
    );
};

import React, { useState, useRef } from 'react';
import { DataNode } from '../types';
import { NotificationHistory } from './NotificationSystem';
import { Notification } from '../types';
import { Button } from './ui/Button';
import { Select } from './ui/Select';
import { Checkbox } from './ui/Checkbox';
import { useClickOutside } from '../hooks/useClickOutside';

type ToolbarProps = {
    searchTerm: string;
    setSearchTerm: (term: string) => void;
    executeSearch: (query: string) => void;
    excludeTerm: string;
    setExcludeTerm: (term: string) => void;
    selectedSchemas: Set<string>;
    setSelectedSchemas: (schemas: Set<string>) => void;
    schemas: string[];
    selectedTypes: Set<string>;
    setSelectedTypes: (types: Set<string>) => void;
    dataModelTypes: string[];
    layout: 'LR' | 'TB';
    setLayout: (layout: 'LR' | 'TB') => void;
    hideUnrelated: boolean;
    setHideUnrelated: (hide: boolean) => void;
    isTraceModeActive: boolean;
    onStartTrace: () => void;
    onOpenImport: () => void;
    onOpenInfo: () => void;
    onExportSVG: () => void;
    onResetView: () => void;
    sqlViewerOpen: boolean;
    onToggleSqlViewer: () => void;
    sqlViewerEnabled: boolean;
    hasDdlData: boolean;
    onOpenDetailSearch: () => void;
    notificationHistory: Notification[];
    onClearNotificationHistory: () => void;
    isTraceLocked: boolean;
    isInTraceExitMode: boolean;
    onToggleLock: () => void;
};

// OPTIMIZATION: Memoize to prevent unnecessary re-renders
export const Toolbar = React.memo((props: ToolbarProps) => {
    const {
        searchTerm, setSearchTerm, executeSearch,
        excludeTerm, setExcludeTerm,
        selectedSchemas, setSelectedSchemas, schemas,
        selectedTypes, setSelectedTypes, dataModelTypes,
        layout, setLayout, hideUnrelated, setHideUnrelated,
        isTraceModeActive, onStartTrace,
        onOpenImport, onOpenInfo, onExportSVG, onResetView,
        sqlViewerOpen, onToggleSqlViewer, sqlViewerEnabled, hasDdlData,
        onOpenDetailSearch,
        notificationHistory, onClearNotificationHistory,
        isTraceLocked, isInTraceExitMode, onToggleLock
    } = props;

    const [isSchemaFilterOpen, setIsSchemaFilterOpen] = useState(false);
    const [isTypeFilterOpen, setIsTypeFilterOpen] = useState(false);
    const schemaFilterRef = useRef<HTMLDivElement>(null);
    const typeFilterRef = useRef<HTMLDivElement>(null);

    // Close dropdowns when clicking outside
    useClickOutside(schemaFilterRef, () => setIsSchemaFilterOpen(false));
    useClickOutside(typeFilterRef, () => setIsTypeFilterOpen(false));

    const handleSearch = (event: React.FormEvent<HTMLFormElement>) => {
        try {
            event.preventDefault();
            executeSearch(searchTerm.trim());
        } catch (error) {
            console.error('[Toolbar] Error during search submission:', error);
        }
    };

    const handleSearchInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        try {
            setSearchTerm(e.target.value);
        } catch (error) {
            console.error('[Toolbar] Error during search input change:', error);
            // Reset to empty string on error
            setSearchTerm('');
        }
    };

    const handleExcludeInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        try {
            setExcludeTerm(e.target.value);
        } catch (error) {
            console.error('[Toolbar] Error during exclude input change:', error);
            setExcludeTerm('');
        }
    };

    return (
        <div className="flex items-center justify-between gap-3 px-4 py-2.5 border-b border-gray-200 bg-white">
            {/* LEFT: Search + Filters */}
            <div className="flex items-center gap-2">
                {/* Search */}
                <div className="relative">
                    <form onSubmit={handleSearch} className="flex items-center">
                        <input
                            type="text"
                            placeholder="Search objects..."
                            value={searchTerm}
                            onChange={handleSearchInputChange}
                            disabled={isTraceModeActive}
                            className="text-sm h-9 w-56 pl-3 pr-9 border rounded-md bg-white border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-600 disabled:opacity-50 transition-colors"
                        />
                        <button type="submit" disabled={isTraceModeActive} className="absolute right-0 top-0 h-9 w-9 flex items-center justify-center text-gray-400 hover:text-primary-600 disabled:opacity-50 transition-colors" title="Search">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" className="w-4 h-4"><path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" /></svg>
                        </button>
                    </form>
                </div>

                {/* Exclude Filter with Hide button */}
                <div className="relative flex items-center gap-1">
                    <input
                        type="text"
                        placeholder="Exclude terms..."
                        value={excludeTerm}
                        onChange={handleExcludeInputChange}
                        disabled={isTraceModeActive}
                        className="text-sm h-9 w-40 pl-3 pr-3 border rounded-md bg-white border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-600 disabled:opacity-50 transition-colors"
                        title="Enter terms to exclude (comma-separated)"
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && excludeTerm.trim()) {
                                // Trigger hide on Enter key
                                e.preventDefault();
                            }
                        }}
                    />
                    <Button
                        onClick={() => {
                            // Notify parent that exclude should be applied
                            console.log('[Toolbar] Hide button clicked - exclude terms:', excludeTerm);
                        }}
                        disabled={isTraceModeActive || !excludeTerm.trim()}
                        variant="primary"
                        className="h-9 px-3 text-sm whitespace-nowrap"
                        title="Hide objects containing these terms"
                    >
                        Hide
                    </Button>
                </div>

                {/* Filter Group */}
                <div className="relative" ref={schemaFilterRef}>
                    <Button onClick={() => setIsSchemaFilterOpen(p => !p)} disabled={isTraceModeActive} variant="icon" title={`Schemas (${selectedSchemas.size}/${schemas.length})`}>
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 0 1 6 3.75h2.25A2.25 2.25 0 0 1 10.5 6v2.25a2.25 2.25 0 0 1-2.25 2.25H6a2.25 2.25 0 0 1-2.25-2.25V6ZM3.75 15.75A2.25 2.25 0 0 1 6 13.5h2.25a2.25 2.25 0 0 1 2.25 2.25V18a2.25 2.25 0 0 1-2.25 2.25H6A2.25 2.25 0 0 1 3.75 18v-2.25ZM13.5 6a2.25 2.25 0 0 1 2.25-2.25H18A2.25 2.25 0 0 1 20.25 6v2.25A2.25 2.25 0 0 1 18 10.5h-2.25a2.25 2.25 0 0 1-2.25-2.25V6ZM13.5 15.75a2.25 2.25 0 0 1 2.25-2.25H18a2.25 2.25 0 0 1 2.25 2.25V18A2.25 2.25 0 0 1 18 20.25h-2.25A2.25 2.25 0 0 1 13.5 18v-2.25Z" />
                        </svg>
                    </Button>
                    {isSchemaFilterOpen && (
                        <div className="absolute top-full mt-2 w-80 bg-white border border-gray-300 rounded-md shadow-lg z-30 p-3 max-h-80 overflow-y-auto">
                            <div className="flex items-center justify-between mb-2 pb-2 border-b border-gray-200">
                                <span className="text-xs font-semibold text-gray-600">Schemas ({selectedSchemas.size}/{schemas.length})</span>
                                <div className="flex gap-2">
                                    <Button
                                        onClick={() => setSelectedSchemas(new Set(schemas))}
                                        variant="secondary"
                                        className="text-xs h-7 px-2"
                                        title="Select all schemas"
                                    >
                                        Select All
                                    </Button>
                                    <Button
                                        onClick={() => setSelectedSchemas(new Set())}
                                        variant="secondary"
                                        className="text-xs h-7 px-2"
                                        title="Unselect all schemas"
                                    >
                                        Unselect All
                                    </Button>
                                </div>
                            </div>
                            <div className="space-y-2">
                                {schemas.map(s => (
                                    <Checkbox key={s} checked={selectedSchemas.has(s)} onChange={() => {
                                        const newSet = new Set(selectedSchemas);
                                        if (newSet.has(s)) newSet.delete(s);
                                        else newSet.add(s);
                                        setSelectedSchemas(newSet);
                                    }} label={s} />
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {dataModelTypes.length > 0 && (
                    <div className="relative" ref={typeFilterRef}>
                        <Button onClick={() => setIsTypeFilterOpen(p => !p)} disabled={isTraceModeActive} variant="icon" title={`Types (${selectedTypes.size}/${dataModelTypes.length})`}>
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M9.568 3H5.25A2.25 2.25 0 0 0 3 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 0 0 5.223-5.223c.542-.827.369-1.908-.33-2.607L11.16 3.66A2.25 2.25 0 0 0 9.568 3Z" />
                                <path strokeLinecap="round" strokeLinejoin="round" d="M6 6h.008v.008H6V6Z" />
                            </svg>
                        </Button>
                        {isTypeFilterOpen && (
                            <div className="absolute top-full mt-2 w-80 bg-white border border-gray-300 rounded-md shadow-lg z-30 p-3 max-h-80 overflow-y-auto">
                                <div className="flex items-center justify-between mb-2 pb-2 border-b border-gray-200">
                                    <span className="text-xs font-semibold text-gray-600">Types ({selectedTypes.size}/{dataModelTypes.length})</span>
                                    <div className="flex gap-2">
                                        <Button
                                            onClick={() => setSelectedTypes(new Set(dataModelTypes))}
                                            variant="secondary"
                                            className="text-xs h-7 px-2"
                                            title="Select all types"
                                        >
                                            Select All
                                        </Button>
                                        <Button
                                            onClick={() => setSelectedTypes(new Set())}
                                            variant="secondary"
                                            className="text-xs h-7 px-2"
                                            title="Unselect all types"
                                        >
                                            Unselect All
                                        </Button>
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    {dataModelTypes.map(t => (
                                        <Checkbox key={t} checked={selectedTypes.has(t)} onChange={() => {
                                            const newSet = new Set(selectedTypes);
                                            if (newSet.has(t)) newSet.delete(t);
                                            else newSet.add(t);
                                            setSelectedTypes(newSet);
                                        }} label={t} />
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Divider */}
                <div className="h-6 w-px bg-gray-300 mx-1"></div>

                {/* Layout Toggle */}
                <Button onClick={() => setLayout(layout === 'LR' ? 'TB' : 'LR')} variant="icon" title={layout === 'LR' ? 'Switch to Vertical Layout' : 'Switch to Horizontal Layout'}>
                    {layout === 'LR' ? (
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25H12" />
                        </svg>
                    ) : (
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 6.75h12M8.25 12h12m-12 5.25h12M3.75 6.75h.007v.008H3.75V6.75Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0ZM3.75 12h.007v.008H3.75V12Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Zm-.375 5.25h.007v.008H3.75v-.008Zm.375 0a.375.375 0 1 1-.75 0 .375.375 0 0 1 .75 0Z" />
                        </svg>
                    )}
                </Button>

                {/* Hide Unrelated Toggle */}
                <Button onClick={() => setHideUnrelated(!hideUnrelated)} disabled={isTraceModeActive} variant="icon" className={hideUnrelated ? 'bg-blue-50 text-blue-600' : ''} title={hideUnrelated ? 'Show All Nodes' : 'Hide Unrelated Nodes'}>
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M12 3c2.755 0 5.455.232 8.083.678.533.09.917.556.917 1.096v1.044a2.25 2.25 0 0 1-.659 1.591l-5.432 5.432a2.25 2.25 0 0 0-.659 1.591v2.927a2.25 2.25 0 0 1-1.244 2.013L9.75 21v-6.568a2.25 2.25 0 0 0-.659-1.591L3.659 7.409A2.25 2.25 0 0 1 3 5.818V4.774c0-.54.384-1.006.917-1.096A48.32 48.32 0 0 1 12 3Z" />
                    </svg>
                </Button>
            </div>

            {/* CENTER: Primary Action (ONE only) */}
            <div className="flex-1 flex items-center justify-center">
                {isInTraceExitMode && isTraceLocked ? (
                    <div className="flex items-center gap-2 px-3 py-1.5 bg-yellow-50 border border-yellow-300 rounded-md text-sm text-yellow-800">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-4 h-4">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
                        </svg>
                        Trace Locked
                        <button onClick={onToggleLock} className="ml-1 hover:underline font-medium">Unlock</button>
                    </div>
                ) : (
                    <Button onClick={onStartTrace} variant="primary" size="md" disabled={isTraceModeActive} title="Start Interactive Trace" className="w-36 flex-shrink-0">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                        </svg>
                        Start Trace
                    </Button>
                )}
            </div>

            {/* RIGHT: Action Icons */}
            <div className="flex items-center gap-1">
                <Button onClick={onOpenDetailSearch} disabled={!hasDdlData} variant="icon" title="Detail Search">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607ZM10.5 7.5v6m3-3h-6" />
                    </svg>
                </Button>

                <Button onClick={onToggleSqlViewer} disabled={!sqlViewerEnabled} variant="icon" className={sqlViewerOpen ? 'bg-blue-50 text-blue-600' : ''} title={sqlViewerOpen ? 'Close SQL Viewer' : 'Open SQL Viewer'}>
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M14.25 9.75 16.5 12l-2.25 2.25m-4.5 0L7.5 12l2.25-2.25M6 20.25h12A2.25 2.25 0 0 0 20.25 18V6A2.25 2.25 0 0 0 18 3.75H6A2.25 2.25 0 0 0 3.75 6v12A2.25 2.25 0 0 0 6 20.25Z" />
                    </svg>
                </Button>

                {/* Divider */}
                <div className="h-6 w-px bg-gray-300 mx-1"></div>

                <Button onClick={onResetView} disabled={isTraceModeActive} variant="icon" title="Reset View">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
                    </svg>
                </Button>

                <Button onClick={onExportSVG} variant="icon" title="Export as SVG">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
                    </svg>
                </Button>

                <Button onClick={onOpenImport} variant="icon" title="Import Data">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
                    </svg>
                </Button>

                <NotificationHistory history={notificationHistory} onClearHistory={onClearNotificationHistory} />

                <Button onClick={onOpenInfo} variant="icon" title="Help">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z" />
                    </svg>
                </Button>
            </div>
        </div>
    );
});

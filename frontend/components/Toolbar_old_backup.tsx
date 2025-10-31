import React, { useState, useRef, useEffect } from 'react';
import { DataNode } from '../types';
import { NotificationHistory } from './NotificationSystem';
import { Notification } from '../types';
import { Button } from './ui/Button';
import { Select } from './ui/Select';
import { Checkbox } from './ui/Checkbox';

type ToolbarProps = {
    searchTerm: string;
    setSearchTerm: (term: string) => void;
    executeSearch: (query: string) => void;
    autocompleteSuggestions: DataNode[];
    setAutocompleteSuggestions: (suggestions: DataNode[]) => void;
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
    isControlsVisible: boolean;
    onToggleControls: () => void;
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

export const Toolbar = (props: ToolbarProps) => {
    const {
        searchTerm, setSearchTerm, executeSearch,
        autocompleteSuggestions, setAutocompleteSuggestions,
        selectedSchemas, setSelectedSchemas, schemas,
        selectedTypes, setSelectedTypes, dataModelTypes,
        layout, setLayout, hideUnrelated, setHideUnrelated,
        isTraceModeActive, onStartTrace, isControlsVisible,
        onToggleControls, onOpenImport, onOpenInfo, onExportSVG, onResetView,
        sqlViewerOpen, onToggleSqlViewer, sqlViewerEnabled, hasDdlData,
        onOpenDetailSearch,
        notificationHistory, onClearNotificationHistory,
        isTraceLocked, isInTraceExitMode, onToggleLock
    } = props;
    
    const [isSchemaFilterOpen, setIsSchemaFilterOpen] = useState(false);
    const [isTypeFilterOpen, setIsTypeFilterOpen] = useState(false);
    const schemaFilterRef = useRef<HTMLDivElement>(null);
    const typeFilterRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (schemaFilterRef.current && !schemaFilterRef.current.contains(event.target as Node)) {
                setIsSchemaFilterOpen(false);
            }
            if (typeFilterRef.current && !typeFilterRef.current.contains(event.target as Node)) {
                setIsTypeFilterOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleSearch = (event: React.FormEvent<HTMLFormElement>) => {
        event.preventDefault();
        setAutocompleteSuggestions([]);
        executeSearch(searchTerm.trim());
    };
    
    const handleSuggestionClick = (node: DataNode) => {
        setSearchTerm(node.name);
        setAutocompleteSuggestions([]);
        executeSearch(node.name);
    };

    return (
        <div className="flex flex-wrap items-center justify-between gap-4 p-4 border-b border-gray-200">
            {/* LEFT SECTION: Search, Filters, View Options */}
            <div className="flex items-center gap-3 flex-wrap">
                {/* Search Input */}
                <div className="relative">
                    <form onSubmit={handleSearch} className="flex items-center">
                        <input
                            type="text"
                            placeholder="Find object..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            onBlur={() => setTimeout(() => setAutocompleteSuggestions([]), 150)}
                            disabled={isTraceModeActive}
                            className="text-sm h-10 w-64 pl-3 pr-10 border rounded-lg bg-white border-gray-300 focus:outline-none focus:ring-2 focus:ring-primary-600 disabled:opacity-50 transition-colors"
                        />
                        <button type="submit" disabled={isTraceModeActive} className="absolute right-0 top-0 h-10 w-10 flex items-center justify-center text-gray-500 hover:text-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors" title="Search">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="2" stroke="currentColor" className="w-5 h-5"><path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607Z" /></svg>
                        </button>
                    </form>
                    {autocompleteSuggestions.length > 0 && (
                        <div className="absolute top-full mt-1 w-64 bg-white border border-gray-300 rounded-md shadow-lg z-30 max-h-40 overflow-y-auto">
                            <ul className="py-1">
                                {autocompleteSuggestions.map(node => (
                                    <li
                                        key={node.id}
                                        className="px-3 py-1.5 text-sm text-gray-800 hover:bg-blue-100 cursor-pointer truncate"
                                        title={node.name}
                                        onMouseDown={() => handleSuggestionClick(node)}
                                    >
                                        {node.name}
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>

                {/* Vertical divider */}
                <div className="h-8 w-px bg-gray-300"></div>

                {/* Filter Group */}
                <div className="relative" ref={schemaFilterRef}>
                    <Button onClick={() => setIsSchemaFilterOpen(p => !p)} disabled={isTraceModeActive} variant="secondary" size="sm">
                        Schemas ({selectedSchemas.size}/{schemas.length})
                    </Button>
                    {isSchemaFilterOpen && (
                        <div className="absolute top-full mt-2 w-56 bg-white border border-gray-300 rounded-md shadow-lg z-30 p-3 max-h-60 overflow-y-auto">
                            <div className="space-y-2">
                                {schemas.map(s => (
                                    <Checkbox
                                        key={s}
                                        checked={selectedSchemas.has(s)}
                                        onChange={() => {
                                            const newSet = new Set(selectedSchemas);
                                            if (newSet.has(s)) newSet.delete(s);
                                            else newSet.add(s);
                                            setSelectedSchemas(newSet);
                                        }}
                                        label={s}
                                    />
                                ))}
                            </div>
                        </div>
                    )}
                </div>
                {dataModelTypes.length > 0 && (
                    <div className="relative" ref={typeFilterRef}>
                        <Button onClick={() => setIsTypeFilterOpen(p => !p)} disabled={isTraceModeActive} variant="secondary" size="sm">
                            Types ({selectedTypes.size}/{dataModelTypes.length})
                        </Button>
                        {isTypeFilterOpen && (
                            <div className="absolute top-full mt-2 w-56 bg-white border border-gray-300 rounded-md shadow-lg z-30 p-3 max-h-60 overflow-y-auto">
                                <div className="space-y-2">
                                    {dataModelTypes.map(t => (
                                        <Checkbox
                                            key={t}
                                            checked={selectedTypes.has(t)}
                                            onChange={() => {
                                                const newSet = new Set(selectedTypes);
                                                if (newSet.has(t)) newSet.delete(t);
                                                else newSet.add(t);
                                                setSelectedTypes(newSet);
                                            }}
                                            label={t}
                                        />
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Vertical divider */}
                <div className="h-8 w-px bg-gray-300"></div>

                {/* View Options Group */}
                <Select value={layout} onChange={(e) => setLayout(e.target.value as 'LR' | 'TB')} size="sm">
                    <option value="LR">Horizontal</option>
                    <option value="TB">Vertical</option>
                </Select>
                <div className={`flex items-center h-8 px-2 rounded-lg hover:bg-gray-100 transition-colors ${isTraceModeActive ? 'opacity-50' : ''}`}>
                    <Checkbox
                        checked={hideUnrelated}
                        onChange={(e) => setHideUnrelated(e.target.checked)}
                        disabled={isTraceModeActive}
                        label="Hide Unrelated"
                    />
                </div>
            </div>

            {/* RIGHT SECTION: Actions & Utilities */}
            <div className="flex items-center gap-2 flex-wrap">
                <Button onClick={onStartTrace} variant="primary" className="bg-blue-100 text-blue-700 hover:bg-blue-200" title="Start Interactive Trace">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5"><path strokeLinecap="round" strokeLinejoin="round" d="M12 9.75v6.75m-4.5-3.5h9M3.75 12a9 9 0 0 1 18 0v.001a9 9 0 0 1-18 0V12Z" /></svg>
                    Start Trace
                </Button>
                <Button
                    onClick={onToggleSqlViewer}
                    disabled={!sqlViewerEnabled}
                    variant={sqlViewerOpen ? 'danger' : 'primary'}
                    className={!sqlViewerOpen ? 'bg-blue-100 text-blue-700 hover:bg-blue-200' : ''}
                    title={
                        !hasDdlData
                            ? 'No DDL data available. Upload Parquet files to view SQL.'
                            : sqlViewerOpen
                            ? 'Close SQL Viewer'
                            : 'View SQL Definitions'
                    }
                >
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
                    </svg>
                    {sqlViewerOpen ? 'Close SQL' : 'View SQL'}
                </Button>
                <Button
                    onClick={onOpenDetailSearch}
                    disabled={!hasDdlData}
                    variant="icon"
                    title={
                        !hasDdlData
                            ? 'No DDL data available. Upload Parquet files to search.'
                            : 'Search All DDL Definitions'
                    }
                >
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="m21 21-5.197-5.197m0 0A7.5 7.5 0 1 0 5.196 5.196a7.5 7.5 0 0 0 10.607 10.607ZM10.5 7.5v6m3-3h-6" />
                    </svg>
                </Button>
                {isInTraceExitMode && (
                    <Button
                        onClick={onToggleLock}
                        variant="icon"
                        className={isTraceLocked ? 'bg-yellow-500 hover:bg-yellow-600 text-white' : ''}
                        title={isTraceLocked ? "Unlock - Allow full view" : "Lock - Preserve traced subset"}
                    >
                        {isTraceLocked ? (
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 1 0-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H6.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
                            </svg>
                        ) : (
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 10.5V6.75a4.5 4.5 0 1 1 9 0v3.75M3.75 21.75h10.5a2.25 2.25 0 0 0 2.25-2.25v-6.75a2.25 2.25 0 0 0-2.25-2.25H3.75a2.25 2.25 0 0 0-2.25 2.25v6.75a2.25 2.25 0 0 0 2.25 2.25Z" />
                            </svg>
                        )}
                    </Button>
                )}

                {/* Vertical divider */}
                <div className="h-8 w-px bg-gray-300"></div>

                {/* Utility Actions */}
                <Button onClick={onResetView} disabled={isTraceModeActive} variant="icon" title="Reset View to Default">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0 3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" />
                    </svg>
                </Button>
                <Button onClick={onToggleControls} variant="icon" title={isControlsVisible ? "Hide Overlays" : "Show Overlays"}>
                    {isControlsVisible ? (
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.243 4.243L6.228 6.228" />
                        </svg>
                    ) : (
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.432 0 .639C20.577 16.49 16.64 19.5 12 19.5s-8.573-3.007-9.963-7.178z" />
                                    <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                        </svg>
                    )}
                </Button>
                <Button onClick={onExportSVG} variant="icon" title="Export as SVG">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                        <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5M16.5 12 12 16.5m0 0L7.5 12m4.5 4.5V3" />
                    </svg>
                </Button>
                <Button onClick={onOpenImport} variant="icon" title="Import & Edit Data">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor" className="w-5 h-5"><path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" /></svg>
                </Button>
                <Button onClick={onOpenInfo} variant="icon" title="About this App">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor" className="w-5 h-5"><path strokeLinecap="round" strokeLinejoin="round" d="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z" /></svg>
                </Button>
                <NotificationHistory history={notificationHistory} onClearHistory={onClearNotificationHistory} />
            </div>
        </div>
    );
};
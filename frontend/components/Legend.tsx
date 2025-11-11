import React, { useState } from 'react';

type LegendProps = {
    isCollapsed: boolean;
    onToggle: () => void;
    schemas: string[];
    schemaColorMap: Map<string, string>;
    selectedSchemas: Set<string>;
};

const LegendIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6 text-gray-700">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 4.5v15m6-15v15m-10.875 0h15.75c.621 0 1.125-.504 1.125-1.125V5.625c0-.621-.504-1.125-1.125-1.125H4.125C3.504 4.5 3 5.004 3 5.625v12.75c0 .621.504 1.125 1.125 1.125z" />
    </svg>
);

export const Legend = React.memo(({ isCollapsed, onToggle, schemas, schemaColorMap, selectedSchemas }: LegendProps) => {
    const [isSchemasExpanded, setIsSchemasExpanded] = useState(false);

    // Filter to show only selected schemas
    const filteredSchemas = schemas.filter(schema => selectedSchemas.has(schema));
    const schemasToShow = isSchemasExpanded ? filteredSchemas : filteredSchemas.slice(0, 8);

    return (
        <div className={`
            absolute top-4 left-4 text-xs rounded-lg bg-white/80 backdrop-blur-sm shadow-lg
            pointer-events-auto z-10 transition-all duration-300 ease-in-out overflow-hidden
            ${isCollapsed ? 'w-14 h-14' : 'w-80'}
        `}>
            <div className="w-80">
                <div
                    className="flex items-center justify-between cursor-pointer select-none p-4 h-14"
                    onClick={onToggle}
                    role="button"
                    aria-expanded={!isCollapsed}
                    aria-controls="legend-content"
                >
                    <div className="flex items-center gap-2">
                        <LegendIcon />
                        <h4 className={`
                            text-sm font-bold text-gray-800 whitespace-nowrap
                            transition-opacity duration-200
                            ${isCollapsed ? 'opacity-0' : 'opacity-100 delay-150'}
                        `}>Schemas</h4>
                    </div>

                    <div className={`
                        transition-opacity duration-200
                        ${isCollapsed ? 'opacity-0' : 'opacity-100 delay-150'}
                    `}>
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="2.5" stroke="currentColor" className={`w-4 h-4 transition-transform duration-300 text-gray-600 ${isCollapsed ? '' : 'rotate-180'}`}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="m4.5 15.75 7.5-7.5 7.5 7.5" />
                        </svg>
                    </div>
                </div>

                <div
                    id="legend-content"
                    className={`
                        px-4 pb-4 overflow-hidden transition-opacity duration-200
                        ${isCollapsed ? 'opacity-0' : 'opacity-100 delay-150'}
                    `}
                >
                    <div className="overflow-y-auto max-h-[calc(40vh-56px)]">
                        {/* Schemas Section */}
                        <div className="grid grid-cols-1 gap-y-1.5 mb-4">
                            {schemasToShow.map(s => (
                                <div key={s} className="flex items-center gap-2" title={s}>
                                    <span style={{ backgroundColor: schemaColorMap.get(s) }} className="w-3 h-3 inline-block rounded-sm ring-1 ring-black/20 flex-shrink-0"></span>
                                    <span className="text-gray-700">{s}</span>
                                </div>
                            ))}
                        </div>
                        {!isSchemasExpanded && filteredSchemas.length > 8 && (
                            <button
                                onClick={() => setIsSchemasExpanded(true)}
                                className="text-blue-600 mt-2 mb-4 text-xs font-semibold hover:underline w-full text-left"
                            >
                                ...and {filteredSchemas.length - 8} more
                            </button>
                        )}

                        {/* Node Types Section (v4.3.0) */}
                        <div className="border-t border-gray-300 pt-3 mt-2">
                            <h5 className="text-xs font-semibold text-gray-700 mb-2">Node Types</h5>
                            <div className="grid grid-cols-1 gap-y-1.5 text-xs">
                                <div className="flex items-center gap-2">
                                    <span className="w-3 h-3 inline-block rounded-full bg-blue-400 ring-1 ring-black/20"></span>
                                    <span className="text-gray-700">Table / View</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className="w-3 h-3 inline-block rounded-md bg-green-400 ring-1 ring-black/20"></span>
                                    <span className="text-gray-700">Stored Procedure</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className="w-3 h-3 inline-block bg-purple-400 ring-1 ring-black/20 transform rotate-45"></span>
                                    <span className="text-gray-700">Function (UDF)</span>
                                </div>
                                <div className="flex items-center gap-2 mt-1">
                                    <svg width="14" height="14" viewBox="0 0 24 24" className="flex-shrink-0">
                                        <circle cx="12" cy="12" r="10" fill="#ff9800" opacity="0.95" />
                                        <text x="12" y="17" fontSize="16" fontWeight="bold" fill="white" textAnchor="middle">?</text>
                                    </svg>
                                    <span className="text-gray-700">Phantom (Not in catalog)</span>
                                </div>
                            </div>
                        </div>

                        {/* Edge Types Section (v4.3.0) */}
                        <div className="border-t border-gray-300 pt-3 mt-3">
                            <h5 className="text-xs font-semibold text-gray-700 mb-2">Edge Types</h5>
                            <div className="grid grid-cols-1 gap-y-1.5 text-xs">
                                <div className="flex items-center gap-2">
                                    <svg width="30" height="12" className="flex-shrink-0">
                                        <line x1="0" y1="6" x2="30" y2="6" stroke="#999" strokeWidth="2" />
                                    </svg>
                                    <span className="text-gray-700">Normal</span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <svg width="30" height="12" className="flex-shrink-0">
                                        <line x1="0" y1="6" x2="30" y2="6" stroke="#ff9800" strokeWidth="2" strokeDasharray="4,4" />
                                    </svg>
                                    <span className="text-gray-700">Phantom connection</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
});

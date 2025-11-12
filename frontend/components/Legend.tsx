import React, { useState, useMemo } from 'react';
import { DataNode } from '../types';

type LegendProps = {
    isCollapsed: boolean;
    onToggle: () => void;
    schemas: string[];
    schemaColorMap: Map<string, string>;
    selectedSchemas: Set<string>;
    nodes: DataNode[];
};

const LegendIcon = () => (
    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-6 h-6 text-gray-700">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 4.5v15m6-15v15m-10.875 0h15.75c.621 0 1.125-.504 1.125-1.125V5.625c0-.621-.504-1.125-1.125-1.125H4.125C3.504 4.5 3 5.004 3 5.625v12.75c0 .621.504 1.125 1.125 1.125z" />
    </svg>
);

export const Legend = React.memo(({ isCollapsed, onToggle, schemas, schemaColorMap, selectedSchemas, nodes }: LegendProps) => {
    const [isSchemasExpanded, setIsSchemasExpanded] = useState(false);

    // Detect phantom schemas (schemas that ONLY contain phantom objects, no regular objects)
    const phantomSchemas = useMemo(() => {
        const schemasWithPhantoms = new Set<string>();
        const schemasWithRegular = new Set<string>();

        nodes.forEach(node => {
            if (node.is_phantom) {
                schemasWithPhantoms.add(node.schema);
            } else {
                schemasWithRegular.add(node.schema);
            }
        });

        // Only mark as phantom if schema has phantom objects but NO regular objects
        const phantomOnlySchemas = new Set<string>();
        schemasWithPhantoms.forEach(schema => {
            if (!schemasWithRegular.has(schema)) {
                phantomOnlySchemas.add(schema);
            }
        });

        return phantomOnlySchemas;
    }, [nodes]);

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
                        <div className="grid grid-cols-1 gap-y-1.5">
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
                                className="text-blue-600 mt-2 text-xs font-semibold hover:underline w-full text-left"
                            >
                                ...and {filteredSchemas.length - 8} more
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
});

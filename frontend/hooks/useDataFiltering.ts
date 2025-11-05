import { useState, useMemo, useEffect } from 'react';
import { DataNode, TraceConfig } from '../types';
import Graph from 'graphology';
import { INTERACTION_CONSTANTS } from '../interaction-constants';

type UseDataFilteringProps = {
    allData: DataNode[];
    lineageGraph: Graph;
    schemas: string[];
    dataModelTypes: string[];
    isTraceModeActive: boolean;
    traceConfig: TraceConfig | null;
    performInteractiveTrace: (config: TraceConfig) => Set<string>;
    isInTraceExitMode: boolean;
    traceExitNodes: Set<string>;
};

export function useDataFiltering({
    allData,
    lineageGraph,
    schemas,
    dataModelTypes,
    isTraceModeActive,
    traceConfig,
    performInteractiveTrace,
    isInTraceExitMode,
    traceExitNodes
}: UseDataFilteringProps) {
    const [selectedSchemas, setSelectedSchemas] = useState<Set<string>>(new Set());
    const [selectedTypes, setSelectedTypes] = useState<Set<string>>(new Set());
    const [searchTerm, setSearchTerm] = useState('');
    const [excludeTerm, setExcludeTerm] = useState('');
    const [hideUnrelated, setHideUnrelated] = useState(false);
    const [highlightedNodes, setHighlightedNodes] = useState<Set<string>>(new Set());

    useEffect(() => {
        setSelectedSchemas(new Set(schemas));
    }, [schemas]);

    useEffect(() => {
        setSelectedTypes(new Set(dataModelTypes));
    }, [dataModelTypes]);

    // Static pre-filter: Apply "Hide Unrelated" and "Exclude" BEFORE any other filters
    // This is memoized separately so it doesn't recalculate when clicking nodes
    const preFilteredData = useMemo(() => {
        let filtered = allData;

        // Apply "Hide Unrelated" filter
        if (hideUnrelated) {
            // Filter out nodes with NO connections in the complete graph
            filtered = filtered.filter(node => {
                if (lineageGraph.hasNode(node.id)) {
                    const neighbors = lineageGraph.neighbors(node.id);
                    return neighbors.length > 0; // Keep only nodes with at least one connection
                }
                return false; // Remove nodes not in graph
            });
        }

        // Apply "Exclude" filter
        if (excludeTerm.trim()) {
            const excludeTerms = excludeTerm.toLowerCase().split(/\s+/).filter(t => t.length > 0);
            filtered = filtered.filter(node => {
                const nodeName = node.name.toLowerCase();
                // Exclude node if ANY exclude term is found in the node name
                return !excludeTerms.some(term => nodeName.includes(term));
            });
        }

        return filtered;
    }, [allData, lineageGraph, hideUnrelated, excludeTerm]);

    const finalVisibleData = useMemo(() => {
        // If in trace mode, the trace config's filters take precedence.
        if (isTraceModeActive && traceConfig) {
            const tracedIds = performInteractiveTrace(traceConfig);
            return preFilteredData.filter(node => tracedIds.has(node.id));
        }

        // If in trace exit mode, show only the traced nodes (preserve trace results)
        // but still allow filtering by schemas and types within this subset
        if (isInTraceExitMode && traceExitNodes.size > 0) {
            return preFilteredData.filter(node =>
                traceExitNodes.has(node.id) &&
                selectedSchemas.has(node.schema) &&
                (dataModelTypes.length === 0 || !node.data_model_type || selectedTypes.has(node.data_model_type))
            );
        }

        // Default behavior: filter by selected schemas and types.
        const baseVisibleNodes: DataNode[] = [];
        lineageGraph.forEachNode((nodeId, attributes) => {
            // Only process nodes that passed the pre-filter
            if (!preFilteredData.find(n => n.id === nodeId)) return;

            if (
                selectedSchemas.has(attributes.schema) &&
                (dataModelTypes.length === 0 || !attributes.data_model_type || selectedTypes.has(attributes.data_model_type))
            ) {
                baseVisibleNodes.push(attributes as DataNode);
            }
        });

        return baseVisibleNodes;
    }, [preFilteredData, lineageGraph, selectedSchemas, selectedTypes, dataModelTypes, isTraceModeActive, traceConfig, performInteractiveTrace, isInTraceExitMode, traceExitNodes, allData]);

    return {
        finalVisibleData,
        selectedSchemas,
        setSelectedSchemas,
        selectedTypes,
        setSelectedTypes,
        searchTerm,
        setSearchTerm,
        excludeTerm,
        setExcludeTerm,
        hideUnrelated,
        setHideUnrelated,
        highlightedNodes,
        setHighlightedNodes,
    };
}
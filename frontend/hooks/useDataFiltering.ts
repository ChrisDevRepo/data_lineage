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
    const [hideUnrelated, setHideUnrelated] = useState(false);
    const [highlightedNodes, setHighlightedNodes] = useState<Set<string>>(new Set());
    const [autocompleteSuggestions, setAutocompleteSuggestions] = useState<DataNode[]>([]);

    useEffect(() => {
        setSelectedSchemas(new Set(schemas));
    }, [schemas]);

    useEffect(() => {
        setSelectedTypes(new Set(dataModelTypes));
    }, [dataModelTypes]);
    
    useEffect(() => {
        if (searchTerm.trim() === '') {
            setAutocompleteSuggestions([]);
            return;
        }

        const suggestions: DataNode[] = [];
        // Use for...of loop with break for early exit (cleaner than try/catch pattern)
        for (const [nodeId, attributes] of lineageGraph.nodeEntries()) {
            if (suggestions.length >= INTERACTION_CONSTANTS.AUTOCOMPLETE_MAX_RESULTS) break;

            if (
                attributes.name.toLowerCase().startsWith(searchTerm.toLowerCase()) &&
                selectedSchemas.has(attributes.schema) &&
                (dataModelTypes.length === 0 || !attributes.data_model_type || selectedTypes.has(attributes.data_model_type))
            ) {
                suggestions.push(attributes as DataNode);
            }
        }

        setAutocompleteSuggestions(suggestions);
    }, [searchTerm, lineageGraph, selectedSchemas, selectedTypes, dataModelTypes]);

    // Static pre-filter: Apply "Hide Unrelated" BEFORE any other filters
    // This is memoized separately so it doesn't recalculate when clicking nodes
    const preFilteredData = useMemo(() => {
        if (hideUnrelated) {
            // Filter out nodes with NO connections in the complete graph
            return allData.filter(node => {
                if (lineageGraph.hasNode(node.id)) {
                    const neighbors = lineageGraph.neighbors(node.id);
                    return neighbors.length > 0; // Keep only nodes with at least one connection
                }
                return false; // Remove nodes not in graph
            });
        }
        return allData; // No pre-filtering if hideUnrelated is off
    }, [allData, lineageGraph, hideUnrelated]);

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
        hideUnrelated,
        setHideUnrelated,
        highlightedNodes,
        setHighlightedNodes,
        autocompleteSuggestions,
        setAutocompleteSuggestions,
    };
}
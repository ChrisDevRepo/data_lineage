import { useState, useMemo, useEffect } from 'react';
import { DataNode, TraceConfig } from '../types';
import Graph from 'graphology';

type UseDataFilteringProps = {
    allData: DataNode[];
    lineageGraph: Graph;
    schemas: string[];
    dataModelTypes: string[];
    isTraceModeActive: boolean;
    traceConfig: TraceConfig | null;
    performInteractiveTrace: (config: TraceConfig) => Set<string>;
};

export function useDataFiltering({
    allData,
    lineageGraph,
    schemas,
    dataModelTypes,
    isTraceModeActive,
    traceConfig,
    performInteractiveTrace
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
        // This logic is complex because `findNode` is not available in all graphology versions,
        // and we need to break early from the loop for performance.
        try {
            lineageGraph.forEachNode((nodeId, attributes) => {
                if (suggestions.length >= 5) {
                    throw new Error('Break'); // Early exit from forEachNode
                }
                if (
                    attributes.name.toLowerCase().startsWith(searchTerm.toLowerCase()) &&
                    selectedSchemas.has(attributes.schema) &&
                    (dataModelTypes.length === 0 || !attributes.data_model_type || selectedTypes.has(attributes.data_model_type))
                ) {
                    suggestions.push(attributes as DataNode);
                }
            });
        } catch (e) {
            if ((e as Error).message !== 'Break') throw e;
        }

        setAutocompleteSuggestions(suggestions);
    }, [searchTerm, lineageGraph, selectedSchemas, selectedTypes, dataModelTypes]);

    const finalVisibleData = useMemo(() => {
        // If in trace mode, the trace config's filters take precedence.
        if (isTraceModeActive && traceConfig) {
            const tracedIds = performInteractiveTrace(traceConfig);
            return allData.filter(node => tracedIds.has(node.id));
        }

        // If a node is highlighted and we want to hide unrelated, this acts as a "focus mode".
        if (hideUnrelated && highlightedNodes.size > 0) {
            return allData.filter(node => highlightedNodes.has(node.id));
        }

        // Default behavior: filter by selected schemas and types.
        const baseVisibleNodes: DataNode[] = [];
        lineageGraph.forEachNode((nodeId, attributes) => {
            if (
                selectedSchemas.has(attributes.schema) &&
                (dataModelTypes.length === 0 || !attributes.data_model_type || selectedTypes.has(attributes.data_model_type))
            ) {
                baseVisibleNodes.push(attributes as DataNode);
            }
        });
        
        // When no node is selected, "Hide Unrelated" filters out nodes that are isolated from other visible nodes.
        if (hideUnrelated) {
            const baseVisibleNodeIds = new Set(baseVisibleNodes.map(n => n.id));

            return baseVisibleNodes.filter(node => {
                const neighbors = lineageGraph.neighbors(node.id);
                // Keep the node if any of its neighbors are also in the visible set.
                return neighbors.some(neighborId => baseVisibleNodeIds.has(neighborId));
            });
        }
        
        return baseVisibleNodes;
    }, [allData, lineageGraph, selectedSchemas, selectedTypes, dataModelTypes, hideUnrelated, highlightedNodes, isTraceModeActive, traceConfig, performInteractiveTrace]);

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
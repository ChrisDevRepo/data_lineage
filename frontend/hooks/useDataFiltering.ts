import { useState, useMemo, useEffect, useRef } from 'react';
import { DataNode, TraceConfig } from '../types';
import Graph from 'graphology';
import { INTERACTION_CONSTANTS } from '../interaction-constants';

type UseDataFilteringProps = {
    allData: DataNode[];
    lineageGraph: Graph;
    schemas: string[];
    dataModelTypes: string[];
    activeExcludeTerms: string[];
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
    activeExcludeTerms,
    isTraceModeActive,
    traceConfig,
    performInteractiveTrace,
    isInTraceExitMode,
    traceExitNodes
}: UseDataFilteringProps) {
    const [selectedSchemas, setSelectedSchemas] = useState<Set<string>>(new Set());
    const [selectedTypes, setSelectedTypes] = useState<Set<string>>(new Set());
    const [searchTerm, setSearchTerm] = useState('');
    const [highlightedNodes, setHighlightedNodes] = useState<Set<string>>(new Set());
    const [autocompleteSuggestions, setAutocompleteSuggestions] = useState<DataNode[]>([]);

    // Initialize hideUnrelated from localStorage or default to true
    const [hideUnrelated, setHideUnrelated] = useState<boolean>(() => {
        try {
            const saved = localStorage.getItem('lineage_filter_preferences');
            if (saved) {
                const { hideUnrelated: savedHideUnrelated } = JSON.parse(saved);
                if (typeof savedHideUnrelated === 'boolean') {
                    return savedHideUnrelated;
                }
            }
        } catch (error) {
            console.error('[useDataFiltering] Failed to load hideUnrelated preference:', error);
        }
        return true; // Default: hide unrelated nodes
    });

    // Debounced versions for performance with large datasets
    const [debouncedSelectedSchemas, setDebouncedSelectedSchemas] = useState<Set<string>>(new Set());
    const [debouncedSelectedTypes, setDebouncedSelectedTypes] = useState<Set<string>>(new Set());
    const debounceTimerRef = useRef<number>();

    // Track if schemas have been initialized (from localStorage or default)
    const hasInitializedSchemas = useRef(false);
    const hasInitializedTypes = useRef(false);

    // Initialize schemas from localStorage or default to all
    useEffect(() => {
        if (schemas.length > 0 && !hasInitializedSchemas.current) {
            hasInitializedSchemas.current = true;

            // Try to load from localStorage first
            try {
                const saved = localStorage.getItem('lineage_filter_preferences');
                if (saved) {
                    const { schemas: savedSchemas } = JSON.parse(saved);
                    if (savedSchemas && Array.isArray(savedSchemas)) {
                        const validSavedSchemas = savedSchemas.filter(s => schemas.includes(s));
                        if (validSavedSchemas.length > 0) {
                            setSelectedSchemas(new Set(validSavedSchemas));
                            return; // Exit early, we loaded from localStorage
                        }
                    }
                }
            } catch (error) {
                console.error('[useDataFiltering] Failed to load schema preferences:', error);
            }

            // Default: select all schemas
            setSelectedSchemas(new Set(schemas));
        }
    }, [schemas]);

    // Initialize types from localStorage or default to all
    useEffect(() => {
        if (dataModelTypes.length > 0 && !hasInitializedTypes.current) {
            hasInitializedTypes.current = true;

            // Try to load from localStorage first
            try {
                const saved = localStorage.getItem('lineage_filter_preferences');
                if (saved) {
                    const { types: savedTypes } = JSON.parse(saved);
                    if (savedTypes && Array.isArray(savedTypes)) {
                        const validSavedTypes = savedTypes.filter(t => dataModelTypes.includes(t));
                        if (validSavedTypes.length > 0) {
                            setSelectedTypes(new Set(validSavedTypes));
                            return; // Exit early, we loaded from localStorage
                        }
                    }
                }
            } catch (error) {
                console.error('[useDataFiltering] Failed to load type preferences:', error);
            }

            // Default: select all types
            setSelectedTypes(new Set(dataModelTypes));
        }
    }, [dataModelTypes]);

    // Debounce filter updates for large datasets (>500 nodes)
    useEffect(() => {
        const shouldDebounce = allData.length > 500;
        const debounceDelay = 150; // 150ms feels responsive while preventing stuttering

        if (debounceTimerRef.current) {
            clearTimeout(debounceTimerRef.current);
        }

        if (shouldDebounce) {
            debounceTimerRef.current = window.setTimeout(() => {
                setDebouncedSelectedSchemas(selectedSchemas);
                setDebouncedSelectedTypes(selectedTypes);
            }, debounceDelay);
        } else {
            // For small datasets (<500 nodes), update immediately
            setDebouncedSelectedSchemas(selectedSchemas);
            setDebouncedSelectedTypes(selectedTypes);
        }

        return () => {
            if (debounceTimerRef.current) {
                clearTimeout(debounceTimerRef.current);
            }
        };
    }, [selectedSchemas, selectedTypes, allData.length]);
    
    useEffect(() => {
        const trimmedSearch = searchTerm.trim();

        // Don't show autocomplete if search term is empty or too short
        if (trimmedSearch === '' || trimmedSearch.length < INTERACTION_CONSTANTS.AUTOCOMPLETE_MIN_CHARS) {
            setAutocompleteSuggestions([]);
            return;
        }

        // Safety check: ensure lineageGraph is initialized before accessing
        if (!lineageGraph || typeof lineageGraph.nodeEntries !== 'function') {
            setAutocompleteSuggestions([]);
            return;
        }

        try {
            const startsWithMatches: DataNode[] = [];
            const containsMatches: DataNode[] = [];
            const lowerSearchTerm = trimmedSearch.toLowerCase();

            // Collect matches, prioritizing startsWith over contains
            lineageGraph.forEachNode((nodeId, attributes) => {
                // Safety check: ensure attributes and required properties exist
                if (!attributes || typeof attributes.name !== 'string' || typeof attributes.schema !== 'string') {
                    console.warn(`[Autocomplete] Skipping node ${nodeId} with invalid attributes:`, attributes);
                    return;
                }

                const lowerName = attributes.name.toLowerCase();
                const matchesFilters =
                    debouncedSelectedSchemas.has(attributes.schema) &&
                    (dataModelTypes.length === 0 || !attributes.data_model_type || debouncedSelectedTypes.has(attributes.data_model_type));

                if (matchesFilters) {
                    if (lowerName.startsWith(lowerSearchTerm)) {
                        startsWithMatches.push(attributes as DataNode);
                    } else if (lowerName.includes(lowerSearchTerm)) {
                        containsMatches.push(attributes as DataNode);
                    }
                }
            });

            // Combine results: startsWith first, then contains, up to max limit
            const suggestions = [
                ...startsWithMatches,
                ...containsMatches
            ].slice(0, INTERACTION_CONSTANTS.AUTOCOMPLETE_MAX_RESULTS);

            setAutocompleteSuggestions(suggestions);
        } catch (error) {
            console.error('[Autocomplete] Error generating suggestions:', error);
            setAutocompleteSuggestions([]);
        }
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

    // Helper function to check if a node should be excluded based on exclude terms
    const shouldExcludeNode = (node: DataNode): boolean => {
        if (activeExcludeTerms.length === 0) return false;

        const nodeName = node.name.toLowerCase();
        return activeExcludeTerms.some(term => nodeName.includes(term));
    };

    const finalVisibleData = useMemo(() => {
        // If in trace mode, the trace config's filters take precedence.
        if (isTraceModeActive && traceConfig) {
            const tracedIds = performInteractiveTrace(traceConfig);
            return preFilteredData.filter(node =>
                tracedIds.has(node.id) && !shouldExcludeNode(node)
            );
        }

        // If in trace exit mode, show only the traced nodes (preserve trace results)
        // but still allow filtering by schemas and types within this subset
        if (isInTraceExitMode && traceExitNodes.size > 0) {
            return preFilteredData.filter(node =>
                traceExitNodes.has(node.id) &&
                debouncedSelectedSchemas.has(node.schema) &&
                (dataModelTypes.length === 0 || !node.data_model_type || debouncedSelectedTypes.has(node.data_model_type)) &&
                !shouldExcludeNode(node)
            );
        }

        // Default behavior: filter by selected schemas and types
        // Optimized O(n) array filtering instead of O(n²) graph iteration
        return preFilteredData.filter(node =>
            debouncedSelectedSchemas.has(node.schema) &&
            (dataModelTypes.length === 0 || !node.data_model_type || debouncedSelectedTypes.has(node.data_model_type)) &&
            !shouldExcludeNode(node)
        );
    }, [preFilteredData, debouncedSelectedSchemas, debouncedSelectedTypes, dataModelTypes, isTraceModeActive, traceConfig, performInteractiveTrace, isInTraceExitMode, traceExitNodes, activeExcludeTerms]);

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
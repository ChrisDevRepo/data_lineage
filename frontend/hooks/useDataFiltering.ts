import { useState, useMemo, useEffect, useRef } from 'react';
import { DataNode, TraceConfig } from '../types';
import Graph from 'graphology';
import { INTERACTION_CONSTANTS } from '../interaction-constants';
import { patternToRegex } from '../utils/layout';

type UseDataFilteringProps = {
    allData: DataNode[];
    lineageGraph: Graph;
    schemas: string[];
    objectTypes: string[];
    dataModelTypes: string[];
    activeExcludeTerms: string[];
    isTraceModeActive: boolean;
    traceConfig: TraceConfig | null;
    performInteractiveTrace: (config: TraceConfig) => Set<string>;
    isInTraceExitMode: boolean;
    traceExitNodes: Set<string>;
    isTraceFilterApplied: boolean;
};

export function useDataFiltering({
    allData,
    lineageGraph,
    schemas,
    objectTypes,
    dataModelTypes,
    activeExcludeTerms,
    isTraceModeActive,
    traceConfig,
    performInteractiveTrace,
    isInTraceExitMode,
    traceExitNodes,
    isTraceFilterApplied
}: UseDataFilteringProps) {
    const [selectedSchemas, setSelectedSchemas] = useState<Set<string>>(new Set());
    const [selectedObjectTypes, setSelectedObjectTypes] = useState<Set<string>>(new Set());
    const [selectedTypes, setSelectedTypes] = useState<Set<string>>(new Set());
    const [searchTerm, setSearchTerm] = useState('');
    const [highlightedNodes, setHighlightedNodes] = useState<Set<string>>(new Set());
    const [autocompleteSuggestions, setAutocompleteSuggestions] = useState<DataNode[]>([]);

    // Initialize hideIsolated from localStorage or default to true
    // "Isolated nodes" = nodes with degree 0 in the COMPLETE graph (no connections at all)
    const [hideIsolated, setHideIsolated] = useState<boolean>(() => {
        try {
            const saved = localStorage.getItem('lineage_filter_preferences');
            if (saved) {
                const { hideIsolated: savedHideIsolated } = JSON.parse(saved);
                if (typeof savedHideIsolated === 'boolean') {
                    return savedHideIsolated;
                }
            }
        } catch (error) {
            console.error('[useDataFiltering] Failed to load hideIsolated preference:', error);
        }
        return true; // Default: hide isolated nodes
    });

    // Initialize hideUnrelated from localStorage or default to false
    // "Unrelated nodes" = nodes with no connections in the FILTERED graph (filter context-aware)
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
        return false; // Default: show unrelated nodes (only hide when filters active)
    });

    // Debounced versions for performance with large datasets
    const [debouncedSelectedSchemas, setDebouncedSelectedSchemas] = useState<Set<string>>(new Set());
    const [debouncedSelectedObjectTypes, setDebouncedSelectedObjectTypes] = useState<Set<string>>(new Set());
    const [debouncedSelectedTypes, setDebouncedSelectedTypes] = useState<Set<string>>(new Set());
    const debounceTimerRef = useRef<number>();

    // Track if schemas have been initialized (from localStorage or default)
    const hasInitializedSchemas = useRef(false);
    const hasInitializedObjectTypes = useRef(false);
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

    // Initialize object types from localStorage or default to all
    useEffect(() => {
        if (objectTypes.length > 0 && !hasInitializedObjectTypes.current) {
            hasInitializedObjectTypes.current = true;

            // Try to load from localStorage first
            try {
                const saved = localStorage.getItem('lineage_filter_preferences');
                if (saved) {
                    const { objectTypes: savedObjectTypes } = JSON.parse(saved);
                    if (savedObjectTypes && Array.isArray(savedObjectTypes)) {
                        const validSavedObjectTypes = savedObjectTypes.filter(t => objectTypes.includes(t));
                        if (validSavedObjectTypes.length > 0) {
                            setSelectedObjectTypes(new Set(validSavedObjectTypes));
                            return; // Exit early, we loaded from localStorage
                        }
                    }
                }
            } catch (error) {
                console.error('[useDataFiltering] Failed to load object type preferences:', error);
            }

            // Default: select all object types
            setSelectedObjectTypes(new Set(objectTypes));
        }
    }, [objectTypes]);

    // Initialize data model types from localStorage or default to all
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
                setDebouncedSelectedObjectTypes(selectedObjectTypes);
                setDebouncedSelectedTypes(selectedTypes);
            }, debounceDelay);
        } else {
            // For small datasets (<500 nodes), update immediately
            setDebouncedSelectedSchemas(selectedSchemas);
            setDebouncedSelectedObjectTypes(selectedObjectTypes);
            setDebouncedSelectedTypes(selectedTypes);
        }

        return () => {
            if (debounceTimerRef.current) {
                clearTimeout(debounceTimerRef.current);
            }
        };
    }, [selectedSchemas, selectedObjectTypes, selectedTypes, allData.length]);
    
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
                    (objectTypes.length === 0 || !attributes.object_type || debouncedSelectedObjectTypes.has(attributes.object_type)) &&
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

    // Static pre-filter: Apply "Hide Isolated" BEFORE any other filters
    // Isolated nodes = degree 0 in COMPLETE graph (no connections at all)
    // This is memoized separately so it doesn't recalculate when clicking nodes
    const preFilteredData = useMemo(() => {
        if (hideIsolated) {
            // Filter out nodes with NO connections in the complete graph
            const filtered = allData.filter(node => {
                if (lineageGraph.hasNode(node.id)) {
                    const neighbors = lineageGraph.neighbors(node.id);
                    return neighbors.length > 0; // Keep only nodes with at least one connection
                }
                return false; // Remove nodes not in graph
            });
            return filtered;
        }
        return allData; // No pre-filtering if hideIsolated is off
    }, [allData, lineageGraph, hideIsolated]);

    // Helper function to check if a node should be excluded based on exclude terms
    // Supports wildcard patterns (e.g., "*_VAT", "tmp_*", "*test*")
    const shouldExcludeNode = (node: DataNode): boolean => {
        if (activeExcludeTerms.length === 0) return false;

        // Convert patterns to regex (supports wildcards like trace mode)
        const excluded = activeExcludeTerms.some(term => {
            const regex = patternToRegex(term);
            return regex.test(node.name);
        });

        return excluded;
    };

    const finalVisibleData = useMemo(() => {
        // If trace filter is applied (during or after trace mode), combine with base filters (AND condition)
        // This ensures trace + schemas + object types + data model types + exclude all work together
        if (isTraceFilterApplied && traceConfig) {
            const tracedIds = performInteractiveTrace(traceConfig);
            const result = preFilteredData.filter(node =>
                tracedIds.has(node.id) &&
                debouncedSelectedSchemas.has(node.schema) &&
                (objectTypes.length === 0 || !node.object_type || debouncedSelectedObjectTypes.has(node.object_type)) &&
                (dataModelTypes.length === 0 || !node.data_model_type || debouncedSelectedTypes.has(node.data_model_type)) &&
                !shouldExcludeNode(node)
            );
            return result;
        }

        // If in trace mode but Apply not clicked yet, show ALL filtered objects (base filters only)
        // The trace is only for highlighting, not for filtering visibility
        if (isTraceModeActive && traceConfig) {
            const result = preFilteredData.filter(node =>
                debouncedSelectedSchemas.has(node.schema) &&
                (objectTypes.length === 0 || !node.object_type || debouncedSelectedObjectTypes.has(node.object_type)) &&
                (dataModelTypes.length === 0 || !node.data_model_type || debouncedSelectedTypes.has(node.data_model_type)) &&
                !shouldExcludeNode(node)
            );
            return result;
        }

        // Default behavior: filter by selected schemas, object types, and data model types
        // Optimized O(n) array filtering instead of O(n²) graph iteration
        const result = preFilteredData.filter(node =>
            debouncedSelectedSchemas.has(node.schema) &&
            (objectTypes.length === 0 || !node.object_type || debouncedSelectedObjectTypes.has(node.object_type)) &&
            (dataModelTypes.length === 0 || !node.data_model_type || debouncedSelectedTypes.has(node.data_model_type)) &&
            !shouldExcludeNode(node)
        );
        return result;
    }, [preFilteredData, debouncedSelectedSchemas, debouncedSelectedObjectTypes, debouncedSelectedTypes, objectTypes, dataModelTypes, isTraceModeActive, traceConfig, performInteractiveTrace, activeExcludeTerms, isTraceFilterApplied]);

    // POST-filter: Apply "Hide Unrelated" as FINAL step (filter context-aware)
    // Unrelated nodes = nodes with no connections in the FILTERED graph
    // Only applied when filters are active (schema/type filters reducing visible set)
    const finalConnectedData = useMemo(() => {
        // Check if any filters are active (not showing all data)
        const hasActiveSchemaFilter = debouncedSelectedSchemas.size < schemas.length;
        const hasActiveObjectTypeFilter = objectTypes.length > 0 && debouncedSelectedObjectTypes.size < objectTypes.length;
        const hasActiveDataModelFilter = dataModelTypes.length > 0 && debouncedSelectedTypes.size < dataModelTypes.length;
        const hasActiveFilters = hasActiveSchemaFilter || hasActiveObjectTypeFilter || hasActiveDataModelFilter;

        // Only apply unrelated filter when:
        // 1. hideUnrelated is enabled
        // 2. Filters are active (reducing the visible set)
        if (!hideUnrelated || !hasActiveFilters) {
            return finalVisibleData; // No post-filtering
        }

        // Build set of visible node IDs for O(1) lookup
        const visibleIds = new Set(finalVisibleData.map(n => n.id));

        // Find nodes that have at least one connection in the filtered graph
        // Performance: O(E) where E = number of edges (~2N typically)
        const connectedIds = new Set<string>();
        lineageGraph.forEachEdge((edge, attributes, source, target) => {
            // Only count edges where BOTH source AND target are visible
            if (visibleIds.has(source) && visibleIds.has(target)) {
                connectedIds.add(source);
                connectedIds.add(target);
            }
        });

        // Filter out nodes with no connections in the filtered context
        const connected = finalVisibleData.filter(node => connectedIds.has(node.id));

        return connected;
    }, [finalVisibleData, hideUnrelated, lineageGraph, debouncedSelectedSchemas, schemas.length, debouncedSelectedObjectTypes, objectTypes.length, debouncedSelectedTypes, dataModelTypes.length]);

    return {
        finalVisibleData: finalConnectedData, // Return post-filtered data
        selectedSchemas,
        setSelectedSchemas,
        selectedObjectTypes,
        setSelectedObjectTypes,
        selectedTypes,
        setSelectedTypes,
        searchTerm,
        setSearchTerm,
        hideIsolated,
        setHideIsolated,
        hideUnrelated,
        setHideUnrelated,
        highlightedNodes,
        setHighlightedNodes,
        autocompleteSuggestions,
        setAutocompleteSuggestions,
    };
}
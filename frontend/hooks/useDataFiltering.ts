import { useState, useMemo, useEffect, useDeferredValue, useRef } from 'react';
import { DataNode, TraceConfig } from '../types';
import Graph from 'graphology';
import { INTERACTION_CONSTANTS } from '../interaction-constants';
import {
    loadSelectedSchemas,
    saveSelectedSchemas,
    loadSelectedTypes,
    saveSelectedTypes,
    loadHideUnrelated,
    saveHideUnrelated,
    matchesWildcard
} from '../utils/localStorage';

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
    appliedExclusions: string;
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
    traceExitNodes,
    appliedExclusions
}: UseDataFilteringProps) {
    const [selectedSchemas, setSelectedSchemas] = useState<Set<string>>(new Set());
    const [selectedTypes, setSelectedTypes] = useState<Set<string>>(new Set());
    const [searchTerm, setSearchTerm] = useState('');
    const [excludeTerm, setExcludeTerm] = useState('');
    const [hideUnrelated, setHideUnrelated] = useState(() => {
        // Try to load from localStorage first, fallback to true
        const stored = loadHideUnrelated();
        return stored !== null ? stored : true;
    });
    const [highlightedNodes, setHighlightedNodes] = useState<Set<string>>(new Set());
    const [autocompleteSuggestions, setAutocompleteSuggestions] = useState<DataNode[]>([]);

    // OPTIMIZATION: Defer expensive autocomplete calculations until user stops typing
    const deferredSearchTerm = useDeferredValue(searchTerm);

    // Debounced versions of selectedSchemas and selectedTypes for expensive layout calculations
    const [debouncedSelectedSchemas, setDebouncedSelectedSchemas] = useState<Set<string>>(new Set());
    const [debouncedSelectedTypes, setDebouncedSelectedTypes] = useState<Set<string>>(new Set());
    const debounceTimerRef = useRef<number | undefined>(undefined);

    // Initialize schemas - load from localStorage or use all schemas
    useEffect(() => {
        if (schemas.length > 0) {
            const storedSchemas = loadSelectedSchemas();
            if (storedSchemas && storedSchemas.length > 0) {
                // Only use stored schemas that still exist in current data
                const validStored = storedSchemas.filter(s => schemas.includes(s));
                if (validStored.length > 0) {
                    const schemasSet = new Set(validStored);
                    setSelectedSchemas(schemasSet);
                    setDebouncedSelectedSchemas(schemasSet);
                    console.log('[Persistence] Restored schemas from localStorage:', validStored);
                    return;
                }
            }
            // Fallback to all schemas
            const allSchemas = new Set(schemas);
            setSelectedSchemas(allSchemas);
            setDebouncedSelectedSchemas(allSchemas);
        }
    }, [schemas]);

    // Initialize types - load from localStorage or use all types
    useEffect(() => {
        if (dataModelTypes.length > 0) {
            const storedTypes = loadSelectedTypes();
            if (storedTypes && storedTypes.length > 0) {
                // Only use stored types that still exist in current data
                const validStored = storedTypes.filter(t => dataModelTypes.includes(t));
                if (validStored.length > 0) {
                    const typesSet = new Set(validStored);
                    setSelectedTypes(typesSet);
                    setDebouncedSelectedTypes(typesSet);
                    console.log('[Persistence] Restored types from localStorage:', validStored);
                    return;
                }
            }
            // Fallback to all types
            const allTypes = new Set(dataModelTypes);
            setSelectedTypes(allTypes);
            setDebouncedSelectedTypes(allTypes);
        }
    }, [dataModelTypes]);

    // Persist selectedSchemas to localStorage whenever it changes
    useEffect(() => {
        if (selectedSchemas.size > 0) {
            saveSelectedSchemas(selectedSchemas);
        }
    }, [selectedSchemas]);

    // Persist selectedTypes to localStorage whenever it changes
    useEffect(() => {
        if (selectedTypes.size > 0) {
            saveSelectedTypes(selectedTypes);
        }
    }, [selectedTypes]);

    // Persist hideUnrelated to localStorage whenever it changes
    useEffect(() => {
        saveHideUnrelated(hideUnrelated);
    }, [hideUnrelated]);

    // Debounce schema and type changes (for large datasets, avoid immediate re-layout)
    useEffect(() => {
        // Clear any pending debounce
        if (debounceTimerRef.current) {
            window.clearTimeout(debounceTimerRef.current);
        }

        // For large datasets (>500 nodes), use debouncing to improve responsiveness
        const shouldDebounce = allData.length > 500;
        const debounceDelay = 150; // 150ms feels responsive while preventing stuttering

        if (shouldDebounce) {
            debounceTimerRef.current = window.setTimeout(() => {
                setDebouncedSelectedSchemas(selectedSchemas);
                setDebouncedSelectedTypes(selectedTypes);
            }, debounceDelay);
        } else {
            // For small datasets, update immediately (no perceptible benefit from debouncing)
            setDebouncedSelectedSchemas(selectedSchemas);
            setDebouncedSelectedTypes(selectedTypes);
        }

        return () => {
            if (debounceTimerRef.current) {
                window.clearTimeout(debounceTimerRef.current);
            }
        };
    }, [selectedSchemas, selectedTypes, allData.length]);

    // OPTIMIZATION: Use deferred search term to reduce autocomplete recalculations
    useEffect(() => {
        console.log('[Autocomplete] searchTerm:', searchTerm, 'length:', searchTerm.trim().length);

        // Only show autocomplete suggestions after 5 characters (combines both optimizations)
        if (deferredSearchTerm.trim() === '' || deferredSearchTerm.trim().length < 5) {
            console.log('[Autocomplete] Blocked: less than 5 characters');
            setAutocompleteSuggestions([]);
            return;
        }

        console.log('[Autocomplete] Proceeding with search...');

        // Safety check: ensure lineageGraph is initialized before accessing
        if (!lineageGraph || typeof lineageGraph.forEachNode !== 'function') {
            console.log('[Autocomplete] Error: lineageGraph not initialized properly');
            setAutocompleteSuggestions([]);
            return;
        }

        try {
            const suggestions: DataNode[] = [];
            const searchLower = searchTerm.toLowerCase();

            // Use forEachNode instead of nodeEntries() for better compatibility
            lineageGraph.forEachNode((nodeId: string, attributes: any) => {
                if (suggestions.length >= INTERACTION_CONSTANTS.AUTOCOMPLETE_MAX_RESULTS) return;

                // Safety check: ensure attributes and required properties exist
                if (!attributes || typeof attributes.name !== 'string' || typeof attributes.schema !== 'string') {
                    console.warn(`[Autocomplete] Skipping node ${nodeId} with invalid attributes:`, attributes);
                    return;
                }

                if (
                    attributes.name.toLowerCase().startsWith(searchLower) &&
                    selectedSchemas.has(attributes.schema) &&
                    (dataModelTypes.length === 0 || !attributes.data_model_type || selectedTypes.has(attributes.data_model_type))
                ) {
                    suggestions.push(attributes as DataNode);
                }
            });

            console.log('[Autocomplete] Found', suggestions.length, 'suggestions');
            setAutocompleteSuggestions(suggestions);
        } catch (error) {
            console.error('[Autocomplete] Error generating suggestions:', error);
            setAutocompleteSuggestions([]);
        }
    }, [deferredSearchTerm, lineageGraph, selectedSchemas, selectedTypes, dataModelTypes]);

    // Static pre-filter: Apply "Hide Unrelated" and exclusion patterns BEFORE any other filters
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

        // Apply exclusion patterns (wildcard matching)
        if (appliedExclusions && appliedExclusions.trim() !== '') {
            const patterns = appliedExclusions.split(';')
                .map(p => p.trim())
                .filter(p => p !== '');

            if (patterns.length > 0) {
                filtered = filtered.filter(node => {
                    // Exclude node if it matches any pattern
                    return !patterns.some(pattern => matchesWildcard(node.name, pattern));
                });
            }
        }

        return filtered;
    }, [allData, lineageGraph, hideUnrelated, appliedExclusions]);

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
                debouncedSelectedSchemas.has(node.schema) &&
                (dataModelTypes.length === 0 || !node.data_model_type || debouncedSelectedTypes.has(node.data_model_type))
            );
        }

        // OPTIMIZED: Use direct array filtering instead of graph iteration
        // This is much faster for large datasets (O(n) instead of O(n) + graph overhead)
        // Uses debounced values to prevent expensive re-layouts during rapid filter changes
        return preFilteredData.filter(node =>
            debouncedSelectedSchemas.has(node.schema) &&
            (dataModelTypes.length === 0 || !node.data_model_type || debouncedSelectedTypes.has(node.data_model_type))
        );
    }, [preFilteredData, debouncedSelectedSchemas, debouncedSelectedTypes, dataModelTypes, isTraceModeActive, traceConfig, performInteractiveTrace, isInTraceExitMode, traceExitNodes]);

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
        autocompleteSuggestions,
        setAutocompleteSuggestions,
    };
}
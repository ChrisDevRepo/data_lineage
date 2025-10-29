import { useState, useCallback } from 'react';
import Graph from 'graphology';
import { TraceConfig, DataNode } from '../types';
import { patternToRegex } from '../utils/layout';

// Helper function to find all DIRECT paths between two nodes
// Direct paths = paths that follow data flow direction (either all downstream or all upstream)
function findAllPathsBetweenNodes(
    startNodeId: string,
    endNodeId: string,
    lineageGraph: Graph,
    config: TraceConfig,
    exclusionRegexes: RegExp[]
): Set<string> {
    const nodesInPath = new Set<string>();

    // Try finding paths in downstream direction (start -> end)
    const downstreamPaths = findDirectionalPaths(
        startNodeId,
        endNodeId,
        lineageGraph,
        config,
        exclusionRegexes,
        'downstream'
    );

    // Try finding paths in upstream direction (end -> start, then reverse)
    const upstreamPaths = findDirectionalPaths(
        endNodeId,
        startNodeId,
        lineageGraph,
        config,
        exclusionRegexes,
        'upstream'
    );

    // Collect all nodes from both directions
    downstreamPaths.forEach(path => {
        path.forEach(nodeId => nodesInPath.add(nodeId));
    });
    upstreamPaths.forEach(path => {
        path.forEach(nodeId => nodesInPath.add(nodeId));
    });

    return nodesInPath;
}

// Find paths in a single direction (either only downstream or only upstream)
function findDirectionalPaths(
    fromNodeId: string,
    toNodeId: string,
    lineageGraph: Graph,
    config: TraceConfig,
    exclusionRegexes: RegExp[],
    direction: 'downstream' | 'upstream'
): string[][] {
    const allPaths: string[][] = [];
    const queue: { id: string; path: string[] }[] = [{ id: fromNodeId, path: [fromNodeId] }];
    const visited = new Map<string, number>(); // Track visit count to allow multiple paths

    while (queue.length > 0) {
        const current = queue.shift()!;
        const { id: currentId, path } = current;

        // Found the target node - save this path
        if (currentId === toNodeId) {
            allPaths.push(path);
            continue;
        }

        // Prevent infinite loops - limit visits per node
        const visitCount = visited.get(currentId) || 0;
        if (visitCount > 3) continue; // Allow up to 3 visits per node (handles cycles)
        visited.set(currentId, visitCount + 1);

        // Only explore in the specified direction
        const getNeighbors = direction === 'downstream'
            ? (cb: (neighbor: string) => void) => lineageGraph.forEachOutNeighbor(currentId, cb)
            : (cb: (neighbor: string) => void) => lineageGraph.forEachInNeighbor(currentId, cb);

        getNeighbors((neighborId) => {
            if (path.includes(neighborId)) return; // Skip if already in current path (cycle)

            const neighborNode = lineageGraph.getNodeAttributes(neighborId) as DataNode;
            if (!neighborNode) return;
            if (!config.includedSchemas.has(neighborNode.schema)) return;

            // Filter by data model type
            if (neighborNode.data_model_type && !config.includedTypes.has(neighborNode.data_model_type)) return;

            // Check exclusion patterns
            const isExcluded = exclusionRegexes.some(regex => regex.test(neighborNode.name));
            if (isExcluded) return;

            queue.push({ id: neighborId, path: [...path, neighborId] });
        });
    }

    return allPaths;
}

export function useInteractiveTrace(
    addNotification: (text: string, type: 'info' | 'error') => void,
    lineageGraph: Graph
) {
    const [isTraceModeActive, setIsTraceModeActive] = useState(false);
    const [traceConfig, setTraceConfig] = useState<TraceConfig | null>(null);

    const performInteractiveTrace = useCallback((config: TraceConfig): Set<string> => {
        if (!config.startNodeId || !lineageGraph || !lineageGraph.hasNode(config.startNodeId)) return new Set();

        const exclusionRegexes = config.exclusionPatterns.map(patternToRegex);

        // Path mode: Find all paths between start and end nodes
        if (config.endNodeId && lineageGraph.hasNode(config.endNodeId)) {
            return findAllPathsBetweenNodes(
                config.startNodeId,
                config.endNodeId,
                lineageGraph,
                config,
                exclusionRegexes
            );
        }

        // Level mode: Traverse by levels (original behavior)
        const visibleIds = new Set<string>([config.startNodeId]);

        const traverse = (
            startNode: string,
            maxLevels: number,
            getNeighbors: (node: string, cb: (neighbor: string) => void) => void
        ) => {
            const queue: { id: string; level: number }[] = [{ id: startNode, level: 0 }];
            const visited = new Set<string>([startNode]);

            let head = 0;
            while (head < queue.length) {
                const { id: currentId, level } = queue[head++];
                if (level >= maxLevels) continue;

                getNeighbors(currentId, (neighborId) => {
                    if (visited.has(neighborId)) return;
                    visited.add(neighborId);

                    const neighborNode = lineageGraph.getNodeAttributes(neighborId) as DataNode;
                    if (!neighborNode) return;
                    if (!config.includedSchemas.has(neighborNode.schema)) return;

                    // Filter by data model type if the node has one
                    if (neighborNode.data_model_type && !config.includedTypes.has(neighborNode.data_model_type)) return;

                    // Check if node matches any exclusion pattern
                    const isExcluded = exclusionRegexes.some(regex => regex.test(neighborNode.name));
                    if (isExcluded) return;

                    // Add the neighbor to the visible set and continue traversing
                    visibleIds.add(neighborId);
                    queue.push({ id: neighborId, level: level + 1 });
                });
            }
        };

        traverse(config.startNodeId, config.upstreamLevels, (node, cb) => lineageGraph.forEachInNeighbor(node, cb));
        traverse(config.startNodeId, config.downstreamLevels, (node, cb) => lineageGraph.forEachOutNeighbor(node, cb));

        return visibleIds;

    }, [lineageGraph]);

    const handleApplyTrace = (config: Omit<TraceConfig, 'startNodeId'> & { startNodeId: string }) => {
        setTraceConfig(config);
        addNotification('Trace applied successfully!', 'info');
    };

    const handleExitTraceMode = useCallback(() => {
        setIsTraceModeActive(false);
        // Don't clear traceConfig immediately - we'll use it to preserve selection
        // setTraceConfig(null);
    }, []);

    return {
        traceConfig,
        isTraceModeActive,
        setIsTraceModeActive,
        performInteractiveTrace,
        handleApplyTrace,
        handleExitTraceMode
    };
}
import { useState, useCallback } from 'react';
import Graph from 'graphology';
import { TraceConfig, DataNode } from '../types';
import { patternToRegex } from '../utils/layout';

export function useInteractiveTrace(
    addNotification: (text: string, type: 'info' | 'error') => void,
    lineageGraph: Graph
) {
    const [isTraceModeActive, setIsTraceModeActive] = useState(false);
    const [traceConfig, setTraceConfig] = useState<TraceConfig | null>(null);

    const performInteractiveTrace = useCallback((config: TraceConfig): Set<string> => {
        if (!config.startNodeId || !lineageGraph || !lineageGraph.hasNode(config.startNodeId)) return new Set();

        const exclusionRegexes = config.exclusionPatterns.map(patternToRegex);
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
import { useMemo } from 'react';
import Graph from 'graphology';
import { DataNode } from '../types';
import { CONSTANTS } from '../constants';

export function useGraphology(allData: DataNode[]) {
    const lineageGraph = useMemo(() => {
        const graph = new Graph({ type: 'directed' });
        const nodeMap = new Map(allData.map(n => [n.id, n]));

        allData.forEach(node => {
            if (!graph.hasNode(node.id)) {
                graph.addNode(node.id, { ...node });
            }
        });

        allData.forEach(node => {
            (node.inputs || []).forEach(inputId => {
                if (nodeMap.has(inputId)) {
                    graph.mergeEdge(inputId, node.id);
                }
            });
            (node.outputs || []).forEach(outputId => {
                if (nodeMap.has(outputId)) {
                    graph.mergeEdge(node.id, outputId);
                }
            });
        });
        return graph;
    }, [allData]);

    const { schemas, schemaColorMap, dataModelTypes } = useMemo(() => {
        const uniqueSchemas = [...new Set(allData.map(n => n.schema))].sort();
        const map = new Map(uniqueSchemas.map((s, i) => [s, CONSTANTS.SCHEMA_PALETTE[i % CONSTANTS.SCHEMA_PALETTE.length]]));
        const uniqueTypes = [...new Set(allData.map(n => n.data_model_type).filter(Boolean) as string[])].sort();
        return { schemas: uniqueSchemas, schemaColorMap: map, dataModelTypes: uniqueTypes };
    }, [allData]);

    return { lineageGraph, schemas, schemaColorMap, dataModelTypes };
}

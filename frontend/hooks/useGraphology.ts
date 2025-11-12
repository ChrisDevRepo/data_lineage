import { useMemo } from 'react';
import Graph from 'graphology';
import { DataNode } from '../types';
import { createSchemaColorMap } from '../utils/schemaColors';
import { logger } from '../utils/logger';

export function useGraphology(allData: DataNode[]) {
    const lineageGraph = useMemo(() => {
        const startTime = Date.now();
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
        logger.perf(`Graph built in ${Date.now() - startTime}ms (${graph.order} nodes, ${graph.size} edges)`);
        return graph;
    }, [allData]);

    const { schemas, schemaColorMap, objectTypes, dataModelTypes } = useMemo(() => {
        const uniqueSchemas = [...new Set(allData.map(n => n.schema))].sort();
        // Use smart color assignment that groups related schemas by layer
        const map = createSchemaColorMap(uniqueSchemas);
        const uniqueObjectTypes = [...new Set(allData.map(n => n.object_type))].sort();
        const uniqueDataModelTypes = [...new Set(allData.map(n => n.data_model_type).filter(Boolean) as string[])].sort();
        return { schemas: uniqueSchemas, schemaColorMap: map, objectTypes: uniqueObjectTypes, dataModelTypes: uniqueDataModelTypes };
    }, [allData]);

    return { lineageGraph, schemas, schemaColorMap, objectTypes, dataModelTypes };
}

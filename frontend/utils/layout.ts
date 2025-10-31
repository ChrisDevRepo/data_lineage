import { Edge, MarkerType, Position, Node as ReactFlowNode } from 'reactflow';
import dagre from 'dagre';
import Graph from 'graphology';
import { DataNode } from '../types';

type LayoutProps = {
    data: DataNode[];
    layout: 'TB' | 'LR';
    schemaColorMap: Map<string, string>;
    lineageGraph: Graph;
    isTraceModeActive: boolean;
};

export const patternToRegex = (pattern: string) => new RegExp('^' + pattern.replace(/\*/g, '.*') + '$', 'i');

export const getDagreLayoutedElements = (props: LayoutProps) => {
    const startTime = Date.now();
    const { data, layout, schemaColorMap, lineageGraph, isTraceModeActive } = props;

    if (data.length === 0) return { nodes: [], edges: [] };

    const visibleNodeIds = new Set(data.map(n => n.id));

    // Create nodes for detail view
    const initialNodes: ReactFlowNode[] = data.map(nodeData => ({
        id: nodeData.id,
        position: { x: 0, y: 0 },
        data: { ...nodeData, schemaColor: schemaColorMap.get(nodeData.schema) },
        type: 'custom',
        width: 192,
        height: 48,
    }));

    // Create edges
    const edgesSet = new Map<string, Edge>();
    if (lineageGraph) {
        lineageGraph.forEachEdge((edge, attrs, source, target) => {
            if (visibleNodeIds.has(source) && visibleNodeIds.has(target)) {
                edgesSet.set(`e-${source}-${target}`, {
                    id: `e-${source}-${target}`,
                    source,
                    target,
                    style: { stroke: '#9ca3af', strokeWidth: 1.5 },
                    markerEnd: { type: MarkerType.ArrowClosed, color: '#9ca3af', width: 20, height: 20 },
                    animated: isTraceModeActive
                });
            }
        });
    }
    const initialEdges: Edge[] = Array.from(edgesSet.values());

    // Apply Dagre layout
    const g = new dagre.graphlib.Graph();
    g.setGraph({ rankdir: layout, nodesep: 50, ranksep: 100, marginx: 20, marginy: 20 });
    g.setDefaultEdgeLabel(() => ({}));

    initialNodes.forEach((node) => {
        g.setNode(node.id, { width: node.width || 192, height: node.height || 48 });
    });

    initialEdges.forEach((edge) => g.setEdge(edge.source, edge.target));

    dagre.layout(g);

    console.log(`[Performance] Layout calculated in ${Date.now() - startTime}ms (${initialNodes.length} nodes, ${initialEdges.length} edges)`);

    return {
        nodes: initialNodes.map((node) => {
            const nodeWithPosition = g.node(node.id);
            const isHorizontal = layout === 'LR';
            node.targetPosition = isHorizontal ? Position.Left : Position.Top;
            node.sourcePosition = isHorizontal ? Position.Right : Position.Bottom;
            node.position = {
                x: nodeWithPosition.x - (node.width || 192) / 2,
                y: nodeWithPosition.y - (node.height || 48) / 2,
            };
            return node;
        }),
        edges: initialEdges,
    };
};

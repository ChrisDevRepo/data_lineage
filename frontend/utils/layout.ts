import { Edge, MarkerType, Position, Node as ReactFlowNode } from 'reactflow';
import dagre from 'dagre';
import Graph from 'graphology';
import { DataNode } from '../types';

type LayoutProps = {
    data: DataNode[];
    viewMode: 'detail' | 'schema';
    layout: 'TB' | 'LR';
    schemas: string[];
    selectedSchemas: Set<string>;
    schemaColorMap: Map<string, string>;
    lineageGraph: Graph;
    isTraceModeActive: boolean;
};

export const patternToRegex = (pattern: string) => new RegExp('^' + pattern.replace(/\*/g, '.*') + '$', 'i');

export const getDagreLayoutedElements = (props: LayoutProps) => {
    const { data, viewMode, layout, schemas, selectedSchemas, schemaColorMap, lineageGraph, isTraceModeActive } = props;

    if (data.length === 0) return { nodes: [], edges: [] };

    let initialNodes: ReactFlowNode[] = [];
    let initialEdges: Edge[] = [];
    const visibleNodeIds = new Set(data.map(n => n.id));

    if (viewMode === 'detail') {
        initialNodes = data.map(nodeData => ({
            id: nodeData.id,
            position: { x: 0, y: 0 },
            data: { ...nodeData, schemaColor: schemaColorMap.get(nodeData.schema) },
            type: 'custom',
            width: 192, height: 48,
        }));

        const edgesSet = new Map<string, Edge>();
        if (lineageGraph) {
            lineageGraph.forEachEdge((edge, attrs, source, target) => {
                if (visibleNodeIds.has(source) && visibleNodeIds.has(target)) {
                    edgesSet.set(`e-${source}-${target}`, {
                        id: `e-${source}-${target}`, source, target,
                        style: { stroke: '#9ca3af', strokeWidth: 1.5 },
                        markerEnd: { type: MarkerType.ArrowClosed, color: '#9ca3af', width: 20, height: 20 },
                        animated: isTraceModeActive
                    });
                }
            });
        }
        initialEdges = Array.from(edgesSet.values());
    } else { // 'schema' view
        initialNodes = schemas.filter(s => selectedSchemas.has(s)).map((schema) => ({
            id: `schema-${schema}`, position: { x: 0, y: 0 },
            data: { label: schema },
            width: 200, height: 80,
            style: {
                backgroundColor: `${schemaColorMap.get(schema)}40`,
                borderColor: schemaColorMap.get(schema),
                borderWidth: 2, borderRadius: '8px', display: 'flex', justifyContent: 'center',
                alignItems: 'center', fontSize: '1.2rem', fontWeight: 'bold',
            }
        }));

        const edgeMap = new Map<string, number>();
        data.forEach(node => {
            lineageGraph.forEachInNeighbor(node.id, (neighborId) => {
                const inputNode = lineageGraph.getNodeAttributes(neighborId) as DataNode;
                if (inputNode && inputNode.schema !== node.schema && selectedSchemas.has(inputNode.schema)) {
                    const edgeId = `e-${inputNode.schema}-${node.schema}`;
                    edgeMap.set(edgeId, (edgeMap.get(edgeId) || 0) + 1);
                }
            });
        });
        initialEdges = Array.from(edgeMap.entries()).map(([edgeId, count]) => {
            const [_, sourceSchema, targetSchema] = edgeId.split('-');
            return {
                id: edgeId, source: `schema-${sourceSchema}`, target: `schema-${targetSchema}`,
                label: `${count} dep${count > 1 ? 's' : ''}`,
                style: { stroke: '#9ca3af', strokeWidth: Math.min(1 + count * 0.5, 8) },
                markerEnd: { type: MarkerType.ArrowClosed, color: '#9ca3af', width: 20, height: 20 },
                animated: isTraceModeActive
            };
        });
    }

    const g = new dagre.graphlib.Graph();
    g.setGraph({ rankdir: layout, nodesep: 50, ranksep: 100, marginx: 20, marginy: 20 });
    g.setDefaultEdgeLabel(() => ({}));

    initialNodes.forEach((node) => {
        g.setNode(node.id, { width: node.width || 192, height: node.height || 48 });
    });

    initialEdges.forEach((edge) => g.setEdge(edge.source, edge.target));

    dagre.layout(g);

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

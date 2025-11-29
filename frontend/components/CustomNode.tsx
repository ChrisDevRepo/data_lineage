import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { CONSTANTS } from '../constants';
import { DataNode } from '../types';

type CustomNodeData = DataNode & {
    isHighlighted: boolean;
    isDimmed: boolean;
    isTraceStartNode?: boolean;
    layoutDir: 'LR' | 'TB';
    schemaColor: string;
    sqlViewerOpen?: boolean;
    onNodeClick?: (nodeData: {
        id: string;
        name: string;
        schema: string;
        objectType: string;
        ddlText: string | null;
    }) => void;
};

export const CustomNode = React.memo(({ data }: NodeProps<CustomNodeData>) => {
    const shapeStyle = CONSTANTS.SHAPE_MAP[data.object_type]?.style || '';
    const isHorizontal = data.layoutDir === 'LR';
    const schemaColor = data.schemaColor || '#7f7f7f';
    const isPhantom = data.is_phantom || false;
    const isDiamond = data.object_type === 'Function';

    // All click handling is done by ReactFlow's onNodeClick in App.tsx
    // This component just handles visual styling
    const isClickableForSql = data.sqlViewerOpen;

    // Phantom styling: dashed border, orange accent
    const phantomBorderStyle = isPhantom ? 'border-dashed !border-orange-500' : '';
    const phantomShadow = isPhantom ? 'shadow-orange-300/50' : '';

    // Trace start node: blue border with ring (takes priority over highlighted)
    const traceStartNodeStyle = data.isTraceStartNode ? '!border-blue-500 !border-4 ring-4 ring-blue-500/50' : '';

    // Highlighted: yellow border (only if not trace start node)
    const highlightedStyle = data.isHighlighted && !data.isTraceStartNode ? 'border-yellow-400 !border-4 ring-4 ring-yellow-400/50' : '';

    const nodeClasses = `
        w-48 h-12 flex items-center justify-center text-sm font-bold
        border-2 shadow-lg text-gray-800
        ${shapeStyle}
        ${phantomBorderStyle}
        ${phantomShadow}
        ${traceStartNodeStyle}
        ${highlightedStyle}
        ${data.isDimmed ? 'opacity-20' : ''}
        ${isClickableForSql ? 'cursor-pointer hover:shadow-xl hover:scale-105' : ''}
        transition-transform duration-200
    `;

    const nodeStyle = {
        backgroundColor: `${schemaColor}30`,
        borderColor: data.isTraceStartNode ? '#3b82f6' : (isPhantom ? '#ff9800' : schemaColor),
    };

    // Only show confidence/parsing method for Stored Procedures
    let nodeTitle = `Object: ${data.schema}.${data.name}\nObject Type: ${data.object_type}\nData Model Type: ${data.data_model_type || 'N/A'}`;

    if (data.isTraceStartNode) {
        nodeTitle += `\n\n🎯 TRACE START NODE`;
        nodeTitle += `\nThis is the starting point of the current trace`;
    }

    if (isPhantom) {
        nodeTitle += `\n\n⚠️  PHANTOM OBJECT (${data.phantom_reason || 'not in catalog'})`;
        nodeTitle += `\nThis object is referenced in SQL but not found in metadata catalog.`;
    }

    if (data.object_type === 'Stored Procedure') {
        nodeTitle += `\nDescription: ${data.description || 'No description provided.'}`;
    }

    if (data.object_type === 'Function') {
        nodeTitle += `\nUser-Defined Function (UDF)`;
    }

    if (isClickableForSql) {
        nodeTitle += `\n\n💡 Click to view SQL definition`;
    }

    return (
        <div className="relative">
            <div
                className={nodeClasses}
                title={nodeTitle}
                style={nodeStyle}
                data-testid="lineage-node"
                data-node-id={data.id}
                data-object-type={data.object_type}
                data-is-phantom={isPhantom}
                data-node-symbol={data.node_symbol || (isDiamond ? 'diamond' : 'circle')}
            >
                <Handle type="target" position={isHorizontal ? Position.Left : Position.Top} className="!bg-gray-500" />
                <div className="truncate px-2">{data.name}</div>
                <Handle type="source" position={isHorizontal ? Position.Right : Position.Bottom} className="!bg-gray-500" />
            </div>
        </div>
    );
});

export const nodeTypes = { custom: CustomNode };

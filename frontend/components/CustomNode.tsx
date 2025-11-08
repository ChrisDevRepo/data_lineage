import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { CONSTANTS } from '../constants';
import { DataNode } from '../types';

type CustomNodeData = DataNode & {
    isHighlighted: boolean;
    isDimmed: boolean;
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

    // All click handling is done by ReactFlow's onNodeClick in App.tsx
    // This component just handles visual styling
    const isClickableForSql = data.sqlViewerOpen;

    const nodeClasses = `
        w-48 h-12 flex items-center justify-center text-sm font-bold
        border-2 shadow-lg text-gray-800
        ${shapeStyle}
        ${data.isHighlighted ? 'border-yellow-400 !border-4 ring-4 ring-yellow-400/50' : ''}
        ${data.isDimmed ? 'opacity-20' : ''}
        ${isClickableForSql ? 'cursor-pointer hover:shadow-xl hover:scale-105' : ''}
        transition-all duration-300
    `;

    const nodeStyle = {
        backgroundColor: `${schemaColor}30`,
        borderColor: schemaColor,
    };

    // Only show confidence/parsing method for Stored Procedures
    let nodeTitle = `Object: ${data.schema}.${data.name}\nObject Type: ${data.object_type}\nData Model Type: ${data.data_model_type || 'N/A'}`;

    if (data.object_type === 'Stored Procedure') {
        nodeTitle += `\nDescription: ${data.description || 'No description provided.'}`;
    }

    if (isClickableForSql) {
        nodeTitle += `\n\n💡 Click to view SQL definition`;
    }

    // Get confidence badge for Stored Procedures (v2.1.0)
    const getConfidenceBadge = () => {
        if (data.object_type !== 'Stored Procedure') return null;

        const confidence = data.confidence || 0;

        // v2.1.0 Simplified confidence model (0, 75, 85, 100)
        if (confidence >= 1.0 || confidence === 100) {
            return <span className="confidence-badge" title="High Confidence (100%)">✅</span>;
        } else if (confidence >= 0.85) {
            return <span className="confidence-badge" title="Good Confidence (85%)">⚠️</span>;
        } else if (confidence >= 0.75) {
            return <span className="confidence-badge" title="Medium Confidence (75%)">⚠️</span>;
        } else {
            return <span className="confidence-badge" title="Low/Failed Confidence (0%)">❌</span>;
        }
    };

    return (
        <div className="relative">
            <div className={nodeClasses} title={nodeTitle} style={nodeStyle}>
                <Handle type="target" position={isHorizontal ? Position.Left : Position.Top} className="!bg-gray-500" />
                <div className="truncate px-2">{data.name}</div>
                <Handle type="source" position={isHorizontal ? Position.Right : Position.Bottom} className="!bg-gray-500" />
            </div>
            {/* Confidence badge for Stored Procedures (v2.1.0) */}
            {getConfidenceBadge() && (
                <div className="absolute -top-1 -right-1 text-sm leading-none">
                    {getConfidenceBadge()}
                </div>
            )}
        </div>
    );
});

export const nodeTypes = { custom: CustomNode };

import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { CONSTANTS } from '../constants';
import { DataNode } from '../types';

type CustomNodeData = DataNode & {
    isHighlighted: boolean;
    isDimmed: boolean;
    layoutDir: 'LR' | 'TB';
    schemaColor: string;
};

export const CustomNode = React.memo(({ data }: NodeProps<CustomNodeData>) => {
    const shapeStyle = CONSTANTS.SHAPE_MAP[data.object_type]?.style || '';
    const isHorizontal = data.layoutDir === 'LR';
    const schemaColor = data.schemaColor || '#7f7f7f';

    const nodeClasses = `
        w-48 h-12 flex items-center justify-center text-sm font-bold
        border-2 shadow-lg text-gray-800
        ${shapeStyle}
        ${data.isHighlighted ? 'border-blue-500 !border-4 ring-4 ring-blue-500/50' : ''}
        ${data.isDimmed ? 'opacity-20' : ''}
        transition-all duration-300
    `;
    
    const nodeStyle = {
        backgroundColor: `${schemaColor}30`,
        borderColor: schemaColor,
    };
    
    const nodeTitle = `Object: ${data.schema}.${data.name}\nObject Type: ${data.object_type}\nData Model Type: ${data.data_model_type || 'N/A'}\nDescription: ${data.description || 'No description provided.'}`;

    return (
        <div className={nodeClasses} title={nodeTitle} style={nodeStyle}>
            <Handle type="target" position={isHorizontal ? Position.Left : Position.Top} className="!bg-gray-500" />
            <div className="truncate px-2">{data.name}</div>
            <Handle type="source" position={isHorizontal ? Position.Right : Position.Bottom} className="!bg-gray-500" />
        </div>
    );
});

export const nodeTypes = { custom: CustomNode };

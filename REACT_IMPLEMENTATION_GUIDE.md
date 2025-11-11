# React Implementation Guide - Phantom Objects & UDF Support

## Overview

This guide shows **exactly** what to change in your React components to visualize:
- ❓ **Phantom objects** (not in catalog)
- ◆ **Functions** (UDFs with diamond symbol)
- Dotted edges for phantom connections

---

## 1. Node Symbol Icons

### **Add Icon Components** (if not already present)

```jsx
// src/components/icons/NodeIcons.jsx
import React from 'react';

export const CircleIcon = ({ color = '#4caf50', size = 24 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24">
    <circle cx="12" cy="12" r="10" fill={color} />
  </svg>
);

export const SquareIcon = ({ color = '#2196f3', size = 24 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24">
    <rect x="2" y="2" width="20" height="20" fill={color} />
  </svg>
);

export const DiamondIcon = ({ color = '#9c27b0', size = 24 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24">
    <path d="M12 2 L22 12 L12 22 L2 12 Z" fill={color} />
  </svg>
);

export const QuestionMarkIcon = ({ color = '#ff9800', size = 24 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24">
    <circle cx="12" cy="12" r="10" fill={color} opacity="0.9" />
    <text
      x="12"
      y="17"
      fontSize="16"
      fontWeight="bold"
      fill="white"
      textAnchor="middle"
    >
      ?
    </text>
  </svg>
);
```

---

## 2. Node Component Update

### **Update your Node rendering logic:**

```jsx
// src/components/LineageNode.jsx (or wherever your nodes are rendered)
import React from 'react';
import { Handle, Position } from 'reactflow';
import { CircleIcon, SquareIcon, DiamondIcon, QuestionMarkIcon } from './icons/NodeIcons';

const LineageNode = ({ data }) => {
  // Get appropriate icon based on node_symbol field
  const getNodeIcon = () => {
    switch (data.node_symbol) {
      case 'question_mark':
        return <QuestionMarkIcon size={32} />;  // Phantoms
      case 'diamond':
        return <DiamondIcon size={32} />;       // Functions
      case 'square':
        return <SquareIcon size={32} />;        // Stored Procedures
      case 'circle':
      default:
        return <CircleIcon size={32} />;        // Tables/Views
    }
  };

  // Get tooltip text
  const getTooltipText = () => {
    if (data.is_phantom) {
      return `⚠️ Phantom ${data.object_type} (${data.phantom_reason})`;
    }
    if (data.object_type && data.object_type.includes('Function')) {
      return `User-Defined Function`;
    }
    return data.description || data.object_type;
  };

  // Get node style based on phantom status
  const nodeStyle = {
    padding: '10px',
    borderRadius: '8px',
    border: data.is_phantom ? '2px dashed #ff9800' : '2px solid #ccc',
    background: 'white',
    minWidth: '150px',
    boxShadow: data.is_phantom
      ? '0 2px 8px rgba(255, 152, 0, 0.3)'
      : '0 2px 8px rgba(0,0,0,0.1)'
  };

  return (
    <div style={nodeStyle} title={getTooltipText()}>
      <Handle type="target" position={Position.Top} />

      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {getNodeIcon()}

        <div>
          <div style={{ fontWeight: 'bold', fontSize: '14px' }}>
            {data.name}
          </div>
          <div style={{ fontSize: '12px', color: '#666' }}>
            {data.schema}
          </div>
          {data.is_phantom && (
            <div style={{
              fontSize: '11px',
              color: '#ff9800',
              marginTop: '4px',
              fontStyle: 'italic'
            }}>
              Not in catalog
            </div>
          )}
        </div>
      </div>

      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};

export default LineageNode;
```

---

## 3. Edge Styling

### **Update edge configuration:**

```jsx
// src/components/LineageGraph.jsx (or wherever you configure edges)
import React, { useMemo } from 'react';
import ReactFlow, { Background, Controls } from 'reactflow';

const LineageGraph = ({ nodes, edges }) => {
  // Style edges based on phantom status
  const styledEdges = useMemo(() => {
    return edges.map(edge => {
      // Check if either source or target is phantom (negative ID)
      const sourceId = parseInt(edge.source);
      const targetId = parseInt(edge.target);
      const isPhantomEdge = sourceId < 0 || targetId < 0;

      return {
        ...edge,
        style: {
          stroke: isPhantomEdge ? '#ff9800' : '#999',
          strokeWidth: 2,
          strokeDasharray: isPhantomEdge ? '5,5' : '0',  // Dotted for phantoms
        },
        animated: false,
        type: 'smoothstep',  // or 'default', 'step', 'straight'
      };
    });
  }, [edges]);

  return (
    <ReactFlow
      nodes={nodes}
      edges={styledEdges}
      fitView
    >
      <Background />
      <Controls />
    </ReactFlow>
  );
};

export default LineageGraph;
```

---

## 4. Legend Component (Optional but Recommended)

### **Add a legend to explain symbols:**

```jsx
// src/components/LineageLegend.jsx
import React from 'react';
import { CircleIcon, SquareIcon, DiamondIcon, QuestionMarkIcon } from './icons/NodeIcons';

const LineageLegend = () => {
  const legendItems = [
    { icon: <CircleIcon size={20} />, label: 'Table/View', color: '#4caf50' },
    { icon: <SquareIcon size={20} />, label: 'Stored Procedure', color: '#2196f3' },
    { icon: <DiamondIcon size={20} />, label: 'Function (UDF)', color: '#9c27b0' },
    { icon: <QuestionMarkIcon size={20} />, label: 'Phantom (Not in catalog)', color: '#ff9800' },
  ];

  return (
    <div style={{
      position: 'absolute',
      bottom: '20px',
      left: '20px',
      background: 'white',
      padding: '16px',
      borderRadius: '8px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
      zIndex: 10
    }}>
      <h4 style={{ margin: '0 0 12px 0', fontSize: '14px' }}>Legend</h4>
      {legendItems.map((item, idx) => (
        <div key={idx} style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          marginBottom: '8px'
        }}>
          {item.icon}
          <span style={{ fontSize: '13px' }}>{item.label}</span>
        </div>
      ))}
      <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: '1px solid #eee' }}>
        <div style={{ fontSize: '12px', color: '#666' }}>
          ─────── Normal edge
        </div>
        <div style={{ fontSize: '12px', color: '#ff9800', marginTop: '4px' }}>
          ─ ─ ─ ─ Phantom edge
        </div>
      </div>
    </div>
  );
};

export default LineageLegend;
```

---

## 5. Data Loading

### **Ensure you're loading the new fields:**

```jsx
// src/hooks/useLineageData.js (or wherever you fetch data)
import { useState, useEffect } from 'react';

export const useLineageData = () => {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);

  useEffect(() => {
    fetch('/api/lineage')  // Your API endpoint
      .then(res => res.json())
      .then(data => {
        // Transform backend data to React Flow format
        const flowNodes = data.nodes.map(node => ({
          id: node.id,  // Already a string (e.g., "-1", "123")
          type: 'custom',
          data: {
            ...node,
            // NEW FIELDS from backend:
            node_symbol: node.node_symbol,      // 'circle', 'diamond', 'square', 'question_mark'
            is_phantom: node.is_phantom,        // true/false
            phantom_reason: node.phantom_reason // 'not_in_catalog'
          },
          position: calculatePosition(node),  // Your layout logic
        }));

        const flowEdges = data.nodes.flatMap(node => [
          ...node.inputs.map(sourceId => ({
            id: `${sourceId}-${node.id}`,
            source: sourceId,
            target: node.id,
          })),
        ]);

        setNodes(flowNodes);
        setEdges(flowEdges);
      });
  }, []);

  return { nodes, edges };
};
```

---

## 6. TypeScript Types (if using TypeScript)

```typescript
// src/types/lineage.ts
export interface LineageNode {
  id: string;  // Can be negative (e.g., "-1")
  name: string;
  schema: string;
  object_type: string;
  description: string;
  data_model_type: string;
  node_symbol: 'circle' | 'diamond' | 'square' | 'question_mark';  // NEW
  inputs: string[];
  outputs: string[];
  confidence: number | null;
  confidence_breakdown?: object;
  is_phantom?: boolean;        // NEW
  phantom_reason?: string;     // NEW
  ddl_text?: string;
}
```

---

## Testing Checklist

After implementing these changes:

- [ ] **Phantom tables** show with ❓ icon
- [ ] **Phantom functions** show with ❓ icon
- [ ] **Real functions** show with ◆ diamond icon
- [ ] **Tables/Views** show with ● circle icon
- [ ] **Stored Procedures** show with ■ square icon
- [ ] **Phantom edges** are dotted/dashed
- [ ] **Tooltips** show appropriate messages
- [ ] **Legend** is visible and accurate
- [ ] **Node borders** are dashed for phantoms

---

## Quick Test

To verify it's working:

1. **Check for negative IDs** in frontend_lineage.json:
   ```bash
   cat lineage_output/frontend_lineage.json | grep '"id": "-'
   ```

2. **Check for node_symbol field**:
   ```bash
   cat lineage_output/frontend_lineage.json | grep 'node_symbol'
   ```

3. **Look for phantom flags**:
   ```bash
   cat lineage_output/frontend_lineage.json | grep 'is_phantom'
   ```

---

## Need Help?

If you encounter issues:
1. Check browser console for errors
2. Verify JSON structure matches expectations
3. Test with sample data first
4. Check that React Flow version supports custom node types

---

**Ready to implement?** Copy these code snippets into your React project and adjust file paths as needed!

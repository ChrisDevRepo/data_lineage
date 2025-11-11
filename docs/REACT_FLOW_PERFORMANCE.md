# React Flow Performance Optimization Guide

**Author:** Based on Łukasz Jaźwa's Medium article
**Date:** 2025-11-11
**Target:** Scale from 500 nodes (current UAT limit) to 5K-10K nodes (production)

---

## Executive Summary

**Current Status:** 500-node visible limit prevents crashes (implemented in v4.3.0)
**Production Goal:** 5K-10K nodes with 60 FPS performance
**Critical Insight:** With 100 "heavy" nodes:
- No optimization: **2 FPS** ❌
- Basic React.memo: **30-40 FPS** ⚠️
- Full optimization: **60 FPS** ✅

---

## Why React Flow Has Performance Issues

React Flow is vulnerable to performance pitfalls because:

1. **Node position changes trigger re-renders** - Every drag operation updates state
2. **Internal state refresh** - Node state changes refresh ReactFlow's internal state
3. **Component cascading** - ReactFlow component re-render affects all children
4. **State interdependencies** - Unoptimized dependencies cause entire diagram re-renders

**Critical Rule:** Optimize early. Performance issues are hard to fix later without major refactoring.

---

## 4 Critical Optimization Techniques

### #1: `<ReactFlow>` Component Memoization (HIGHEST PRIORITY)

**Problem:** Anonymous functions or non-memoized objects passed to `<ReactFlow>` cause ALL nodes to re-render.

**Bad Code:**
```typescript
<ReactFlow
  nodes={nodes}
  edges={edges}
  nodeTypes={nodeTypes}
  onNodeClick={() => {}}  // ❌ Anonymous function
/>
```

**Impact:** 100 default nodes drop from 60 FPS → **10 FPS**

**Solution:**
```typescript
// ✅ Memoize all objects
const nodeTypes = useMemo(() => ({ custom: CustomNode }), []);

// ✅ Memoize all functions
const onNodeClick = useCallback((event, node) => {
  console.log('clicked', node);
}, []);

<ReactFlow
  nodes={nodes}
  edges={edges}
  nodeTypes={nodeTypes}
  onNodesChange={onNodesChange}
  onEdgesChange={onEdgesChange}
  onConnect={onConnect}
  onNodeClick={onNodeClick}  // ✅ Memoized
/>
```

**Rule:** EVERY prop passed to `<ReactFlow>` must be:
- **Objects:** Wrapped in `useMemo()` or defined outside component
- **Functions:** Wrapped in `useCallback()`
- **Dependencies:** Must be stable (no non-memoized functions in dependency arrays)

---

### #2: Avoid Direct Dependencies on Node/Edge Arrays

**Problem:** Fetching `nodes.filter()` in components causes re-renders on EVERY node state change (e.g., dragging).

**Bad Code:**
```typescript
// ❌ CustomNode.tsx
export const CustomNode: React.FC<NodeProps> = () => {
  const selectedNodes = useStore(
    (state) => state.nodes.filter((node) => node.selected)
  );

  return <div>{selectedNodes.map(node => node.id)}</div>;
};
```

**Impact:** 100 default nodes drop to **12 FPS**

**Why:** `state.nodes` reference changes on EVERY dragging tick → ALL nodes re-render

**Solution 1: Separate State (Recommended)**
```typescript
// ✅ Store
const useStore = create((set) => ({
  nodes: [],
  selectedNodes: [],  // Separate field
  setSelectedNodes: (nodes) => set({ selectedNodes: nodes }),
}));

// ✅ Diagram
const onSelectionChange = useCallback(
  (event: OnSelectionChangeParams) => {
    setSelectedNodes(event.nodes);
  },
  [setSelectedNodes]
);

<ReactFlow
  onSelectionChange={onSelectionChange}
/>

// ✅ CustomNode.tsx - Only re-renders when selection actually changes
const selectedNodes = useStore((state) => state.selectedNodes);
```

**Solution 2: Shallow Comparison (For Primitive Arrays)**
```typescript
// ✅ Using Zustand's useShallow
const selectedNodeIds = useStore(
  useShallow((state) =>
    state.nodes.filter(n => n.selected).map(n => n.id)
  )
);
```

**Rule:** Never directly access `state.nodes` or `state.edges` in components unless necessary.

---

### #3: Wrap Custom Nodes/Edges in React.memo

**Problem:** Without `React.memo`, ALL nodes re-render even when their props haven't changed.

**Bad Code:**
```typescript
// ❌ No memoization
export const CustomNode: React.FC<NodeProps> = ({ data }) => {
  return <div>{data.label}</div>;
};
```

**Impact:** With anonymous function in ReactFlow: **10 FPS**

**Solution:**
```typescript
// ✅ Basic memoization
export const CustomNode: React.FC<NodeProps> = memo(({ data }) => {
  return <div>{data.label}</div>;
});
```

**Impact:** 100 default nodes: **60 FPS** (stable after 1 second)

**Advanced: Memo "Heavy" Content**
```typescript
// ✅ For complex children (DataGrid, Charts, etc.)
export const CustomNode: React.FC<NodeProps> = memo(({ data }) => {
  return (
    <div>
      <HeavyContent data={data} />
    </div>
  );
});

// ✅ Wrap heavy components separately
const HeavyContent = memo(({ data }) => (
  <DataGrid
    rows={data.rows}
    columns={data.columns}
    // ... MaterialUI DataGrid props
  />
));
```

**Impact:** 100 "heavy" nodes: **60 FPS** (vs 30-40 FPS without internal memo)

**Rule:**
- ALL custom nodes/edges MUST be wrapped in `React.memo`
- "Heavy" child components (DataGrid, Charts) MUST be separately memoized

---

### #4: Zustand Store Configuration

**Problem:** Without proper config, arrays/objects from store get new references on EVERY state change.

**Bad Code:**
```typescript
// ❌ Array recreated on every state change
const [selectedNodes, otherProp] = useStore((state) => [
  state.selectedNodes,
  state.otherProp,
]);
```

**Impact:** Can cause **Maximum update depth exceeded** errors

**Solution 1: useShallow Hook**
```typescript
// ✅ Memoizes array reference
const [selectedNodes, otherProp] = useStore(
  useShallow((state) => [
    state.selectedNodes,
    state.otherProp,
  ])
);
```

**Drawback:** Must remember to use `useShallow` every time

**Solution 2: Configure Store with Shallow (RECOMMENDED)**
```typescript
// ✅ Configure store once
import { createWithEqualityFn } from 'zustand/traditional';
import { shallow } from 'zustand/shallow';

const useStore = createWithEqualityFn<AppState>(
  (set, get) => ({
    nodes: [],
    selectedNodes: [],
    // ... other state
  }),
  shallow  // Default shallow comparison
);

// ✅ Now works automatically
const [selectedNodes, otherProp] = useStore((state) => [
  state.selectedNodes,
  state.otherProp,
]);
```

**Rule:** Configure store with `shallow` to avoid manual `useShallow` usage.

---

## Performance Benchmarks (100 Nodes)

| Optimization Level | Default Nodes (FPS) | Heavy Nodes (FPS) |
|-------------------|---------------------|-------------------|
| No optimization | 10 | 2 |
| ReactFlow memoization only | 50-60 | 30 |
| + React.memo on nodes | 60 | 35-40 |
| + React.memo on heavy content | 60 | 60 |

**Target:** 60 FPS with "heavy" nodes (DataGrid, Charts, complex UI)

---

## Implementation Checklist for Production

### Phase 1: Critical (Required for 1K+ nodes)
- [ ] **Audit all `<ReactFlow>` props** - Ensure ALL are memoized
- [ ] **Wrap ALL custom nodes in `React.memo`**
- [ ] **Configure Zustand store with `shallow`**
- [ ] **Remove direct `state.nodes` dependencies** - Use separate state fields

### Phase 2: Advanced (Required for 5K-10K nodes)
- [ ] **Wrap heavy child components in `React.memo`** (DataGrid, QuestionMarkIcon)
- [ ] **Optimize CSS** - Reduce animations, shadows, gradients on nodes
- [ ] **Profile with React DevTools** - Identify remaining bottlenecks
- [ ] **Test stress scenarios** - 5K nodes with dragging/panning

### Phase 3: Optional (For 10K+ nodes)
- [ ] **Consider WebGL-based library** (Sigma.js, Cytoscape.js)
- [ ] **Implement progressive loading** - Load nodes in batches
- [ ] **Add clustering** - Group distant nodes visually
- [ ] **Server-side rendering** - Pre-render initial layout

---

## Current Implementation Status (v4.3.0)

### ✅ Implemented
- 500-node visible limit with smart prioritization
- Basic node limiting prevents browser crashes

### ⚠️ Not Yet Implemented
- [ ] `<ReactFlow>` props memoization audit
- [ ] Custom nodes wrapped in `React.memo`
- [ ] Zustand store configured with `shallow`
- [ ] Separate state for frequently changing data
- [ ] Heavy component memoization (QuestionMarkIcon, CustomNode children)

### 📋 Recommended Next Sprint
1. **Audit `App.tsx`** - Verify all ReactFlow props are memoized
2. **Wrap `CustomNode.tsx` in `memo()`**
3. **Configure Zustand with `shallow`** (if using Zustand)
4. **Test with 1,000 nodes** - Remove 500-node limit temporarily
5. **Measure FPS** - Use browser DevTools Performance tab
6. **Iterate** - Profile and optimize bottlenecks

---

## Testing Performance

### Browser DevTools
1. Open Chrome DevTools → Performance tab
2. Click "Record"
3. Drag a node for 3-5 seconds
4. Stop recording
5. Check **FPS graph** - Should be 60 FPS (green bar)

### Stress Test
```typescript
// Generate test data
const generateNodes = (count: number) => {
  return Array.from({ length: count }, (_, i) => ({
    id: `${i}`,
    type: 'custom',
    position: { x: Math.random() * 1000, y: Math.random() * 1000 },
    data: { label: `Node ${i}` },
  }));
};

// Test with increasing counts
const nodes = generateNodes(1000);  // 1K
const nodes = generateNodes(5000);  // 5K
const nodes = generateNodes(10000); // 10K
```

### Success Criteria
- **1K nodes:** 60 FPS during dragging
- **5K nodes:** 45-60 FPS during dragging
- **10K nodes:** 30-45 FPS during dragging (consider WebGL)

---

## Additional Resources

- **React Flow Official Docs:** https://reactflow.dev/learn/advanced-use/performance
- **Stress Test Example:** https://reactflow.dev/examples/nodes/stress
- **Medium Article:** "The ultimate guide to optimize React Flow project performance" by Łukasz Jaźwa
- **GitHub Discussion:** https://github.com/xyflow/xyflow/discussions/4975

---

## Conclusion

**For UAT:** 500-node limit is sufficient with current implementation.

**For Production (5K-10K nodes):** MUST implement all Phase 1 optimizations:
1. Memoize ALL ReactFlow props
2. Wrap ALL custom nodes in React.memo
3. Configure Zustand with shallow
4. Eliminate direct nodes/edges array dependencies

**Expected Result:** 60 FPS with proper memoization, even with "heavy" nodes (DataGrid, complex UI).

---

**Document Version:** 1.0
**Last Updated:** 2025-11-11
**Status:** Ready for next sprint implementation

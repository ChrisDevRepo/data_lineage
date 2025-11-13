# Graphology BFS - When to Use Library vs Manual Implementation

## Executive Summary

**Graphology and graphology-traversal are excellent, production-ready libraries.**

This document explains when to use the library vs when a simple manual implementation is clearer.

---

## Two BFS Use Cases in This Codebase

### ✅ Case 1: Interactive Trace - **USING LIBRARY**

**Requirements:**
- Start from **1 node**
- Traverse **one direction** (upstream OR downstream)
- Stop at **specific depth** (e.g., 3 levels)

**Library API:** Perfect fit
```typescript
bfsFromNode(graph, startNode, (nodeId, attr, depth) => {
    if (depth >= maxLevels) return true; // Stop at depth
    visibleIds.add(nodeId);
    return false; // Continue
}, { mode: 'inbound' }); // or 'outbound'
```

**Result:** Simplified code, well-tested library ✅

---

### ⚠️ Case 2: Focus Schema Filtering - **MANUAL IMPLEMENTATION**

**Requirements:**
1. Start from **10+ nodes simultaneously** (all focus schemas)
2. Traverse **both directions** (upstream AND downstream at once)
3. Filter by schema while traversing

**Library limitations:**
- `bfsFromNode(graph, startNode, ...)` accepts **1 node only**
- `mode` is `'inbound'` **OR** `'outbound'` (not both)
- No bidirectional mode for directed graphs

**Workaround attempts:**

❌ **Option A:** Call library 10 times
- Separate tracking per call (incorrect results)
- More complex than manual BFS

❌ **Option B:** Create temporary super-root node
- Modifies graph structure
- Still single-direction
- Complex cleanup logic

❌ **Option C:** Run library twice (inbound + outbound)
- Need to recreate graph structure
- Complex edge case handling
- Way more code than manual BFS

**✅ Manual implementation:** Simple and clear
```typescript
// 12 lines total - simpler than any library workaround
const reachable = new Set(focusNodeIds); // Start with ALL focus nodes
const queue = Array.from(focusNodeIds);  // Queue ALL at once

while (queue.length > 0) {
    const nodeId = queue.shift()!;
    const neighbors = graph.neighbors(nodeId); // Bidirectional: in + out

    for (const neighbor of neighbors) {
        if (visibleIds.has(neighbor) && !reachable.has(neighbor)) {
            reachable.add(neighbor);
            queue.push(neighbor);
        }
    }
}
```

**Why this is better:**
- ✅ Starts from 10+ nodes naturally (no library support needed)
- ✅ `graph.neighbors()` is bidirectional by default (in + out neighbors)
- ✅ 12 lines - simpler than any library workaround
- ✅ No graph modifications, no cleanup needed
- ✅ Clear, readable, correct

---

## Decision Matrix

| Requirement | Library Support | Manual BFS |
|-------------|----------------|------------|
| Single source | ✅ Perfect | ✅ Works |
| Multiple sources | ❌ Not supported | ✅ Natural |
| Unidirectional | ✅ Perfect | ✅ Works |
| Bidirectional | ❌ Not supported | ✅ Natural |
| Depth-limited | ✅ Perfect | ✅ Works |
| Conditional filtering | ✅ Via callback | ✅ Via if statements |

---

## Best Practice Guidelines

### ✅ Use graphology-traversal when:
1. Requirements match library API
2. Code becomes simpler
3. Single source + unidirectional + depth-limited

### ✅ Use manual BFS when:
1. Library doesn't support requirements
2. Workarounds are more complex than manual code
3. Multi-source OR bidirectional traversal needed

**Key principle:** Use the library when it makes code simpler. If workarounds are more complex than a simple loop, use the loop.

---

## Testing

Both implementations are thoroughly tested:

**Interactive Trace (library):**
- `frontend/test_interactive_trace_bfs.mjs`
- 4/4 tests pass
- Old vs new: identical results

**Focus Schema Filtering (manual):**
- `frontend/test_focus_schema_filtering.mjs`
- 5/5 tests pass
- Includes prima example verification

---

## Conclusion

**Graphology is NOT wrong - it's an excellent library.**

We use it extensively:
- ✅ Graph data structure (entire codebase)
- ✅ BFS for Interactive Trace
- ✅ Graph utilities and algorithms

For Focus Schema Filtering, the 12-line manual BFS is the **simpler, clearer solution** because the library API doesn't match our specific needs.

**This is good engineering practice** - not every problem requires a library if the manual solution is clearer.

---

**Last Updated**: 2025-11-13
**Version**: v4.3.3
**Files:** `frontend/hooks/useDataFiltering.ts`, `frontend/hooks/useInteractiveTrace.ts`

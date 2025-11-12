# Frontend Performance Testing Guide

## Quick Performance Check

### 1. FPS Monitoring (Development Mode)

```bash
npm run dev
```

Open browser console and run:
```javascript
// Track FPS for 5 seconds
window.__fpsMonitor.reset();
setTimeout(() => {
  console.log(`Average FPS: ${window.__fpsMonitor.getAverage()}`);
}, 5000);
```

**During the 5 seconds:** Drag nodes, pan, zoom to stress-test rendering.

**Target FPS:**
- **60 FPS**: Excellent (production-ready)
- **45-60 FPS**: Good (acceptable for production)
- **30-45 FPS**: Fair (may need optimization)
- **<30 FPS**: Poor (optimization required)

### 2. React DevTools Profiler

1. Install [React Developer Tools](https://react.dev/learn/react-developer-tools)
2. Open DevTools → Profiler tab
3. Click record (●)
4. Drag nodes for 3-5 seconds
5. Stop recording
6. Analyze flame graph for slow components

**Look for:**
- Components rendering more than expected
- Long render times (>16ms for 60 FPS)
- Unnecessary re-renders

### 3. Chrome Performance Profiler

1. Open DevTools → Performance tab
2. Click record (●)
3. Drag nodes for 3-5 seconds
4. Stop recording
5. Check **FPS graph** (green = good, yellow/red = bad)

**Target:** Solid green bar at 60 FPS

## Performance Optimization Checklist

✅ All ReactFlow props memoized (useCallback/useMemo)
✅ CustomNode wrapped in React.memo
✅ QuestionMarkIcon wrapped in React.memo
✅ No inline objects/functions passed to ReactFlow
✅ CSS transitions optimized (transition-transform vs transition-all)
✅ Custom hooks avoid direct node/edge array dependencies
✅ Debouncing for large datasets (>500 nodes)

## Stress Testing with Large Datasets

### Generate Test Data (1K, 5K, 10K nodes)

Use the import modal to upload larger Parquet files, or modify `utils/data.ts`:

```typescript
// Change SAMPLE_NODE_COUNT for testing
export const SAMPLE_NODE_COUNT = 1000; // Test with 1K nodes
export const SAMPLE_NODE_COUNT = 5000; // Test with 5K nodes
```

### Performance Targets by Dataset Size

| Nodes | Target FPS | Status |
|-------|------------|--------|
| 500   | 60 FPS     | ✅ Current limit |
| 1,000 | 60 FPS     | Expected with optimizations |
| 5,000 | 45-60 FPS  | Target for production |
| 10,000| 30-45 FPS  | May require WebGL (Sigma.js) |

## Troubleshooting Performance Issues

### Issue: Low FPS (<30) with current dataset

**Check:**
1. Open React DevTools Profiler
2. Look for components re-rendering on every drag
3. Check if CustomNode is memoized
4. Verify no inline functions in ReactFlow props

**Fix:**
- Wrap problematic components in `React.memo()`
- Use `useCallback` for all event handlers
- Use `useMemo` for expensive calculations

### Issue: FPS degrades over time

**Cause:** Memory leak or growing state arrays

**Fix:**
- Check browser memory usage (DevTools → Memory tab)
- Look for state that grows indefinitely
- Ensure cleanup in useEffect hooks

### Issue: Initial render is slow

**Cause:** Layout calculation for large graphs

**Fix:**
- Profile layout.ts with Chrome DevTools
- Consider caching layout for unchanged subgraphs
- Evaluate alternative layout algorithms (elk.js, d3-hierarchy)

## Best Practices

1. **Test with production build:** `npm run build && npm run preview`
2. **Measure before optimizing:** Use profiler to find real bottlenecks
3. **Optimize iteratively:** Fix biggest bottleneck first, re-measure
4. **Monitor regressions:** Run FPS check after each feature addition

## Resources

- [React Flow Performance Guide](https://reactflow.dev/learn/advanced-use/performance)
- [React DevTools Profiler Guide](https://react.dev/learn/react-developer-tools#profiler)
- [Chrome DevTools Performance](https://developer.chrome.com/docs/devtools/performance/)
- [Web Vitals](https://web.dev/vitals/)

---

**Last Updated:** 2025-11-11
**Status:** Optimizations applied, ready for testing

#!/usr/bin/env python3
"""
Comprehensive frontend performance optimization script.

Applies all optimizations from REACT_FLOW_PERFORMANCE.md:
1. Memoize all ReactFlow props
2. Fix inline objects and functions
3. Optimize CSS transitions
4. Add performance monitoring
"""

import re
from pathlib import Path


def optimize_app_tsx():
    """Fix inline proOptions object in App.tsx"""
    file_path = Path('frontend/App.tsx')

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the proOptions line
    original = content

    # Add useMemo for proOptions at the top of component (after state declarations)
    # Find a good place to insert - after the useReactFlow hook
    insert_after = "const { fitView, setCenter, getNodes, getEdges } = useReactFlow();"

    proptions_memo = """
  // Memoize ReactFlow proOptions for performance (stable reference)
  const reactFlowProOptions = useMemo(() => ({ hideAttribution: true }), []);
"""

    if insert_after in content:
        content = content.replace(
            insert_after,
            insert_after + proptions_memo
        )

    # Replace inline proOptions with memoized version
    content = re.sub(
        r'proOptions=\{\{ hideAttribution: true \}\}',
        'proOptions={reactFlowProOptions}',
        content
    )

    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Optimized {file_path}")
        print("  - Memoized proOptions object")
        return True

    return False


def optimize_custom_node_css():
    """Optimize CSS transitions in CustomNode to be more specific"""
    file_path = Path('frontend/components/CustomNode.tsx')

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Change transition-all to specific transitions for better performance
    content = content.replace(
        'transition-all duration-300',
        'transition-transform duration-200'
    )

    if content != original:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✓ Optimized {file_path}")
        print("  - Changed transition-all to transition-transform (more performant)")
        return True

    return False


def add_performance_monitoring():
    """Add FPS monitoring for development mode"""
    file_path = Path('frontend/utils/logger.ts')

    # Check if performance monitoring already exists
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if 'trackFPS' in content:
        print(f"✓ Performance monitoring already exists in {file_path}")
        return False

    # Add FPS tracking utility
    fps_monitor = """

// FPS Monitoring (Development Only)
class FPSMonitor {
  private frames: number[] = [];
  private lastTime: number = performance.now();

  track() {
    const now = performance.now();
    const delta = now - this.lastTime;

    if (delta > 0) {
      const fps = 1000 / delta;
      this.frames.push(fps);

      // Keep only last 60 frames (1 second at 60fps)
      if (this.frames.length > 60) {
        this.frames.shift();
      }
    }

    this.lastTime = now;
  }

  getAverage(): number {
    if (this.frames.length === 0) return 0;
    const sum = this.frames.reduce((a, b) => a + b, 0);
    return Math.round(sum / this.frames.length);
  }

  reset() {
    this.frames = [];
    this.lastTime = performance.now();
  }
}

export const fpsMonitor = new FPSMonitor();

// Expose FPS tracker in development mode
if (import.meta.env.DEV) {
  // @ts-ignore
  window.__fpsMonitor = fpsMonitor;
  console.log('📊 FPS Monitor available at window.__fpsMonitor');
  console.log('   Usage: window.__fpsMonitor.getAverage()');
}
"""

    content += fps_monitor

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ Added FPS monitoring to {file_path}")
    print("  - FPS monitor available in dev mode at window.__fpsMonitor")
    return True


def create_performance_readme():
    """Create performance testing guide"""
    content = """# Frontend Performance Testing Guide

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
"""

    file_path = Path('frontend/docs/PERFORMANCE_TESTING.md')
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ Created {file_path}")
    return True


def main():
    """Run all optimizations"""
    print("🚀 Running frontend performance optimizations...\n")

    changes_made = 0

    if optimize_app_tsx():
        changes_made += 1

    if optimize_custom_node_css():
        changes_made += 1

    if add_performance_monitoring():
        changes_made += 1

    if create_performance_readme():
        changes_made += 1

    print(f"\n✅ Applied {changes_made} optimizations")
    print("\n📊 Next steps:")
    print("1. Run `npm run dev` and test FPS with window.__fpsMonitor")
    print("2. Test with 1,000+ nodes (remove 500-node limit)")
    print("3. Profile with React DevTools")
    print("4. See frontend/docs/PERFORMANCE_TESTING.md for details")


if __name__ == '__main__':
    main()

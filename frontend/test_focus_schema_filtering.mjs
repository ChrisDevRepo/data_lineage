// Focus Schema Filtering - Correctness Test
// Validates the manual BFS implementation for focus schema filtering
import Graph from 'graphology';

console.log('🧪 FOCUS SCHEMA FILTERING - CORRECTNESS TEST\n');
console.log('='.repeat(70));

// Manual BFS implementation (production code)
function focusSchemaFilter(graph, allNodes, focusSchemas, selectedSchemas) {
    const focusNodes = allNodes.filter(n => focusSchemas.has(n.schema));
    const focusNodeIds = new Set(focusNodes.map(n => n.id));
    const visibleNodes = allNodes.filter(n => selectedSchemas.has(n.schema));
    const visibleIds = new Set(visibleNodes.map(n => n.id));

    const reachable = new Set(focusNodeIds);
    const queue = Array.from(focusNodeIds);

    while (queue.length > 0) {
        const nodeId = queue.shift();
        try {
            const neighbors = graph.neighbors(nodeId); // Bidirectional
            for (const neighbor of neighbors) {
                if (visibleIds.has(neighbor) && !reachable.has(neighbor)) {
                    reachable.add(neighbor);
                    queue.push(neighbor);
                }
            }
        } catch (e) {}
    }

    return Array.from(reachable).sort();
}

// Test runner
function runTest(testName, graphSetup, focusSchemas, selectedSchemas, expectedNodes) {
    console.log(`\n📋 TEST: ${testName}`);
    console.log('-'.repeat(70));

    const { graph, nodes } = graphSetup();
    const result = focusSchemaFilter(graph, nodes, focusSchemas, selectedSchemas);

    console.log(`Focus schemas: [${Array.from(focusSchemas).join(', ')}]`);
    console.log(`Selected schemas: [${Array.from(selectedSchemas).join(', ')}]`);
    console.log(`Graph: ${graph.order} nodes, ${graph.size} edges`);
    console.log(`Result: [${result.join(', ')}]`);
    console.log(`Expected: [${expectedNodes.join(', ')}]`);

    const isCorrect = result.length === expectedNodes.length &&
                     result.every((id, i) => id === expectedNodes[i]);

    if (isCorrect) {
        console.log('✅ PASS');
        return true;
    } else {
        console.log('❌ FAIL');
        return false;
    }
}

// ============================================================================
// TEST 1: Prima Example (User's Original Scenario)
// ============================================================================
function primaExample() {
    const graph = new Graph({ type: 'directed' });
    const nodes = [
        { id: '1', schema: 'consumption_financehub', name: 'Table1' },
        { id: '2', schema: 'consumption_financehub', name: 'Table2' },
        { id: '3', schema: 'siteperformance', name: 'TableSP' },
        { id: '4', schema: 'consumption_prima', name: 'TablePrima' },
        { id: '5', schema: 'consumption_prima', name: 'TablePrima2' },
    ];

    nodes.forEach(n => graph.addNode(n.id, n));
    graph.addEdge('1', '3');  // financehub → siteperformance
    graph.addEdge('3', '4');  // siteperformance → prima.TablePrima
    graph.addEdge('2', '5');  // financehub → prima.TablePrima2 (DIRECT)

    return { graph, nodes };
}

// ============================================================================
// TEST 2: Multiple Focus Schemas
// ============================================================================
function multipleFocus() {
    const graph = new Graph({ type: 'directed' });
    const nodes = [
        { id: '1', schema: 'focus_a', name: 'FocusA' },
        { id: '2', schema: 'focus_b', name: 'FocusB' },
        { id: '3', schema: 'extended', name: 'ExtA' },
        { id: '4', schema: 'extended', name: 'ExtB' },
        { id: '5', schema: 'extended', name: 'Shared' },
    ];

    nodes.forEach(n => graph.addNode(n.id, n));
    graph.addEdge('1', '3');
    graph.addEdge('2', '4');
    graph.addEdge('3', '5');
    graph.addEdge('4', '5');

    return { graph, nodes };
}

// ============================================================================
// TEST 3: Bidirectional Paths
// ============================================================================
function bidirectionalPaths() {
    const graph = new Graph({ type: 'directed' });
    const nodes = [
        { id: '1', schema: 'focus', name: 'Focus' },
        { id: '2', schema: 'extended', name: 'Upstream' },
        { id: '3', schema: 'extended', name: 'Downstream' },
    ];

    nodes.forEach(n => graph.addNode(n.id, n));
    graph.addEdge('2', '1');  // 2 → 1 (upstream to focus)
    graph.addEdge('1', '3');  // 1 → 3 (focus to downstream)

    return { graph, nodes };
}

// ============================================================================
// TEST 4: Blocked by Unselected Schema
// ============================================================================
function blockedPath() {
    const graph = new Graph({ type: 'directed' });
    const nodes = [
        { id: '1', schema: 'focus', name: 'Focus' },
        { id: '2', schema: 'unselected', name: 'Blocker' },
        { id: '3', schema: 'extended', name: 'Unreachable' },
    ];

    nodes.forEach(n => graph.addNode(n.id, n));
    graph.addEdge('1', '2');
    graph.addEdge('2', '3');

    return { graph, nodes };
}

// ============================================================================
// TEST 5: Cyclic Graph
// ============================================================================
function cyclicGraph() {
    const graph = new Graph({ type: 'directed' });
    const nodes = [
        { id: '1', schema: 'focus', name: 'A' },
        { id: '2', schema: 'extended', name: 'B' },
        { id: '3', schema: 'extended', name: 'C' },
    ];

    nodes.forEach(n => graph.addNode(n.id, n));
    graph.addEdge('1', '2');
    graph.addEdge('2', '3');
    graph.addEdge('3', '2'); // Cycle: 2 ↔ 3

    return { graph, nodes };
}

// ============================================================================
// RUN ALL TESTS
// ============================================================================
const tests = [
    {
        name: 'Prima Example',
        setup: primaExample,
        focus: new Set(['consumption_financehub']),
        selected: new Set(['consumption_financehub', 'consumption_prima']),
        expected: ['1', '2', '5'] // financehub nodes + prima.TablePrima2 (direct), NOT prima.TablePrima (through unselected)
    },
    {
        name: 'Multiple Focus Schemas',
        setup: multipleFocus,
        focus: new Set(['focus_a', 'focus_b']),
        selected: new Set(['focus_a', 'focus_b', 'extended']),
        expected: ['1', '2', '3', '4', '5'] // All nodes
    },
    {
        name: 'Bidirectional Paths',
        setup: bidirectionalPaths,
        focus: new Set(['focus']),
        selected: new Set(['focus', 'extended']),
        expected: ['1', '2', '3'] // Focus + both upstream and downstream
    },
    {
        name: 'Blocked by Unselected Schema',
        setup: blockedPath,
        focus: new Set(['focus']),
        selected: new Set(['focus', 'extended']),
        expected: ['1'] // Only focus, extended.Unreachable is blocked
    },
    {
        name: 'Cyclic Graph',
        setup: cyclicGraph,
        focus: new Set(['focus']),
        selected: new Set(['focus', 'extended']),
        expected: ['1', '2', '3'] // All nodes in cycle are reachable
    }
];

let passed = 0;
let failed = 0;

tests.forEach(test => {
    const result = runTest(test.name, test.setup, test.focus, test.selected, test.expected);
    if (result) passed++;
    else failed++;
});

// ============================================================================
// SUMMARY
// ============================================================================
console.log('\n' + '='.repeat(70));
console.log('📊 SUMMARY');
console.log('='.repeat(70));
console.log(`\nTests passed: ${passed}/${tests.length}`);
console.log(`Tests failed: ${failed}/${tests.length}`);

if (failed === 0) {
    console.log('\n✅ ALL TESTS PASSED - Focus schema filtering is correct!');
    console.log('\n🎉 Production ready\n');
    process.exit(0);
} else {
    console.log('\n❌ SOME TESTS FAILED');
    process.exit(1);
}

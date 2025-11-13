// Interactive Trace BFS - Old vs New Comparison
// This BFS is a PERFECT fit for graphology-traversal!
import Graph from 'graphology';
import { bfsFromNode } from 'graphology-traversal';

console.log('🧪 INTERACTIVE TRACE BFS - OLD VS NEW COMPARISON\n');
console.log('='.repeat(70));

// OLD implementation (manual BFS with level tracking)
function oldTraverse(lineageGraph, startNode, maxLevels, getNeighbors, includedSchemas, includedTypes) {
    const queue = [{ id: startNode, level: 0 }];
    const visited = new Set([startNode]);
    const visibleIds = new Set([startNode]);

    let head = 0;
    while (head < queue.length) {
        const { id: currentId, level } = queue[head++];
        if (level >= maxLevels) continue;

        getNeighbors(currentId, (neighborId) => {
            if (visited.has(neighborId)) return;
            visited.add(neighborId);

            const neighborNode = lineageGraph.getNodeAttributes(neighborId);
            if (!neighborNode) return;
            if (!includedSchemas.has(neighborNode.schema)) return;
            if (neighborNode.data_model_type && !includedTypes.has(neighborNode.data_model_type)) return;

            visibleIds.add(neighborId);
            queue.push({ id: neighborId, level: level + 1 });
        });
    }

    return visibleIds;
}

// NEW implementation (graphology-traversal)
function newTraverse(lineageGraph, startNode, maxLevels, mode, includedSchemas, includedTypes) {
    const visibleIds = new Set();

    bfsFromNode(lineageGraph, startNode, (nodeId, attr, depth) => {
        // Filter by schema
        if (!includedSchemas.has(attr.schema)) return true;

        // Filter by data model type
        if (attr.data_model_type && !includedTypes.has(attr.data_model_type)) return true;

        // Add to visible set
        visibleIds.add(nodeId);

        // Stop exploring this node's neighbors if we've reached max depth
        // depth=0 is start, depth=1 is 1 step away, etc.
        // maxLevels=1 means explore nodes at depth 0 and 1, but not 1's neighbors (depth 2)
        if (depth >= maxLevels) return true;

        return false; // Continue traversal from this node
    }, { mode });

    return visibleIds;
}

// Test graph
function createTestGraph() {
    const graph = new Graph({ type: 'directed' });
    const nodes = [
        { id: '1', schema: 'dbo', data_model_type: 'table', name: 'Start' },
        { id: '2', schema: 'dbo', data_model_type: 'table', name: 'Level1A' },
        { id: '3', schema: 'dbo', data_model_type: 'table', name: 'Level1B' },
        { id: '4', schema: 'dbo', data_model_type: 'view', name: 'Level2A' },
        { id: '5', schema: 'dbo', data_model_type: 'table', name: 'Level2B' },
        { id: '6', schema: 'excluded', data_model_type: 'table', name: 'ExcludedSchema' },
        { id: '7', schema: 'dbo', data_model_type: 'function', name: 'ExcludedType' },
    ];

    nodes.forEach(n => graph.addNode(n.id, n));

    // Downstream edges (1 → 2 → 4, 1 → 3 → 5)
    graph.addEdge('1', '2');
    graph.addEdge('1', '3');
    graph.addEdge('2', '4');
    graph.addEdge('3', '5');
    graph.addEdge('2', '6'); // To excluded schema
    graph.addEdge('3', '7'); // To excluded type

    return { graph, nodes };
}

// Run test
function runTest(testName, maxLevels, mode, includedSchemas, includedTypes, expected) {
    console.log(`\n📋 TEST: ${testName}`);
    console.log('-'.repeat(70));

    const { graph } = createTestGraph();
    const startNode = '1';

    const getNeighbors = mode === 'outbound'
        ? (node, cb) => graph.forEachOutNeighbor(node, cb)
        : (node, cb) => graph.forEachInNeighbor(node, cb);

    // Performance test
    const oldStart = performance.now();
    const oldResult = oldTraverse(graph, startNode, maxLevels, getNeighbors, includedSchemas, includedTypes);
    const oldTime = performance.now() - oldStart;

    const newStart = performance.now();
    const newResult = newTraverse(graph, startNode, maxLevels, mode, includedSchemas, includedTypes);
    const newTime = performance.now() - newStart;

    // Correctness check
    const oldArray = Array.from(oldResult).sort();
    const newArray = Array.from(newResult).sort();
    const expectedArray = expected.sort();

    const oldCorrect = oldArray.length === expectedArray.length &&
                      oldArray.every((id, i) => id === expectedArray[i]);
    const newCorrect = newArray.length === expectedArray.length &&
                      newArray.every((id, i) => id === expectedArray[i]);
    const identical = oldArray.length === newArray.length &&
                     oldArray.every((id, i) => id === newArray[i]);

    console.log(`Max levels: ${maxLevels}`);
    console.log(`Mode: ${mode}`);
    console.log(`Schemas: [${Array.from(includedSchemas).join(', ')}]`);
    console.log(`Types: [${Array.from(includedTypes).join(', ')}]`);
    console.log('');
    console.log(`Old result: [${oldArray.join(', ')}] (${oldTime.toFixed(3)}ms)`);
    console.log(`New result: [${newArray.join(', ')}] (${newTime.toFixed(3)}ms)`);
    console.log(`Expected:   [${expectedArray.join(', ')}]`);
    console.log('');
    console.log(`Old correct: ${oldCorrect ? '✅' : '❌'}`);
    console.log(`New correct: ${newCorrect ? '✅' : '❌'}`);
    console.log(`Identical:   ${identical ? '✅' : '❌'}`);
    console.log(`Speedup:     ${(oldTime / newTime).toFixed(2)}x`);

    return oldCorrect && newCorrect && identical;
}

// ============================================================================
// RUN TESTS
// ============================================================================
const tests = [
    {
        name: 'Downstream 1 level',
        maxLevels: 1,
        mode: 'outbound',
        schemas: new Set(['dbo']),
        types: new Set(['table', 'view']),
        expected: ['1', '2', '3'] // Start + level 1
    },
    {
        name: 'Downstream 2 levels',
        maxLevels: 2,
        mode: 'outbound',
        schemas: new Set(['dbo']),
        types: new Set(['table', 'view']),
        expected: ['1', '2', '3', '4', '5'] // Start + level 1 + level 2
    },
    {
        name: 'Downstream with type filter',
        maxLevels: 2,
        mode: 'outbound',
        schemas: new Set(['dbo']),
        types: new Set(['table']), // Exclude 'view' (node 4)
        expected: ['1', '2', '3', '5'] // Excludes node 4 (view)
    },
    {
        name: 'Upstream (create reverse graph first)',
        maxLevels: 2,
        mode: 'inbound',
        schemas: new Set(['dbo']),
        types: new Set(['table', 'view']),
        expected: ['1'] // Node 1 has no upstream neighbors
    }
];

let passed = 0;
let failed = 0;

tests.forEach(test => {
    const result = runTest(test.name, test.maxLevels, test.mode, test.schemas, test.types, test.expected);
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
    console.log('\n✅ ALL TESTS PASSED - graphology-traversal is correct and faster!');
    console.log('\n🎉 Ready to replace manual BFS in useInteractiveTrace.ts\n');
    process.exit(0);
} else {
    console.log('\n❌ SOME TESTS FAILED');
    process.exit(1);
}

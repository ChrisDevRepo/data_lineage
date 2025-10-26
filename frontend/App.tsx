import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
  ReactFlow,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  MiniMap,
  useReactFlow,
  ReactFlowProvider,
  Node as ReactFlowNode,
} from 'reactflow';
import { dfsFromNode } from 'graphology-traversal';
import { CustomNode, nodeTypes } from './components/CustomNode';
import { Legend } from './components/Legend';
import { Toolbar } from './components/Toolbar';
import { ImportDataModal } from './components/ImportDataModal';
import { InfoModal } from './components/InfoModal';
import { InteractiveTracePanel } from './components/InteractiveTracePanel';
import { NotificationContainer, NotificationHistory } from './components/NotificationSystem';
import { useGraphology } from './hooks/useGraphology';
import { useNotifications } from './hooks/useNotifications';
import { useInteractiveTrace } from './hooks/useInteractiveTrace';
import { useDataFiltering } from './hooks/useDataFiltering';
import { getDagreLayoutedElements } from './utils/layout';
import { generateSampleData } from './utils/data';
import { DataNode } from './types';
import { CONSTANTS } from './constants';

// --- Main App Component ---
function DataLineageVisualizer() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const { fitView, setCenter, getNodes, getEdges } = useReactFlow();

  // --- State Management ---
  const [allData, setAllData] = useState<DataNode[]>(generateSampleData);
  const [sampleData] = useState<DataNode[]>(() => generateSampleData());
  const [layout, setLayout] = useState<'LR' | 'TB'>('LR');
  const [viewMode, setViewMode] = useState<'detail' | 'schema'>('detail');
  const [focusedNodeId, setFocusedNodeId] = useState<string | null>(null);

  // --- Custom Hooks for Logic Encapsulation ---
  const { addNotification, activeToasts, removeActiveToast, notificationHistory, clearNotificationHistory } = useNotifications();
  const { lineageGraph, schemas, schemaColorMap, dataModelTypes } = useGraphology(allData);
  const { traceConfig, isTraceModeActive, setIsTraceModeActive, performInteractiveTrace, handleApplyTrace, handleExitTraceMode } = useInteractiveTrace(addNotification, lineageGraph);
  const {
    finalVisibleData,
    selectedSchemas,
    setSelectedSchemas,
    selectedTypes,
    setSelectedTypes,
    searchTerm,
    setSearchTerm,
    hideUnrelated,
    setHideUnrelated,
    highlightedNodes,
    setHighlightedNodes,
    autocompleteSuggestions,
    setAutocompleteSuggestions,
  } = useDataFiltering({ allData, lineageGraph, schemas, dataModelTypes, isTraceModeActive, traceConfig, performInteractiveTrace });

  // --- UI State ---
  const [isLegendCollapsed, setIsLegendCollapsed] = useState(true);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [isInfoModalOpen, setIsInfoModalOpen] = useState(false);
  const [isControlsVisible, setIsControlsVisible] = useState(true);

  // --- Memos for Derived State and Layouting ---
  const layoutedElements = useMemo(() => {
    return getDagreLayoutedElements({
      data: finalVisibleData,
      viewMode,
      layout,
      schemas,
      selectedSchemas,
      schemaColorMap,
      lineageGraph,
      isTraceModeActive,
    });
  }, [finalVisibleData, viewMode, layout, schemaColorMap, schemas, selectedSchemas, lineageGraph, isTraceModeActive]);

  const finalNodes = useMemo(() => {
    const currentHighlights = isTraceModeActive && traceConfig?.startNodeId
      ? new Set([traceConfig.startNodeId])
      : highlightedNodes;

    return layoutedElements.nodes.map(n => ({
      ...n,
      data: {
        ...n.data,
        isHighlighted: currentHighlights.has(n.id),
        isDimmed: !isTraceModeActive && highlightedNodes.size > 0 && !highlightedNodes.has(n.id),
        layoutDir: layout
      }
    }));
  }, [layoutedElements.nodes, highlightedNodes, layout, isTraceModeActive, traceConfig]);

  // --- Effects to Synchronize State with React Flow ---
  useEffect(() => {
    setNodes(finalNodes);
    setEdges(layoutedElements.edges);
  }, [finalNodes, layoutedElements.edges, setNodes, setEdges]);

  useEffect(() => {
    if (nodes.length > 0) {
      const timeoutId = setTimeout(() => fitView({ padding: 0.2, duration: 500 }), 150);
      return () => clearTimeout(timeoutId);
    }
  }, [nodes.length, fitView, isTraceModeActive]);
  
  // --- Effect for handling window resize ---
  useEffect(() => {
    // Debounce resize events to avoid excessive calls
    let timeoutId: number | undefined;
    const debouncedHandleResize = () => {
      clearTimeout(timeoutId);
      timeoutId = window.setTimeout(() => {
        fitView({ duration: 200 });
      }, 150);
    };

    window.addEventListener('resize', debouncedHandleResize);

    return () => {
      clearTimeout(timeoutId);
      window.removeEventListener('resize', debouncedHandleResize);
    };
  }, [fitView]); // Dependency on fitView ensures it's not stale

  // --- Event Handlers ---
  const handleNodeClick = (_: React.MouseEvent, node: ReactFlowNode) => {
    if (viewMode === 'schema' || isTraceModeActive) return;
  
    if (focusedNodeId === node.id) {
      // If the already-focused node is clicked again, clear the focus.
      setFocusedNodeId(null);
      setHighlightedNodes(new Set());
    } else {
      // Focus on the new node and highlight its immediate neighborhood.
      setFocusedNodeId(node.id);
      const nodesToHighlight = new Set<string>([node.id]);
      if (lineageGraph.hasNode(node.id)) {
        // Use `neighbors` to get both incoming and outgoing connections (level 1 parents and children)
        const neighbors = lineageGraph.neighbors(node.id);
        neighbors.forEach(neighborId => {
          nodesToHighlight.add(neighborId);
        });
      }
      setHighlightedNodes(nodesToHighlight);
    }
  };
  
  const handleDataImport = (newData: DataNode[]) => {
    const processedData = newData.map(node => ({ ...node, schema: node.schema.toUpperCase() }));
    setAllData(processedData);
    
    // Reset view state for a clean slate after import
    setFocusedNodeId(null);
    setHighlightedNodes(new Set());
    setSearchTerm('');

    addNotification('Data imported successfully! The view has been refreshed.', 'info');
    setIsImportModalOpen(false);
  };
  
  const executeSearch = (query: string) => {
    if (viewMode === 'schema' || isTraceModeActive) return;
    setFocusedNodeId(null);
    if (!query) {
      setHighlightedNodes(new Set());
      fitView({ duration: 500 });
      return;
    }
    const foundNodeData = allData.find(d => d.name.toLowerCase() === query.toLowerCase());
    if (!foundNodeData) {
      addNotification('No object found with that name.', 'error');
      return;
    }
    const reactFlowNode = nodes.find(n => n.id === foundNodeData.id);
    if (!reactFlowNode) {
      addNotification('Object found, but it is not visible with the current filters.', 'error');
      return;
    }
    setHighlightedNodes(new Set([foundNodeData.id]));
    setCenter(
      reactFlowNode.position.x + (reactFlowNode.width || 192) / 2,
      reactFlowNode.position.y + (reactFlowNode.height || 48) / 2,
      { zoom: 1.2, duration: 800 }
    );
    setSearchTerm('');
  };

  const handlePaneClick = () => {
    if (!isTraceModeActive) {
      setHighlightedNodes(new Set());
      setFocusedNodeId(null);
    }
  };

  const miniMapNodeColor = (node: ReactFlowNode): string => {
    if (viewMode === 'schema' || !node.data.schema) return '#e2e8f0';
    return schemaColorMap.get(node.data.schema) || '#e2e8f0';
  };

  const handleExportSVG = useCallback(() => {
    const nodesToExport = getNodes();
    const edgesToExport = getEdges();

    if (nodesToExport.length === 0) {
        addNotification('Nothing to export.', 'error');
        return;
    }

    const PADDING = 50;
    const minX = Math.min(...nodesToExport.map(n => n.position.x));
    const minY = Math.min(...nodesToExport.map(n => n.position.y));
    const maxX = Math.max(...nodesToExport.map(n => n.position.x + (n.width || 0)));
    const maxY = Math.max(...nodesToExport.map(n => n.position.y + (n.height || 0)));
    const width = maxX - minX + PADDING * 2;
    const height = maxY - minY + PADDING * 2;
    const offsetX = -minX + PADDING;
    const offsetY = -minY + PADDING;

    const isHorizontal = layout === 'LR';

    const edgePaths = edgesToExport.map(edge => {
        const sourceNode = nodesToExport.find(n => n.id === edge.source);
        const targetNode = nodesToExport.find(n => n.id === edge.target);
        if (!sourceNode || !targetNode) return '';
        
        const sourceX = sourceNode.position.x + (isHorizontal ? (sourceNode.width || 0) : (sourceNode.width || 0) / 2) + offsetX;
        const sourceY = sourceNode.position.y + (isHorizontal ? (sourceNode.height || 0) / 2 : (sourceNode.height || 0)) + offsetY;
        const targetX = targetNode.position.x + (isHorizontal ? 0 : (targetNode.width || 0) / 2) + offsetX;
        const targetY = targetNode.position.y + (isHorizontal ? (targetNode.height || 0) / 2 : 0) + offsetY;

        if (isHorizontal) {
            const cpx1 = sourceX + (targetX - sourceX) * 0.5;
            return `<path d="M ${sourceX},${sourceY} C ${cpx1},${sourceY} ${cpx1},${targetY} ${targetX},${targetY}" stroke="#9ca3af" stroke-width="1.5" fill="none" marker-end="url(#arrow)" />`;
        }
        const cpy1 = sourceY + (targetY - sourceY) * 0.5;
        return `<path d="M ${sourceX},${sourceY} C ${sourceX},${cpy1} ${targetX},${cpy1} ${targetX},${targetY}" stroke="#9ca3af" stroke-width="1.5" fill="none" marker-end="url(#arrow)" />`;
    }).join('');
    
    const nodeElements = nodesToExport.map(node => {
        const { position, width: nodeWidth = 192, height: nodeHeight = 48, data } = node;
        const x = position.x + offsetX;
        const y = position.y + offsetY;

        const { style } = CONSTANTS.SHAPE_MAP[data.object_type] || {};
        const rx = style === 'rounded-full' ? nodeHeight / 2 : (style === 'rounded-md' ? 6 : 0);
        const strokeDasharray = style === 'border-dashed' ? '5, 5' : 'none';
        const color = schemaColorMap.get(data.schema) || '#7f7f7f';

        return `
            <g transform="translate(${x}, ${y})">
                <rect width="${nodeWidth}" height="${nodeHeight}" rx="${rx}" fill="${color}30" stroke="${color}" stroke-width="2" stroke-dasharray="${strokeDasharray}"/>
                <text x="${nodeWidth / 2}" y="${nodeHeight / 2}" dominant-baseline="middle" text-anchor="middle" font-family="sans-serif" font-size="14px" font-weight="bold" fill="#1f2937">
                    ${data.name}
                </text>
            </g>
        `;
    }).join('');

    const svgString = `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}"><defs><marker id="arrow" viewBox="0 -5 10 10" refX="8" refY="0" markerWidth="6" markerHeight="6" orient="auto"><path d="M0,-5L10,0L0,5" fill="#9ca3af"></path></marker></defs><g>${edgePaths}${nodeElements}</g></svg>`;
    const blob = new Blob([svgString], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'data-lineage.svg';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    addNotification('SVG export started.', 'info');
  }, [getNodes, getEdges, addNotification, schemaColorMap, layout]);

  return (
    <div className="w-screen h-screen flex flex-col font-sans">
      <header className="flex items-center justify-between p-3 bg-white shadow-md flex-shrink-0 z-20 border-b border-gray-200 text-gray-800">
        <h1 className="text-2xl font-bold">Data Lineage Visualizer</h1>
      </header>
      <main className="flex-grow p-4 relative bg-gray-100 overflow-hidden">
        <NotificationContainer activeToasts={activeToasts} onDismissToast={removeActiveToast} />
        <div className={`w-full h-full bg-white rounded-lg shadow-md flex flex-col text-gray-800 transition-all duration-300 ${isTraceModeActive ? 'pr-80' : ''}`}>
          <Toolbar
            viewMode={viewMode}
            setViewMode={setViewMode}
            searchTerm={searchTerm}
            setSearchTerm={setSearchTerm}
            executeSearch={executeSearch}
            autocompleteSuggestions={autocompleteSuggestions}
            setAutocompleteSuggestions={setAutocompleteSuggestions}
            selectedSchemas={selectedSchemas}
            setSelectedSchemas={setSelectedSchemas}
            schemas={schemas}
            selectedTypes={selectedTypes}
            setSelectedTypes={setSelectedTypes}
            dataModelTypes={dataModelTypes}
            layout={layout}
            setLayout={setLayout}
            hideUnrelated={hideUnrelated}
            setHideUnrelated={setHideUnrelated}
            isTraceModeActive={isTraceModeActive}
            onStartTrace={() => setIsTraceModeActive(true)}
            isControlsVisible={isControlsVisible}
            onToggleControls={() => setIsControlsVisible(p => !p)}
            onOpenImport={() => setIsImportModalOpen(true)}
            onOpenInfo={() => setIsInfoModalOpen(true)}
            onExportSVG={handleExportSVG}
            notificationHistory={notificationHistory}
            onClearNotificationHistory={clearNotificationHistory}
          />
          <div className="relative flex-grow rounded-b-lg">
            {isTraceModeActive && (
              <div className="absolute top-4 left-1/2 -translate-x-1/2 z-20 bg-blue-600 text-white px-4 py-2 rounded-lg shadow-lg flex items-center gap-4">
                <span className="font-semibold">You are in Interactive Trace Mode.</span>
                <button onClick={handleExitTraceMode} className="text-blue-100 hover:text-white underline font-bold">Exit</button>
              </div>
            )}
            <ReactFlow
              nodes={nodes} edges={edges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
              nodeTypes={nodeTypes}
              onPaneClick={handlePaneClick}
              onNodeClick={handleNodeClick}
              fitView
              minZoom={0.1}
              proOptions={{ hideAttribution: true }}
            >
              <Controls />
              {isControlsVisible && <MiniMap nodeColor={miniMapNodeColor} nodeStrokeWidth={3} nodeBorderRadius={2} zoomable pannable className="bg-white/80" ariaLabel="Minimap" />}
              <Background color={'#a1a1aa'} gap={16} />
              {isControlsVisible && viewMode === 'detail' && 
                <Legend 
                  isCollapsed={isLegendCollapsed} 
                  onToggle={() => setIsLegendCollapsed(p => !p)} 
                  schemas={schemas} 
                  schemaColorMap={schemaColorMap} 
                />}
            </ReactFlow>
          </div>
        </div>
        <InteractiveTracePanel 
          isOpen={isTraceModeActive} 
          onClose={handleExitTraceMode} 
          onApply={handleApplyTrace} 
          availableSchemas={schemas} 
          allData={allData} 
          addNotification={addNotification} 
        />
      </main>
      <ImportDataModal 
        isOpen={isImportModalOpen} 
        onClose={() => setIsImportModalOpen(false)} 
        onImport={handleDataImport} 
        currentData={allData} 
        defaultSampleData={sampleData} 
      />
      <InfoModal
        isOpen={isInfoModalOpen}
        onClose={() => setIsInfoModalOpen(false)}
      />
    </div>
  );
}

export default function App() {
  return (
    <ReactFlowProvider>
      <DataLineageVisualizer />
    </ReactFlowProvider>
  );
}
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
import { SqlViewer } from './components/SqlViewer';
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
  // Start with empty data, load from API asynchronously
  const [allData, setAllData] = useState<DataNode[]>([]);
  const [isLoadingData, setIsLoadingData] = useState(true);
  const [sampleData] = useState<DataNode[]>(() => generateSampleData());

  // Load data from API on mount (async to avoid blocking UI)
  useEffect(() => {
    const loadLatestData = async () => {
      const startTime = Date.now();

      try {
        const response = await fetch('http://localhost:8000/api/latest-data');

        if (!response.ok) {
          throw new Error(`API returned ${response.status}`);
        }

        const data = await response.json();
        const headerValue = response.headers.get('x-data-available');

        // Simple check: if we got an array with data, use it
        if (Array.isArray(data) && data.length > 0) {
          setAllData(data);
        } else {
          setAllData(generateSampleData());
        }
      } catch (error) {
        console.error('Failed to load from API:', error);
        setAllData(generateSampleData());
      } finally {
        // Ensure loading screen shows for at least 500ms for better UX
        const elapsed = Date.now() - startTime;
        const minDelay = 500;
        if (elapsed < minDelay) {
          setTimeout(() => setIsLoadingData(false), minDelay - elapsed);
        } else {
          setIsLoadingData(false);
        }
      }
    };

    loadLatestData();
  }, []);
  const [layout, setLayout] = useState<'LR' | 'TB'>('LR');
  const [viewMode, setViewMode] = useState<'detail' | 'schema'>('detail');
  const [focusedNodeId, setFocusedNodeId] = useState<string | null>(null);

  // --- Custom Hooks for Logic Encapsulation ---
  const { addNotification, activeToasts, removeActiveToast, notificationHistory, clearNotificationHistory } = useNotifications();
  const { lineageGraph, schemas, schemaColorMap, dataModelTypes } = useGraphology(allData);
  const { traceConfig, isTraceModeActive, setIsTraceModeActive, performInteractiveTrace, handleApplyTrace, handleExitTraceMode } = useInteractiveTrace(addNotification, lineageGraph);
  // Store previous trace results for when we exit trace mode (as state for reactivity)
  const [traceExitNodes, setTraceExitNodes] = useState<Set<string>>(new Set());
  const [isInTraceExitMode, setIsInTraceExitMode] = useState(false);

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
  } = useDataFiltering({
    allData,
    lineageGraph,
    schemas,
    dataModelTypes,
    isTraceModeActive,
    traceConfig,
    performInteractiveTrace,
    isInTraceExitMode,
    traceExitNodes
  });

  // --- Detect DDL Availability (memoized for performance) ---
  // DDL is now fetched on-demand via API, so always available when data is loaded
  const hasDdlData = allData.length > 0;

  // Enable SQL viewer only in Detail View
  const sqlViewerEnabled = hasDdlData && viewMode === 'detail';

  // --- UI State ---
  const [isLegendCollapsed, setIsLegendCollapsed] = useState(true);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [isInfoModalOpen, setIsInfoModalOpen] = useState(false);
  const [isControlsVisible, setIsControlsVisible] = useState(true);

  // --- SQL Viewer State ---
  const [sqlViewerOpen, setSqlViewerOpen] = useState(false);
  const [sqlViewerWidth, setSqlViewerWidth] = useState(33); // Default 33% (1/3 of screen)
  const [isResizing, setIsResizing] = useState(false);
  const [selectedNodeForSql, setSelectedNodeForSql] = useState<{
    id: string;
    name: string;
    schema: string;
    objectType: string;
  } | null>(null);

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

  // OPTIMIZATION: Create Map for O(1) lookups instead of O(n) find()
  const allDataMap = useMemo(() => {
    return new Map(allData.map(node => [node.id, node]));
  }, [allData]);

  const finalNodes = useMemo(() => {
    // Build set of level 1 neighbors (nodes directly connected to highlighted node)
    const level1Neighbors = new Set<string>();
    if (highlightedNodes.size > 0) {
      highlightedNodes.forEach(nodeId => {
        if (lineageGraph.hasNode(nodeId)) {
          const neighbors = lineageGraph.neighbors(nodeId);
          neighbors.forEach(neighborId => level1Neighbors.add(neighborId));
        }
      });
    }

    return layoutedElements.nodes.map(n => {
      // OPTIMIZATION: Use Map for O(1) lookup instead of O(n) find()
      const originalNode = allDataMap.get(n.id);

      const isHighlighted = highlightedNodes.has(n.id);

      // Dim nodes that are MORE THAN 1 level away:
      // - If there ARE highlighted nodes AND
      // - SQL viewer is NOT open (when SQL viewer is open, no dimming) AND
      // - This node is NOT highlighted AND
      // - This node is NOT a level 1 neighbor
      // OPTIMIZATION: sqlViewerOpen removed from dependencies - dimming is visual only
      const shouldBeDimmed = highlightedNodes.size > 0 &&
                             !sqlViewerOpen &&
                             !isHighlighted &&
                             !level1Neighbors.has(n.id);

      return {
        ...n,
        data: {
          ...n.data,
          isHighlighted: isHighlighted,
          isDimmed: shouldBeDimmed,
          layoutDir: layout,
          ddl_text: originalNode?.ddl_text
        }
      };
    });
  }, [layoutedElements.nodes, highlightedNodes, layout, sqlViewerOpen, allDataMap, lineageGraph]);

  // --- Effects to Synchronize State with React Flow ---
  useEffect(() => {
    setNodes(finalNodes);
    setEdges(layoutedElements.edges);
  }, [finalNodes, layoutedElements.edges, setNodes, setEdges]);

  // Track if this is the initial load to only fitView once
  const hasInitiallyFittedRef = useRef(false);

  useEffect(() => {
    if (nodes.length > 0 && !hasInitiallyFittedRef.current) {
      // Only auto-fit on initial load
      const timeoutId = setTimeout(() => {
        fitView({ padding: 0.2, duration: 500 });
        hasInitiallyFittedRef.current = true;
      }, 150);
      return () => clearTimeout(timeoutId);
    }
  }, [nodes.length, fitView]);
  
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

  // --- Effect to store trace results when in trace mode ---
  useEffect(() => {
    if (isTraceModeActive && traceConfig) {
      // Reset trace exit mode when entering trace mode
      setIsInTraceExitMode(false);
      const tracedIds = performInteractiveTrace(traceConfig);
      setTraceExitNodes(tracedIds);
    }
  }, [isTraceModeActive, traceConfig, performInteractiveTrace]);

  // --- Effect to preserve selection when exiting trace mode ---
  useEffect(() => {
    if (!isTraceModeActive && traceExitNodes.size > 0 && !isInTraceExitMode) {
      // Apply the stored trace results as highlighted nodes in detail mode
      // This shows the traced objects at the same depth level as in trace mode
      setHighlightedNodes(traceExitNodes);
      // Mark that we're in trace exit mode (showing trace results in detail view)
      setIsInTraceExitMode(true);
    }
  }, [isTraceModeActive, setHighlightedNodes, isInTraceExitMode, traceExitNodes]);

  // --- Event Handlers ---
  const handleNodeClick = useCallback((_: React.MouseEvent, node: ReactFlowNode) => {
    // In schema view, do nothing
    if (viewMode === 'schema') return;

    // Exit trace exit mode if we're clicking a node
    if (isInTraceExitMode) {
      setIsInTraceExitMode(false);
      setTraceExitNodes(new Set());
    }

    // Update SQL viewer if it's open (only in detail view, not in trace mode)
    // OPTIMIZATION: Only update if node actually changed (prevents unnecessary re-renders)
    if (sqlViewerOpen && !isTraceModeActive) {
      if (selectedNodeForSql?.id !== node.id) {
        const originalNode = allDataMap.get(node.id);
        if (originalNode) {
          setSelectedNodeForSql({
            id: originalNode.id,
            name: originalNode.name,
            schema: originalNode.schema,
            objectType: originalNode.object_type
          });
        }
      }
    }

    // Simple toggle logic: click to highlight (yellow), click again to unhighlight
    if (focusedNodeId === node.id) {
      // Clicking the same node again - unhighlight it
      setFocusedNodeId(null);
      setHighlightedNodes(new Set());
    } else {
      // Clicking a different node - highlight it in yellow
      // All other nodes remain visible (no dimming)
      setFocusedNodeId(node.id);
      setHighlightedNodes(new Set([node.id]));
    }
  }, [viewMode, isInTraceExitMode, sqlViewerOpen, isTraceModeActive, selectedNodeForSql?.id, allDataMap, focusedNodeId, setHighlightedNodes, setIsInTraceExitMode, setTraceExitNodes]);
  
  const handleDataImport = (newData: DataNode[]) => {
    const processedData = newData.map(node => ({ ...node, schema: node.schema.toUpperCase() }));
    setAllData(processedData);

    // Note: Only parquet uploads via API are persisted to backend
    // JSON imports are temporary and will be lost on page refresh
    // To persist data, upload parquet files instead

    // Reset view state for a clean slate after import
    setFocusedNodeId(null);
    setHighlightedNodes(new Set());
    setSearchTerm('');
    hasInitiallyFittedRef.current = false; // Allow fitView on new data

    addNotification('Data imported successfully! Note: JSON imports are temporary. Upload parquet files to persist data.', 'info');
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
    // Clear highlights and focused node when clicking outside
    setHighlightedNodes(new Set());
    setFocusedNodeId(null);

    // If in trace exit mode, clear the trace results and exit that mode
    if (isInTraceExitMode) {
      setTraceExitNodes(new Set());
      setIsInTraceExitMode(false);
    }
  };

  const handleResetView = () => {
    // Reset all filters and selections to default
    setSelectedSchemas(new Set(schemas));
    setSelectedTypes(new Set(dataModelTypes));
    setHighlightedNodes(new Set());
    setFocusedNodeId(null);
    setSearchTerm('');
    setHideUnrelated(false);
    setViewMode('detail');
    setTraceExitNodes(new Set());
    setIsInTraceExitMode(false);

    // Also close SQL viewer and clear selection
    setSqlViewerOpen(false);
    setSelectedNodeForSql(null);

    // Fit view after reset
    setTimeout(() => fitView({ padding: 0.2, duration: 500 }), 100);

    addNotification('View reset to default.', 'info');
  };

  // Wrapper for trace apply that adds auto-fit and highlight
  const handleApplyTraceWithFit = useCallback((config: Parameters<typeof handleApplyTrace>[0]) => {
    // Call original handler
    handleApplyTrace(config);

    // Highlight the start node
    setHighlightedNodes(new Set([config.startNodeId]));

    // Auto-fit view after a short delay (to let layout calculate)
    setTimeout(() => {
      fitView({ padding: 0.2, duration: 800 });
    }, 200);
  }, [handleApplyTrace, fitView]);

  // --- SQL Viewer Toggle Handler ---
  const handleToggleSqlViewer = () => {
    if (!sqlViewerEnabled) return;

    setSqlViewerOpen(!sqlViewerOpen);
    if (sqlViewerOpen) {
      setSelectedNodeForSql(null); // Clear selection when closing
    }
  };

  // --- SQL Viewer Resize Handler ---
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  }, []);

  useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e: MouseEvent) => {
      // Get the main container element (the flex parent)
      const mainContainer = document.querySelector('.flex-grow.rounded-b-lg.flex') as HTMLElement;
      if (!mainContainer) return;

      const containerRect = mainContainer.getBoundingClientRect();
      const containerWidth = containerRect.width;

      // Calculate distance from right edge
      const distanceFromRight = containerRect.right - e.clientX;

      // Convert to percentage
      const newWidthPercent = (distanceFromRight / containerWidth) * 100;

      // Constrain between 20% and 60%
      const constrainedWidth = Math.min(Math.max(newWidthPercent, 20), 60);
      setSqlViewerWidth(constrainedWidth);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    // Add cursor style to body during resize
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing]);

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

  // Show loading screen while data is being loaded from API
  if (isLoadingData) {
    return (
      <div className="w-screen h-screen flex items-center justify-center bg-gray-100">
        <div className="text-center max-w-md px-6">
          {/* Animated spinner */}
          <div className="inline-block animate-spin rounded-full h-20 w-20 border-b-4 border-blue-600 mb-6"></div>

          {/* Main message */}
          <h2 className="text-gray-800 text-2xl font-bold mb-3">Loading Lineage Data</h2>

          {/* Status message */}
          <p className="text-gray-600 text-base mb-4">
            Fetching latest data from server...
          </p>

          {/* Progress indicator */}
          <div className="w-full bg-gray-200 rounded-full h-2 mb-4 overflow-hidden">
            <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '70%' }}></div>
          </div>

          {/* Additional info */}
          <p className="text-gray-500 text-sm italic">
            This may take a moment for large datasets
          </p>
        </div>
      </div>
    );
  }

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
            onResetView={handleResetView}
            sqlViewerOpen={sqlViewerOpen}
            onToggleSqlViewer={handleToggleSqlViewer}
            sqlViewerEnabled={sqlViewerEnabled}
            hasDdlData={hasDdlData}
            notificationHistory={notificationHistory}
            onClearNotificationHistory={clearNotificationHistory}
          />
          <div className="relative flex-grow rounded-b-lg flex overflow-hidden">
            {/* Graph Container - Dynamic width when SQL viewer open, 100% when closed */}
            <div className={`relative ${!isResizing ? 'transition-all duration-300' : ''}`} style={{ width: sqlViewerOpen ? `${100 - sqlViewerWidth}%` : '100%' }}>
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

            {/* SQL Viewer Container - Dynamic width with resize handle */}
            {sqlViewerOpen && (
              <>
                {/* Resize Handle */}
                <div
                  onMouseDown={handleMouseDown}
                  className={`w-1 bg-gray-300 hover:bg-blue-500 cursor-col-resize transition-colors ${isResizing ? 'bg-blue-500' : ''}`}
                  style={{ userSelect: 'none' }}
                />
                {/* SQL Viewer Panel */}
                <div style={{ width: `${sqlViewerWidth}%`, height: '100%' }} className="border-l border-gray-300">
                  <SqlViewer
                    isOpen={sqlViewerOpen}
                    selectedNode={selectedNodeForSql}
                  />
                </div>
              </>
            )}
          </div>
        </div>
        <InteractiveTracePanel
          isOpen={isTraceModeActive}
          onClose={handleExitTraceMode}
          onApply={handleApplyTraceWithFit}
          availableSchemas={schemas}
          inheritedSchemaFilter={selectedSchemas}
          availableTypes={dataModelTypes}
          inheritedTypeFilter={selectedTypes}
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
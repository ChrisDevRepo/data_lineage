import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import {
  ReactFlow,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
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
import { NotificationContainer, NotificationHistory } from './components/NotificationSystem';
import { SqlViewer } from './components/SqlViewer';
import { DetailSearchModal } from './components/DetailSearchModal';
import { NodeContextMenu } from './components/NodeContextMenu';
import { InlineTraceControls } from './components/InlineTraceControls';
import { useGraphology } from './hooks/useGraphology';
import { useNotifications } from './hooks/useNotifications';
import { useInteractiveTrace } from './hooks/useInteractiveTrace';
import { useDataFiltering } from './hooks/useDataFiltering';
import { getDagreLayoutedElements } from './utils/layout';
import { generateSampleData } from './utils/data';
import { DataNode } from './types';
import { CONSTANTS } from './constants';
import { INTERACTION_CONSTANTS } from './interaction-constants';
import { API_BASE_URL } from './config';

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
  const [closeDropdownsTrigger, setCloseDropdownsTrigger] = useState(0);

  // Load data from API on mount (async to avoid blocking UI)
  useEffect(() => {
    const loadLatestData = async () => {
      const startTime = Date.now();

      try {
        const fetchStart = Date.now();
        const response = await fetch(`${API_BASE_URL}/api/latest-data`);
        console.log(`[Performance] API fetch took ${Date.now() - fetchStart}ms`);

        if (!response.ok) {
          throw new Error(`API returned ${response.status}`);
        }

        const parseStart = Date.now();
        const data = await response.json();
        console.log(`[Performance] JSON parse took ${Date.now() - parseStart}ms, data size: ${data.length} objects`);
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
        const elapsed = Date.now() - startTime;
        console.log(`[Performance] Total data load time: ${elapsed}ms`);
        setIsLoadingData(false);
      }
    };

    loadLatestData();
  }, []);
  const [layout, setLayout] = useState<'LR' | 'TB'>('LR');
  const [focusedNodeId, setFocusedNodeId] = useState<string | null>(null);
  const [excludeTerm, setExcludeTerm] = useState('');
  const [activeExcludeTerms, setActiveExcludeTerms] = useState<string[]>([]);

  // --- Custom Hooks for Logic Encapsulation ---
  const { addNotification, activeToasts, removeActiveToast, notificationHistory, clearNotificationHistory } = useNotifications();
  const { lineageGraph, schemas, schemaColorMap, dataModelTypes } = useGraphology(allData);
  const { traceConfig, isTraceModeActive, setIsTraceModeActive, performInteractiveTrace, handleApplyTrace, handleExitTraceMode } = useInteractiveTrace(addNotification, lineageGraph);
  // Store previous trace results for when we exit trace mode (as state for reactivity)
  const [traceExitNodes, setTraceExitNodes] = useState<Set<string>>(new Set());
  const [isInTraceExitMode, setIsInTraceExitMode] = useState(false);
  const [isTraceLocked, setIsTraceLocked] = useState(false);

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
    activeExcludeTerms,
    isTraceModeActive,
    traceConfig,
    performInteractiveTrace,
    isInTraceExitMode,
    traceExitNodes
  });

  // --- Callback to apply exclude terms ---
  const applyExcludeTerms = useCallback(() => {
    if (excludeTerm.trim()) {
      // Split by comma, trim whitespace, filter empty strings, convert to lowercase
      const terms = excludeTerm
        .split(',')
        .map(term => term.trim().toLowerCase())
        .filter(term => term.length > 0);

      setActiveExcludeTerms(terms);
      console.log('[App] Applied exclude terms:', terms);

      // Show notification
      addNotification(`Excluding ${terms.length} term(s): ${terms.join(', ')}`, 'info');
    }
  }, [excludeTerm, addNotification]);

  // --- localStorage Persistence ---
  const hasInitializedPreferences = useRef(false);

  // Load saved layout preference (schemas/types/hideUnrelated are loaded in useDataFiltering)
  useEffect(() => {
    try {
      const saved = localStorage.getItem('lineage_filter_preferences');
      if (saved) {
        const { layout: savedLayout } = JSON.parse(saved);
        if (savedLayout === 'LR' || savedLayout === 'TB') {
          setLayout(savedLayout);
        }
        console.log('[localStorage] Loaded layout preference:', savedLayout);
      }
    } catch (error) {
      console.error('[localStorage] Failed to load layout preference:', error);
    }
  }, []); // Run once on mount

  // Mark preferences as initialized after schemas are loaded
  useEffect(() => {
    if (schemas.length > 0 && selectedSchemas.size > 0 && !hasInitializedPreferences.current) {
      hasInitializedPreferences.current = true;
      console.log('[localStorage] Preferences initialized, will now save on changes');
    }
  }, [schemas.length, selectedSchemas.size]);

  // Save preferences to localStorage whenever they change (but only after initialization)
  useEffect(() => {
    // Don't save until preferences have been loaded/initialized
    if (!hasInitializedPreferences.current) {
      return;
    }

    try {
      const preferences = {
        schemas: Array.from(selectedSchemas),
        types: Array.from(selectedTypes),
        hideUnrelated,
        layout
      };
      localStorage.setItem('lineage_filter_preferences', JSON.stringify(preferences));
      console.log('[localStorage] Saved preferences:', preferences);
    } catch (error) {
      console.error('[localStorage] Failed to save preferences:', error);
    }
  }, [selectedSchemas, selectedTypes, hideUnrelated, layout]);

  // --- Detect DDL Availability (memoized for performance) ---
  // DDL is now fetched on-demand via API, so always available when data is loaded
  const hasDdlData = allData.length > 0;

  // Enable SQL viewer when DDL data is available
  const sqlViewerEnabled = hasDdlData;

  // --- UI State ---
  const [isLegendCollapsed, setIsLegendCollapsed] = useState(true);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [isInfoModalOpen, setIsInfoModalOpen] = useState(false);
  const [isDetailSearchOpen, setIsDetailSearchOpen] = useState(false);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; nodeId: string; nodeName: string } | null>(null);

  // --- SQL Viewer State ---
  const [sqlViewerOpen, setSqlViewerOpen] = useState(false);
  const [sqlViewerWidth, setSqlViewerWidth] = useState(INTERACTION_CONSTANTS.SQL_VIEWER_WIDTH_DEFAULT_PCT);
  const [isResizing, setIsResizing] = useState(false);
  const [selectedNodeForSql, setSelectedNodeForSql] = useState<{
    id: string;
    name: string;
    schema: string;
    objectType: string;
    ddl_text?: string | null; // Optional: only present in JSON uploads
  } | null>(null);

  // --- Memos for Derived State and Layouting ---
  const layoutedElements = useMemo(() => {
    return getDagreLayoutedElements({
      data: finalVisibleData,
      layout,
      schemaColorMap,
      lineageGraph,
      isTraceModeActive,
    });
  }, [finalVisibleData, layout, schemaColorMap, lineageGraph, isTraceModeActive]);

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
      // - This node is NOT highlighted AND
      // - This node is NOT a level 1 neighbor
      const shouldBeDimmed = highlightedNodes.size > 0 &&
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
  }, [layoutedElements.nodes, highlightedNodes, layout, allDataMap, lineageGraph]);

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
        fitView({
          padding: INTERACTION_CONSTANTS.FIT_VIEW_PADDING,
          duration: INTERACTION_CONSTANTS.FIT_VIEW_DURATION_MS
        });
        hasInitiallyFittedRef.current = true;
      }, INTERACTION_CONSTANTS.INITIAL_FIT_VIEW_DELAY_MS);
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
      // Automatically lock the trace results
      setIsTraceLocked(true);
    }
  }, [isTraceModeActive, setHighlightedNodes, isInTraceExitMode, traceExitNodes]);

  // --- Event Handlers ---
  const handleNodeContextMenu = useCallback((event: React.MouseEvent, node: ReactFlowNode) => {
    event.preventDefault();
    const originalNode = allDataMap.get(node.id);
    if (originalNode) {
      setContextMenu({
        x: event.clientX,
        y: event.clientY,
        nodeId: node.id,
        nodeName: originalNode.name
      });
    }
  }, [allDataMap]);

  const handleNodeClick = useCallback((_: React.MouseEvent, node: ReactFlowNode) => {
    // If locked, don't exit trace mode - just allow node interactions
    if (isTraceLocked) {
      // Allow highlighting within the locked subset, but don't clear the trace
      // Just update the focused node for SQL viewer, etc.
    } else if (isInTraceExitMode) {
      // Exit trace exit mode if we're clicking a node and not locked
      setIsInTraceExitMode(false);
      setTraceExitNodes(new Set());
    }

    // Update SQL viewer if it's open (only in detail view, not in trace mode)
    // OPTIMIZATION: Only update if node actually changed (prevents unnecessary re-renders)
    if (sqlViewerOpen && !isTraceModeActive) {
      if (selectedNodeForSql?.id !== node.id) {
        const originalNode = allDataMap.get(node.id);
        if (originalNode) {
          const nodeForSql: any = {
            id: originalNode.id,
            name: originalNode.name,
            schema: originalNode.schema,
            objectType: originalNode.object_type
          };

          // Only add ddl_text if it exists in source data (JSON mode)
          if ('ddl_text' in originalNode) {
            nodeForSql.ddl_text = originalNode.ddl_text;
          }

          setSelectedNodeForSql(nodeForSql);
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
  }, [isInTraceExitMode, isTraceLocked, sqlViewerOpen, isTraceModeActive, selectedNodeForSql?.id, allDataMap, focusedNodeId, setHighlightedNodes, setIsInTraceExitMode, setTraceExitNodes]);
  
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
    // Don't auto-close modal - let user close it after viewing summary
    // setIsImportModalOpen(false);
  };
  
  const executeSearch = (query: string) => {
    try {
      if (isTraceModeActive) return;
      setFocusedNodeId(null);
      if (!query) {
        setHighlightedNodes(new Set());
        fitView({ duration: 500 });
        return;
      }

      // Safety check: ensure query is a valid string
      if (typeof query !== 'string') {
        console.error('[Search] Invalid query type:', typeof query);
        addNotification('Invalid search query. Please try again.', 'error');
        return;
      }

      const foundNodeData = allData.find(d => d.name && d.name.toLowerCase() === query.toLowerCase());
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
    } catch (error) {
      console.error('[Search] Error during search:', error);
      addNotification('An error occurred while searching. Please try again.', 'error');
    }
  };

  const handlePaneClick = () => {
    // Close any open dropdowns in toolbar
    setCloseDropdownsTrigger(prev => prev + 1);

    // Close context menu
    setContextMenu(null);

    // If locked, don't clear anything - just return
    if (isTraceLocked) {
      return;
    }

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
    setIsTraceModeActive(false); // Exit trace mode if active
    setTraceExitNodes(new Set());
    setIsInTraceExitMode(false);
    setIsTraceLocked(false);

    // Also close SQL viewer and clear selection
    setSqlViewerOpen(false);
    setSelectedNodeForSql(null);

    // Fit view after reset
    setTimeout(() => fitView({ padding: 0.2, duration: 500 }), 100);

    addNotification('View reset to default.', 'info');
  };

  const handleCloseDetailSearch = useCallback((nodeId: string | null) => {
    setIsDetailSearchOpen(false);

    if (nodeId) {
      // Highlight the selected node
      setHighlightedNodes(new Set([nodeId]));

      // Zoom to the node with animation
      setTimeout(() => {
        const node = getNodes().find(n => n.id === nodeId);
        if (node) {
          setCenter(node.position.x + 100, node.position.y, {
            duration: 800,
            zoom: 1.5
          });
        }
      }, 100);
    }
  }, [getNodes, setCenter, setHighlightedNodes]);

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

  // --- Inline Trace Handlers ---
  const handleStartTracing = useCallback((nodeId: string) => {
    // Set up initial trace config with default values
    const initialConfig = {
      startNodeId: nodeId,
      endNodeId: null,
      upstreamLevels: 3,
      downstreamLevels: 3,
      includedSchemas: selectedSchemas,
      includedTypes: selectedTypes,
      exclusionPatterns: activeExcludeTerms
    };
    handleApplyTrace(initialConfig);
    setIsTraceModeActive(true);
  }, [handleApplyTrace, selectedSchemas, selectedTypes, activeExcludeTerms]);

  const handleInlineTraceApply = useCallback((config: { startNodeId: string; upstreamLevels: number; downstreamLevels: number }) => {
    // Build full config using existing filters
    const fullConfig = {
      startNodeId: config.startNodeId,
      endNodeId: null,
      upstreamLevels: config.upstreamLevels,
      downstreamLevels: config.downstreamLevels,
      includedSchemas: selectedSchemas,
      includedTypes: selectedTypes,
      exclusionPatterns: activeExcludeTerms
    };
    handleApplyTrace(fullConfig);

    // Highlight the start node
    setHighlightedNodes(new Set([config.startNodeId]));

    // Auto-fit view
    setTimeout(() => {
      fitView({ padding: 0.2, duration: 800 });
    }, 200);
  }, [handleApplyTrace, selectedSchemas, selectedTypes, activeExcludeTerms, fitView, setHighlightedNodes]);

  const handleEndTracing = useCallback(() => {
    handleExitTraceMode();
  }, [handleExitTraceMode]);

  // --- Lock Toggle Handler ---
  const handleToggleLock = () => {
    setIsTraceLocked(prev => {
      const newState = !prev;
      if (newState) {
        addNotification('Trace locked - node subset preserved', 'info');
      } else {
        // When unlocking, clear the trace
        setIsInTraceExitMode(false);
        setTraceExitNodes(new Set());
        addNotification('Trace unlocked - full view restored', 'info');
      }
      return newState;
    });
  };

  // --- SQL Viewer Toggle Handler ---
  const handleToggleSqlViewer = () => {
    if (!sqlViewerEnabled) return;

    setSqlViewerOpen(!sqlViewerOpen);
    if (sqlViewerOpen) {
      setSelectedNodeForSql(null); // Clear selection when closing
    }
  };

  // --- View Transition Handlers (Detail Search <-> SQL Viewer) ---
  const handleSwitchToSqlViewer = useCallback((nodeId: string) => {
    // Close detail search
    setIsDetailSearchOpen(false);

    // Find the node data
    const originalNode = allDataMap.get(nodeId);
    if (originalNode) {
      const nodeForSql: any = {
        id: originalNode.id,
        name: originalNode.name,
        schema: originalNode.schema,
        objectType: originalNode.object_type
      };

      // Only add ddl_text if it exists in source data (JSON mode)
      if ('ddl_text' in originalNode) {
        nodeForSql.ddl_text = originalNode.ddl_text;
      }

      setSelectedNodeForSql(nodeForSql);
      setSqlViewerOpen(true);

      // Highlight and zoom to the node in the graph
      setHighlightedNodes(new Set([nodeId]));
      setTimeout(() => {
        const node = getNodes().find(n => n.id === nodeId);
        if (node) {
          setCenter(node.position.x + 100, node.position.y, {
            duration: 800,
            zoom: 1.2
          });
        }
      }, 100);
    }
  }, [allDataMap, getNodes, setCenter, setHighlightedNodes]);

  const handleSwitchToDetailSearch = useCallback(() => {
    if (selectedNodeForSql) {
      // Store current node for detail search
      const nodeId = selectedNodeForSql.id;

      // Close SQL viewer
      setSqlViewerOpen(false);

      // Open detail search (without search query, just showing the node)
      setIsDetailSearchOpen(true);

      // The detail search modal will need to be enhanced to accept an initial node
      // For now, we'll just open it and let the user see their last search
    }
  }, [selectedNodeForSql]);

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

  const handleExportSVG = useCallback(async () => {
    const nodesToExport = getNodes();
    const edgesToExport = getEdges();

    if (nodesToExport.length === 0) {
        addNotification('Nothing to export.', 'error');
        return;
    }

    // Convert logo to base64
    let logoBase64 = '';
    try {
      const response = await fetch('/logo.png');
      const blob = await response.blob();
      logoBase64 = await new Promise((resolve) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result as string);
        reader.readAsDataURL(blob);
      });
    } catch (error) {
      console.error('Failed to load logo:', error);
    }

    const PADDING = 50;
    const HEADER_HEIGHT = 100; // Space for logo and title at top
    const LEGEND_WIDTH = 280; // Space for legend on left
    const LEGEND_PADDING = 20;

    const minX = Math.min(...nodesToExport.map(n => n.position.x));
    const minY = Math.min(...nodesToExport.map(n => n.position.y));
    const maxX = Math.max(...nodesToExport.map(n => n.position.x + (n.width || 0)));
    const maxY = Math.max(...nodesToExport.map(n => n.position.y + (n.height || 0)));
    const graphWidth = maxX - minX + PADDING * 2;
    const graphHeight = maxY - minY + PADDING * 2;
    const width = graphWidth + LEGEND_WIDTH + LEGEND_PADDING;
    const height = graphHeight + HEADER_HEIGHT;
    const offsetX = -minX + PADDING + LEGEND_WIDTH + LEGEND_PADDING;
    const offsetY = -minY + PADDING + HEADER_HEIGHT;

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

    // Generate legend elements - calculate proper height for all schemas
    const legendItems = schemas.map((schema, index) => {
      const color = schemaColorMap.get(schema) || '#7f7f7f';
      const y = HEADER_HEIGHT + 60 + (index * 28);
      return `
        <g transform="translate(20, ${y})">
          <rect width="16" height="16" rx="2" fill="${color}" stroke="rgba(0,0,0,0.2)" stroke-width="1"/>
          <text x="24" y="8" dominant-baseline="middle" font-family="sans-serif" font-size="13px" fill="#374151">${schema}</text>
        </g>
      `;
    }).join('');

    // Calculate legend height to fit all schemas (28px per schema + 60px for header + 20px padding)
    const legendHeight = Math.min(schemas.length * 28 + 80, height - HEADER_HEIGHT - 40);

    const svgString = `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="${width}" height="${height}">
      <defs>
        <marker id="arrow" viewBox="0 -5 10 10" refX="8" refY="0" markerWidth="6" markerHeight="6" orient="auto">
          <path d="M0,-5L10,0L0,5" fill="#9ca3af"></path>
        </marker>
      </defs>

      <!-- Background -->
      <rect width="${width}" height="${height}" fill="#ffffff"/>

      <!-- Header with Logo -->
      <g id="header">
        ${logoBase64 ? `<image href="${logoBase64}" x="20" y="20" width="200" height="60" preserveAspectRatio="xMinYMin meet"/>` : ''}
        <!-- Colorful accent bar -->
        <defs>
          <linearGradient id="accentGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" style="stop-color:#3b82f6;stop-opacity:1" />
            <stop offset="50%" style="stop-color:#4ec9b0;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#fb923c;stop-opacity:1" />
          </linearGradient>
        </defs>
        <rect x="0" y="${HEADER_HEIGHT - 10}" width="${width}" height="4" fill="url(#accentGradient)"/>
      </g>

      <!-- Schema Legend -->
      <g id="legend">
        <text x="20" y="${HEADER_HEIGHT + 40}" font-family="sans-serif" font-size="16px" font-weight="bold" fill="#1f2937">Schemas</text>
        ${legendItems}
      </g>

      <!-- Graph Content -->
      <g id="graph">
        ${edgePaths}
        ${nodeElements}
      </g>
    </svg>`;
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
  }, [getNodes, getEdges, addNotification, schemaColorMap, layout, schemas]);

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
      <header className="flex-shrink-0 z-20">
        <div className="flex items-center justify-between px-4 py-2 bg-white shadow-sm">
          <img src="/logo.png" alt="Data Lineage Visualizer" className="h-10" />
        </div>
        {/* Colorful accent bar matching logo theme */}
        <div className="h-1 bg-gradient-to-r from-blue-500 via-teal-400 to-orange-400"></div>
      </header>
      <main className="flex-grow p-4 relative bg-gray-100 overflow-hidden">
        <NotificationContainer activeToasts={activeToasts} onDismissToast={removeActiveToast} />
        <div className={`w-full h-full bg-white rounded-lg shadow-md flex flex-col text-gray-800 transition-all duration-300 ${isTraceModeActive ? 'pr-80' : ''}`}>
          <Toolbar
            searchTerm={searchTerm}
            setSearchTerm={setSearchTerm}
            executeSearch={executeSearch}
            excludeTerm={excludeTerm}
            setExcludeTerm={setExcludeTerm}
            applyExcludeTerms={applyExcludeTerms}
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
            onOpenImport={() => setIsImportModalOpen(true)}
            onOpenInfo={() => setIsInfoModalOpen(true)}
            onExportSVG={handleExportSVG}
            onResetView={handleResetView}
            sqlViewerOpen={sqlViewerOpen}
            onToggleSqlViewer={handleToggleSqlViewer}
            sqlViewerEnabled={sqlViewerEnabled}
            hasDdlData={hasDdlData}
            onOpenDetailSearch={() => setIsDetailSearchOpen(true)}
            notificationHistory={notificationHistory}
            onClearNotificationHistory={clearNotificationHistory}
            isTraceLocked={isTraceLocked}
            isInTraceExitMode={isInTraceExitMode}
            onToggleLock={handleToggleLock}
            closeDropdownsTrigger={closeDropdownsTrigger}
          />
          {isTraceModeActive && traceConfig && (
            <InlineTraceControls
              startNodeId={traceConfig.startNodeId}
              startNodeName={allData.find(n => n.id === traceConfig.startNodeId)?.name || ''}
              allData={allData}
              onApply={handleInlineTraceApply}
              onEnd={handleEndTracing}
            />
          )}
          <div className="relative flex-grow rounded-b-lg flex overflow-hidden">
            {/* Graph Container - Dynamic width when SQL viewer open, 100% when closed */}
            <div className={`relative ${!isResizing ? 'transition-all duration-300' : ''}`} style={{ width: sqlViewerOpen ? `${100 - sqlViewerWidth}%` : '100%' }}>
              <ReactFlow
                nodes={nodes} edges={edges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
                nodeTypes={nodeTypes}
                onPaneClick={handlePaneClick}
                onNodeClick={handleNodeClick}
                onNodeContextMenu={handleNodeContextMenu}
                fitView
                minZoom={0.1}
                proOptions={{ hideAttribution: true }}
              >
                <Controls />
                <Background color={'#a1a1aa'} gap={16} />
                <Legend
                  isCollapsed={isLegendCollapsed}
                  onToggle={() => setIsLegendCollapsed(p => !p)}
                  schemas={schemas}
                  schemaColorMap={schemaColorMap}
                  selectedSchemas={selectedSchemas}
                />
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
                    onSwitchToDetailSearch={handleSwitchToDetailSearch}
                  />
                </div>
              </>
            )}
          </div>
        </div>
      </main>
      <ImportDataModal
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        onImport={handleDataImport}
        currentData={allData}
        defaultSampleData={sampleData}
        addNotification={addNotification} 
      />
      <InfoModal
        isOpen={isInfoModalOpen}
        onClose={() => setIsInfoModalOpen(false)}
      />
      <DetailSearchModal
        isOpen={isDetailSearchOpen}
        allData={allData}
        onClose={handleCloseDetailSearch}
        onSwitchToSqlViewer={handleSwitchToSqlViewer}
      />
      {contextMenu && (
        <NodeContextMenu
          x={contextMenu.x}
          y={contextMenu.y}
          nodeId={contextMenu.nodeId}
          nodeName={contextMenu.nodeName}
          onStartTracing={() => handleStartTracing(contextMenu.nodeId)}
          onShowSql={sqlViewerEnabled ? () => {
            const originalNode = allDataMap.get(contextMenu.nodeId);
            if (originalNode) {
              const nodeForSql: any = {
                id: originalNode.id,
                name: originalNode.name,
                schema: originalNode.schema,
                objectType: originalNode.object_type
              };
              if ('ddl_text' in originalNode) {
                nodeForSql.ddl_text = originalNode.ddl_text;
              }
              setSelectedNodeForSql(nodeForSql);
              setSqlViewerOpen(true);
            }
          } : undefined}
          sqlViewerEnabled={sqlViewerEnabled}
          onClose={() => setContextMenu(null)}
        />
      )}
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
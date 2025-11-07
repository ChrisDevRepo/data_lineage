import React, { useState, useEffect, useMemo, useRef } from 'react';
import Editor from '@monaco-editor/react';
import { DataNode } from '../types';
import { tokens } from '../design-tokens';
import { Checkbox } from './ui/Checkbox';
import { API_BASE_URL } from '../config';
import { useClickOutside } from '../hooks/useClickOutside';

// Debounce utility
function debounce<T extends (...args: any[]) => any>(func: T, wait: number): T {
  let timeout: NodeJS.Timeout | null = null;
  return ((...args: Parameters<T>) => {
    if (timeout) clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  }) as T;
}

interface DetailSearchModalProps {
  isOpen: boolean;
  allData: DataNode[];
  onClose: (selectedNodeId: string | null) => void;
  onSwitchToSqlViewer?: (nodeId: string) => void;
  initialNodeId?: string | null; // Pre-load this node's DDL when opening
}

interface SearchResult {
  id: string;
  name: string;
  type: string;
  schema: string;
  score: number;
  snippet: string;
}

interface FilterOptions {
  schemas: string[];
  objectTypes: string[];
}

export const DetailSearchModal: React.FC<DetailSearchModalProps> = ({ isOpen, allData, onClose, onSwitchToSqlViewer, initialNodeId = null }) => {
  // State
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [selectedResult, setSelectedResult] = useState<SearchResult | null>(null);
  const [isSearching, setIsSearching] = useState(false);
  const [ddlText, setDdlText] = useState<string | null>(null);
  const [isLoadingDdl, setIsLoadingDdl] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Resize state - default to 25% for top panel
  const [topPanelHeight, setTopPanelHeight] = useState(25);
  const [isResizing, setIsResizing] = useState(false);

  // Filter state - Changed to Sets for multi-select
  const [selectedSchemas, setSelectedSchemas] = useState<Set<string>>(new Set());
  const [selectedObjectTypes, setSelectedObjectTypes] = useState<Set<string>>(new Set());
  const [showSearchHelp, setShowSearchHelp] = useState(false);
  const [showSchemaFilter, setShowSchemaFilter] = useState(false);
  const [showTypeFilter, setShowTypeFilter] = useState(false);

  const editorRef = useRef<any>(null);
  const resizeRef = useRef<{ startY: number; startHeight: number } | null>(null);
  const schemaFilterRef = useRef<HTMLDivElement>(null);
  const typeFilterRef = useRef<HTMLDivElement>(null);

  // Auto-close dropdowns when clicking outside
  useClickOutside(schemaFilterRef, () => setShowSchemaFilter(false));
  useClickOutside(typeFilterRef, () => setShowTypeFilter(false));

  // Extract unique schemas and object types from allData using useMemo to prevent re-renders
  const filterOptions = useMemo<FilterOptions>(() => {
    if (!allData || allData.length === 0) {
      return { schemas: [], objectTypes: [] };
    }

    const schemas = new Set<string>();
    const objectTypes = new Set<string>();

    allData.forEach(node => {
      if (node.schema) schemas.add(node.schema);
      if (node.object_type) objectTypes.add(node.object_type);
    });

    return {
      schemas: Array.from(schemas).sort(),
      objectTypes: Array.from(objectTypes).sort()
    };
  }, [allData]);

  // Handle resize mouse events
  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
    resizeRef.current = {
      startY: e.clientY,
      startHeight: topPanelHeight
    };
  };

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing || !resizeRef.current) return;

      const deltaY = e.clientY - resizeRef.current.startY;
      const viewportHeight = window.innerHeight;
      const deltaPercent = (deltaY / viewportHeight) * 100;

      let newHeight = resizeRef.current.startHeight + deltaPercent;

      // Constrain between 15% and 60%
      newHeight = Math.max(15, Math.min(60, newHeight));

      setTopPanelHeight(newHeight);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
      resizeRef.current = null;
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing]);

  // Handle ESC key to close modal
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        handleClose();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  // Debounced search function
  const debouncedSearch = useMemo(
    () => debounce(async (query: string, schemas: Set<string>, objectTypes: Set<string>) => {
      if (!query.trim()) {
        setResults([]);
        setIsSearching(false);
        return;
      }

      setIsSearching(true);
      setError(null);

      try {
        const response = await fetch(
          `${API_BASE_URL}/api/search-ddl?q=${encodeURIComponent(query)}`
        );

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: response.statusText }));
          throw new Error(errorData.detail || 'Search failed');
        }

        let data = await response.json();

        // Client-side filtering by schemas and object types (multi-select)
        if (schemas.size > 0) {
          data = data.filter((result: SearchResult) => schemas.has(result.schema));
        }
        if (objectTypes.size > 0) {
          data = data.filter((result: SearchResult) => objectTypes.has(result.type));
        }

        setResults(data);
      } catch (err) {
        console.error('[DetailSearchModal] Search failed:', err);
        setError(err instanceof Error ? err.message : 'Search failed');
        setResults([]);
      } finally {
        setIsSearching(false);
      }
    }, 300),
    []
  );

  // Trigger search when query or filters change
  useEffect(() => {
    if (searchQuery.trim()) {
      setIsSearching(true);
      debouncedSearch(searchQuery, selectedSchemas, selectedObjectTypes);
    } else {
      setResults([]);
      setIsSearching(false);
    }
  }, [searchQuery, selectedSchemas, selectedObjectTypes, debouncedSearch]);

  // Handle result click - fetch full DDL
  const handleResultClick = async (result: SearchResult) => {
    setSelectedResult(result);
    setIsLoadingDdl(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/ddl/${result.id}`);

      if (!response.ok) {
        throw new Error('Failed to load DDL');
      }

      const data = await response.json();
      setDdlText(data.ddl_text);
    } catch (err) {
      console.error('[DetailSearchModal] Failed to load DDL:', err);
      setError('Failed to load DDL');
      setDdlText(null);
    } finally {
      setIsLoadingDdl(false);
    }
  };

  // Handle close
  const handleClose = () => {
    // Pass last selected object ID to parent for zoom
    onClose(selectedResult?.id || null);

    // Reset state
    setSearchQuery('');
    setResults([]);
    setSelectedResult(null);
    setDdlText(null);
    setError(null);
    setIsSearching(false);
    setIsLoadingDdl(false);
    setSelectedSchemas(new Set());
    setSelectedObjectTypes(new Set());
    setShowSearchHelp(false);
    setShowSchemaFilter(false);
    setShowTypeFilter(false);
  };

  // Handle editor mount
  const handleEditorDidMount = (editor: any, monaco: any) => {
    editorRef.current = editor;

    // Configure find widget
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyF, () => {
      editor.getAction('actions.find').run();
    });
  };

  // Trigger Monaco search when DDL loads
  useEffect(() => {
    if (editorRef.current && ddlText && searchQuery.trim() && !isLoadingDdl) {
      // Small delay to ensure editor is fully rendered
      const timer = setTimeout(() => {
        try {
          const editor = editorRef.current;

          // Clean search query for Monaco (remove boolean operators, quotes, wildcards)
          const cleanQuery = searchQuery
            .replace(/\b(AND|OR|NOT)\b/gi, ' ')
            .replace(/["'*]/g, '')
            .trim()
            .split(/\s+/)
            .filter(term => term.length > 2)
            .join(' ');

          if (cleanQuery) {
            // Trigger the find action
            editor.trigger('search', 'actions.find', null);

            // Set the search string in the find widget
            const findController = editor.getContribution('editor.contrib.findController');
            if (findController) {
              findController.getState().change({ searchString: cleanQuery }, false);
              // Find and select first match
              editor.trigger('search', 'editor.action.nextMatchFindAction', null);
            }
          }
        } catch (error) {
          console.error('[DetailSearchModal] Error triggering Monaco search:', error);
        }
      }, 100);

      return () => clearTimeout(timer);
    }
  }, [ddlText, searchQuery, isLoadingDdl]);

  // Auto-load DDL when initialNodeId is provided (switching from SQL view)
  useEffect(() => {
    if (isOpen && initialNodeId && allData.length > 0) {
      // Find the node in allData
      const node = allData.find(n => n.id === initialNodeId);
      if (node) {
        // Create a search result object for this node
        const result: SearchResult = {
          id: node.id,
          name: node.name,
          type: node.object_type,
          schema: node.schema,
          score: 1.0,
          snippet: ''
        };

        // Load its DDL
        handleResultClick(result);
      }
    }
  }, [isOpen, initialNodeId, allData]);

  // Highlight matching text in search results
  const highlightText = (text: string, query: string) => {
    if (!query.trim()) {
      return text;
    }

    // Check if the text already contains <mark> tags from backend snippet
    if (text.includes('<mark>') && text.includes('</mark>')) {
      // Parse the HTML and render with proper highlighting
      const parts: JSX.Element[] = [];
      let lastIndex = 0;
      const markRegex = /<mark>(.*?)<\/mark>/g;
      let match;
      let key = 0;

      while ((match = markRegex.exec(text)) !== null) {
        // Add text before the match
        if (match.index > lastIndex) {
          parts.push(<span key={key++}>{text.substring(lastIndex, match.index)}</span>);
        }
        // Add the highlighted match
        parts.push(
          <mark key={key++} className="bg-yellow-200 text-gray-900 font-semibold px-0.5 rounded">
            {match[1]}
          </mark>
        );
        lastIndex = match.index + match[0].length;
      }

      // Add remaining text
      if (lastIndex < text.length) {
        parts.push(<span key={key++}>{text.substring(lastIndex)}</span>);
      }

      return <>{parts}</>;
    }

    // Fallback: client-side highlighting for object names
    // Remove boolean operators and quotes for highlighting
    const cleanQuery = query.replace(/\b(AND|OR|NOT)\b/gi, '')
      .replace(/["']/g, '')
      .trim();

    if (!cleanQuery) return text;

    // Split by whitespace, asterisks, AND underscores/numbers to get word parts
    // This allows "DimCustomers_0" to highlight "DimCustomers"
    const terms = cleanQuery.split(/[\s*_\d]+/).filter(term => term.length > 2);

    if (terms.length === 0) return text;

    // Escape special regex characters for each term
    const escapedTerms = terms.map(term => term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));

    // Create regex pattern that matches any of the terms (case-insensitive)
    const pattern = new RegExp(`(${escapedTerms.join('|')})`, 'gi');

    // Split text by matches while preserving the matched terms
    const parts = text.split(pattern);

    return (
      <>
        {parts.map((part, index) => {
          if (!part) return null; // Skip empty parts

          // Check if this part matches any search term (case-insensitive)
          const isMatch = terms.some(term => part.toLowerCase() === term.toLowerCase());

          return isMatch ? (
            <mark key={index} className="bg-yellow-200 text-gray-900 font-semibold px-0.5 rounded">
              {part}
            </mark>
          ) : (
            <span key={index}>{part}</span>
          );
        })}
      </>
    );
  };

  // Get icon by object type
  const getObjectIcon = (type: string) => {
    const iconClass = "w-4 h-4";
    switch (type) {
      case 'Stored Procedure':
        return <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" /></svg>;
      case 'View':
        return <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></svg>;
      case 'Table':
        return <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" /></svg>;
      case 'Function':
        return <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" /></svg>;
      default:
        return <svg className={iconClass} fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>;
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Full-screen backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-[9998]"
        onClick={handleClose}
      />

      {/* Modal content - Full screen overlay */}
      <div
        className="fixed inset-0 bg-white z-[9999] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header Row 1: Logo and Icon Bar (reusing main toolbar style) */}
        <div>
          <div className="flex items-center justify-between px-4 py-2 bg-white shadow-sm">
            <img src="/logo.png" alt="Data Lineage Visualizer" className="h-10" />

            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600 font-medium">Detail Search Mode</span>
              <button
                onClick={handleClose}
                className="w-9 h-9 flex items-center justify-center hover:bg-gray-100 text-gray-600 rounded transition-colors"
                title="Close (ESC)"
              >
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>
          {/* Colorful accent bar matching logo theme */}
          <div className="h-1 bg-gradient-to-r from-blue-500 via-teal-400 to-orange-400"></div>
        </div>

        {/* Header Row 2: Search Controls */}
        <div className="flex items-center gap-3 px-4 py-2.5 bg-white border-b border-gray-200">
          {/* Search input */}
          <div className="relative flex-1 max-w-2xl">
            <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              placeholder="Search DDL definitions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              autoFocus
              className="w-full h-9 pl-9 pr-3 bg-white border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-600 transition-colors"
            />
          </div>

          {/* Schema filter - Multi-select */}
          <div className="relative" ref={schemaFilterRef}>
            <button
              onClick={() => {
                setShowSchemaFilter(!showSchemaFilter);
                if (!showSchemaFilter) setShowTypeFilter(false); // Close other dropdown
              }}
              className={`h-9 px-3 bg-white border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-600 cursor-pointer whitespace-nowrap ${selectedSchemas.size > 0 ? 'bg-blue-50 border-blue-400' : ''}`}
              title={`Schemas (${selectedSchemas.size > 0 ? selectedSchemas.size : 'All'})`}
            >
              Schemas ({selectedSchemas.size > 0 ? selectedSchemas.size : filterOptions.schemas.length})
            </button>
            {showSchemaFilter && (
              <div className="absolute top-full mt-2 w-64 bg-white border border-gray-300 rounded-md shadow-lg z-30 max-h-60 overflow-hidden flex flex-col">
                <div className="p-2 border-b border-gray-200 bg-gray-50">
                  <button
                    onClick={() => {
                      if (selectedSchemas.size === filterOptions.schemas.length) {
                        setSelectedSchemas(new Set());
                      } else {
                        setSelectedSchemas(new Set(filterOptions.schemas));
                      }
                    }}
                    className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                  >
                    {selectedSchemas.size === filterOptions.schemas.length ? 'Deselect All' : 'Select All'}
                  </button>
                </div>
                <div className="p-3 space-y-2 overflow-y-auto">
                  {filterOptions.schemas.map(schema => (
                    <Checkbox
                      key={schema}
                      checked={selectedSchemas.has(schema)}
                      onChange={() => {
                        const newSet = new Set(selectedSchemas);
                        if (newSet.has(schema)) newSet.delete(schema);
                        else newSet.add(schema);
                        setSelectedSchemas(newSet);
                      }}
                      label={schema}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Object type filter - Multi-select */}
          <div className="relative" ref={typeFilterRef}>
            <button
              onClick={() => {
                setShowTypeFilter(!showTypeFilter);
                if (!showTypeFilter) setShowSchemaFilter(false); // Close other dropdown
              }}
              className={`h-9 px-3 bg-white border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-primary-600 cursor-pointer whitespace-nowrap ${selectedObjectTypes.size > 0 ? 'bg-blue-50 border-blue-400' : ''}`}
              title={`Types (${selectedObjectTypes.size > 0 ? selectedObjectTypes.size : 'All'})`}
            >
              Types ({selectedObjectTypes.size > 0 ? selectedObjectTypes.size : filterOptions.objectTypes.length})
            </button>
            {showTypeFilter && (
              <div className="absolute top-full mt-2 w-64 bg-white border border-gray-300 rounded-md shadow-lg z-30 max-h-60 overflow-hidden flex flex-col">
                <div className="p-2 border-b border-gray-200 bg-gray-50">
                  <button
                    onClick={() => {
                      if (selectedObjectTypes.size === filterOptions.objectTypes.length) {
                        setSelectedObjectTypes(new Set());
                      } else {
                        setSelectedObjectTypes(new Set(filterOptions.objectTypes));
                      }
                    }}
                    className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                  >
                    {selectedObjectTypes.size === filterOptions.objectTypes.length ? 'Deselect All' : 'Select All'}
                  </button>
                </div>
                <div className="p-3 space-y-2 overflow-y-auto">
                  {filterOptions.objectTypes.map(type => (
                    <Checkbox
                      key={type}
                      checked={selectedObjectTypes.has(type)}
                      onChange={() => {
                        const newSet = new Set(selectedObjectTypes);
                        if (newSet.has(type)) newSet.delete(type);
                        else newSet.add(type);
                        setSelectedObjectTypes(newSet);
                      }}
                      label={type}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Search status indicators */}
          <div className="flex items-center gap-2">
            {isSearching && (
              <div className="w-5 h-5 border-2 border-gray-300 border-t-primary-600 rounded-full animate-spin" />
            )}

            {results.length > 0 && !isSearching && (
              <span className="text-sm text-gray-600 whitespace-nowrap">
                {results.length} {results.length === 1 ? 'match' : 'matches'}
              </span>
            )}

            {/* Search help toggle */}
            <button
              onClick={() => setShowSearchHelp(!showSearchHelp)}
              className={`h-9 w-9 flex items-center justify-center border border-gray-300 rounded-md transition-colors ${
                showSearchHelp ? 'bg-blue-50 text-blue-600' : 'hover:bg-gray-50'
              }`}
              title="Search syntax help"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </button>

            {/* Clear filters button */}
            {(selectedSchemas.size > 0 || selectedObjectTypes.size > 0) && (
              <button
                onClick={() => {
                  setSelectedSchemas(new Set());
                  setSelectedObjectTypes(new Set());
                }}
                className="h-9 px-3 bg-white hover:bg-gray-50 border border-gray-300 rounded-md text-sm transition-colors whitespace-nowrap"
                title="Clear filters"
              >
                Clear Filters
              </button>
            )}
          </div>
        </div>

        {/* Search help panel */}
        {showSearchHelp && (
          <div className="px-4 py-3 bg-blue-50 border-b border-blue-200">
            <div className="p-3 bg-white border border-blue-300 rounded text-xs text-gray-700 leading-relaxed">
              <div className="font-medium mb-2 text-primary-600">
                Advanced Search Syntax:
              </div>
              <div className="grid grid-cols-[auto_1fr] gap-y-2 gap-x-4">
                <code className="text-orange-600 bg-white px-1.5 py-0.5 rounded">customer AND order</code>
                <span>Both words must appear</span>

                <code className="text-orange-600 bg-white px-1.5 py-0.5 rounded">customer OR client</code>
                <span>Either word can appear</span>

                <code className="text-orange-600 bg-white px-1.5 py-0.5 rounded">customer NOT temp</code>
                <span>Exclude results with "temp"</span>

                <code className="text-orange-600 bg-white px-1.5 py-0.5 rounded">"SELECT * FROM"</code>
                <span>Exact phrase search</span>

                <code className="text-orange-600 bg-white px-1.5 py-0.5 rounded">cust*</code>
                <span>Wildcard (matches customer, customers, etc.)</span>
              </div>
            </div>
          </div>
        )}

        {/* Content area */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Results panel (top panel with dynamic height) */}
          <div
            style={{ height: `${topPanelHeight}%` }}
            className="bg-gray-50 border-b border-gray-200 overflow-auto p-4"
          >
            <h3 className="flex items-center gap-2 m-0 mb-4 text-sm text-gray-600 font-medium">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Search Results
            </h3>

            {error && !isSearching && (
              <div className="p-4 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
                {error}
              </div>
            )}

            {!searchQuery.trim() && results.length === 0 && !error && (
              <div className="text-center text-gray-500 py-8 text-sm">
                Start typing to search across all DDL definitions...
              </div>
            )}

            {searchQuery.trim() && results.length === 0 && !isSearching && !error && (
              <div className="text-center text-gray-500 py-8 text-sm">
                No matches found for "{searchQuery}"
              </div>
            )}

            {results.map((result) => (
              <div
                key={result.id}
                onClick={() => handleResultClick(result)}
                className={`p-3 mb-2 rounded cursor-pointer transition-all ${
                  selectedResult?.id === result.id
                    ? 'bg-primary-50 border-2 border-primary-600'
                    : 'bg-white border border-gray-200 hover:bg-gray-50 hover:border-gray-300'
                }`}
              >
                <div className="flex items-center gap-2 mb-1">
                  {selectedResult?.id === result.id && (
                    <svg className="w-4 h-4 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                  <span className="text-gray-600">{getObjectIcon(result.type)}</span>
                  <span className="text-sm font-medium text-gray-800">{highlightText(result.name, searchQuery)}</span>
                  <span className="text-xs text-gray-500 ml-auto">
                    (score: {result.score.toFixed(2)})
                  </span>
                </div>
                <div className={`text-xs text-gray-600 ${selectedResult?.id === result.id ? 'ml-8' : 'ml-6'}`}>
                  {result.schema} • {result.type}
                </div>
                {result.snippet && (
                  <div
                    className={`text-xs text-gray-500 mt-1 italic overflow-hidden text-ellipsis whitespace-nowrap ${
                      selectedResult?.id === result.id ? 'ml-8' : 'ml-6'
                    }`}
                  >
                    ...{highlightText(result.snippet, searchQuery)}...
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Resize divider */}
          <div
            onMouseDown={handleMouseDown}
            className={`h-1 cursor-ns-resize relative ${
              isResizing ? 'bg-primary-600' : 'bg-gray-200 hover:bg-primary-600'
            }`}
            style={{ transition: isResizing ? 'none' : 'background 0.2s' }}
          >
            {/* Visual indicator */}
            <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-10 h-0.5 bg-gray-400 rounded" />
          </div>

          {/* DDL viewer panel (bottom panel with dynamic height) */}
          <div className="flex-1 bg-white flex flex-col min-h-0">
            {/* DDL header */}
            <div className="flex items-center gap-3 px-4 py-3 bg-gray-50 border-b border-gray-200">
              <svg className="w-4 h-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <h3 className="flex-1 m-0 text-sm text-gray-700 font-normal">
                {selectedResult ? `${selectedResult.name} - DDL` : 'DDL Viewer'}
              </h3>
              {ddlText && !isLoadingDdl && (
                <>
                  <div className="text-xs text-gray-500 italic">
                    Press{' '}
                    <kbd className="bg-gray-200 px-1.5 py-0.5 rounded border border-gray-300 font-mono text-xs">
                      Ctrl+F
                    </kbd>{' '}
                    to search
                  </div>
                  {onSwitchToSqlViewer && selectedResult && (
                    <button
                      onClick={() => onSwitchToSqlViewer(selectedResult.id)}
                      className="h-8 px-3 flex items-center gap-2 bg-white hover:bg-blue-50 border border-gray-300 hover:border-blue-400 rounded text-xs font-medium text-gray-700 hover:text-blue-700 transition-all"
                      title="Switch to graph view with side panel"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
                      </svg>
                      <span>View in Graph</span>
                    </button>
                  )}
                </>
              )}
            </div>

            {/* DDL content */}
            <div className="flex-1 bg-gray-50 min-h-0">
              {!selectedResult ? (
                <div className="flex items-center justify-center h-full text-gray-500 text-sm">
                  Click on a search result to view its DDL
                </div>
              ) : isLoadingDdl ? (
                <div className="flex flex-col items-center justify-center h-full text-gray-500">
                  <div className="w-10 h-10 border-4 border-gray-300 border-t-primary-600 rounded-full animate-spin" />
                  <p className="mt-4 text-sm">Loading DDL...</p>
                </div>
              ) : error ? (
                <div className="flex flex-col items-center justify-center h-full text-red-600 p-8">
                  <p className="text-sm font-medium">Failed to Load DDL</p>
                  <p className="text-sm text-gray-500 mt-2">{error}</p>
                </div>
              ) : !ddlText ? (
                <div className="flex items-center justify-center h-full text-gray-500 text-sm">
                  No DDL available for this object
                </div>
              ) : (
                <Editor
                  height="100%"
                  language="sql"
                  theme="light"
                  value={ddlText}
                  onMount={handleEditorDidMount}
                  options={{
                    readOnly: true,
                    minimap: { enabled: false },
                    scrollBeyondLastLine: false,
                    wordWrap: 'on',
                    fontSize: 14,
                    lineNumbers: 'on',
                    renderWhitespace: 'selection',
                    scrollbar: {
                      vertical: 'visible',
                      horizontal: 'visible',
                      verticalScrollbarSize: 16,
                      horizontalScrollbarSize: 16,
                    },
                    overviewRulerBorder: true,
                    overviewRulerLanes: 3,
                    find: {
                      addExtraSpaceOnTop: false,
                      autoFindInSelection: 'never',
                      seedSearchStringFromSelection: 'always',
                    },
                  }}
                />
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Spinner animation */}
      <style>
        {`
          @keyframes spin {
            from {
              transform: rotate(0deg);
            }
            to {
              transform: rotate(360deg);
            }
          }
        `}
      </style>
    </>
  );
};

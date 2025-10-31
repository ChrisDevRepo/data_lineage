import React, { useState, useEffect, useMemo, useRef } from 'react';
import Editor from '@monaco-editor/react';
import { DataNode } from '../types';

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

export const DetailSearchModal: React.FC<DetailSearchModalProps> = ({ isOpen, allData, onClose }) => {
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

  // Filter state
  const [selectedSchema, setSelectedSchema] = useState<string>('');
  const [selectedObjectType, setSelectedObjectType] = useState<string>('');
  const [showSearchHelp, setShowSearchHelp] = useState(false);

  const editorRef = useRef<any>(null);
  const resizeRef = useRef<{ startY: number; startHeight: number } | null>(null);

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

  // Debounced search function
  const debouncedSearch = useMemo(
    () => debounce(async (query: string, schema: string, objectType: string) => {
      if (!query.trim()) {
        setResults([]);
        setIsSearching(false);
        return;
      }

      setIsSearching(true);
      setError(null);

      try {
        const response = await fetch(
          `http://localhost:8000/api/search-ddl?q=${encodeURIComponent(query)}`
        );

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: response.statusText }));
          throw new Error(errorData.detail || 'Search failed');
        }

        let data = await response.json();

        // Client-side filtering by schema and object type
        if (schema) {
          data = data.filter((result: SearchResult) => result.schema === schema);
        }
        if (objectType) {
          data = data.filter((result: SearchResult) => result.type === objectType);
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
      debouncedSearch(searchQuery, selectedSchema, selectedObjectType);
    } else {
      setResults([]);
      setIsSearching(false);
    }
  }, [searchQuery, selectedSchema, selectedObjectType, debouncedSearch]);

  // Handle result click - fetch full DDL
  const handleResultClick = async (result: SearchResult) => {
    setSelectedResult(result);
    setIsLoadingDdl(true);
    setError(null);

    try {
      const response = await fetch(`http://localhost:8000/api/ddl/${result.id}`);

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
    setSelectedSchema('');
    setSelectedObjectType('');
    setShowSearchHelp(false);
  };

  // Handle editor mount
  const handleEditorDidMount = (editor: any, monaco: any) => {
    editorRef.current = editor;

    // Configure find widget
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyF, () => {
      editor.getAction('actions.find').run();
    });
  };

  // Get icon by object type
  const getObjectIcon = (type: string) => {
    switch (type) {
      case 'Stored Procedure':
        return '📦';
      case 'View':
        return '👁';
      case 'Table':
        return '📊';
      case 'Function':
        return '⚡';
      default:
        return '📄';
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Full-screen backdrop */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: 'rgba(0, 0, 0, 0.7)',
          zIndex: 9998,
        }}
        onClick={handleClose}
      />

      {/* Modal content - Full screen overlay */}
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          background: '#1e1e1e',
          zIndex: 9999,
          display: 'flex',
          flexDirection: 'column',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: '0.75rem',
            padding: '1rem 1.5rem',
            background: '#252526',
            borderBottom: '1px solid #3e3e42',
          }}
        >
          {/* First row: Search input and close button */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <span style={{ fontSize: '1.2rem' }}>🔍</span>
            <input
              type="text"
              placeholder="Search DDL definitions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              autoFocus
              style={{
                flex: 1,
                padding: '0.5rem 1rem',
                background: '#3c3c3c',
                border: '1px solid #5a5a5a',
                borderRadius: '4px',
                color: '#d4d4d4',
                fontSize: '14px',
                outline: 'none',
              }}
            />
            {isSearching && (
              <div
                style={{
                  width: '20px',
                  height: '20px',
                  border: '2px solid #555',
                  borderTopColor: '#569CD6',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite',
                }}
              />
            )}
            {results.length > 0 && !isSearching && (
              <span style={{ fontSize: '13px', color: '#888', whiteSpace: 'nowrap' }}>
                {results.length} {results.length === 1 ? 'match' : 'matches'}
              </span>
            )}
            <button
              onClick={handleClose}
              style={{
                width: '32px',
                height: '32px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                background: 'transparent',
                border: 'none',
                color: '#d4d4d4',
                fontSize: '20px',
                cursor: 'pointer',
                borderRadius: '4px',
              }}
              onMouseOver={(e) => (e.currentTarget.style.background = '#3e3e42')}
              onMouseOut={(e) => (e.currentTarget.style.background = 'transparent')}
              title="Close (ESC)"
            >
              ×
            </button>
          </div>

          {/* Second row: Filters and help */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', paddingLeft: '2.2rem' }}>
            {/* Schema filter */}
            <select
              value={selectedSchema}
              onChange={(e) => setSelectedSchema(e.target.value)}
              style={{
                padding: '0.35rem 0.75rem',
                background: '#3c3c3c',
                border: '1px solid #5a5a5a',
                borderRadius: '4px',
                color: '#d4d4d4',
                fontSize: '12px',
                cursor: 'pointer',
                outline: 'none',
              }}
            >
              <option value="">All Schemas</option>
              {filterOptions.schemas.map(schema => (
                <option key={schema} value={schema}>{schema}</option>
              ))}
            </select>

            {/* Object type filter */}
            <select
              value={selectedObjectType}
              onChange={(e) => setSelectedObjectType(e.target.value)}
              style={{
                padding: '0.35rem 0.75rem',
                background: '#3c3c3c',
                border: '1px solid #5a5a5a',
                borderRadius: '4px',
                color: '#d4d4d4',
                fontSize: '12px',
                cursor: 'pointer',
                outline: 'none',
              }}
            >
              <option value="">All Types</option>
              {filterOptions.objectTypes.map(type => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>

            {/* Search help toggle */}
            <button
              onClick={() => setShowSearchHelp(!showSearchHelp)}
              style={{
                padding: '0.35rem 0.75rem',
                background: showSearchHelp ? '#404040' : 'transparent',
                border: '1px solid #5a5a5a',
                borderRadius: '4px',
                color: '#569CD6',
                fontSize: '12px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.25rem',
              }}
              title="Search syntax help"
            >
              <span>?</span>
              <span>Help</span>
            </button>

            {/* Clear filters button */}
            {(selectedSchema || selectedObjectType) && (
              <button
                onClick={() => {
                  setSelectedSchema('');
                  setSelectedObjectType('');
                }}
                style={{
                  padding: '0.35rem 0.75rem',
                  background: 'transparent',
                  border: '1px solid #5a5a5a',
                  borderRadius: '4px',
                  color: '#888',
                  fontSize: '12px',
                  cursor: 'pointer',
                }}
                title="Clear filters"
              >
                Clear Filters
              </button>
            )}
          </div>

          {/* Search help panel */}
          {showSearchHelp && (
            <div
              style={{
                padding: '0.75rem',
                background: '#2d2d2d',
                border: '1px solid #3e3e42',
                borderRadius: '4px',
                fontSize: '12px',
                color: '#cccccc',
                lineHeight: '1.6',
                marginLeft: '2.2rem',
              }}
            >
              <div style={{ fontWeight: 500, marginBottom: '0.5rem', color: '#569CD6' }}>
                Advanced Search Syntax:
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '0.5rem 1rem' }}>
                <code style={{ color: '#ce9178' }}>customer AND order</code>
                <span>Both words must appear</span>

                <code style={{ color: '#ce9178' }}>customer OR client</code>
                <span>Either word can appear</span>

                <code style={{ color: '#ce9178' }}>customer NOT temp</code>
                <span>Exclude results with "temp"</span>

                <code style={{ color: '#ce9178' }}>"SELECT * FROM"</code>
                <span>Exact phrase search</span>

                <code style={{ color: '#ce9178' }}>cust*</code>
                <span>Wildcard (matches customer, customers, etc.)</span>
              </div>
            </div>
          )}
        </div>

        {/* Content area */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
          {/* Results panel (top panel with dynamic height) */}
          <div
            style={{
              height: `${topPanelHeight}%`,
              background: '#1e1e1e',
              borderBottom: '1px solid #3e3e42',
              overflow: 'auto',
              padding: '1rem',
            }}
          >
            <h3 style={{ margin: '0 0 1rem 0', fontSize: '14px', color: '#888', fontWeight: 500 }}>
              📋 Search Results
            </h3>

            {error && !isSearching && (
              <div
                style={{
                  padding: '1rem',
                  background: '#3e2020',
                  border: '1px solid #6e4040',
                  borderRadius: '4px',
                  color: '#f48771',
                  fontSize: '13px',
                }}
              >
                {error}
              </div>
            )}

            {!searchQuery.trim() && results.length === 0 && !error && (
              <div style={{ textAlign: 'center', color: '#666', padding: '2rem', fontSize: '13px' }}>
                Start typing to search across all DDL definitions...
              </div>
            )}

            {searchQuery.trim() && results.length === 0 && !isSearching && !error && (
              <div style={{ textAlign: 'center', color: '#666', padding: '2rem', fontSize: '13px' }}>
                No matches found for "{searchQuery}"
              </div>
            )}

            {results.map((result) => (
              <div
                key={result.id}
                onClick={() => handleResultClick(result)}
                style={{
                  padding: '0.75rem',
                  marginBottom: '0.5rem',
                  background: selectedResult?.id === result.id ? '#2a2d2e' : '#252526',
                  border: `1px solid ${selectedResult?.id === result.id ? '#007acc' : '#3e3e42'}`,
                  borderRadius: '4px',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
                onMouseOver={(e) => {
                  if (selectedResult?.id !== result.id) {
                    e.currentTarget.style.background = '#2a2d2e';
                  }
                }}
                onMouseOut={(e) => {
                  if (selectedResult?.id !== result.id) {
                    e.currentTarget.style.background = '#252526';
                  }
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
                  {selectedResult?.id === result.id && <span style={{ color: '#4ec9b0' }}>✓</span>}
                  <span style={{ fontSize: '16px' }}>{getObjectIcon(result.type)}</span>
                  <span style={{ fontSize: '14px', fontWeight: 500, color: '#d4d4d4' }}>{result.name}</span>
                  <span style={{ fontSize: '12px', color: '#888', marginLeft: 'auto' }}>
                    (score: {result.score.toFixed(2)})
                  </span>
                </div>
                <div style={{ fontSize: '12px', color: '#888', marginLeft: selectedResult?.id === result.id ? '2rem' : '1.5rem' }}>
                  {result.schema} • {result.type}
                </div>
                {result.snippet && (
                  <div
                    style={{
                      fontSize: '12px',
                      color: '#888',
                      marginTop: '0.25rem',
                      fontStyle: 'italic',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap',
                      marginLeft: selectedResult?.id === result.id ? '2rem' : '1.5rem',
                    }}
                  >
                    ...{result.snippet}...
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Resize divider */}
          <div
            onMouseDown={handleMouseDown}
            style={{
              height: '4px',
              background: isResizing ? '#007acc' : '#3e3e42',
              cursor: 'ns-resize',
              transition: isResizing ? 'none' : 'background 0.2s',
              position: 'relative',
            }}
            onMouseOver={(e) => {
              if (!isResizing) {
                e.currentTarget.style.background = '#007acc';
              }
            }}
            onMouseOut={(e) => {
              if (!isResizing) {
                e.currentTarget.style.background = '#3e3e42';
              }
            }}
          >
            {/* Visual indicator */}
            <div
              style={{
                position: 'absolute',
                top: '50%',
                left: '50%',
                transform: 'translate(-50%, -50%)',
                width: '40px',
                height: '2px',
                background: '#888',
                borderRadius: '1px',
              }}
            />
          </div>

          {/* DDL viewer panel (bottom panel with dynamic height) */}
          <div style={{ flex: 1, background: '#1e1e1e', display: 'flex', flexDirection: 'column', minHeight: 0 }}>
            {/* DDL header */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.75rem',
                padding: '0.75rem 1rem',
                background: '#252526',
                borderBottom: '1px solid #3e3e42',
              }}
            >
              <h3 style={{ flex: 1, margin: 0, fontSize: '14px', color: '#cccccc', fontWeight: 400 }}>
                {selectedResult ? `📄 ${selectedResult.name} - DDL` : '📄 DDL Viewer'}
              </h3>
              {ddlText && !isLoadingDdl && (
                <div style={{ fontSize: '12px', color: '#858585', fontStyle: 'italic' }}>
                  Press{' '}
                  <kbd
                    style={{
                      background: '#3c3c3c',
                      padding: '2px 6px',
                      borderRadius: '3px',
                      border: '1px solid #5a5a5a',
                      fontFamily: 'monospace',
                      fontSize: '11px',
                    }}
                  >
                    Ctrl+F
                  </kbd>{' '}
                  to search
                </div>
              )}
            </div>

            {/* DDL content */}
            <div style={{ flex: 1, background: '#1e1e1e', minHeight: 0 }}>
              {!selectedResult ? (
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    height: '100%',
                    color: '#888',
                    fontSize: '13px',
                  }}
                >
                  Click on a search result to view its DDL
                </div>
              ) : isLoadingDdl ? (
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    height: '100%',
                    color: '#888',
                  }}
                >
                  <div
                    style={{
                      width: '40px',
                      height: '40px',
                      border: '4px solid #333',
                      borderTopColor: '#569CD6',
                      borderRadius: '50%',
                      animation: 'spin 1s linear infinite',
                    }}
                  />
                  <p style={{ marginTop: '1rem', fontSize: '13px' }}>Loading DDL...</p>
                </div>
              ) : error ? (
                <div
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    height: '100%',
                    color: '#f48771',
                    padding: '2rem',
                  }}
                >
                  <p style={{ fontSize: '14px', fontWeight: 500 }}>Failed to Load DDL</p>
                  <p style={{ fontSize: '13px', color: '#888' }}>{error}</p>
                </div>
              ) : !ddlText ? (
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    height: '100%',
                    color: '#888',
                    fontSize: '13px',
                  }}
                >
                  No DDL available for this object
                </div>
              ) : (
                <Editor
                  height="100%"
                  language="sql"
                  theme="vs-dark"
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

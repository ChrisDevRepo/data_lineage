import React, { useState, useEffect, useRef, useMemo } from 'react';
import Prism from 'prismjs';
import 'prismjs/themes/prism-tomorrow.css';  // Dark theme for syntax highlighting
import 'prismjs/components/prism-sql';        // SQL syntax support

type SqlViewerProps = {
  isOpen: boolean;
  selectedNode: {
    id: string;
    name: string;
    schema: string;
    objectType: string;
  } | null;
};

// Cache for syntax highlighting results (prevents re-highlighting same DDL)
const highlightCache = new Map<string, string>();

export const SqlViewer: React.FC<SqlViewerProps> = React.memo(({ isOpen, selectedNode }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [ddlText, setDdlText] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const codeRef = useRef<HTMLPreElement>(null);

  // Fetch DDL on demand when node changes
  useEffect(() => {
    console.log('[SqlViewer] Effect triggered:', { selectedNode: selectedNode?.id, isOpen });

    if (!selectedNode || !isOpen) {
      setDdlText(null);
      setError(null);
      return;
    }

    const fetchDDL = async () => {
      console.log('[SqlViewer] Fetching DDL for object:', selectedNode.id);
      setIsLoading(true);
      setError(null);

      try {
        const url = `http://localhost:8000/api/ddl/${selectedNode.id}`;
        console.log('[SqlViewer] Fetch URL:', url);

        const response = await fetch(url);
        console.log('[SqlViewer] Response status:', response.status);

        if (!response.ok) {
          throw new Error(`Failed to fetch DDL: ${response.statusText}`);
        }

        const data = await response.json();
        console.log('[SqlViewer] DDL fetched, length:', data.ddl_text?.length);
        setDdlText(data.ddl_text);
      } catch (err) {
        console.error('[SqlViewer] Failed to fetch DDL:', err);
        setError(err instanceof Error ? err.message : 'Failed to load DDL');
        setDdlText(null);
      } finally {
        setIsLoading(false);
      }
    };

    fetchDDL();
  }, [selectedNode?.id, isOpen]);

  // Memoize syntax highlighting with cache (OPTIMIZATION: Avoid re-highlighting same DDL)
  const highlightedDdl = useMemo(() => {
    if (!ddlText) return '';

    // Check cache first
    const cacheKey = `${selectedNode?.id}_${ddlText.length}`;
    if (highlightCache.has(cacheKey)) {
      return highlightCache.get(cacheKey)!;
    }

    // Perform expensive syntax highlighting
    const highlighted = Prism.highlight(
      ddlText,
      Prism.languages.sql,
      'sql'
    );

    // Store in cache (limit cache size to prevent memory leak)
    if (highlightCache.size > 50) {
      const firstKey = highlightCache.keys().next().value;
      highlightCache.delete(firstKey);
    }
    highlightCache.set(cacheKey, highlighted);

    return highlighted;
  }, [selectedNode?.id, ddlText]);

  // Reset search when node changes
  useEffect(() => {
    setSearchQuery('');
  }, [selectedNode?.id]);

  // Consolidated effect: Handle both syntax highlighting AND search highlighting
  // OPTIMIZATION: Reduced from 3 effects to 1, eliminating race conditions
  useEffect(() => {
    if (!codeRef.current || !highlightedDdl) return;

    if (searchQuery) {
      // Apply search highlighting on top of syntax highlighting
      const escapedQuery = searchQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const regex = new RegExp(escapedQuery, 'gi');
      const html = highlightedDdl.replace(
        regex,
        (match) => `<mark class="search-highlight">${match}</mark>`
      );

      codeRef.current.innerHTML = html;

      // Scroll to first match
      const firstMatch = codeRef.current.querySelector('.search-highlight');
      if (firstMatch) {
        firstMatch.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    } else {
      // No search - show pure syntax highlighting
      codeRef.current.innerHTML = highlightedDdl;
    }
  }, [searchQuery, highlightedDdl]);

  if (!isOpen) return null;

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      background: '#1e1e1e',
      color: '#d4d4d4',
      fontFamily: 'Consolas, Monaco, "Courier New", monospace'
    }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem',
        padding: '0.75rem 1rem',
        background: '#252526',
        borderBottom: '1px solid #3e3e42',
        minHeight: '52px'
      }}>
        <h2 style={{
          flex: 1,
          margin: 0,
          color: '#cccccc',
          fontSize: '0.95rem',
          fontWeight: 400,
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap'
        }}>
          {selectedNode
            ? `${selectedNode.name} - DDL`
            : 'DDL Viewer'}
        </h2>

        {/* Search box - only show when SQL is loaded */}
        {ddlText && !isLoading && (
          <input
            type="text"
            placeholder="Search SQL..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '200px',
              minWidth: '150px',
              flexShrink: 0,
              padding: '0.4rem 0.6rem',
              border: '1px solid #3e3e42',
              borderRadius: '4px',
              background: '#3c3c3c',
              color: '#ffffff',
              fontSize: '13px'
            }}
            onFocus={(e) => {
              e.target.style.outline = 'none';
              e.target.style.borderColor = '#007acc';
            }}
            onBlur={(e) => {
              e.target.style.borderColor = '#3e3e42';
            }}
          />
        )}
      </div>

      {/* SQL content */}
      <div
        className="sql-viewer-content"
        style={{
          flex: 1,
          overflow: 'auto',
          padding: '1rem',
          background: '#1e1e1e',
          minHeight: 0 // Ensure flex child can scroll
        }}
      >
        {!selectedNode ? (
          // Empty state: No node selected
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            color: '#888888',
            textAlign: 'center',
            padding: '2rem'
          }}>
            <p style={{ margin: '0.5rem 0', fontSize: '16px' }}>
              Click on any Stored Procedure or View to see its SQL definition
            </p>
          </div>
        ) : isLoading ? (
          // Loading state
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            color: '#888888',
            textAlign: 'center',
            padding: '2rem'
          }}>
            <div style={{
              width: '40px',
              height: '40px',
              border: '4px solid #333',
              borderTopColor: '#569CD6',
              borderRadius: '50%',
              animation: 'spin 1s linear infinite'
            }} />
            <p style={{ marginTop: '1rem', fontSize: '14px' }}>Loading DDL...</p>
          </div>
        ) : error ? (
          // Error state
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            color: '#f48771',
            textAlign: 'center',
            padding: '2rem'
          }}>
            <p style={{ margin: '0.5rem 0', fontSize: '16px', fontWeight: 500 }}>
              Failed to Load DDL
            </p>
            <p style={{ margin: '0.5rem 0', fontSize: '14px', color: '#888888' }}>
              {error}
            </p>
          </div>
        ) : !ddlText ? (
          // Empty state: Node selected but no DDL available
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            color: '#888888',
            textAlign: 'center',
            padding: '2rem'
          }}>
            {selectedNode.objectType === 'Table' ? (
              // Table without DDL - explain what would be shown
              <>
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor" style={{ width: '64px', height: '64px', marginBottom: '1rem', color: '#666666' }}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 01-1.125-1.125M3.375 19.5h7.5c.621 0 1.125-.504 1.125-1.125m-9.75 0V5.625m0 12.75v-1.5c0-.621.504-1.125 1.125-1.125m18.375 2.625V5.625m0 12.75c0 .621-.504 1.125-1.125 1.125m1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125m0 3.75h-7.5A1.125 1.125 0 0112 18.375m9.75-12.75c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125m19.5 0v1.5c0 .621-.504 1.125-1.125 1.125M2.25 5.625v1.5c0 .621.504 1.125 1.125 1.125m0 0h17.25m-17.25 0h7.5c.621 0 1.125.504 1.125 1.125M3.375 8.25c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125m17.25-3.75c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5m0 0v1.5m0-1.5h7.5m-7.5 0v-1.5m7.5 1.5v-1.5m0 1.5v1.5" />
                </svg>
                <p style={{ margin: '0.5rem 0', fontSize: '16px', fontWeight: 500 }}>
                  Table Structure Not Available
                </p>
                <p style={{
                  margin: '0.5rem 0',
                  fontSize: '14px',
                  color: '#666666',
                  maxWidth: '400px',
                  lineHeight: '1.6'
                }}>
                  When table column metadata is included in the dataset, this panel will display:
                </p>
                <ul style={{
                  textAlign: 'left',
                  fontSize: '13px',
                  color: '#777777',
                  lineHeight: '1.8',
                  marginTop: '1rem'
                }}>
                  <li>Column names and data types</li>
                  <li>Precision and scale for numeric columns</li>
                  <li>Max length for string columns</li>
                  <li>Nullable constraints</li>
                </ul>
                <p style={{
                  margin: '1.5rem 0 0 0',
                  fontSize: '12px',
                  color: '#555555',
                  fontStyle: 'italic',
                  maxWidth: '400px',
                  lineHeight: '1.6'
                }}>
                  To enable this feature, ensure the backend includes <code style={{ background: '#2d2d2d', padding: '2px 6px', borderRadius: '3px', color: '#d4d4d4' }}>table_columns.parquet</code> when uploading data.
                </p>
              </>
            ) : (
              // Stored Procedure or View without DDL
              <>
                <p style={{ margin: '0.5rem 0', fontSize: '16px' }}>
                  No SQL definition available for this object
                </p>
                <p style={{
                  margin: '0.5rem 0',
                  fontSize: '14px',
                  color: '#666666',
                  fontStyle: 'italic'
                }}>
                  (DDL not included in this dataset)
                </p>
              </>
            )}
          </div>
        ) : (
          // SQL content with syntax highlighting
          <pre
            ref={codeRef}
            className="language-sql"
            style={{
              margin: 0,
              fontSize: '14px',
              lineHeight: '1.6',
              color: '#d4d4d4',
              background: 'transparent',
              padding: 0,
              border: 'none'
            }}
          >
            <code
              className="language-sql"
              dangerouslySetInnerHTML={{ __html: highlightedDdl }}
            />
          </pre>
        )}
      </div>

      {/* Inline styles for search highlighting */}
      <style>
        {`
          .search-highlight {
            background-color: #ffd700;
            color: #000000;
            padding: 2px 4px;
            border-radius: 2px;
            font-weight: bold;
          }

          /* Custom scrollbar for dark theme - More visible */
          /* Firefox support */
          .sql-viewer-content {
            scrollbar-width: thin;
            scrollbar-color: #5a5a5a #252526;
          }

          /* Webkit browsers (Chrome, Safari, Edge) */
          .sql-viewer-content::-webkit-scrollbar {
            width: 14px;
            height: 14px;
          }

          .sql-viewer-content::-webkit-scrollbar-track {
            background: #252526;
            border-left: 1px solid #3e3e42;
          }

          .sql-viewer-content::-webkit-scrollbar-thumb {
            background: #5a5a5a;
            border: 2px solid #252526;
            border-radius: 8px;
          }

          .sql-viewer-content::-webkit-scrollbar-thumb:hover {
            background: #6e6e6e;
          }

          .sql-viewer-content::-webkit-scrollbar-thumb:active {
            background: #808080;
          }

          .sql-viewer-content::-webkit-scrollbar-corner {
            background: #252526;
          }

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
    </div>
  );
});

import React, { useState, useEffect, useRef } from 'react';
import Editor from '@monaco-editor/react';

type SqlViewerProps = {
  isOpen: boolean;
  selectedNode: {
    id: string;
    name: string;
    schema: string;
    objectType: string;
    ddl_text?: string | null; // Optional: only present in JSON uploads
  } | null;
};

export const SqlViewer: React.FC<SqlViewerProps> = React.memo(({ isOpen, selectedNode }) => {
  const [ddlText, setDdlText] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const editorRef = useRef<any>(null);

  // Fetch DDL on demand when node changes
  useEffect(() => {
    if (!selectedNode || !isOpen) {
      setDdlText(null);
      setError(null);
      setIsLoading(false);
      return;
    }

    // Small Mode: Check if DDL is embedded in the node data (JSON upload)
    if ('ddl_text' in selectedNode) {
      setDdlText(selectedNode.ddl_text); // Could be null or actual DDL
      setError(null);
      setIsLoading(false);
      return; // No API call needed!
    }

    // Large Mode: Fetch from DuckDB via API (Parquet upload)
    const fetchDDL = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const url = `http://localhost:8000/api/ddl/${selectedNode.id}`;
        const response = await fetch(url);

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: response.statusText }));
          setError(errorData.detail || 'Failed to fetch DDL');
          setDdlText(null);
          return;
        }

        const data = await response.json();
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

  // Handle editor mount
  const handleEditorDidMount = (editor: any, monaco: any) => {
    editorRef.current = editor;

    // Configure find widget to open automatically with Ctrl+F
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyF, () => {
      editor.getAction('actions.find').run();
    });
  };

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

        {/* Search hint - only show when SQL is loaded */}
        {ddlText && !isLoading && (
          <div style={{
            fontSize: '12px',
            color: '#858585',
            fontStyle: 'italic',
            marginRight: '0.5rem'
          }}>
            Press <kbd style={{
              background: '#3c3c3c',
              padding: '2px 6px',
              borderRadius: '3px',
              border: '1px solid #5a5a5a',
              fontFamily: 'monospace',
              fontSize: '11px'
            }}>Ctrl+F</kbd> to search
          </div>
        )}
      </div>

      {/* SQL content */}
      <div
        className="sql-viewer-content"
        style={{
          flex: 1,
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
          // Monaco Editor with syntax highlighting and built-in search
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

      {/* Inline styles for loading spinner */}
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
    </div>
  );
});

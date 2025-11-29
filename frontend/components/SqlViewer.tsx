import React, { useState, useEffect, useRef } from 'react';
import Editor from '@monaco-editor/react';
import { SpinnerContainer } from './ui/Spinner';
import { API_BASE_URL } from '../config';
import { MONACO_EDITOR_OPTIONS } from '../constants/monacoConfig';

type SqlViewerProps = {
  isOpen: boolean;
  selectedNode: {
    id: string;
    name: string;
    schema: string;
    objectType: string;
    ddl_text?: string | null; // Optional: only present in JSON uploads
  } | null;
  onClose?: () => void;
};

export const SqlViewer: React.FC<SqlViewerProps> = React.memo(({ isOpen, selectedNode, onClose }) => {
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
        const url = `${API_BASE_URL}/api/ddl/${selectedNode.id}`;
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
    <div className="flex flex-col h-full bg-white text-gray-800 font-mono">
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-3 bg-gray-50 border-b border-gray-200 min-h-[52px]">
        <h2 className="flex-1 m-0 text-gray-700 text-base font-normal overflow-hidden overflow-ellipsis whitespace-nowrap">
          {selectedNode
            ? `${selectedNode.name} - DDL`
            : 'DDL Viewer'}
        </h2>

        {/* Search hint - only show when SQL is loaded */}
        {ddlText && !isLoading && (
          <div className="text-xs text-gray-500 italic mr-2">
            Press <kbd className="bg-gray-200 px-1.5 py-0.5 rounded border border-gray-300 font-mono text-xs">
              Ctrl+F
            </kbd> to search
          </div>
        )}

        {/* Close Button */}
        {onClose && (
          <button
            onClick={onClose}
            className="h-8 w-8 flex items-center justify-center bg-white hover:bg-red-50 border border-gray-300 hover:border-red-400 rounded text-gray-500 hover:text-red-600 transition-all"
            title="Close SQL Viewer"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* SQL content */}
      <div className="sql-viewer-content flex-1 bg-gray-50 min-h-0">
        {!selectedNode ? (
          // Empty state: No node selected
          <div className="flex flex-col items-center justify-center h-full text-gray-500 text-center p-8">
            <p className="my-2 text-base">
              Right-click on any node and select "Show SQL" to view its definition
            </p>
          </div>
        ) : isLoading ? (
          // Loading state
          <SpinnerContainer message="Loading DDL..." />
        ) : error ? (
          // Error state
          <div className="flex flex-col items-center justify-center h-full text-red-600 text-center p-8">
            <p className="my-2 text-base font-medium">
              Failed to Load DDL
            </p>
            <p className="my-2 text-sm text-gray-500">
              {error}
            </p>
          </div>
        ) : !ddlText ? (
          // Empty state: Node selected but no DDL available
          <div className="flex flex-col items-center justify-center h-full text-gray-500 text-center p-8">
            {selectedNode.objectType === 'Table' ? (
              // Table without DDL - explain what would be shown
              <>
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth="1.5" stroke="currentColor" className="w-16 h-16 mb-4 text-gray-400">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.375 19.5h17.25m-17.25 0a1.125 1.125 0 01-1.125-1.125M3.375 19.5h7.5c.621 0 1.125-.504 1.125-1.125m-9.75 0V5.625m0 12.75v-1.5c0-.621.504-1.125 1.125-1.125m18.375 2.625V5.625m0 12.75c0 .621-.504 1.125-1.125 1.125m1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125m0 3.75h-7.5A1.125 1.125 0 0112 18.375m9.75-12.75c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125m19.5 0v1.5c0 .621-.504 1.125-1.125 1.125M2.25 5.625v1.5c0 .621.504 1.125 1.125 1.125m0 0h17.25m-17.25 0h7.5c.621 0 1.125.504 1.125 1.125M3.375 8.25c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125m17.25-3.75c.621 0 1.125.504 1.125 1.125v1.5c0 .621-.504 1.125-1.125 1.125m-17.25 0h7.5m0 0v1.5m0-1.5h7.5m-7.5 0v-1.5m7.5 1.5v-1.5m0 1.5v1.5" />
                </svg>
                <p className="my-2 text-base font-medium text-gray-700">
                  Table Structure Not Available
                </p>
                <p className="my-2 text-sm text-gray-600 max-w-md leading-relaxed">
                  When table column metadata is included in the dataset, this panel will display:
                </p>
                <ul className="text-left text-sm text-gray-600 leading-loose mt-4">
                  <li>Column names and data types</li>
                  <li>Precision and scale for numeric columns</li>
                  <li>Max length for string columns</li>
                  <li>Nullable constraints</li>
                </ul>
                <p className="mt-6 text-xs text-gray-500 italic max-w-md leading-relaxed">
                  To enable this feature, ensure the backend includes <code className="bg-gray-200 px-1.5 py-0.5 rounded text-gray-800">table_columns.parquet</code> when uploading data.
                </p>
              </>
            ) : (
              // Stored Procedure or View without DDL
              <>
                <p className="my-2 text-base text-gray-600">
                  No SQL definition available for this object
                </p>
                <p className="my-2 text-sm text-gray-500 italic">
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
            theme="light"
            value={ddlText}
            onMount={handleEditorDidMount}
            options={MONACO_EDITOR_OPTIONS}
          />
        )}
      </div>
    </div>
  );
});

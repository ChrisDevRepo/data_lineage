import React, { useState, useEffect, useRef } from 'react';
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
    ddlText: string | null;
  } | null;
};

export const SqlViewer: React.FC<SqlViewerProps> = ({ isOpen, selectedNode }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [highlightedDdl, setHighlightedDdl] = useState('');
  const codeRef = useRef<HTMLPreElement>(null);

  // Syntax highlight DDL when selected node changes
  useEffect(() => {
    if (selectedNode?.ddlText) {
      // Use Prism.js for T-SQL syntax highlighting
      const highlighted = Prism.highlight(
        selectedNode.ddlText,
        Prism.languages.sql,
        'sql'
      );
      setHighlightedDdl(highlighted);
      setSearchQuery(''); // Reset search when node changes
    } else {
      setHighlightedDdl('');
      setSearchQuery('');
    }
  }, [selectedNode]);

  // Handle search highlighting
  useEffect(() => {
    if (!searchQuery || !highlightedDdl || !codeRef.current) return;

    // Create regex for case-insensitive search
    const regex = new RegExp(searchQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');

    // Wrap matches in <mark> tags for highlighting
    let html = highlightedDdl.replace(
      regex,
      (match) => `<mark class="search-highlight">${match}</mark>`
    );

    if (codeRef.current) {
      codeRef.current.innerHTML = html;

      // Scroll to first match
      const firstMatch = codeRef.current.querySelector('.search-highlight');
      if (firstMatch) {
        firstMatch.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [searchQuery, highlightedDdl]);

  // Update code when not searching (show pure syntax highlighting)
  useEffect(() => {
    if (!searchQuery && highlightedDdl && codeRef.current) {
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
        gap: '1rem',
        padding: '1rem',
        background: '#252526',
        borderBottom: '1px solid #3e3e42'
      }}>
        <h2 style={{
          flex: 1,
          margin: 0,
          color: '#ffffff',
          fontSize: '1.1rem',
          fontWeight: 400
        }}>
          {selectedNode
            ? `${selectedNode.schema}.${selectedNode.name} - DDL`
            : 'DDL Viewer'}
        </h2>

        {/* Search box - only show when SQL is loaded */}
        {selectedNode?.ddlText && (
          <input
            type="text"
            placeholder="Search SQL..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '250px',
              padding: '0.5rem',
              border: '1px solid #3e3e42',
              borderRadius: '4px',
              background: '#3c3c3c',
              color: '#ffffff',
              fontSize: '14px'
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
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '1rem',
        background: '#1e1e1e'
      }}>
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
        ) : !selectedNode.ddlText ? (
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
            <p style={{ margin: '0.5rem 0', fontSize: '16px' }}>
              No SQL definition available for this object
            </p>
            <p style={{
              margin: '0.5rem 0',
              fontSize: '14px',
              color: '#666666',
              fontStyle: 'italic'
            }}>
              {selectedNode.objectType === 'Table'
                ? '(Tables don\'t have DDL definitions)'
                : '(DDL not included in this dataset)'}
            </p>
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

          /* Custom scrollbar for dark theme */
          .sql-viewer-content::-webkit-scrollbar {
            width: 12px;
          }

          .sql-viewer-content::-webkit-scrollbar-track {
            background: #1e1e1e;
          }

          .sql-viewer-content::-webkit-scrollbar-thumb {
            background: #424242;
            border-radius: 6px;
          }

          .sql-viewer-content::-webkit-scrollbar-thumb:hover {
            background: #555555;
          }
        `}
      </style>
    </div>
  );
};

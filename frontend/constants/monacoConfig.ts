/**
 * Shared Monaco Editor configuration for SQL viewing
 *
 * Used by:
 * - SqlViewer.tsx
 * - DetailSearchModal.tsx
 *
 * v2 (2025-11-08): Added domReadOnly to prevent keyboard capture from search input
 */

export const MONACO_EDITOR_OPTIONS = {
  readOnly: true,
  domReadOnly: true, // BUG-002.2 fix: Prevent editor from capturing keyboard events outside its DOM
  minimap: { enabled: false },
  scrollBeyondLastLine: false,
  wordWrap: 'on' as const,
  fontSize: 14,
  lineNumbers: 'on' as const,
  renderWhitespace: 'selection' as const,
  scrollbar: {
    vertical: 'visible' as const,
    horizontal: 'visible' as const,
    verticalScrollbarSize: 16,
    horizontalScrollbarSize: 16,
  },
  overviewRulerBorder: true,
  overviewRulerLanes: 3,
  find: {
    addExtraSpaceOnTop: false,
    autoFindInSelection: 'never' as const,
    seedSearchStringFromSelection: 'always' as const,
  },
};

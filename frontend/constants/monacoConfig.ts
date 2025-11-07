/**
 * Shared Monaco Editor configuration for SQL viewing
 *
 * Used by:
 * - SqlViewer.tsx
 * - DetailSearchModal.tsx
 */

export const MONACO_EDITOR_OPTIONS = {
  readOnly: true,
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

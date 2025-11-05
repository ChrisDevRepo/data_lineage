/**
 * Constants for user interaction behaviors across the application.
 * Centralizes magic numbers to improve maintainability and consistency.
 */

export const INTERACTION_CONSTANTS = {
  // Search and autocomplete
  AUTOCOMPLETE_MAX_RESULTS: 5,
  SEARCH_DEBOUNCE_MS: 300,

  // View and layout
  FIT_VIEW_PADDING: 0.2,
  FIT_VIEW_DURATION_MS: 500,
  FIT_VIEW_AFTER_SEARCH_MS: 800,
  SEARCH_ZOOM_LEVEL: 1.2,

  // Window resize
  WINDOW_RESIZE_DEBOUNCE_MS: 150,
  WINDOW_RESIZE_FIT_DURATION_MS: 200,

  // SQL Viewer panel
  SQL_VIEWER_WIDTH_DEFAULT_PCT: 33,
  SQL_VIEWER_WIDTH_MIN_PCT: 20,
  SQL_VIEWER_WIDTH_MAX_PCT: 60,

  // Detail Search modal
  DETAIL_SEARCH_HEIGHT_DEFAULT_PCT: 25,
  DETAIL_SEARCH_HEIGHT_MIN_PCT: 15,
  DETAIL_SEARCH_HEIGHT_MAX_PCT: 60,

  // Initial load delays
  INITIAL_FIT_VIEW_DELAY_MS: 150,

  // Path tracing
  MAX_NODE_VISITS_IN_PATH: 3, // Prevent infinite loops in cyclic graphs

  // Job status polling
  JOB_STATUS_POLL_INTERVAL_MS: 500,

  // JSON file size limit
  JSON_MAX_SIZE_MB: 10,
} as const;

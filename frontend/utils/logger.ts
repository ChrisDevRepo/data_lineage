/**
 * Conditional logging utility for development
 *
 * Logs are only shown in development mode.
 * In production builds, all debug/perf logs are removed.
 */

const isDev = import.meta.env.DEV;

export const logger = {
  /**
   * Debug information - only in development
   */
  debug: (...args: any[]) => {
    if (isDev) {
      console.log('[DEBUG]', ...args);
    }
  },

  /**
   * Performance metrics - only in development
   */
  perf: (...args: any[]) => {
    if (isDev) {
      console.log('[PERF]', ...args);
    }
  },

  /**
   * Warnings - shown in all environments
   */
  warn: (...args: any[]) => {
    console.warn('[WARN]', ...args);
  },

  /**
   * Errors - shown in all environments
   */
  error: (...args: any[]) => {
    console.error('[ERROR]', ...args);
  },

  /**
   * Info messages - shown in all environments
   */
  info: (...args: any[]) => {
    console.info('[INFO]', ...args);
  },
};

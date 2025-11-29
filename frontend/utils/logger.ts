/**
 * Conditional logging utility for development
 *
 * Logs are only shown in development mode.
 * In production builds, all debug/perf logs are removed.
 *
 * Set VITE_VERBOSE_LOGS=false to disable verbose logging for better performance
 */

const isDev = import.meta.env.DEV;
const verboseLogs = import.meta.env.VITE_VERBOSE_LOGS !== 'false';

export const logger = {
  /**
   * Debug information - only in development with verbose logs enabled
   */
  debug: (...args: any[]) => {
    if (isDev && verboseLogs) {
      console.log('[DEBUG]', ...args);
    }
  },

  /**
   * Performance metrics - only in development with verbose logs enabled
   */
  perf: (...args: any[]) => {
    if (isDev && verboseLogs) {
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


// FPS Monitoring (Development Only)
class FPSMonitor {
  private frames: number[] = [];
  private lastTime: number = performance.now();

  track() {
    const now = performance.now();
    const delta = now - this.lastTime;

    if (delta > 0) {
      const fps = 1000 / delta;
      this.frames.push(fps);

      // Keep only last 60 frames (1 second at 60fps)
      if (this.frames.length > 60) {
        this.frames.shift();
      }
    }

    this.lastTime = now;
  }

  getAverage(): number {
    if (this.frames.length === 0) return 0;
    const sum = this.frames.reduce((a, b) => a + b, 0);
    return Math.round(sum / this.frames.length);
  }

  reset() {
    this.frames = [];
    this.lastTime = performance.now();
  }
}

export const fpsMonitor = new FPSMonitor();

// Expose FPS tracker in development mode
if (import.meta.env.DEV) {
  // @ts-ignore
  window.__fpsMonitor = fpsMonitor;
  console.log('📊 FPS Monitor available at window.__fpsMonitor');
  console.log('   Usage: window.__fpsMonitor.getAverage()');
}

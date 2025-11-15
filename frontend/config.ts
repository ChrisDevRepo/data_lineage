/**
 * Frontend Configuration
 *
 * Centralized configuration for API URLs and other environment-specific settings.
 * Uses Vite environment variables (https://vitejs.dev/guide/env-and-mode.html)
 */

// API Base URL - defaults to empty string for relative URLs (same domain)
// In production, VITE_API_URL should be empty for same-domain API calls
// For development, it falls back to localhost
export const API_BASE_URL = import.meta.env.VITE_API_URL !== undefined 
    ? import.meta.env.VITE_API_URL 
    : (import.meta.env.DEV ? 'http://localhost:8000' : '');

// Export for easy import throughout the app
export default {
    API_BASE_URL
};

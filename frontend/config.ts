/**
 * Frontend Configuration
 *
 * Centralized configuration for API URLs and other environment-specific settings.
 * Uses Vite environment variables (https://vitejs.dev/guide/env-and-mode.html)
 */

// API Base URL - defaults to localhost for development
// In production, set VITE_API_URL in .env.production or Azure App Service configuration
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Export for easy import throughout the app
export default {
    API_BASE_URL
};

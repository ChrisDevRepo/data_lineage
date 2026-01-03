/**
 * Design Token System
 *
 * Centralized design tokens for the Data Lineage Visualizer.
 * Single source of truth for colors, typography, spacing, and visual properties.
 *
 * Usage:
 * import { tokens } from './design-tokens';
 * const myColor = tokens.colors.primary[600];
 */

export const tokens = {
  // ============================================================================
  // COLORS
  // ============================================================================
  colors: {
    // Primary Brand Color - Blue
    primary: {
      50: '#eff6ff',
      100: '#dbeafe',
      200: '#bfdbfe',
      300: '#93c5fd',
      400: '#60a5fa',
      500: '#3b82f6',
      600: '#2563eb',  // Main brand color
      700: '#1d4ed8',
      800: '#1e40af',
      900: '#1e3a8a',
    },

    // Semantic Colors
    success: {
      50: '#f0fdf4',
      100: '#dcfce7',
      200: '#bbf7d0',
      500: '#22c55e',
      600: '#16a34a',
      700: '#15803d',
      900: '#14532d',
    },

    warning: {
      50: '#fef9c3',
      100: '#fef3c7',
      400: '#facc15',
      500: '#eab308',
      600: '#ca8a04',
    },

    error: {
      50: '#fef2f2',
      100: '#fee2e2',
      500: '#ef4444',
      600: '#dc2626',
      700: '#b91c1c',
    },

    // Background Colors
    background: {
      primary: '#ffffff',       // Main white background
      secondary: '#f9fafb',     // Light gray (gray-50)
      tertiary: '#f3f4f6',      // Medium gray (gray-100)
      elevated: '#ffffff',      // Elevated panels/cards
    },

    // Text Colors
    text: {
      primary: '#1f2937',       // Dark gray (gray-800)
      secondary: '#374151',     // Medium gray (gray-700)
      tertiary: '#6b7280',      // Light gray (gray-500)
      muted: '#9ca3af',         // Very light gray (gray-400)
      inverse: '#ffffff',       // White text on dark backgrounds
    },

    // Border Colors
    border: {
      light: '#e5e7eb',         // gray-200
      medium: '#d1d5db',        // gray-300
      dark: '#9ca3af',          // gray-400
      focus: '#2563eb',         // primary-600
    },

    // Interactive States
    interactive: {
      hover: '#f3f4f6',         // gray-100
      active: '#e5e7eb',        // gray-200
      disabled: '#9ca3af',      // gray-400
      focus: '#2563eb',         // primary-600
    },

    // Highlight Colors (for traced/selected nodes)
    highlight: {
      yellow: '#facc15',        // warning-400
      yellowLight: '#fef3c7',   // warning-100
      blue: '#007acc',          // VS Code blue (keep for compatibility)
      blueLight: '#dbeafe',     // primary-100
      teal: '#4ec9b0',          // Success indicator
    },

    // Schema Colors (for data visualization nodes)
    // Expanded palette supporting 30 unique schemas
    schema: {
      colors: [
        // Tableau 10 (Primary colors)
        '#4E79A7',  // Blue
        '#F28E2B',  // Orange
        '#E15759',  // Red
        '#76B7B2',  // Teal
        '#59A14F',  // Green
        '#EDC948',  // Yellow
        '#B07AA1',  // Purple
        '#FF9DA7',  // Pink
        '#9C755F',  // Brown
        '#BAB0AC',  // Gray
        // Tableau 20 (Light variants)
        '#A0CBE8',  // Light Blue
        '#FFBE7D',  // Light Orange
        '#FF9D9A',  // Light Red
        '#86BCB6',  // Light Teal
        '#8CD17D',  // Light Green
        '#F1CE63',  // Light Yellow
        '#D4A6C8',  // Light Purple
        '#FFC2CD',  // Light Pink
        '#D7B5A6',  // Light Brown
        '#D4D4D4',  // Light Gray
        // Additional distinct colors
        '#17BECF',  // Cyan
        '#BCBD22',  // Olive
        '#9467BD',  // Dark Purple
        '#E377C2',  // Magenta
        '#7F7F7F',  // Dark Gray
        '#8C564B',  // Brown
        '#1F77B4',  // Steel Blue
        '#FF7F0E',  // Dark Orange
        '#2CA02C',  // Forest Green
        '#D62728',  // Crimson
      ],
      opacity: '30',  // For node backgrounds (append to hex)
    },

    // Overlay/Backdrop Colors
    overlay: {
      light: 'rgba(0, 0, 0, 0.5)',
      medium: 'rgba(0, 0, 0, 0.7)',
      dark: 'rgba(0, 0, 0, 0.85)',
    },
  },

  // ============================================================================
  // TYPOGRAPHY
  // ============================================================================
  typography: {
    // Font Families
    fontFamily: {
      sans: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol"',
      mono: 'Consolas, Monaco, "Andale Mono", "Ubuntu Mono", "Courier New", monospace',
    },

    // Font Sizes (rem-based for accessibility)
    fontSize: {
      xs: '0.75rem',      // 12px
      sm: '0.875rem',     // 14px
      base: '1rem',       // 16px
      lg: '1.125rem',     // 18px
      xl: '1.25rem',      // 20px
      '2xl': '1.5rem',    // 24px
      '3xl': '1.875rem',  // 30px
      '4xl': '2.25rem',   // 36px
    },

    // Font Weights
    fontWeight: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },

    // Line Heights
    lineHeight: {
      tight: 1.25,
      normal: 1.5,
      relaxed: 1.6,
      loose: 2,
    },
  },

  // ============================================================================
  // SPACING
  // ============================================================================
  spacing: {
    xs: '0.25rem',    // 4px
    sm: '0.5rem',     // 8px
    md: '0.75rem',    // 12px
    lg: '1rem',       // 16px
    xl: '1.5rem',     // 24px
    '2xl': '2rem',    // 32px
    '3xl': '3rem',    // 48px
    '4xl': '4rem',    // 64px
  },

  // ============================================================================
  // BORDERS
  // ============================================================================
  borders: {
    width: {
      none: '0',
      thin: '1px',
      medium: '2px',
      thick: '4px',
    },
    radius: {
      none: '0',
      sm: '0.25rem',    // 4px
      md: '0.375rem',   // 6px
      lg: '0.5rem',     // 8px
      xl: '0.75rem',    // 12px
      '2xl': '1rem',    // 16px
      full: '9999px',   // Fully rounded
    },
  },

  // ============================================================================
  // SHADOWS
  // ============================================================================
  shadows: {
    none: 'none',
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
    inner: 'inset 0 2px 4px 0 rgba(0, 0, 0, 0.06)',
  },

  // ============================================================================
  // TRANSITIONS
  // ============================================================================
  transitions: {
    duration: {
      fast: '150ms',
      normal: '200ms',
      slow: '300ms',
      slower: '500ms',
    },
    timing: {
      linear: 'linear',
      easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
      easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
      easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
    },
  },

  // ============================================================================
  // Z-INDEX SCALE
  // ============================================================================
  zIndex: {
    base: 0,
    dropdown: 10,
    sticky: 20,
    fixed: 30,
    overlay: 40,
    modal: 50,
    popover: 60,
    toast: 70,
    tooltip: 80,
  },

  // ============================================================================
  // COMPONENT-SPECIFIC TOKENS
  // ============================================================================
  components: {
    // Button heights
    button: {
      height: {
        sm: '2rem',     // 32px
        md: '2.5rem',   // 40px
        lg: '3rem',     // 48px
      },
      padding: {
        sm: '0.5rem 0.75rem',   // 8px 12px
        md: '0.75rem 1rem',     // 12px 16px
        lg: '1rem 1.5rem',      // 16px 24px
      },
    },

    // Input heights (match button heights)
    input: {
      height: {
        sm: '2rem',
        md: '2.5rem',
        lg: '3rem',
      },
    },

    // Modal sizes
    modal: {
      width: {
        sm: '24rem',    // 384px
        md: '32rem',    // 512px
        lg: '48rem',    // 768px
        xl: '64rem',    // 1024px
        full: '100%',
      },
    },

    // Icon sizes
    icon: {
      xs: '1rem',       // 16px
      sm: '1.25rem',    // 20px
      md: '1.5rem',     // 24px
      lg: '2rem',       // 32px
      xl: '3rem',       // 48px
    },
  },
};

// ============================================================================
// TAILWIND CSS VARIABLES (for use in Tailwind config)
// ============================================================================
export const tailwindColors = {
  primary: tokens.colors.primary,
  success: tokens.colors.success,
  warning: tokens.colors.warning,
  error: tokens.colors.error,
};

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Get schema color with opacity
 * @param index - Schema index (0-29, wraps around for more)
 * @param opacity - Opacity value (0-100), defaults to 30
 */
export function getSchemaColor(index: number, opacity: number = 30): string {
  const color = tokens.colors.schema.colors[index % 30];
  const opacityHex = Math.round((opacity / 100) * 255).toString(16).padStart(2, '0');
  return `${color}${opacityHex}`;
}

/**
 * Get transition CSS string
 * @param properties - CSS properties to transition
 * @param duration - Duration key from tokens
 * @param timing - Timing function key from tokens
 */
export function getTransition(
  properties: string[],
  duration: keyof typeof tokens.transitions.duration = 'normal',
  timing: keyof typeof tokens.transitions.timing = 'easeInOut'
): string {
  const durationValue = tokens.transitions.duration[duration];
  const timingValue = tokens.transitions.timing[timing];
  return properties.map(prop => `${prop} ${durationValue} ${timingValue}`).join(', ');
}

export default tokens;

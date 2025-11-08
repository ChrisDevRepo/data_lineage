/**
 * Confidence Icon Utilities
 *
 * Single source of truth for confidence level icons and thresholds.
 * Used by both CustomNode badge and description formatting.
 *
 * v2.1.0 Simplified Model: Only 3 categories
 * - High (85-100): ✅ Good
 * - Medium (75): ⚠️ Acceptable
 * - Low/Failed (0): ❌ Failed
 */

export interface ConfidenceLevel {
    icon: string;
    label: string;
    title: string;
}

/**
 * Get confidence level for a given confidence score.
 *
 * @param confidence - Confidence score (0-100 or 0.0-1.0)
 * @returns Confidence level with icon, label, and title
 */
export function getConfidenceLevel(confidence: number): ConfidenceLevel {
    // Support both formats: discrete (0, 75, 85, 100) and decimal (0.0-1.0)
    const conf = confidence > 1 ? confidence : confidence * 100;

    // 3 categories (simplified from 4)
    if (conf >= 80) {
        return {
            icon: '✅',
            label: 'Good',
            title: '✅ Good (85-100%)'
        };
    } else if (conf >= 70) {
        return {
            icon: '⚠️',
            label: 'Acceptable',
            title: '⚠️ Acceptable (75%)'
        };
    } else {
        return {
            icon: '❌',
            label: 'Failed',
            title: '❌ Failed (0%)'
        };
    }
}

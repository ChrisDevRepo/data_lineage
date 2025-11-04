/**
 * localStorage Utilities for Filter Persistence
 *
 * Saves user filter preferences (schemas, types, hideUnrelated) to localStorage
 * so they persist across page reloads.
 */

const STORAGE_KEY_PREFIX = 'lineage_viz_';

export const StorageKeys = {
    SELECTED_SCHEMAS: `${STORAGE_KEY_PREFIX}selected_schemas`,
    SELECTED_TYPES: `${STORAGE_KEY_PREFIX}selected_types`,
    HIDE_UNRELATED: `${STORAGE_KEY_PREFIX}hide_unrelated`,
} as const;

/**
 * Save selected schemas to localStorage
 */
export const saveSelectedSchemas = (schemas: Set<string>): void => {
    try {
        const schemasArray = Array.from(schemas);
        localStorage.setItem(StorageKeys.SELECTED_SCHEMAS, JSON.stringify(schemasArray));
    } catch (error) {
        console.warn('[localStorage] Failed to save selected schemas:', error);
    }
};

/**
 * Load selected schemas from localStorage
 */
export const loadSelectedSchemas = (): string[] | null => {
    try {
        const stored = localStorage.getItem(StorageKeys.SELECTED_SCHEMAS);
        if (stored) {
            return JSON.parse(stored);
        }
        return null;
    } catch (error) {
        console.warn('[localStorage] Failed to load selected schemas:', error);
        return null;
    }
};

/**
 * Save selected types to localStorage
 */
export const saveSelectedTypes = (types: Set<string>): void => {
    try {
        const typesArray = Array.from(types);
        localStorage.setItem(StorageKeys.SELECTED_TYPES, JSON.stringify(typesArray));
    } catch (error) {
        console.warn('[localStorage] Failed to save selected types:', error);
    }
};

/**
 * Load selected types from localStorage
 */
export const loadSelectedTypes = (): string[] | null => {
    try {
        const stored = localStorage.getItem(StorageKeys.SELECTED_TYPES);
        if (stored) {
            return JSON.parse(stored);
        }
        return null;
    } catch (error) {
        console.warn('[localStorage] Failed to load selected types:', error);
        return null;
    }
};

/**
 * Save hideUnrelated preference to localStorage
 */
export const saveHideUnrelated = (hide: boolean): void => {
    try {
        localStorage.setItem(StorageKeys.HIDE_UNRELATED, JSON.stringify(hide));
    } catch (error) {
        console.warn('[localStorage] Failed to save hideUnrelated:', error);
    }
};

/**
 * Load hideUnrelated preference from localStorage
 */
export const loadHideUnrelated = (): boolean | null => {
    try {
        const stored = localStorage.getItem(StorageKeys.HIDE_UNRELATED);
        if (stored !== null) {
            return JSON.parse(stored);
        }
        return null;
    } catch (error) {
        console.warn('[localStorage] Failed to load hideUnrelated:', error);
        return null;
    }
};

/**
 * Clear all filter preferences from localStorage
 */
export const clearFilterPreferences = (): void => {
    try {
        localStorage.removeItem(StorageKeys.SELECTED_SCHEMAS);
        localStorage.removeItem(StorageKeys.SELECTED_TYPES);
        localStorage.removeItem(StorageKeys.HIDE_UNRELATED);
        console.log('[localStorage] Filter preferences cleared');
    } catch (error) {
        console.warn('[localStorage] Failed to clear filter preferences:', error);
    }
};

/**
 * Wildcard matching function - only supports * wildcard (no regex)
 * @param text - The text to match against
 * @param pattern - The wildcard pattern (e.g., "*_TMP", "TEMP_*", "*_BAK")
 * @returns true if text matches the pattern
 */
export const matchesWildcard = (text: string, pattern: string): boolean => {
    // Split pattern by * and escape regex special characters in each part
    const regexPattern = pattern
        .split('*')
        .map(part => part.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'))
        .join('.*');
    return new RegExp(`^${regexPattern}$`, 'i').test(text);
};

/**
 * Save exclusion patterns to localStorage
 */
export const saveExclusionPatterns = (patterns: string): void => {
    try {
        localStorage.setItem(`${STORAGE_KEY_PREFIX}exclusion_patterns`, patterns);
    } catch (error) {
        console.warn('[localStorage] Failed to save exclusion patterns:', error);
    }
};

/**
 * Load exclusion patterns from localStorage
 */
export const loadExclusionPatterns = (): string | null => {
    try {
        return localStorage.getItem(`${STORAGE_KEY_PREFIX}exclusion_patterns`);
    } catch (error) {
        console.warn('[localStorage] Failed to load exclusion patterns:', error);
        return null;
    }
};

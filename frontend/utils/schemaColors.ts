/**
 * Schema Color Palette System (v2.0 - HSL Color Theory)
 *
 * Requirements:
 * 1. Good contrast between different departments (startup, enterprise, metrics)
 * 2. Same color family for department layers (staging, transformation, consumption)
 * 3. Staging = lightest (75%), Transformation = medium (63%), Consumption = darkest (51%)
 * 4. All colors remain bright and readable for text visibility
 * 5. Colors persist across page reloads using localStorage
 * 6. Based on HSL color theory for perceptual uniformity
 */

import { logger } from './logger';

// HSL-based color families with 3 brightness levels
// Each family uses same hue and saturation, varying only lightness
// 20 color families for maximum variety across many departments
const colorFamilies = {
  // Original 10 families
  blue: ['#8dc5f5', '#5da9f0', '#2d8deb'],      // HSL: (215°, 80%, 75%) -> 63% -> 51%
  green: ['#88e5b8', '#54d69e', '#20c784'],     // HSL: (145°, 75%, 72%) -> 60% -> 48%
  purple: ['#b399f0', '#9166e5', '#6f33da'],    // HSL: (270°, 75%, 73%) -> 61% -> 49%
  orange: ['#ffb380', '#ff954d', '#ff771a'],    // HSL: (25°, 100%, 75%) -> 63% -> 55%
  pink: ['#f5a3d0', '#ed70b3', '#e53d96'],      // HSL: (330°, 80%, 75%) -> 65% -> 55%
  teal: ['#70e8d4', '#3dd9bf', '#0acaaa'],      // HSL: (170°, 75%, 67%) -> 57% -> 47%
  red: ['#ff9999', '#ff6666', '#ff3333'],       // HSL: (0°, 100%, 80%) -> 70% -> 60%
  indigo: ['#a3a8f5', '#7078ed', '#3d48e5'],    // HSL: (235°, 80%, 75%) -> 65% -> 55%
  amber: ['#ffd966', '#ffc933', '#ffb800'],     // HSL: (45°, 100%, 70%) -> 60% -> 50%
  cyan: ['#80e5ff', '#4dd9ff', '#1accff'],      // HSL: (195°, 100%, 75%) -> 65% -> 55%

  // Additional 10 families for backup
  lime: ['#c4f566', '#a6ed33', '#88d600'],      // HSL: (75°, 90%, 68%) -> 58% -> 48%
  magenta: ['#f580f5', '#ed4ded', '#e01ae0'],   // HSL: (300°, 85%, 72%) -> 62% -> 52%
  violet: ['#d1a3f5', '#ba70ed', '#a33de5'],    // HSL: (285°, 80%, 75%) -> 65% -> 55%
  coral: ['#ff9e80', '#ff6b4d', '#ff381a'],     // HSL: (10°, 100%, 75%) -> 63% -> 55%
  emerald: ['#66f5b8', '#33ed9e', '#00d684'],   // HSL: (155°, 90%, 68%) -> 58% -> 48%
  sky: ['#80d4ff', '#4dc2ff', '#1ab0ff'],       // HSL: (200°, 100%, 75%) -> 65% -> 55%
  rose: ['#ffa3c4', '#ff70a6', '#ff3d88'],      // HSL: (340°, 100%, 75%) -> 65% -> 55%
  lavender: ['#d4c4f5', '#ba9eed', '#9e70e5'],  // HSL: (260°, 75%, 75%) -> 65% -> 55%
  mint: ['#99f5d4', '#66eda6', '#33d677'],      // HSL: (150°, 85%, 75%) -> 63% -> 51%
  peach: ['#ffc499', '#ffad66', '#ff9633'],     // HSL: (30°, 100%, 75%) -> 65% -> 55%
};

const colorFamilyNames = Object.keys(colorFamilies) as Array<keyof typeof colorFamilies>;

// Layer keywords for automatic detection
const layerKeywords = {
  staging: ['staging', 'stg', 'raw', 'landing', 'source', 'bronze'],
  transformation: ['transformation', 'transform', 'tfm', 'processed', 'intermediate', 'silver'],
  consumption: ['consumption', 'cons', 'mart', 'final', 'presentation', 'pub', 'published', 'gold'],
};

// Detect layer type from schema name
function detectLayer(schemaName: string): 'staging' | 'transformation' | 'consumption' | null {
  const lowerName = schemaName.toLowerCase();

  for (const keyword of layerKeywords.staging) {
    if (lowerName.includes(keyword)) return 'staging';
  }
  for (const keyword of layerKeywords.transformation) {
    if (lowerName.includes(keyword)) return 'transformation';
  }
  for (const keyword of layerKeywords.consumption) {
    if (lowerName.includes(keyword)) return 'consumption';
  }

  return null;
}

// Extract department/domain from schema name (after layer indicator)
// Pattern: LAYER_DEPARTMENT (e.g., "staging_startup", "transformation_enterprisemetric", "consumption_finance")
function extractDepartment(schemaName: string): string {
  const lowerName = schemaName.toLowerCase();

  // Split by underscores and dashes to identify parts
  const parts = lowerName.split(/[_-]+/).filter(p => p.length > 0);

  // Find first layer keyword in the parts
  let layerPartIndex = -1;
  for (let i = 0; i < parts.length; i++) {
    const part = parts[i];
    // Check if this part is a layer keyword
    for (const layerType of Object.values(layerKeywords)) {
      if (layerType.includes(part)) {
        layerPartIndex = i;
        break;
      }
    }
    if (layerPartIndex >= 0) break;
  }

  // If layer found at beginning, department is everything AFTER it
  if (layerPartIndex === 0 && parts.length > 1) {
    return parts.slice(1).join('');
  }

  // Fallback: If layer found elsewhere, try substring matching
  for (const layer of Object.values(layerKeywords).flat()) {
    const layerWithSeparator = layer + '_';
    const index = lowerName.indexOf(layerWithSeparator);
    if (index === 0) {
      // Layer at start, extract everything after it
      return lowerName.substring(layerWithSeparator.length).replace(/[_-]/g, '').trim();
    }
  }

  // No clear layer prefix found, use whole name as department
  return parts.join('');
}

// Simple hash function for consistent color assignment
function hashString(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return Math.abs(hash);
}

// Storage key for persisting color assignments (v2 for new HSL system)
const STORAGE_KEY = 'schema_color_assignments_v2';

// Load saved color assignments from localStorage
function loadColorAssignments(): Record<string, { family: string; level: number }> {
  try {
    const saved = localStorage.getItem(STORAGE_KEY);
    return saved ? JSON.parse(saved) : {};
  } catch (error) {
    console.error('[SchemaColors] Failed to load saved colors:', error);
    return {};
  }
}

// Save color assignments to localStorage
function saveColorAssignments(assignments: Record<string, { family: string; level: number }>) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(assignments));
  } catch (error) {
    console.error('[SchemaColors] Failed to save colors:', error);
  }
}

/**
 * Generate color palette for schemas with intelligent layer detection
 * @param schemas - Array of schema names
 * @returns Map of schema name to color hex code
 */
export function generateSchemaColors(schemas: string[]): Map<string, string> {
  const colorMap = new Map<string, string>();
  const savedAssignments = loadColorAssignments();
  const departmentColorFamily = new Map<string, string>();
  const usedFamilies = new Set<string>();
  let familyIndex = 0;

  // Generating schema colors

  // Track statistics for logging
  const stats = {
    newAssignments: 0,
    fromCache: 0,
    byLayer: { staging: 0, transformation: 0, consumption: 0, unknown: 0 }
  };

  // Process each schema
  schemas.forEach(schema => {
    // Check if we have a saved assignment
    if (savedAssignments[schema]) {
      const { family, level } = savedAssignments[schema];
      if (colorFamilies[family as keyof typeof colorFamilies]) {
        const color = colorFamilies[family as keyof typeof colorFamilies][level];
        colorMap.set(schema, color);
        departmentColorFamily.set(extractDepartment(schema), family);
        usedFamilies.add(family);
        stats.fromCache++;
        return;
      }
    }

    // Detect layer and department
    const layer = detectLayer(schema);
    const department = extractDepartment(schema);

    // Determine color level based on layer
    let colorLevel = 1; // Default: middle brightness (transformation)
    if (layer === 'staging') {
      colorLevel = 0;  // Lightest (75% lightness)
      stats.byLayer.staging++;
    } else if (layer === 'transformation') {
      colorLevel = 1;  // Medium (63% lightness)
      stats.byLayer.transformation++;
    } else if (layer === 'consumption') {
      colorLevel = 2;  // Darkest (51% lightness)
      stats.byLayer.consumption++;
    } else {
      stats.byLayer.unknown++;
    }

    // Assign color family based on department
    let colorFamily: string;

    if (departmentColorFamily.has(department)) {
      // Reuse color family for same department
      colorFamily = departmentColorFamily.get(department)!;
    } else {
      // Assign new color family
      // First try to use hash-based selection for consistency
      const hash = hashString(department);
      const preferredIndex = hash % colorFamilyNames.length;
      const preferredFamily = colorFamilyNames[preferredIndex];

      if (!usedFamilies.has(preferredFamily)) {
        colorFamily = preferredFamily;
      } else {
        // Find next available family
        let found = false;
        for (let i = 0; i < colorFamilyNames.length; i++) {
          const testFamily = colorFamilyNames[(preferredIndex + i) % colorFamilyNames.length];
          if (!usedFamilies.has(testFamily)) {
            colorFamily = testFamily;
            found = true;
            break;
          }
        }
        if (!found) {
          // All families used, cycle through
          colorFamily = colorFamilyNames[familyIndex % colorFamilyNames.length];
          familyIndex++;
        }
      }

      departmentColorFamily.set(department, colorFamily);
      usedFamilies.add(colorFamily);
    }

    // Get color from family and level
    const color = colorFamilies[colorFamily as keyof typeof colorFamilies][colorLevel];
    colorMap.set(schema, color);

    // Save assignment for persistence
    savedAssignments[schema] = { family: colorFamily, level: colorLevel };
    stats.newAssignments++;
  });

  // Save all assignments for persistence across reloads
  saveColorAssignments(savedAssignments);

  // Color assignment complete (debug logs removed for cleaner console)

  return colorMap;
}

/**
 * Clear saved color assignments (useful for testing or reset)
 */
export function clearSavedColors() {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch (error) {
    console.error('[SchemaColors] Failed to clear saved colors:', error);
  }
}

/**
 * Create schema color map (alias for backward compatibility)
 */
export function createSchemaColorMap(schemas: string[]): Map<string, string> {
  return generateSchemaColors(schemas);
}

/**
 * Get color palette information for debugging/documentation
 */
export function getColorPaletteInfo() {
  return {
    families: colorFamilyNames,
    levelsPerFamily: 3,
    lightnessValues: ['75% (staging)', '63% (transformation)', '51% (consumption)'],
    totalColors: colorFamilyNames.length * 3,
    colorTheory: 'HSL-based with consistent hue/saturation, varying lightness',
    persistence: 'localStorage with key: ' + STORAGE_KEY,
  };
}

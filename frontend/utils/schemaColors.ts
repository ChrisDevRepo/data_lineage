/**
 * Schema Color Palette System
 *
 * Requirements:
 * 1. Good contrast between different departments (startup, enterprise, metrics)
 * 2. Same color family for department layers (staging, transformation, consumption)
 * 3. Staging = lightest, Consumption = darkest (but still bright/readable)
 * 4. Colors persist across page reloads
 */

// Color families with 3 brightness levels (light to dark)
const colorFamilies = {
  blue: ['#93c5fd', '#3b82f6', '#1d4ed8'],      // Light blue -> Blue -> Dark blue
  green: ['#86efac', '#22c55e', '#15803d'],     // Light green -> Green -> Dark green
  purple: ['#c4b5fd', '#8b5cf6', '#6d28d9'],    // Light purple -> Purple -> Dark purple
  orange: ['#fdba74', '#f97316', '#c2410c'],    // Light orange -> Orange -> Dark orange
  pink: ['#f9a8d4', '#ec4899', '#be185d'],      // Light pink -> Pink -> Dark pink
  teal: ['#5eead4', '#14b8a6', '#0f766e'],      // Light teal -> Teal -> Dark teal
  red: ['#fca5a5', '#ef4444', '#b91c1c'],       // Light red -> Red -> Dark red
  indigo: ['#a5b4fc', '#6366f1', '#4338ca'],    // Light indigo -> Indigo -> Dark indigo
  yellow: ['#fde047', '#eab308', '#a16207'],    // Light yellow -> Yellow -> Dark yellow
  cyan: ['#67e8f9', '#06b6d4', '#0e7490'],      // Light cyan -> Cyan -> Dark cyan
};

const colorFamilyNames = Object.keys(colorFamilies) as Array<keyof typeof colorFamilies>;

// Layer keywords for automatic detection
const layerKeywords = {
  staging: ['staging', 'stg', 'raw', 'landing', 'source'],
  transformation: ['transformation', 'transform', 'tfm', 'processed', 'intermediate'],
  consumption: ['consumption', 'cons', 'mart', 'final', 'presentation', 'pub', 'published'],
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

// Extract department/domain from schema name (before layer indicator)
function extractDepartment(schemaName: string): string {
  const lowerName = schemaName.toLowerCase();

  // Try to find layer keyword and extract department before it
  for (const layer of Object.values(layerKeywords).flat()) {
    const index = lowerName.indexOf(layer);
    if (index > 0) {
      // Extract part before layer keyword, remove separators
      return lowerName.substring(0, index).replace(/[_-]/g, '').trim();
    }
  }

  // No layer found, use whole name as department
  return lowerName.replace(/[_-]/g, '').trim();
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

// Storage key for persisting color assignments
const STORAGE_KEY = 'schema_color_assignments';

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
        return;
      }
    }

    // Detect layer and department
    const layer = detectLayer(schema);
    const department = extractDepartment(schema);

    // Determine color level based on layer
    let colorLevel = 1; // Default: middle brightness
    if (layer === 'staging') colorLevel = 0; // Lightest
    else if (layer === 'transformation') colorLevel = 1; // Medium
    else if (layer === 'consumption') colorLevel = 2; // Darkest

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
  });

  // Save all assignments
  saveColorAssignments(savedAssignments);

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

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

// HSL-based color families with 3 brightness levels
// Each family uses same hue and saturation, varying only lightness
const colorFamilies = {
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
    console.log(`[SchemaColors] Saved ${Object.keys(assignments).length} color assignments to localStorage`);
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

  console.log(`[SchemaColors] Generating colors for ${schemas.length} schemas using HSL color theory`);

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

  // Log detailed statistics
  console.log(`[SchemaColors] ✓ Color assignment complete`);
  console.log(`[SchemaColors]   Total schemas: ${colorMap.size}`);
  console.log(`[SchemaColors]   Color families used: ${usedFamilies.size}/${colorFamilyNames.length}`);
  console.log(`[SchemaColors]   From cache: ${stats.fromCache} | New: ${stats.newAssignments}`);
  console.log(`[SchemaColors]   By layer: Staging=${stats.byLayer.staging}, Transformation=${stats.byLayer.transformation}, Consumption=${stats.byLayer.consumption}, Unknown=${stats.byLayer.unknown}`);

  // Show sample assignments for first 5 schemas (for debugging)
  if (schemas.length > 0 && stats.newAssignments > 0) {
    console.log(`[SchemaColors] Sample assignments:`);
    let sampleCount = 0;
    for (const schema of schemas) {
      if (sampleCount >= 5) break;
      const assignment = savedAssignments[schema];
      if (assignment) {
        const layer = detectLayer(schema);
        const dept = extractDepartment(schema);
        const color = colorMap.get(schema);
        console.log(`[SchemaColors]   "${schema}" -> dept="${dept}", layer="${layer || 'unknown'}", family="${assignment.family}", level=${assignment.level}, color="${color}"`);
        sampleCount++;
      }
    }
  }

  return colorMap;
}

/**
 * Clear saved color assignments (useful for testing or reset)
 */
export function clearSavedColors() {
  try {
    localStorage.removeItem(STORAGE_KEY);
    console.log('[SchemaColors] Cleared all saved color assignments');
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

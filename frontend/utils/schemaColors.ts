/**
 * Smart Schema Color Assignment
 *
 * Assigns colors to schemas based on their category and layer.
 * Related schemas (same department, different layers) get similar colors.
 *
 * Pattern: STAGING -> Dark (30%), TRANSFORMATION -> Medium (50%), CONSUMPTION -> Bright (70%)
 *
 * Example:
 * - STAGING_FINANCE -> Dark Blue (30% brightness)
 * - TRANSFORMATION_FINANCE -> Medium Blue (50% brightness)
 * - CONSUMPTION_FINANCE -> Bright Blue (70% brightness)
 */

// Color families with Light (CONSUMPTION), Medium (TRANSFORMATION), Dark (STAGING) variants
// Each family maintains the SAME HUE, only varying in brightness/saturation
// CONSUMPTION = Light (70% brightness), TRANSFORMATION = Medium (50%), STAGING = Dark (30%)
// Brightness pattern: STAGING (darkest) -> TRANSFORMATION (medium) -> CONSUMPTION (brightest)
// 20 distinct color families to ensure each department gets unique colors
const COLOR_FAMILIES = [
  // Primary colors (0-9)
  ['#80B3E6', '#5B9BD5', '#3D7AB6'],  // 0. Blue (hue: 210°)
  ['#FFB366', '#FF9933', '#CC7A29'],  // 1. Orange (hue: 30°)
  ['#FF8080', '#E15759', '#B34545'],  // 2. Red (hue: 0°)
  ['#66CCCC', '#4DB8B8', '#339999'],  // 3. Teal/Cyan (hue: 180°)
  ['#80CC66', '#5FB34D', '#4D9939'],  // 4. Green (hue: 120°)
  ['#FFD966', '#FFC947', '#CCA336'],  // 5. Yellow (hue: 45°)
  ['#C299CC', '#A673B3', '#805299'],  // 6. Purple (hue: 280°)
  ['#FF99CC', '#E673A3', '#B35280'],  // 7. Pink/Magenta (hue: 330°)
  ['#66B3FF', '#3399FF', '#2973CC'],  // 8. Sky Blue (hue: 210°, high saturation)
  ['#C2A680', '#9C8566', '#7A6B52'],  // 9. Brown (hue: 30°, low saturation)

  // Extended colors (10-19)
  ['#99E699', '#66CC66', '#4DA64D'],  // 10. Lime Green (hue: 120°, high saturation)
  ['#FFCC80', '#FFB366', '#CC8F52'],  // 11. Amber (hue: 35°)
  ['#D999CC', '#B866A6', '#944D85'],  // 12. Orchid (hue: 310°)
  ['#80D9D9', '#4DC2C2', '#39A3A3'],  // 13. Aqua (hue: 180°, high saturation)
  ['#D9B380', '#B8935C', '#997A4D'],  // 14. Tan (hue: 30°)
  ['#B8A3D9', '#9973B8', '#735299'],  // 15. Lavender (hue: 280°, lighter)
  ['#FFD966', '#FFBF40', '#CCA336'],  // 16. Gold (hue: 45°)
  ['#80FFCC', '#4DFFB3', '#33CC8F'],  // 17. Mint (hue: 160°)
  ['#FFB399', '#FF8566', '#CC6652'],  // 18. Coral (hue: 15°, red-orange)
  ['#B3B3B3', '#8C8C8C', '#666666'],  // 19. Gray (no hue)
];

type LayerType = 'STAGING' | 'TRANSFORMATION' | 'CONSUMPTION' | 'OTHER';

interface SchemaCategory {
  baseName: string;
  layers: Map<LayerType, string>;  // layer -> schema name
}

/**
 * Extract category and layer from schema name
 *
 * Split on FIRST underscore only, case-insensitive layer matching
 *
 * Examples:
 * - STAGING_FINANCE -> { baseName: 'FINANCE', layer: 'STAGING' }
 * - CONSUMPTION_PRIMA -> { baseName: 'PRIMA', layer: 'CONSUMPTION' }
 * - Consumption_FinanceHub -> { baseName: 'FinanceHub', layer: 'CONSUMPTION' }
 * - Transformation_FinanceHub -> { baseName: 'FinanceHub', layer: 'TRANSFORMATION' }
 * - dbo -> { baseName: 'dbo', layer: 'OTHER' }
 */
function parseSchemaName(schema: string): { baseName: string; layer: LayerType } {
  // Split on first underscore only
  const firstUnderscoreIndex = schema.indexOf('_');

  if (firstUnderscoreIndex === -1) {
    // No underscore, treat as OTHER
    return {
      layer: 'OTHER',
      baseName: schema,
    };
  }

  const layerPart = schema.substring(0, firstUnderscoreIndex);
  const baseName = schema.substring(firstUnderscoreIndex + 1);

  // Case-insensitive layer matching
  const layerUpper = layerPart.toUpperCase();

  if (layerUpper === 'STAGING' || layerUpper === 'TRANSFORMATION' || layerUpper === 'CONSUMPTION') {
    return {
      layer: layerUpper as LayerType,
      baseName: baseName,  // Keep original casing for base name
    };
  }

  // Not a recognized layer, treat entire schema as base name
  return {
    layer: 'OTHER',
    baseName: schema,
  };
}

/**
 * Create schema color map with smart grouping
 *
 * @param schemas - Array of schema names
 * @returns Map of schema name to hex color
 */
export function createSchemaColorMap(schemas: string[]): Map<string, string> {
  // Group schemas by category (case-insensitive base name matching)
  const categories = new Map<string, SchemaCategory>();

  for (const schema of schemas) {
    const { baseName, layer } = parseSchemaName(schema);

    // Normalize base name to uppercase for grouping (case-insensitive matching)
    const normalizedBaseName = baseName.toUpperCase();

    if (!categories.has(normalizedBaseName)) {
      categories.set(normalizedBaseName, {
        baseName: normalizedBaseName,
        layers: new Map(),
      });
    }

    categories.get(normalizedBaseName)!.layers.set(layer, schema);
  }

  // Assign color families to categories
  const colorMap = new Map<string, string>();
  const sortedCategories = Array.from(categories.values()).sort((a, b) =>
    a.baseName.localeCompare(b.baseName)
  );

  sortedCategories.forEach((category, index) => {
    const colorFamily = COLOR_FAMILIES[index % COLOR_FAMILIES.length];

    // Assign colors based on layer
    category.layers.forEach((schema, layer) => {
      let color: string;

      switch (layer) {
        case 'STAGING':
          color = colorFamily[2];  // Dark (30% brightness - darkest)
          break;
        case 'TRANSFORMATION':
          color = colorFamily[1];  // Medium (50% brightness)
          break;
        case 'CONSUMPTION':
          color = colorFamily[0];  // Light (70% brightness - brightest)
          break;
        default:
          color = colorFamily[1];  // Medium for OTHER
      }

      colorMap.set(schema, color);
    });
  });

  return colorMap;
}

/**
 * Get color for a schema (backward compatibility)
 *
 * @param schemaColorMap - Schema to color map
 * @param schema - Schema name
 * @returns Hex color string
 */
export function getColorForSchema(schemaColorMap: Map<string, string>, schema: string): string {
  return schemaColorMap.get(schema) || '#7f7f7f';  // Default gray
}

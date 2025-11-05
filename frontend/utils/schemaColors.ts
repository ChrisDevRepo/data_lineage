/**
 * Smart Schema Color Assignment
 *
 * Assigns colors to schemas based on their category and layer.
 * Related schemas (same department, different layers) get similar colors.
 *
 * Pattern: STAGING -> Light (65%), TRANSFORMATION -> Medium (55%), CONSUMPTION -> Dark (45%)
 * Narrow 20% brightness range ensures colors look very similar while still distinguishable
 *
 * Example:
 * - STAGING_FINANCE -> Light Blue (65% lightness)
 * - TRANSFORMATION_FINANCE -> Medium Blue (55% lightness)
 * - CONSUMPTION_FINANCE -> Dark Blue (45% lightness)
 */

// Color families with Light (STAGING), Medium (TRANSFORMATION), Dark (CONSUMPTION) variants
// Each family maintains the SAME HUE AND SATURATION, only varying in lightness (brightness)
// STAGING = Light (65% lightness), TRANSFORMATION = Medium (55% lightness), CONSUMPTION = Dark (45% lightness)
// Lightness pattern: STAGING (brightest) -> TRANSFORMATION (medium) -> CONSUMPTION (darkest)
// Narrow 20% range (65%-45%) ensures colors look very similar while still distinguishable
// All colors in a family have identical hue and saturation for visual consistency
// 20 distinct color families to ensure each department gets unique colors
const COLOR_FAMILIES = [
  // Primary colors (0-9)
  ['#67A6E4', '#3C8CDD', '#2273C3'],  // 0. Blue (hue: 210°, sat: 70%)
  ['#E9A663', '#E28C36', '#C9731D'],  // 1. Orange (hue: 30°, sat: 75%)
  ['#E46767', '#DD3C3C', '#C32222'],  // 2. Red (hue: 0°, sat: 70%)
  ['#70DBDB', '#47D1D1', '#2EB8B8'],  // 3. Teal/Cyan (hue: 180°, sat: 60%)
  ['#75D775', '#4DCB4D', '#34B234'],  // 4. Green (hue: 120°, sat: 55%)
  ['#E9D263', '#E2C636', '#C9AC1D'],  // 5. Yellow (hue: 50°, sat: 75%)
  ['#B579D2', '#9F53C6', '#8639AC'],  // 6. Purple (hue: 280°, sat: 50%)
  ['#E06CA6', '#D7428C', '#BD2873'],  // 7. Pink/Magenta (hue: 330°, sat: 65%)
  ['#63BCE9', '#36A9E2', '#1D8FC9'],  // 8. Sky Blue (hue: 200°, sat: 75%)
  ['#CE9F7E', '#C08459', '#A66A3F'],  // 9. Brown (hue: 25°, sat: 45%)

  // Extended colors (10-19)
  ['#A6DB70', '#8CD147', '#73B82E'],  // 10. Lime Green (hue: 90°, sat: 60%)
  ['#E4BB67', '#DDA73C', '#C38E22'],  // 11. Amber (hue: 40°, sat: 70%)
  ['#D775C6', '#CB4DB6', '#B2349D'],  // 12. Orchid (hue: 310°, sat: 55%)
  ['#6CE0D6', '#42D7CA', '#28BDB1'],  // 13. Aqua (hue: 175°, sat: 65%)
  ['#D2AD79', '#C69653', '#AC7C39'],  // 14. Tan (hue: 35°, sat: 50%)
  ['#A679D2', '#8C53C6', '#7339AC'],  // 15. Lavender (hue: 270°, sat: 50%)
  ['#E9C763', '#E2B736', '#C99E1D'],  // 16. Gold (hue: 45°, sat: 75%)
  ['#70DBB8', '#47D1A3', '#2EB88A'],  // 17. Mint (hue: 160°, sat: 60%)
  ['#E48767', '#DD643C', '#C34B22'],  // 18. Coral (hue: 15°, sat: 70%)
  ['#A6A6A6', '#8C8C8C', '#737373'],  // 19. Gray (hue: 0°, sat: 0%)
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
 * Schema naming convention: LAYER_DEPARTMENT
 * - First part (LAYER): determines brightness (STAGING, TRANSFORMATION, CONSUMPTION)
 * - Second part (DEPARTMENT): determines color family (STARTUP, ENTERPRISE, METRIC, etc.)
 *
 * Example:
 * - STAGING_STARTUP, TRANSFORMATION_STARTUP, CONSUMPTION_STARTUP → all use ORANGE family, different brightness
 * - STAGING_ENTERPRISE, TRANSFORMATION_ENTERPRISE, CONSUMPTION_ENTERPRISE → all use BLUE family, different brightness
 *
 * @param schemas - Array of schema names
 * @returns Map of schema name to hex color
 */
export function createSchemaColorMap(schemas: string[]): Map<string, string> {
  // Group schemas by department (base name after underscore)
  // All schemas with same department get same color family, but different brightness
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

  // Assign ONE color family per department (e.g., all STARTUP schemas get orange)
  const colorMap = new Map<string, string>();
  const sortedCategories = Array.from(categories.values()).sort((a, b) =>
    a.baseName.localeCompare(b.baseName)
  );

  sortedCategories.forEach((category, index) => {
    // Each department gets ONE color family (same hue & saturation, varies only in lightness)
    const colorFamily = COLOR_FAMILIES[index % COLOR_FAMILIES.length];

    // Assign colors based on layer
    category.layers.forEach((schema, layer) => {
      let color: string;

      switch (layer) {
        case 'STAGING':
          color = colorFamily[0];  // Light (75% lightness - brightest)
          break;
        case 'TRANSFORMATION':
          color = colorFamily[1];  // Medium (55% lightness)
          break;
        case 'CONSUMPTION':
          color = colorFamily[2];  // Dark (35% lightness - darkest)
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

/**
 * Smart Schema Color Assignment
 *
 * Assigns colors to schemas based on their category and layer.
 * Related schemas (same department, different layers) get similar colors.
 *
 * Pattern: STAGING -> Light (60%), TRANSFORMATION -> Medium (55%), CONSUMPTION -> Dark (50%)
 * Very narrow 10% brightness range ensures colors look nearly identical while still distinguishable
 *
 * Example:
 * - STAGING_FINANCE -> Light Blue (60% lightness)
 * - TRANSFORMATION_FINANCE -> Medium Blue (55% lightness)
 * - CONSUMPTION_FINANCE -> Dark Blue (50% lightness)
 */

// Color families with Light (STAGING), Medium (TRANSFORMATION), Dark (CONSUMPTION) variants
// Each family maintains the SAME HUE AND SATURATION, only varying in lightness (brightness)
// STAGING = Light (60% lightness), TRANSFORMATION = Medium (55% lightness), CONSUMPTION = Dark (50% lightness)
// Lightness pattern: STAGING (brightest) -> TRANSFORMATION (medium) -> CONSUMPTION (darkest)
// Very narrow 10% range (60%-50%) ensures colors look nearly identical while still distinguishable
// All colors in a family have identical hue and saturation for visual consistency
// 20 distinct color families to ensure each department gets unique colors
const COLOR_FAMILIES = [
  // Primary colors (0-9)
  ['#5299E0', '#3C8CDD', '#2680D9'],  // 0. Blue (hue: 210°, sat: 70%)
  ['#E6994C', '#E28C36', '#DF8020'],  // 1. Orange (hue: 30°, sat: 75%)
  ['#E05252', '#DD3C3C', '#D92626'],  // 2. Red (hue: 0°, sat: 70%)
  ['#5CD6D6', '#47D1D1', '#33CCCC'],  // 3. Teal/Cyan (hue: 180°, sat: 60%)
  ['#61D161', '#4DCB4D', '#39C639'],  // 4. Green (hue: 120°, sat: 55%)
  ['#E6CC4C', '#E2C636', '#DFBF20'],  // 5. Yellow (hue: 50°, sat: 75%)
  ['#AA66CC', '#9F53C6', '#9540BF'],  // 6. Purple (hue: 280°, sat: 50%)
  ['#DB5799', '#D7428C', '#D22D80'],  // 7. Pink/Magenta (hue: 330°, sat: 65%)
  ['#4CB2E6', '#36A9E2', '#209FDF'],  // 8. Sky Blue (hue: 200°, sat: 75%)
  ['#C7916B', '#C08459', '#B97646'],  // 9. Brown (hue: 25°, sat: 45%)

  // Extended colors (10-19)
  ['#99D65C', '#8CD147', '#80CC33'],  // 10. Lime Green (hue: 90°, sat: 60%)
  ['#E0B152', '#DDA73C', '#D99D26'],  // 11. Amber (hue: 40°, sat: 70%)
  ['#D161BE', '#CB4DB6', '#C639AE'],  // 12. Orchid (hue: 310°, sat: 55%)
  ['#57DBD0', '#42D7CA', '#2DD2C5'],  // 13. Aqua (hue: 175°, sat: 65%)
  ['#CCA166', '#C69653', '#BF8A40'],  // 14. Tan (hue: 35°, sat: 50%)
  ['#9966CC', '#8C53C6', '#8040BF'],  // 15. Lavender (hue: 270°, sat: 50%)
  ['#E6BF4C', '#E2B736', '#DFAF20'],  // 16. Gold (hue: 45°, sat: 75%)
  ['#5CD6AD', '#47D1A3', '#33CC99'],  // 17. Mint (hue: 160°, sat: 60%)
  ['#E07552', '#DD643C', '#D95326'],  // 18. Coral (hue: 15°, sat: 70%)
  ['#999999', '#8C8C8C', '#808080'],  // 19. Gray (hue: 0°, sat: 0%)
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

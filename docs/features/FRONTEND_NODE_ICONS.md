# Frontend Node Visual Indicators (Emoji Icons)

**Version:** 4.2.1 (Proposed Enhancement)
**Date:** 2025-11-07
**Status:** 📋 Specification (Not yet implemented)

---

## Overview

Adds **emoji status indicators** to React Flow nodes to quickly indicate parse quality and catalog validation status, independent of schema legend colors.

**Implementation:** Ultra-simple - just add emoji characters to node data (no CSS, no components needed!).

### User Request

> "In the node the colors are bounded to schema legend but could we add a small checkbox icon for okay, an X for users that have to fix, and a ! where we found objects but do not have an object ID (table or view not in our base DMV definition)"

---

## Visual Indicator Types (Emojis)

### 1. ✅ Checkmark Emoji (High Confidence)
**Emoji:** `✅`
**Conditions:**
- Confidence ≥ 0.85
- All dependencies validated in catalog

**Display:**
- Emoji in node name or top-right corner
- Tooltip: "High confidence | All dependencies validated"

**Example:**
```
┌─────────────────────────┐
│ ✅ spLoadFactSales      │  ← Green checkmark emoji
│ CONSUMPTION_FINANCE     │
│ Confidence: 0.95        │
└─────────────────────────┘
```

---

### 2. ❌ X Emoji (Needs Fixing)
**Emoji:** `❌`
**Conditions:**
- Confidence < 0.65
- Parse failed or significant issues detected

**Display:**
- Emoji in node name or top-right corner
- Tooltip: Shows `parse_failure_reason`
- Example: "Dynamic SQL detected → Add @LINEAGE hints"

**Example:**
```
┌─────────────────────────┐
│ ❌ spLoadProjectRegions │  ← Red X emoji
│ CONSUMPTION_PRIMA       │
│ Confidence: 0.00        │
└─────────────────────────┘
```

---

### 3. ⚠️ Warning Emoji (Unknown Dependencies)
**Emoji:** `⚠️`
**Conditions:**
- Object found in DDL but NOT in DMV catalog
- Dependency extracted but `object_id` is NULL
- Cross-database reference or external object

**Display:**
- Emoji in node name or top-right corner
- Tooltip: "Contains unknown dependencies (not in catalog)"
- Lists unknown objects: `schema.table1, schema.table2`

**Example:**
```
┌─────────────────────────┐
│ ⚠️ spLoadDataMart       │  ← Warning emoji
│ CONSUMPTION_FINANCE     │
│ Confidence: 0.75        │
│ Unknown: ExternalDB.Tbl │
└─────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Backend Enhancement

#### 1.1. Enhanced Parser Output (`quality_aware_parser.py`)

Add `unknown_dependencies` tracking:

```python
def parse(self, object_id: int, ddl: str) -> Dict[str, Any]:
    # ... existing parsing logic ...

    # Track unknown dependencies (v4.2.1)
    unknown_tables = []
    for table_name in all_extracted_tables:
        if not self._table_exists_in_catalog(table_name):
            unknown_tables.append(table_name)

    return {
        'object_id': object_id,
        'inputs': input_ids,
        'outputs': output_ids,
        'confidence': confidence,
        'parse_failure_reason': parse_failure_reason,
        'unknown_dependencies': unknown_tables,  # NEW
        'unknown_count': len(unknown_tables)     # NEW
    }
```

#### 1.2. Enhanced Frontend Metadata (`frontend_formatter.py`)

Calculate icon status:

```python
def _determine_node_icon(
    self,
    confidence: float,
    parse_failure_reason: str | None,
    unknown_count: int
) -> Dict[str, Any]:
    """
    Determine which icon to display on the node.

    Returns:
        {
            'icon': 'checkmark' | 'x' | 'exclamation',
            'color': 'green' | 'red' | 'orange',
            'tooltip': "Description for hover"
        }
    """
    # Priority 1: Parse failure (X)
    if confidence < 0.65:
        return {
            'icon': 'x',
            'color': 'red',
            'tooltip': f"❌ Needs fixing: {parse_failure_reason or 'Low confidence'}"
        }

    # Priority 2: Unknown dependencies (!)
    if unknown_count > 0:
        return {
            'icon': 'exclamation',
            'color': 'orange',
            'tooltip': f"⚠️ {unknown_count} unknown dependencies (not in catalog)"
        }

    # Priority 3: High confidence (✓)
    if confidence >= 0.85:
        return {
            'icon': 'checkmark',
            'color': 'green',
            'tooltip': "✅ High confidence | All dependencies validated"
        }

    # Default: No icon for medium confidence (0.65-0.84)
    return {
        'icon': 'none',
        'color': 'transparent',
        'tooltip': ""
    }
```

#### 1.3. Enhanced Frontend Node Format

```json
{
  "id": "8606994",
  "name": "spLoadProjectRegions",
  "schema": "CONSUMPTION_PRIMA",
  "confidence": 0.0,
  "description": "❌ Parse Failed: 0.00 | Dynamic SQL...",
  "status_icon": {
    "icon": "x",
    "color": "red",
    "tooltip": "❌ Needs fixing: Dynamic SQL detected → Add @LINEAGE hints"
  },
  "unknown_dependencies": ["ExternalDB.Table1", "TempDB.#TempTable"],
  "unknown_count": 2
}
```

---

### Phase 2: Frontend Implementation (React Flow) - ULTRA SIMPLE!

#### Option 1: Prefix Node Name (Simplest)

Just add emoji to the node name in backend:

```python
# frontend_formatter.py

name_with_icon = f"{emoji} {node['name']}"  # "✅ spLoadFactSales"
```

**Frontend:** Zero code changes needed! ✅

#### Option 2: Separate Icon Field (More Flexible)

```json
{
  "id": "123",
  "name": "spLoadFactSales",
  "status_emoji": "✅",
  "status_tooltip": "High confidence"
}
```

**Frontend:**
```typescript
// components/LineageNode.tsx

function LineageNode({ data }: LineageNodeProps) {
  return (
    <div className="lineage-node">
      <div className="node-header">
        {data.status_emoji && (
          <span title={data.status_tooltip} style={{ marginRight: '4px' }}>
            {data.status_emoji}
          </span>
        )}
        {data.name}
      </div>
      <div className="node-schema">{data.schema}</div>
      <div className="node-description">{data.description}</div>
    </div>
  );
}
```

**That's it! No CSS needed - emojis work out of the box!** ✨

---

## Icon Priority Logic

When multiple conditions apply, show icons in this priority order:

1. **✗ (X)** - Parse failure (confidence < 0.65)
2. **! (Exclamation)** - Unknown dependencies
3. **✓ (Checkmark)** - High confidence (≥ 0.85)
4. **No icon** - Medium confidence (0.65-0.84) with no issues

### Examples

| Confidence | Unknown Deps | Icon | Reason |
|------------|--------------|------|--------|
| 0.00 | 2 | ✗ | Parse failure takes priority |
| 0.75 | 3 | ! | Unknown deps detected |
| 0.95 | 0 | ✓ | High confidence, all validated |
| 0.70 | 0 | (none) | Medium confidence, no issues |

---

## User Benefits

### 1. **Quick Visual Scanning**
Users can quickly identify problematic SPs without reading descriptions.

### 2. **Independent of Schema Colors**
Icons work alongside schema legend colors (Consumption = blue, Staging = green, etc.)

### 3. **Actionable Prioritization**
- Red ✗ = Fix immediately (add hints)
- Orange ! = Review dependencies (may need catalog update)
- Green ✓ = Verified correct

### 4. **Clear Communication**
Each icon has descriptive tooltip explaining the issue.

---

## Visual Mock-ups

### Graph View with Icons

```
     ┌────────────────────┐
     │ spLoadFactGL   ✗  │  ← Needs fixing (Dynamic SQL)
     │ CONSUMPTION_FIN    │
     └─────────┬──────────┘
               │
               ▼
     ┌────────────────────┐
     │ FactGL         ✓  │  ← High confidence
     │ CONSUMPTION_FIN    │
     └────────────────────┘
               │
               ▼
     ┌────────────────────┐
     │ DimAccount      !  │  ← Unknown dependencies
     │ EXTERNAL_DB        │
     └────────────────────┘
```

---

## Implementation Checklist

### Backend (Python)
- [ ] Add `unknown_dependencies` tracking to parser
- [ ] Implement `_table_exists_in_catalog()` method
- [ ] Add `_determine_node_icon()` to frontend formatter
- [ ] Update `frontend_lineage.json` schema with `status_icon`
- [ ] Add unknown dependencies to parser output

### Frontend (React)
- [ ] Update `LineageNode` component with icon rendering
- [ ] Add icon CSS styles
- [ ] Implement tooltip functionality
- [ ] Add icon animation (fade-in, hover effects)
- [ ] Update type definitions for `status_icon`

### Testing
- [ ] Test icon display for all confidence levels
- [ ] Test unknown dependency detection
- [ ] Test icon tooltips
- [ ] Test icon priority logic
- [ ] Test animation and hover effects

### Documentation
- [ ] Update frontend README with icon specification
- [ ] Add icon examples to user guide
- [ ] Document icon priority logic
- [ ] Update API documentation for `status_icon` field

---

## Future Enhancements

### Phase 3: Interactive Actions
- Click X icon → Open hint editor modal
- Click ! icon → Show unknown dependencies list
- Click ✓ icon → Show validation details

### Phase 4: Additional Icons
- 🔄 (Refresh) - SP re-parsed recently
- 👁️ (Eye) - User is viewing/editing this SP
- 🔒 (Lock) - SP has manual overrides (UAT validated)

---

## Related Features

- **Parse Failure Workflow** (`docs/features/PARSE_FAILURE_WORKFLOW.md`)
- **Comment Hints Guide** (`docs/guides/COMMENT_HINTS_DEVELOPER_GUIDE.md`)
- **Confidence Model** (`docs/reference/PARSER_SPECIFICATION.md#confidence-model`)

---

**Author:** Claude Code (Sonnet 4.5)
**Date:** 2025-11-07
**Status:** 📋 Specification Ready for Implementation

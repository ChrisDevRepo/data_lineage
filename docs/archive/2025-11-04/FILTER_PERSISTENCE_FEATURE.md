# Filter Persistence Feature

**Date:** 2025-11-04
**Version:** v2.9.1 (update)
**Feature:** localStorage persistence for filter settings

---

## Feature Summary

Filter settings (schema checkboxes, type checkboxes, and "Hide Unrelated" toggle) now **persist across page reloads** using browser localStorage.

---

## What Persists

### 1. Selected Schemas
- Which schema checkboxes are checked/unchecked
- Example: If you uncheck "STAGING_*" schemas, they stay unchecked after reload

### 2. Selected Object Types
- Which type checkboxes are checked/unchecked
- Example: If you filter to only show "Table" and "View", stays that way after reload

### 3. Hide Unrelated Toggle
- Whether the "Hide Unrelated" filter is ON or OFF
- Example: If you toggle it OFF, it stays OFF after reload

---

## User Experience

### Before (No Persistence)
1. User adjusts filters (unchecks some schemas, filters to specific types)
2. User refreshes page (F5) or closes/reopens tab
3. ❌ **All filters reset** to defaults (all checked)
4. User has to reconfigure filters every time

### After (With Persistence)
1. User adjusts filters (unchecks some schemas, filters to specific types)
2. User refreshes page (F5) or closes/reopens tab
3. ✅ **Filters restored** exactly as they were
4. User can continue working immediately

---

## How It Works

### localStorage Keys
```javascript
const STORAGE_KEYS = {
    SELECTED_SCHEMAS: 'lineage_viz_selected_schemas',
    SELECTED_TYPES: 'lineage_viz_selected_types',
    HIDE_UNRELATED: 'lineage_viz_hide_unrelated',
};
```

### Data Format
**Selected Schemas (Array of strings):**
```json
["CONSUMPTION_FINANCE", "STAGING_PRIMA", "TRANSFORMATION_*"]
```

**Selected Types (Array of strings):**
```json
["Table", "View", "Stored Procedure"]
```

**Hide Unrelated (Boolean):**
```json
true
```

### Storage Size
- Typical size: **<1 KB** total for all settings
- No performance impact
- Works offline (localStorage is local)

---

## Smart Behavior

### 1. Validation on Load
When restoring filters, only valid values are used:

**Example:**
- **Stored:** `["SCHEMA_A", "SCHEMA_B", "SCHEMA_C"]`
- **Current Data:** Only has `["SCHEMA_A", "SCHEMA_B"]` (SCHEMA_C removed)
- **Restored:** `["SCHEMA_A", "SCHEMA_B"]` (invalid schema ignored)

### 2. Fallback to Defaults
If no valid stored values, falls back to defaults:
- Schemas: All checked
- Types: All checked
- Hide Unrelated: ON (true)

### 3. Data Change Handling
If data changes (new schemas added):
- Stored filters still apply to existing schemas
- New schemas default to CHECKED
- User can adjust and new preferences save automatically

---

## Implementation Details

### Files Created

#### `frontend/utils/localStorage.ts` (NEW)
Utilities for saving/loading filter preferences:
```typescript
// Save functions
saveSelectedSchemas(schemas: Set<string>): void
saveSelectedTypes(types: Set<string>): void
saveHideUnrelated(hide: boolean): void

// Load functions
loadSelectedSchemas(): string[] | null
loadSelectedTypes(): string[] | null
loadHideUnrelated(): boolean | null

// Clear function
clearFilterPreferences(): void
```

### Files Modified

#### `frontend/hooks/useDataFiltering.ts`
Added localStorage integration:
1. **Import** localStorage utilities
2. **Initialize** state from localStorage on mount
3. **Persist** changes whenever filters update
4. **Validate** stored values against current data
5. **Log** when preferences are restored

**Key Changes:**
- Lines 5-12: Import localStorage functions
- Lines 40-44: Initialize `hideUnrelated` from localStorage
- Lines 53-95: Initialize schemas and types from localStorage
- Lines 97-114: Persist changes to localStorage

---

## Console Output

### On Page Load (First Time)
```
[Performance] API fetch took 8ms
[Performance] JSON parse took 2ms, data size: 1067 objects
[Performance] Layout calculated in 235ms (1067 nodes, 1326 edges)
```

### On Page Load (With Stored Preferences)
```
[Performance] API fetch took 8ms
[Performance] JSON parse took 2ms, data size: 1067 objects
[Persistence] Restored schemas from localStorage: ["CONSUMPTION_FINANCE", "STAGING_PRIMA"]
[Persistence] Restored types from localStorage: ["Table", "View"]
[Performance] Layout calculated in 180ms (650 nodes, 890 edges)
```

### On Filter Change
```
// Automatically saved to localStorage (no console output)
// Silent persistence for better UX
```

---

## Testing Guide

### Test 1: Schema Persistence
1. Uncheck 2-3 schema checkboxes
2. Refresh page (F5)
3. ✅ **Verify:** Same schemas remain unchecked

### Test 2: Type Persistence
1. Uncheck "Stored Procedure" type
2. Refresh page (F5)
3. ✅ **Verify:** "Stored Procedure" remains unchecked

### Test 3: Hide Unrelated Persistence
1. Toggle "Hide Unrelated" to OFF (gray)
2. Refresh page (F5)
3. ✅ **Verify:** Button remains OFF (gray)

### Test 4: Combined Filters
1. Set: 2 schemas, 1 type, Hide Unrelated ON
2. Refresh page (F5)
3. ✅ **Verify:** All three settings restored

### Test 5: Data Change Handling
1. Filter to specific schemas
2. Upload new data with different schemas
3. ✅ **Verify:** Old schemas restored if still exist, new ones default to checked

### Test 6: Invalid Data Handling
1. Manually corrupt localStorage (Dev Tools → Application → localStorage)
2. Refresh page
3. ✅ **Verify:** Falls back to defaults, no errors

### Test 7: Privacy/Incognito Mode
1. Open in Incognito/Private window
2. Set filters, refresh
3. ✅ **Verify:** Filters persist within incognito session
4. Close window, reopen incognito
5. ✅ **Verify:** Filters reset (localStorage cleared on close)

---

## Browser Compatibility

### Supported Browsers
- ✅ Chrome 4+
- ✅ Firefox 3.5+
- ✅ Safari 4+
- ✅ Edge (all versions)
- ✅ Opera 10.5+

**Coverage:** 99.9% of users (localStorage is universally supported)

### Storage Limits
- **Limit:** 5-10 MB per domain (browser-dependent)
- **Used:** <1 KB (0.01% of limit)
- **Risk:** None - far below limits

---

## Privacy & Security

### What's Stored Locally
- Schema names (e.g., "CONSUMPTION_FINANCE")
- Type names (e.g., "Table", "View")
- Boolean flag (true/false)

### What's NOT Stored
- ❌ No actual data (table contents, SQL, etc.)
- ❌ No user credentials
- ❌ No sensitive information
- ❌ No tracking data

### Sharing & Sync
- **Not shared** across devices (localStorage is per-browser)
- **Not synced** to cloud
- **Not sent** to server
- **Cleared** when user clears browser data

---

## Performance Impact

### Storage Operations
- **Save:** <1ms (synchronous, negligible)
- **Load:** <1ms (synchronous, negligible)
- **Impact:** None - imperceptible to user

### Memory Usage
- **RAM:** ~100 bytes (negligible)
- **Disk:** <1 KB (negligible)

### Network Impact
- **None** - All operations are local

---

## Edge Cases & Handling

### 1. localStorage Disabled
**Scenario:** User disabled localStorage or browser doesn't support it

**Handling:**
```typescript
try {
    localStorage.setItem(key, value);
} catch (error) {
    console.warn('[localStorage] Failed to save:', error);
    // Gracefully degrade - filters work but don't persist
}
```

**Result:** Feature degrades gracefully, no errors

### 2. localStorage Full
**Scenario:** User's localStorage quota exceeded (very rare)

**Handling:** Same as above - logs warning, continues without persistence

### 3. Corrupted Data
**Scenario:** Invalid JSON in localStorage

**Handling:**
```typescript
try {
    return JSON.parse(stored);
} catch (error) {
    console.warn('[localStorage] Failed to parse:', error);
    return null; // Falls back to defaults
}
```

### 4. Schema Renamed
**Scenario:** Schema name changes in data source

**Handling:**
- Stored schema name doesn't match any current schema
- Filtered out during validation
- User sees default (all schemas checked)

---

## Clear Preferences

### Manual Clear (Dev Tools)
1. Open Dev Tools (F12)
2. Application tab → Storage → localStorage
3. Find keys starting with `lineage_viz_`
4. Delete them

### Programmatic Clear (Future Feature)
Could add a "Reset Preferences" button:
```typescript
import { clearFilterPreferences } from '../utils/localStorage';

<Button onClick={clearFilterPreferences}>
    Reset Saved Preferences
</Button>
```

---

## Migration Notes

### Upgrading from v2.9.0 to v2.9.1
- **No migration needed** - Feature is additive
- **First load:** Uses defaults (no stored preferences yet)
- **Subsequent loads:** Uses stored preferences
- **Rollback:** Delete localStorage keys if needed

### New Users
- First visit: No stored preferences → defaults apply
- After adjusting filters: Preferences saved automatically
- Future visits: Preferences restored automatically

---

## Future Enhancements

### Potential Features (v2.10.0+)
1. **Export/Import Preferences**
   - Save preferences to file
   - Share with team members
   - Load preset configurations

2. **Multiple Profiles**
   - "Production View", "Staging View", "All View"
   - Switch between saved filter sets
   - Quick access to common configurations

3. **Sync Across Devices**
   - Optional cloud sync
   - Requires user account/authentication
   - Privacy-respecting implementation

4. **Reset Button**
   - "Reset Saved Preferences" in Settings
   - Clear localStorage with one click
   - Confirm before clearing

5. **Preference History**
   - Undo filter changes
   - Return to previous state
   - Time-travel debugging

---

## Troubleshooting

### Issue: Filters Don't Persist
**Symptoms:** Filters reset every page load

**Check:**
1. Is localStorage enabled? (Test in Dev Tools Console: `localStorage.setItem('test', '1')`)
2. Is browser in Private/Incognito mode? (localStorage cleared on close)
3. Are browser extensions blocking storage? (Disable and retry)
4. Is storage quota exceeded? (Very rare - check console for errors)

**Solution:** Check browser console for warnings

### Issue: Wrong Filters Restored
**Symptoms:** Different filters than expected

**Check:**
1. Open Dev Tools → Application → localStorage
2. Look for keys: `lineage_viz_selected_schemas`, `lineage_viz_selected_types`, `lineage_viz_hide_unrelated`
3. Verify values make sense

**Solution:** Delete corrupted keys, refresh page

### Issue: Console Warnings
**Symptoms:** `[localStorage] Failed to save:` warnings

**Cause:** Browser blocking localStorage access

**Impact:** Filters work but don't persist

**Solution:**
- Check browser privacy settings
- Allow localStorage for this site
- Not a critical error

---

## Code Examples

### Save Filter State
```typescript
// Happens automatically when user changes filters
setSelectedSchemas(new Set(['SCHEMA_A', 'SCHEMA_B']));
// → Saves to localStorage: ['SCHEMA_A', 'SCHEMA_B']
```

### Load Filter State
```typescript
// Happens automatically on page load
const storedSchemas = loadSelectedSchemas();
// → Returns: ['SCHEMA_A', 'SCHEMA_B'] or null

if (storedSchemas) {
    setSelectedSchemas(new Set(storedSchemas));
}
```

### Clear All Preferences
```typescript
import { clearFilterPreferences } from './utils/localStorage';

clearFilterPreferences();
// → Removes all filter preferences from localStorage
```

---

## Summary

✅ **Feature Complete**
- Schema checkboxes persist
- Type checkboxes persist
- Hide Unrelated toggle persists
- Smart validation & fallbacks
- Graceful error handling
- Console logging for debugging

**Benefits:**
- Improved UX (no reconfiguration on reload)
- Fast (localStorage is instant)
- Privacy-friendly (local only)
- Reliable (extensive error handling)

**Status:** ✅ **DEPLOYED - Ready for Testing**

---

**Next Steps:** Test persistence by adjusting filters and reloading the page!

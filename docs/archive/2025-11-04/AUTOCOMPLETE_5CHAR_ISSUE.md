# Autocomplete 5-Character Minimum Issue

**Date:** 2025-11-04
**Status:** ⚠️ INCOMPLETE - Code changes applied but not working
**Priority:** Medium

## Problem Description

The autocomplete feature in the main toolbar search box should only trigger after typing 5 or more characters. Code changes were implemented but the feature is not working when manually typing in the browser.

## Changes Made

### Files Modified

1. **`frontend/hooks/useDataFiltering.ts:148-194`**
   - Added 5-character minimum check in the autocomplete useEffect
   - Added console logging for debugging:
     ```typescript
     console.log('[Autocomplete] searchTerm:', searchTerm, 'length:', searchTerm.trim().length);

     if (searchTerm.trim() === '' || searchTerm.trim().length < 5) {
         console.log('[Autocomplete] Blocked: less than 5 characters');
         setAutocompleteSuggestions([]);
         return;
     }

     console.log('[Autocomplete] Proceeding with search...');
     ```

2. **`frontend/components/Toolbar.tsx:94-103`**
   - Added console logging to `handleSearchInputChange`:
     ```typescript
     console.log('[Toolbar] Input changed to:', e.target.value, 'length:', e.target.value.length);
     ```

3. **`frontend/components/CustomNode.tsx:45-50`**
   - ✅ WORKING - Removed bracketed source info from tooltips (e.g., "(parser)", "(dmv)")

4. **`frontend/components/DetailSearchModal.tsx:147,190,316,512-522`**
   - ✅ WORKING - Added 5-character minimum to Detail Search modal
   - Shows character counter: "Type at least 5 characters to start searching... (X/5)"

## Root Cause Analysis

### Code Verification
- ✅ Code changes are present in source files
- ✅ Vite is serving the updated transpiled JavaScript
- ✅ Console logs are included in the served bundle
- ❌ React state (`searchTerm`) is not being updated when typing

### Key Finding
When typing in the search box, the console shows:
```
[Autocomplete] searchTerm:  length: 0
[Autocomplete] Blocked: less than 5 characters
```

Even after typing "spLoadSAP" (9 characters), `searchTerm` remains empty, indicating:
1. **Either** the `onChange` handler is not firing
2. **Or** `setSearchTerm` is not updating the state
3. **Or** there's a state binding/props passing issue

### Missing Evidence
- No `[Toolbar] Input changed to:` logs appear in console
- This suggests the `onChange` handler (`handleSearchInputChange`) is not being called
- Needs manual browser testing to confirm if this is a React synthetic event issue or actual broken functionality

## What Works
1. ✅ Detail Search modal (separate search in modal) respects 5-character minimum
2. ✅ Tooltip cleanup (removed source info in brackets)
3. ✅ Code is properly transpiled and served by Vite

## What Doesn't Work
1. ❌ Main toolbar search autocomplete - `searchTerm` state not updating
2. ❌ No console logs from `handleSearchInputChange` appear
3. ❌ Autocomplete dropdown never appears regardless of character count

## Next Steps to Debug

### Manual Testing Required
1. Open http://localhost:3000 in browser
2. Hard refresh: `Ctrl+Shift+F5` or `Ctrl+Shift+R`
3. Open DevTools Console (F12)
4. Type "s" in the main search box (top-left toolbar)
5. Check console for: `[Toolbar] Input changed to: s length: 1`
6. Continue typing "pLoadSAP"
7. Document what console messages appear

### If `[Toolbar]` Logs Appear
- State is updating correctly
- Problem is in autocomplete logic (filtering, schema matching, etc.)
- Check if `selectedSchemas` includes the schema containing "spLoadSAP"

### If `[Toolbar]` Logs DON'T Appear
- React onChange handler is not firing
- Possible causes:
  - React event system issue
  - Props not passed correctly through component hierarchy
  - Input being recreated/unmounted
  - Disabled state or other attribute preventing events

## Technical Details

### Component Hierarchy
```
App.tsx
├── useDataFiltering (hook)
│   ├── searchTerm (state)
│   ├── setSearchTerm (state setter)
│   └── autocompleteSuggestions (state)
└── Toolbar
    └── <input onChange={handleSearchInputChange} />
```

### State Flow
1. User types in `<input>` (Toolbar.tsx:112-120)
2. `onChange` triggers `handleSearchInputChange` (Toolbar.tsx:94-103)
3. Calls `setSearchTerm(e.target.value)` (passed from App.tsx via props)
4. State update triggers `useEffect` in `useDataFiltering.ts:148-194`
5. If length >= 5, searches through `lineageGraph` for matches
6. Updates `autocompleteSuggestions` state
7. Toolbar renders dropdown with suggestions (Toolbar.tsx:124-135)

### Browser Cache Issues
- Vite cache was cleared: `rm -rf frontend/node_modules/.vite`
- Servers were restarted multiple times
- Source maps show line 106 (old code) vs actual line 149 (new code)
  - This is expected - source maps can have offset line numbers
  - Verified actual served JS contains correct code

## Workaround
For now, the Detail Search modal works correctly with the 5-character minimum. Users can:
1. Click "Detail Search" button (magnifying glass icon)
2. Use the modal search which properly enforces the 5-character minimum
3. Modal shows live character counter

## Files to Review When Fixing
1. `frontend/components/Toolbar.tsx` - Input and onChange handler
2. `frontend/hooks/useDataFiltering.ts` - Autocomplete logic
3. `frontend/App.tsx` - State management and props passing

## Testing Commands
```bash
# Restart servers
./stop-app.sh && ./start-app.sh

# Clear Vite cache and restart
rm -rf frontend/node_modules/.vite && ./stop-app.sh && ./start-app.sh

# Check what's being served
curl -s "http://localhost:3000/components/Toolbar.tsx" | grep "handleSearchInputChange"
curl -s "http://localhost:3000/hooks/useDataFiltering.ts" | grep "5 characters"
```

## Related Files
- `frontend/hooks/useDataFiltering.ts` - Main autocomplete logic
- `frontend/components/Toolbar.tsx` - Search input component
- `frontend/components/DetailSearchModal.tsx` - Working example of 5-char minimum
- `frontend/App.tsx` - State management
- `frontend/interaction-constants.ts` - AUTOCOMPLETE_MAX_RESULTS = 5

---

**Note:** All code changes are committed and ready. The issue is in state propagation/event handling, not in the business logic of the 5-character check.

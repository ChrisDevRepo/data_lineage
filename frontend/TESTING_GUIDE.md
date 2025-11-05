# Manual Testing Guide for Search UI Changes

## Summary of Changes

This guide helps verify the three main UI changes implemented:

1. **Exclude Textbox on Main Toolbar** - Filter out objects by term
2. **Removed Autocomplete** - No dropdown appears when typing in search
3. **Match Highlighting in DetailSearchModal** - Yellow highlights on search matches

---

## Prerequisites

1. Start the backend server:
   ```bash
   cd /home/user/sandbox/api
   python3 main.py
   ```

2. Start the frontend dev server:
   ```bash
   cd /home/user/sandbox/frontend
   npm run dev
   ```

3. Open browser to: http://localhost:3000

---

## Test 1: Exclude Textbox on Main Toolbar

### Expected Behavior
- A new input field with placeholder "Exclude terms..." should appear next to the main search box
- Typing terms (space-separated) should filter out objects whose names contain those terms

### Steps to Test

1. Look at the main toolbar (top of the page, below the logo)
2. Verify you see TWO input fields side by side:
   - First: "Search objects..." (width: ~56 chars)
   - Second: "Exclude terms..." (width: ~48 chars)

3. Type in the exclude box: `temp test`
4. Observe that objects with "temp" or "test" in their names disappear from the graph

### Code Location
- File: `frontend/components/Toolbar.tsx:117-128`
- Logic: `frontend/hooks/useDataFiltering.ts:61-69`

### What to Look For
✓ Input field is visible and styled consistently with main search
✓ Placeholder text reads "Exclude terms..."
✓ Typing filters the graph in real-time
✓ Multiple terms work (space-separated)
✓ Case-insensitive filtering

---

## Test 2: Removed Autocomplete from Main Search

### Expected Behavior
- Typing in the main "Search objects..." box should NOT show a dropdown
- Previously, after 2+ characters, a dropdown with suggestions would appear
- Now, no dropdown should appear at all

### Steps to Test

1. Click on the main "Search objects..." input field
2. Type any text (e.g., "customer")
3. Wait 1-2 seconds
4. Verify that NO dropdown menu appears below the search box

### Code Changes
- Removed from `Toolbar.tsx`: lines 120-130 (autocomplete dropdown JSX)
- Removed from `Toolbar.tsx`: handleSuggestionClick function
- Removed from `Toolbar.tsx`: autocompleteSuggestions prop
- Removed from `useDataFiltering.ts`: lines 44-83 (autocomplete generation logic)

### What to Look For
✓ No dropdown appears when typing
✓ Search still works when pressing Enter or clicking search button
✓ UI feels cleaner and simpler

---

## Test 3: Match Highlighting in DetailSearchModal

### Expected Behavior
- Search results in the Detail Search modal should have yellow highlights on matching terms
- The highlight should appear in the snippet preview text

### Steps to Test

1. Click the "Detail Search" button in the toolbar (magnifying glass with plus icon)
   - Note: This button requires backend data to be loaded

2. In the modal, type a search query: `SELECT customer`

3. Wait for results to appear

4. Look at each result item in the top panel - examine the snippet text (gray italic text below the object name)

5. Verify that search terms are highlighted with:
   - Yellow background (`bg-yellow-200`)
   - Slightly rounded corners
   - The exact text that matches your query

### Code Location
- File: `frontend/components/DetailSearchModal.tsx:38-69` (highlightMatches function)
- Usage: `frontend/components/DetailSearchModal.tsx:588`

### What to Look For
✓ Matching terms have yellow background
✓ Multiple occurrences are all highlighted
✓ Boolean operators (AND, OR, NOT) are NOT highlighted
✓ Only actual search terms are highlighted

---

## Visual Verification Checklist

### Toolbar Layout (Top of Page)
```
[Logo]                                                      [Icons]
────────────────────────────────────────────────────────────────
[Search objects...  🔍] [Exclude terms...] [⋮] [⋮] ... [Start Trace]
```

### DetailSearchModal Layout (When Opened)
```
────────────────────────────────────────────────────────────────
Detail Search Mode                                     [Close X]
────────────────────────────────────────────────────────────────
[Search DDL definitions...] [Schemas (2)] [Types (4)] ...
────────────────────────────────────────────────────────────────

Search Results
┌──────────────────────────────────────────────────────────────┐
│ ✓ spCustomerOrders                           (score: 2.45)   │
│   CONSUMPTION_FINANCE • Stored Procedure                     │
│   ...SELECT * FROM Customers WHERE...  ← YELLOW HIGHLIGHT    │
└──────────────────────────────────────────────────────────────┘

DDL Viewer
[Full SQL code appears here...]
```

---

## Known Limitations

1. **DetailSearchModal highlights require backend data**
   - The Detail Search button will be disabled if no DDL data is loaded
   - You need to upload Parquet files via the Import button first

2. **Exclude filter applies globally**
   - The exclude filter affects all views (not just current visible nodes)
   - Clear the exclude box to restore all objects

3. **Highlighting doesn't work for complex queries**
   - Quoted phrases ("exact match") won't show individual word highlights
   - Wildcards (*) are parsed as literal characters for highlighting

---

## Troubleshooting

### "Detail Search button is disabled"
→ Backend needs data. Upload Parquet files or ensure API is running with data.

### "No exclude input visible"
→ Check that you're on the main page (not in trace mode or a modal)

### "Highlighting not working"
→ Ensure you have search results with snippets. Empty results won't show highlights.

---

## Code Review Summary

All changes have been successfully implemented and are ready for testing:

| Change | Status | Files Modified |
|--------|--------|----------------|
| Exclude textbox on toolbar | ✅ Complete | Toolbar.tsx, App.tsx, useDataFiltering.ts |
| Remove autocomplete | ✅ Complete | Toolbar.tsx, useDataFiltering.ts |
| Add match highlighting | ✅ Complete | DetailSearchModal.tsx |

**Build Status**: ✅ Successful (no TypeScript errors)
**Commit**: `b8ec243` on branch `claude/move-search-exclude-textbox-011CUpwai9rU4SyjnHRdwnFu`

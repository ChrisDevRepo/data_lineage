# SQL Viewer Feature - Ready to Implement ✅

**Date:** 2025-10-27
**Status:** ✅ All plans approved, ready to start coding
**Estimated Time:** 6.5 hours (1 day)

---

## 📚 Documentation Complete

### 1. **Main Implementation Plan**
📄 [SQL_VIEWER_IMPLEMENTATION_PLAN.md](./SQL_VIEWER_IMPLEMENTATION_PLAN.md)

**Contains:**
- Complete architecture verification
- 9 implementation phases with code examples
- File-by-file changes required
- Testing checklist
- Timeline breakdown

### 2. **Backward Compatibility Plan**
📄 [BACKWARD_COMPATIBILITY_PLAN.md](./BACKWARD_COMPATIBILITY_PLAN.md)

**Contains:**
- How old JSON files (v2.0) will continue to work
- Detection logic for DDL availability
- User experience for different scenarios
- Migration path for existing users
- Zero breaking changes guaranteed

### 3. **Architecture Analysis**
📄 [SQL_VIEWER_ARCHITECTURE_ANALYSIS.md](./SQL_VIEWER_ARCHITECTURE_ANALYSIS.md)

**Contains:**
- Detailed comparison: Embed DDL vs Lazy-Load
- Real data size analysis (903 KB for 211 objects)
- Network performance (same container = <1ms)
- Decision rationale for Approach A

---

## ✅ Key Decisions Finalized

### 1. **Approach:** Embed DDL in JSON (Approach A)
**Why:**
- Same Docker container = no network latency
- Dataset is manageable (903 KB currently, ~2-4 MB typical)
- Instant UX (click node → SQL appears immediately)
- Simpler architecture (no new API endpoints)

### 2. **Backward Compatibility:** Guaranteed
**How:**
- `ddl_text` field is **optional** in TypeScript (`?`)
- Frontend detects DDL availability automatically
- SQL viewer button disabled when no DDL present
- Clear tooltips explain why button is disabled
- Old JSON files continue to work without changes

### 3. **Syntax Highlighting:** Prism.js
**Why:**
- Lightweight (4 KB gzipped vs 1.5 MB for Monaco)
- Perfect for read-only viewing
- Professional appearance (like VS Code)
- Simple to implement (5 minutes)

---

## 🛠️ Implementation Phases

| Phase | File | Task | Time |
|-------|------|------|------|
| **1** | `frontend_formatter.py` | Add DDL to JSON output | 30 min |
| **2** | `types.ts` | Add optional `ddl_text` field | 5 min |
| **3** | `package.json` | Install Prism.js | 5 min |
| **4** | `SqlViewer.tsx` (NEW) | Create SQL viewer component | 2 hours |
| **5** | `Toolbar.tsx` | Add toggle button | 30 min |
| **6** | `CustomNode.tsx` | Add click handler | 30 min |
| **7** | `App.tsx` | Integrate all components | 1 hour |
| **8** | `App.tsx` | Add CSS styling | 30 min |
| **9** | All files | Testing | 1 hour |
| | | **TOTAL** | **6.5 hours** |

---

## 📋 Files to Change

### Modify (6 files):
- [x] `lineage_v3/output/frontend_formatter.py` - Add DDL field
- [x] `frontend/types.ts` - Add optional type
- [x] `frontend/package.json` - Add Prism.js dependency
- [x] `frontend/components/Toolbar.tsx` - Add toggle button
- [x] `frontend/components/CustomNode.tsx` - Add click handler
- [x] `frontend/App.tsx` - Add state, layout, CSS

### Create (1 file):
- [ ] `frontend/components/SqlViewer.tsx` - New component

---

## 🎯 Success Criteria

**Backend:**
- [ ] JSON includes `ddl_text` field for SPs and Views
- [ ] Tables have `ddl_text: null`
- [ ] File size < 5 MB (currently ~925 KB ✅)

**Frontend:**
- [ ] Old JSON (v2.0) imports successfully
- [ ] SQL viewer button appears in toolbar
- [ ] Button disabled when no DDL data available
- [ ] Button disabled in Overview mode
- [ ] Split view opens at 50/50 width
- [ ] Syntax highlighting works for T-SQL
- [ ] Search highlights matches in yellow
- [ ] Clicking nodes updates SQL instantly
- [ ] Tables show "No DDL available" message
- [ ] Large SQL (47 KB) scrolls smoothly
- [ ] No performance impact on graph rendering
- [ ] TypeScript compiles without errors

---

## 🚀 Ready to Start

### Next Steps:

1. **Start with Phase 1 (Backend)**
   ```bash
   # File: lineage_v3/output/frontend_formatter.py
   # Task: Add include_ddl parameter and query definitions table
   ```

2. **Then Phase 2-3 (Types & Dependencies)**
   ```bash
   cd frontend
   # Edit types.ts
   npm install prismjs@^1.29.0
   ```

3. **Then Phase 4-8 (Components & Integration)**
   ```bash
   # Create SqlViewer.tsx
   # Modify Toolbar.tsx, CustomNode.tsx, App.tsx
   ```

4. **Finally Phase 9 (Testing)**
   ```bash
   # Start backend: python api/main.py
   # Start frontend: npm run dev
   # Upload Parquet → Verify SQL viewer works
   ```

---

## 📖 Quick Reference

### What is Prism.js?
Lightweight syntax highlighting library (~4 KB) that makes code look professional with color-coded keywords, strings, and comments.

### What gets embedded in JSON?
- **Stored Procedures:** Full DDL from definitions.parquet
- **Views:** Full DDL from definitions.parquet
- **Tables:** `null` (tables don't have DDL)

### How does backward compatibility work?
- `ddl_text?` is optional in TypeScript
- Frontend detects: `hasDdlData = allData.some(n => n.ddl_text)`
- If false → Button disabled
- If true → Button enabled

### How does the UI work?
1. User clicks "View SQL" button → Split view opens (50/50)
2. User clicks SP/View node → SQL appears with syntax highlighting
3. User types in search box → Matches highlighted in yellow
4. User clicks "Close SQL" → Returns to full-width graph

---

## 🐛 Edge Cases Handled

- ✅ Old JSON without `ddl_text` field
- ✅ New JSON with `ddl_text` field
- ✅ Sample data (no DDL)
- ✅ Tables clicked (show message)
- ✅ Large SQL files (>50 KB)
- ✅ Empty search
- ✅ No search matches
- ✅ Overview mode (button disabled)

---

## 📞 Need Help?

**Documentation:**
- Implementation: [SQL_VIEWER_IMPLEMENTATION_PLAN.md](./SQL_VIEWER_IMPLEMENTATION_PLAN.md)
- Compatibility: [BACKWARD_COMPATIBILITY_PLAN.md](./BACKWARD_COMPATIBILITY_PLAN.md)
- Architecture: [SQL_VIEWER_ARCHITECTURE_ANALYSIS.md](./SQL_VIEWER_ARCHITECTURE_ANALYSIS.md)

**Code Examples:**
- All phases include working code snippets
- Copy-paste ready implementations
- Clear comments explaining each part

---

## ✅ Approval Status

- [x] Architecture verified (single Docker container)
- [x] Approach selected (Embed DDL in JSON)
- [x] Backward compatibility guaranteed
- [x] Implementation plan complete
- [x] Timeline estimated (6.5 hours)
- [x] Success criteria defined
- [x] Testing plan ready

**Status:** 🟢 **APPROVED - READY TO IMPLEMENT**

---

**Let's start coding!** 🚀

Begin with Phase 1: `lineage_v3/output/frontend_formatter.py`

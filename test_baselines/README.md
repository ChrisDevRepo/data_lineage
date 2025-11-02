# Frontend Test Baselines

Visual regression testing baseline screenshots for Data Lineage Visualizer.

## Structure

```
test_baselines/
└── desktop/          # Desktop baselines (1920x1080)
    ├── homepage_loaded.png
    ├── search_modal.png
    └── graph_detail.png
```

## Usage

**Create/Update Baselines:**
```bash
/sub_DL_TestFrontend baseline
```

**Run Visual Regression Tests:**
```bash
/sub_DL_TestFrontend visual
```

## When to Update

- Initial setup (first time)
- After intentional design changes
- After major UI refactoring

**Important:** Only update baselines after design/product approval. Review screenshots carefully before committing to version control.

## Baseline Views

1. **homepage_loaded.png** - Main graph view with data loaded (763 nodes, 756 edges)
2. **search_modal.png** - DetailSearchModal open with schemas dropdown visible
3. **graph_detail.png** - Node selected with detail panel/DDL viewer shown

## Visual Regression Strategy

- **Resolution:** 1920x1080 (desktop only, mobile out of scope)
- **Tolerance:** 0.1% pixel difference (minor rendering variations)
- **Storage:** ~500KB total (3 PNG images)
- **Version Control:** Committed to Git (Git LFS recommended but optional)

---

**Last Updated:** 2025-11-02
**Frontend Version:** v2.9.0

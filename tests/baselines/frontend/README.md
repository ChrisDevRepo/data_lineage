# Frontend Visual Regression Baselines

**Location:** `tests/baselines/frontend/`
**Purpose:** Visual regression testing baseline screenshots for Data Lineage Visualizer

## Structure

```
tests/baselines/frontend/
└── desktop/          # Desktop baselines (1920x1080)
    └── homepage_loaded.png  # Main graph view (140KB)
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

## Baseline View

1. **homepage_loaded.png** - Main graph view with data loaded (763 nodes, 756 edges)

## Visual Regression Strategy

- **Resolution:** 1920x1080 (desktop only, mobile out of scope)
- **Tolerance:** 0.1% pixel difference (minor rendering variations)
- **Storage:** ~140KB (1 PNG image)
- **Version Control:** Committed to Git (no LFS needed)

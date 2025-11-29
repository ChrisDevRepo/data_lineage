# Requirements Structure

This directory contains modular Python dependencies organized by component.

## Files

| File | Purpose | Use Case |
|------|---------|----------|
| `base.txt` | Shared dependencies | Required by all components |
| `parser.txt` | Parser CLI | Data lineage parsing only |
| `api.txt` | FastAPI backend | API server only |

## Installation

### Production (Full Stack)
```bash
pip install -r requirements.txt
```
Installs: Parser + API (all production dependencies)

### Component-Specific

**Parser Only:**
```bash
pip install -r requirements/parser.txt
```
Use when: Running parser CLI without API server

**API Only:**
```bash
pip install -r requirements/api.txt
```
Use when: Running API server with pre-parsed data

## Dependency Tree

```
base.txt
├── pydantic, pydantic-settings
├── python-dotenv
└── rich

parser.txt
├── base.txt (inherited)
├── duckdb, pyarrow, pandas
├── sqlglot
└── click

api.txt
├── base.txt (inherited)
├── fastapi
├── uvicorn
└── python-multipart
```

## Best Practices

### Virtual Environment
Always use a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### Updating Dependencies
1. Update version in appropriate file (`base.txt`, `parser.txt`, etc.)
2. Test with: `pip install -r requirements.txt`

### Adding New Dependencies
- **Shared by all components** → `base.txt`
- **Parser-specific** → `parser.txt`
- **API-specific** → `api.txt`

## Migration Notes

**Old Structure (Deprecated):**
```
requirements.txt          # Parser deps
api/requirements.txt      # API deps (duplicated pydantic)
```

**New Structure (Current):**
```
requirements.txt          # Full production (references requirements/)
requirements/
  ├── base.txt           # Shared deps (no duplication)
  ├── parser.txt         # Parser deps + base
  └── api.txt            # API deps + base
```

**Benefits:**
- ✅ No duplicate dependencies
- ✅ Clear separation of concerns
- ✅ Flexible deployment scenarios
- ✅ Industry standard structure

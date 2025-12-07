# Docker Hub Repository Settings

## Repository Information

**Repository Name:** `chwagneraltyca/data-lineage-visualizer`

**Docker Hub URL:** https://hub.docker.com/r/chwagneraltyca/data-lineage-visualizer

---

## Short Description
(Max 100 characters - paste this in Docker Hub)

```
Interactive data lineage visualization for Microsoft SQL Server family databases
```

---

## Full Description
(Paste the content of DOCKERHUB_README.md in Docker Hub Overview tab)

See: `DOCKERHUB_README.md`

---

## Tags

**Paste these tags in Docker Hub:**

```
data-lineage
sql-server
azure-sql
synapse-analytics
microsoft-fabric
data-governance
metadata
visualization
fastapi
react
duckdb
dependency-analysis
impact-analysis
sql-parser
yaml-config
python
typescript
docker
container
```

---

## Links

### GitHub Repository
**URL:** https://github.com/ChrisDevRepo/data_lineage

### Live Demo
**URL:** https://datalineage.chwagner.eu/

### Video Demo
**URL:** https://www.youtube.com/watch?v=uZAk9PqHwJc

---

## Logo/Icon

**Upload this file as repository icon in Docker Hub:**
- File: `docs/images/data-lineage-gui.png` (screenshot)
- Alternative: `frontend/public/logo.png` (app logo)

**Steps to upload logo:**
1. Go to https://hub.docker.com/r/chwagneraltyca/data-lineage-visualizer/general
2. Click "Change" next to the repository icon
3. Upload `frontend/public/logo.png`

---

## Categories

Select these categories in Docker Hub:

- Analytics
- Database
- Development Tools
- Monitoring

---

## Visibility

**Current:** Private (by default on first push)

**Recommended:** Make Public when ready

**Steps to make public:**
1. Go to https://hub.docker.com/r/chwagneraltyca/data-lineage-visualizer/settings/general
2. Click "Make Public"
3. Confirm

---

## How to Update Docker Hub

### 1. Update Short Description
1. Go to https://hub.docker.com/r/chwagneraltyca/data-lineage-visualizer/general
2. Edit "Short description" field
3. Paste the short description from above
4. Click "Update"

### 2. Update Full Description (Overview)
1. Go to https://hub.docker.com/r/chwagneraltyca/data-lineage-visualizer
2. Click "Overview" tab
3. Click "Edit"
4. Paste content from `DOCKERHUB_README.md`
5. Click "Update"

### 3. Add Links
1. Go to https://hub.docker.com/r/chwagneraltyca/data-lineage-visualizer/settings/general
2. Under "External Links", add:
   - GitHub: https://github.com/ChrisDevRepo/data_lineage
   - Demo: https://datalineage.chwagner.eu/
   - Video: https://www.youtube.com/watch?v=uZAk9PqHwJc

### 4. Add Tags
1. Go to https://hub.docker.com/r/chwagneraltyca/data-lineage-visualizer/settings/general
2. Under "Search Tags", add the tags listed above

---

## Quick Reference

**Image Name:** `chwagneraltyca/data-lineage-visualizer`
**Latest Tag:** `1.0.1`, `latest`
**Port:** 8000
**Volume:** `/app/config`
**Health Check:** http://localhost:8000/health

**Pull Command:**
```bash
docker pull chwagneraltyca/data-lineage-visualizer:latest
```

**Run Command:**
```bash
docker run -d -p 8000:8000 -v data-lineage-config:/app/config chwagneraltyca/data-lineage-visualizer:latest
```

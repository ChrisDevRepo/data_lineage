# Docker Deployment

**Version:** 1.0.1 • **Author:** Christian Wagner

Production-ready Docker image for local deployment.

---

## Quick Start

```bash
cd .docker && docker-compose up -d
```

**Access:** http://localhost:8000

---

## Configuration

All data stored in `/app/config` volume:
- `.env` - Configuration (auto-created from template)
- `data/` - DuckDB database and outputs
- `logs/` - Application logs
- `rules/` - SQL extraction rules (customizable)
- `queries/` - Query templates (customizable)

**Access from host:** `.docker/config-data/` (when using docker-compose)

**Edit config:** `.docker/config-data/.env`

---

## Management

**View logs:**
```bash
docker logs datalineage -f
```

**Stop:**
```bash
cd .docker && docker-compose down
```

**Upgrade (preserves data):**
```bash
docker-compose down
# Rebuild with new code
docker-compose up -d --build
```

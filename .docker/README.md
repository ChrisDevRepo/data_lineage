# Data Lineage Visualizer - Docker Deployment

**Version:** 1.0.1
**Author:** Christian Wagner
**License:** MIT

Production Docker image for local deployment of Data Lineage Visualizer.

Supports: SQL Server, Azure SQL, Synapse Analytics, Microsoft Fabric (MS SQL Server family).

---

## Quick Start

### Prerequisites
```bash
# 1. Build frontend (required before Docker build)
cd frontend
npm install
npm run build

# 2. Return to project root
cd ..
```

### Option 1: Docker Compose (Recommended)
```bash
cd .docker
docker-compose up -d
```

Access: http://localhost:8000

### Option 2: Docker Build + Run
```bash
# Build image
docker build -t datalineage:1.0.1 -f .docker/Dockerfile .

# Run with bind mount (easy host access)
mkdir -p .docker/config-data
docker run -d \
  --name datalineage \
  -p 8000:8000 \
  -v "$(pwd)/.docker/config-data:/app/config" \
  -e ALLOWED_ORIGINS="http://localhost:8000" \
  datalineage:1.0.1
```

---

## Volume Structure

All runtime data is stored in `/app/config`:

```
config-data/              (External volume)
├── .env                  Configuration
├── data/                 DuckDB + outputs + uploads
├── logs/                 Application logs (7-day rotation)
├── rules/                SQL extraction rules (YAML)
├── queries/              Query templates (YAML)
└── util/                 User scripts
```

### Accessing Files from Host

```bash
# View logs
tail -f .docker/config-data/logs/app.log

# Edit configuration
nano .docker/config-data/.env

# View data
ls -lh .docker/config-data/data/

# Customize SQL rules
nano .docker/config-data/rules/tsql/10_extract_targets_tsql.yaml
```

---

## Configuration

Edit `.docker/config-data/.env` after first run:

```env
ALLOWED_ORIGINS=http://localhost:8000
LOG_LEVEL=INFO
RUN_MODE=production
SQL_DIALECT=tsql
```

---

## Upgrade

```bash
# 1. Pull/build new image
docker build -t datalineage:1.0.2 -f .docker/Dockerfile .

# 2. Stop old container
docker stop datalineage && docker rm datalineage

# 3. Start new container (same volume!)
docker run -d \
  --name datalineage \
  -p 8000:8000 \
  -v "$(pwd)/.docker/config-data:/app/config" \
  datalineage:1.0.2

# Data, config, and logs are preserved!
```

---

## Troubleshooting

### Check logs
```bash
docker logs datalineage
```

### Check health
```bash
curl http://localhost:8000/health
```

### Interactive shell
```bash
docker exec -it datalineage /bin/bash
ls -la /app/config
```

---

## See Also

- **Main README:** `../README.md`
- **Azure Deployment:** `../.azure-deploy/README.md`
- **VSCode Dev Container:** `../.devcontainer/README.md`

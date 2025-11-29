# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-23

### Added

**Core Features:**
- Interactive data lineage visualization with React Flow
- YAML-based regex parser with metadata catalog validation
- Parquet file upload, database direct connection (SQL Server/Azure SQL/Synapse/Fabric), and JSON import
- Interactive graph with trace mode, filtering, and full-text search
- Developer panel with logs and YAML rules browser

**Database Support:**
- T-SQL dialect (SQL Server, Azure SQL, Synapse dedicated pools, Fabric)
- All object types: Tables, Views, Stored Procedures, Functions

**Deployment:**
- Docker support with multi-stage builds
- Azure Container Apps deployment templates
- VS Code dev container configuration

**Documentation:**
- Architecture, API, configuration, and interface contracts documentation

### Technical Stack
- FastAPI backend + DuckDB analytics workspace
- React + TypeScript frontend with React Flow visualization
- Graphology for graph algorithms

---

## Links

- [Demo](https://datalineage.chwagner.eu/) - Try the live demo
- [Documentation](docs/) - Complete documentation

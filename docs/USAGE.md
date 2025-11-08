# Usage Guide

How to use the Data Lineage Visualizer for parsing SQL and viewing lineage.

## Running the Parser

### Basic Usage

```bash
# Parse Parquet files
python lineage_v3/main.py run --parquet parquet_snapshots/

# Incremental mode (faster, recommended)
python lineage_v3/main.py run --parquet parquet_snapshots/ --incremental
```

### Required Files
- `objects.parquet` - Object metadata
- `dependencies.parquet` - DMV dependencies  
- `definitions.parquet` - DDL for SPs/Views

### Optional Files
- `table_columns.parquet` - Column metadata for tables
- `query_logs.parquet` - Runtime execution logs

## Confidence Scores

The parser assigns confidence scores (v2.1.0 simplified model):

| Score | Meaning | Interpretation |
|-------|---------|----------------|
| **100** | Perfect | Found 90%+ of expected tables |
| **85** | Good | Found 70-89% of expected tables |
| **75** | Acceptable | Found 50-69% of expected tables |
| **0** | Failed | Parse error or <50% completeness |

**Special Cases:**
- Orchestrators (only EXEC, no tables) → 100%
- Parse failures → 0%

## Improving Low Confidence SPs

### Use Comment Hints

Add hints directly in your SQL to guide the parser:

```sql
CREATE PROCEDURE spLoadCustomers
AS
-- @LINEAGE_INPUTS: DimCustomers, FactOrders
-- @LINEAGE_OUTPUTS: StagingCustomers

BEGIN
    -- Dynamic SQL that parser can't analyze
    EXEC sp_executesql @sql
END
```

### Supported Hint Types

```sql
-- Single table
-- @LINEAGE_INPUTS: DimCustomer

-- Multiple tables
-- @LINEAGE_INPUTS: DimCustomer, FactOrders, DimProduct

-- With schema
-- @LINEAGE_INPUTS: dbo.DimCustomer, staging.TempData

-- Outputs
-- @LINEAGE_OUTPUTS: FactCustomerOrders
```

### When to Use Hints

✅ **USE hints for:**
- Dynamic SQL (sp_executesql, EXEC(@var))
- WHILE loops with table references
- Conditional logic (IF/ELSE with different tables)
- External SP calls with unclear dependencies

❌ **DON'T use hints for:**
- Simple SELECT/INSERT/UPDATE statements
- Static SQL (parser handles these automatically)

## Parser Development

**⚠️ MANDATORY: Always use evaluation framework for parser changes**

```bash
# 1. Create baseline
/sub_DL_OptimizeParsing init --name baseline_YYYYMMDD_description

# 2. Run evaluation
/sub_DL_OptimizeParsing run --mode full --baseline baseline_YYYYMMDD_description

# 3. Make changes to quality_aware_parser.py

# 4. Re-evaluate
/sub_DL_OptimizeParsing run --mode full --baseline baseline_YYYYMMDD_description

# 5. Compare results
/sub_DL_OptimizeParsing compare --run1 run_X --run2 run_Y
```

**Pass criteria:** Zero regressions, expected improvements only.

## Troubleshooting

### Port Conflicts

```bash
./stop-app.sh  # Kills processes on ports 3000 & 8000
```

### Parser Issues

**"No DDL found":**
- Check `definitions.parquet` exists
- Verify object_id matches between files

**"Low confidence warnings":**
- Add `@LINEAGE_INPUTS/@LINEAGE_OUTPUTS` hints
- Check smoke test expectations are accurate

**"Parse failures":**
- Review `parse_failure_reason` in node description
- Common causes: Dynamic SQL, WHILE loops, complex CTEs

### Frontend Issues

**Graph not loading:**
- Check API is running (http://localhost:8000/health)
- Verify `data/latest_frontend_lineage.json` exists
- Check browser console for errors

**Slow performance:**
- Reduce visible nodes with schema/type filters
- Use "Hide Unrelated" to remove isolated nodes
- Limit search results

### Database Issues

**DuckDB locked:**
```bash
# Stop all processes
./stop-app.sh

# Remove lock
rm data/lineage_workspace.duckdb.wal
```

**Migration errors:**
- Delete `data/lineage_workspace.duckdb`
- Re-run parser (will recreate with latest schema)

## Best Practices

### For Developers

1. **Use hints sparingly** - Let parser work first
2. **Run evaluation** - Before every parser change
3. **Document patterns** - Add examples to PARSER_EVOLUTION_LOG
4. **Test incrementally** - Small changes, frequent testing

### For Analysts

1. **Start with high confidence** - Review 100/85 score SPs first
2. **Fix low confidence** - Add hints for 75/0 score SPs
3. **Validate results** - Check traced dependencies make sense
4. **Report issues** - Document parsing failures in BUGS.md

### For Administrators

1. **Monitor performance** - Track parser execution time
2. **Archive old data** - Keep only recent snapshots
3. **Update regularly** - Pull latest parser improvements
4. **Backup database** - Preserve DuckDB workspace

## Advanced Features

### Incremental Parsing

Parser remembers previous runs in DuckDB:
- Re-parses only modified/new objects
- Re-parses low confidence objects (<0.85)
- 50-90% faster than full refresh

```bash
python lineage_v3/main.py run --parquet data/ --incremental
```

### Trace Mode

Find upstream/downstream dependencies:

1. Right-click node → "Start Trace"
2. Adjust upstream/downstream levels
3. Click "Apply" → Banner appears
4. Click X on banner to clear trace

### Detail Search

Search across all DDL definitions:

1. Click "Detail Search" in toolbar
2. Type search term
3. Press Enter
4. Click result to view DDL
5. Use Ctrl+F to search within DDL

See [REFERENCE.md](REFERENCE.md) for technical specifications.

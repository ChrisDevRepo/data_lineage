"""
Re-parse all 349 SPs to populate expected_count and found_count fields.

This script:
1. Connects to existing workspace database
2. Gets all stored procedures
3. Re-parses each with QualityAwareParser
4. Updates lineage_metadata with expected_count and found_count
"""
import sys
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lineage_v3.core import DuckDBWorkspace
from lineage_v3.parsers import QualityAwareParser

def reparse_all_sps():
    """Re-parse all stored procedures to populate expected_count/found_count."""

    workspace_path = "data/lineage_workspace.duckdb"

    logger.info(f"Opening workspace: {workspace_path}")

    with DuckDBWorkspace(workspace_path=workspace_path) as db:
        # Create parser
        parser = QualityAwareParser(db)

        # Get all stored procedures
        sps = db.connection.execute("""
            SELECT
                o.object_id,
                o.schema_name,
                o.object_name,
                o.modify_date
            FROM objects o
            WHERE o.object_type = 'Stored Procedure'
            ORDER BY o.schema_name, o.object_name
        """).fetchall()

        total = len(sps)
        logger.info(f"Found {total} stored procedures to re-parse")

        success_count = 0
        error_count = 0

        for idx, (object_id, schema, name, modify_date) in enumerate(sps, 1):
            sp_name = f"{schema}.{name}"

            try:
                # Parse
                logger.info(f"[{idx}/{total}] Parsing {sp_name}...")
                result = parser.parse_object(object_id)

                # Update metadata WITH expected_count and found_count
                db.update_metadata(
                    object_id=object_id,
                    modify_date=modify_date,
                    primary_source=result.get('primary_source', 'parser'),
                    confidence=result['confidence'],
                    inputs=result.get('inputs', []),
                    outputs=result.get('outputs', []),
                    confidence_breakdown=result.get('confidence_breakdown'),
                    parse_failure_reason=result.get('parse_failure_reason'),
                    expected_count=result.get('expected_count'),
                    found_count=result.get('found_count')
                )

                success_count += 1

                # Log key metrics
                expected = result.get('expected_count', 'None')
                found = result.get('found_count', 'None')
                conf = result['confidence']
                inputs_len = len(result.get('inputs', []))
                outputs_len = len(result.get('outputs', []))

                logger.info(
                    f"  ✅ {sp_name}: conf={conf}, "
                    f"expected={expected}, found={found}, "
                    f"inputs={inputs_len}, outputs={outputs_len}"
                )

            except Exception as e:
                error_count += 1
                logger.error(f"  ❌ Failed to parse {sp_name}: {e}")

                # Store failure
                try:
                    db.update_metadata(
                        object_id=object_id,
                        modify_date=modify_date,
                        primary_source='parser',
                        confidence=0.0,
                        inputs=[],
                        outputs=[],
                        parse_failure_reason=f"Parser error: {str(e)[:200]}"
                    )
                except Exception as meta_error:
                    logger.error(f"  ❌ Failed to store error metadata: {meta_error}")

        logger.info("="*80)
        logger.info(f"Re-parsing complete!")
        logger.info(f"  Total SPs: {total}")
        logger.info(f"  Success: {success_count}")
        logger.info(f"  Errors: {error_count}")
        logger.info(f"  Success rate: {success_count/total*100:.1f}%")
        logger.info("="*80)

if __name__ == "__main__":
    reparse_all_sps()

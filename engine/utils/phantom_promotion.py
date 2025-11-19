#!/usr/bin/env python3
"""
Phantom Promotion Utility
==========================

Detects and promotes phantom objects when real metadata becomes available.

v4.3.0: Phantom Objects Feature

This utility:
1. Finds phantoms that now exist in real metadata (objects table)
2. Marks phantoms as promoted and links to real object_id
3. Identifies affected stored procedures that referenced the phantom
4. Returns list of SPs that need re-parsing

Usage:
    from engine.utils.phantom_promotion import promote_phantoms

    workspace = DuckDBWorkspace("lineage_workspace.duckdb")
    workspace.connect()

    # Check for promotions after metadata upload
    results = promote_phantoms(workspace)

    if results['promoted']:
        print(f"Promoted {len(results['promoted'])} phantoms")
        print(f"Re-parse {len(results['affected_sps'])} stored procedures")

Author: Claude Code Agent
Version: 1.0.0
Date: 2025-11-11
"""

import logging
from typing import Dict, List, Set, Any
from datetime import datetime

logger = logging.getLogger(__name__)


def promote_phantoms(workspace) -> Dict[str, Any]:
    """
    Promote phantoms that now exist in real metadata.

    Finds phantom objects whose schema.name now exists in objects table,
    marks them as promoted, and returns affected SPs for re-parsing.

    Args:
        workspace: DuckDB workspace instance

    Returns:
        {
            'promoted': [
                {
                    'phantom_id': -123,
                    'real_id': 456,
                    'schema_name': 'dbo',
                    'object_name': 'Table1'
                },
                ...
            ],
            'affected_sps': [789, 790, ...],  # SP object_ids to re-parse
            'summary': {
                'phantoms_promoted': int,
                'sps_affected': int
            }
        }
    """
    promoted = []
    affected_sp_ids = set()

    # STEP 1: Find phantoms that now exist in real metadata
    find_query = """
        SELECT
            p.object_id as phantom_id,
            o.object_id as real_id,
            p.schema_name,
            p.object_name
        FROM phantom_objects p
        JOIN objects o
            ON LOWER(p.schema_name) = LOWER(o.schema_name)
            AND LOWER(p.object_name) = LOWER(o.object_name)
        WHERE p.is_promoted = FALSE
    """

    results = workspace.query(find_query)

    if not results:
        logger.info("No phantoms to promote")
        return {
            'promoted': [],
            'affected_sps': [],
            'summary': {
                'phantoms_promoted': 0,
                'sps_affected': 0
            }
        }

    logger.info(f"Found {len(results)} phantoms ready for promotion")

    # STEP 2: For each phantom, mark as promoted and find affected SPs
    for row in results:
        phantom_id, real_id, schema_name, object_name = row

        # Mark phantom as promoted
        promote_query = """
            UPDATE phantom_objects
            SET is_promoted = TRUE,
                promoted_to_id = ?
            WHERE object_id = ?
        """
        workspace.query(promote_query, params=[real_id, phantom_id])

        # Find affected SPs
        sp_query = """
            SELECT DISTINCT referencing_sp_id
            FROM phantom_references
            WHERE phantom_id = ?
        """
        sp_results = workspace.query(sp_query, params=[phantom_id])

        for sp_row in sp_results:
            affected_sp_ids.add(sp_row[0])

        promoted.append({
            'phantom_id': phantom_id,
            'real_id': real_id,
            'schema_name': schema_name,
            'object_name': object_name
        })

        logger.info(f"Promoted phantom {schema_name}.{object_name}: {phantom_id} → {real_id}")

    logger.info(f"Promotion complete: {len(promoted)} phantoms, {len(affected_sp_ids)} SPs affected")

    return {
        'promoted': promoted,
        'affected_sps': list(affected_sp_ids),
        'summary': {
            'phantoms_promoted': len(promoted),
            'sps_affected': len(affected_sp_ids)
        }
    }


def reparse_affected_sps(workspace, sp_ids: List[int]) -> Dict[str, Any]:
    """
    Re-parse stored procedures affected by phantom promotion.

    Args:
        workspace: DuckDB workspace instance
        sp_ids: List of stored procedure object_ids to re-parse

    Returns:
        {
            'success_count': int,
            'failed_count': int,
            'results': [...]
        }
    """
    from engine.parsers import QualityAwareParser

    if not sp_ids:
        return {
            'success_count': 0,
            'failed_count': 0,
            'results': []
        }

    logger.info(f"Re-parsing {len(sp_ids)} stored procedures after phantom promotion...")

    parser = QualityAwareParser(workspace)
    success_count = 0
    failed_count = 0
    results = []

    for sp_id in sp_ids:
        try:
            # Re-parse the stored procedure
            result = parser.parse_object(sp_id)

            # Update metadata in workspace
            workspace.update_metadata(
                object_id=sp_id,
                modify_date=None,  # Keep existing modify_date
                primary_source=result.get('source', 'parser'),
                confidence=result['confidence'],
                inputs=result.get('inputs', []),
                outputs=result.get('outputs', []),
                confidence_breakdown=result.get('confidence_breakdown')
            )

            success_count += 1
            results.append({
                'sp_id': sp_id,
                'status': 'success',
                'confidence': result['confidence']
            })

            logger.debug(f"Re-parsed SP {sp_id}: confidence {result['confidence']}")

        except Exception as e:
            failed_count += 1
            results.append({
                'sp_id': sp_id,
                'status': 'failed',
                'error': str(e)
            })
            logger.error(f"Failed to re-parse SP {sp_id}: {e}")

    logger.info(f"Re-parsing complete: {success_count} success, {failed_count} failed")

    return {
        'success_count': success_count,
        'failed_count': failed_count,
        'results': results
    }


def promote_and_reparse(workspace) -> Dict[str, Any]:
    """
    Convenience function: promote phantoms and re-parse affected SPs.

    Args:
        workspace: DuckDB workspace instance

    Returns:
        Combined results from promotion and re-parsing
    """
    # Step 1: Promote phantoms
    promotion_results = promote_phantoms(workspace)

    # Step 2: Re-parse affected SPs
    reparse_results = reparse_affected_sps(workspace, promotion_results['affected_sps'])

    return {
        'promotion': promotion_results,
        'reparse': reparse_results
    }

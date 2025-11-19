"""
Onion Layer SQL Preprocessor

Processes SQL by peeling layers from outside to inside:
- Layer 0: Extract procedure body
- Layer 1: Remove variable declarations
- Layer 2: Process TRY/CATCH blocks
- Layer 3: Remove transaction wrappers
- Core: Business logic remains

Author: Based on user's "onion peeling" architectural insight
Version: 1.0.0
Date: 2025-11-12
"""

import re
import logging

logger = logging.getLogger(__name__)


class OnionPreprocessor:
    """
    Preprocesses SQL by peeling structural layers from outside to inside.

    This approach eliminates rule conflicts and matches SQL's natural nested structure.
    """

    def process(self, sql: str) -> str:
        """
        Process SQL by peeling layers from outside to inside.

        Args:
            sql: Raw SQL DDL

        Returns:
            Cleaned SQL with only business logic remaining
        """
        logger.debug("Starting onion layer preprocessing")

        original_length = len(sql)

        # Layer 0: Extract procedure body
        sql = self._layer0_extract_body(sql)
        logger.debug(f"Layer 0 (extract body): {len(sql)} chars")

        # Layer 1: Remove variable declarations
        sql = self._layer1_remove_declarations(sql)
        logger.debug(f"Layer 1 (remove declarations): {len(sql)} chars")

        # Layer 2: Process TRY/CATCH blocks
        sql = self._layer2_process_try_catch(sql)
        logger.debug(f"Layer 2 (process try/catch): {len(sql)} chars")

        # Layer 3: Remove transaction wrappers
        sql = self._layer3_remove_transactions(sql)
        logger.debug(f"Layer 3 (remove transactions): {len(sql)} chars")

        final_length = len(sql)
        reduction_pct = ((original_length - final_length) / original_length * 100) if original_length > 0 else 0
        logger.debug(f"Onion preprocessing complete: {original_length} → {final_length} chars ({reduction_pct:.1f}% reduction)")

        return sql.strip()

    def _layer0_extract_body(self, sql: str) -> str:
        """
        Layer 0: Extract procedure body from CREATE PROCEDURE wrapper.

        Removes: CREATE PROCEDURE ... AS BEGIN ... END wrapper
        Keeps: Inner body content
        """
        # Pattern: CREATE PROC ... AS BEGIN ... END
        # We want to extract everything between the outermost BEGIN and END

        # Try to find CREATE PROC and extract body
        match = re.search(
            r'CREATE\s+PROC(?:EDURE)?\s+.*?\s+AS\s+BEGIN\s+(.*)\s+END\s*$',
            sql,
            re.IGNORECASE | re.DOTALL
        )

        if match:
            body = match.group(1).strip()
            logger.debug("Extracted procedure body (removed CREATE PROC wrapper)")
            return body

        # If no match, try simpler pattern (already extracted or ALTER PROC)
        match = re.search(
            r'(?:CREATE|ALTER)\s+PROC(?:EDURE)?\s+.*?\s+AS\s+(.*)',
            sql,
            re.IGNORECASE | re.DOTALL
        )

        if match:
            body = match.group(1).strip()
            # Remove trailing END if present
            if body.upper().endswith('END'):
                body = body[:-3].strip()
            logger.debug("Extracted procedure body (alternate pattern)")
            return body

        # No CREATE PROC found, return as-is (may already be extracted)
        logger.debug("No CREATE PROC wrapper found, using SQL as-is")
        return sql

    def _layer1_remove_declarations(self, sql: str) -> str:
        """
        Layer 1: Remove all variable declarations and assignments.

        Removes:
        - DECLARE @var ... (all forms)
        - SET @var = ... (variable assignments, not session options)
        - SET NOCOUNT, SET XACT_ABORT (session options)

        This is the outermost logic layer (setup code).
        """
        # Remove all DECLARE statements
        sql = re.sub(
            r'\bDECLARE\s+@\w+[^;]*;?',
            '',
            sql,
            flags=re.IGNORECASE | re.MULTILINE
        )

        # Remove SET @variable assignments
        sql = re.sub(
            r'\bSET\s+@\w+[^;]*;?',
            '',
            sql,
            flags=re.IGNORECASE | re.MULTILINE
        )

        # Remove SET session options (NOCOUNT, XACT_ABORT, etc.)
        sql = re.sub(
            r'\bSET\s+(NOCOUNT|XACT_ABORT|ANSI_NULLS|QUOTED_IDENTIFIER|ANSI_PADDING|ANSI_WARNINGS|ARITHABORT)\s+(ON|OFF)\s*;?',
            '',
            sql,
            flags=re.IGNORECASE | re.MULTILINE
        )

        logger.debug("Removed all variable declarations and SET statements")
        return sql

    def _layer2_process_try_catch(self, sql: str) -> str:
        """
        Layer 2: Process TRY/CATCH blocks.

        TRY blocks: Keep content (business logic)
        CATCH blocks: Remove content (error handling)

        This handles the error handling layer.
        """
        # Step 1: Mark TRY/CATCH blocks with comments for identification
        sql = re.sub(r'\bBEGIN\s+TRY\b', 'BEGIN /* TRY */', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bEND\s+TRY\b', 'END /* TRY */', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bBEGIN\s+CATCH\b', 'BEGIN /* CATCH */', sql, flags=re.IGNORECASE)
        sql = re.sub(r'\bEND\s+CATCH\b', 'END /* CATCH */', sql, flags=re.IGNORECASE)

        # Step 2: Remove CATCH blocks entirely (they contain error handling, not business logic)
        sql = re.sub(
            r'BEGIN\s+/\*\s*CATCH\s*\*/.*?END\s+/\*\s*CATCH\s*\*/',
            '',
            sql,
            flags=re.DOTALL | re.IGNORECASE
        )

        # Step 3: Unwrap TRY blocks (remove BEGIN TRY / END TRY markers, keep content)
        sql = re.sub(r'BEGIN\s+/\*\s*TRY\s*\*/', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'END\s+/\*\s*TRY\s*\*/', '', sql, flags=re.IGNORECASE)

        logger.debug("Processed TRY/CATCH blocks (kept TRY content, removed CATCH)")
        return sql

    def _layer3_remove_transactions(self, sql: str) -> str:
        """
        Layer 3: Remove transaction control wrappers.

        Removes:
        - BEGIN TRANSACTION
        - COMMIT TRANSACTION
        - ROLLBACK TRANSACTION (and everything after it - failure path)

        These are wrappers around business logic, not the logic itself.
        """
        # Remove BEGIN TRANSACTION
        sql = re.sub(
            r'\bBEGIN\s+TRANSACTION\s*;?',
            '',
            sql,
            flags=re.IGNORECASE
        )

        # Remove COMMIT TRANSACTION
        sql = re.sub(
            r'\bCOMMIT\s+TRANSACTION\s*;?',
            '',
            sql,
            flags=re.IGNORECASE
        )

        # Remove ROLLBACK and everything after it (failure recovery path)
        sql = re.sub(
            r'ROLLBACK\s+TRANSACTION\s*;.*?(?=END|BEGIN|$)',
            '',
            sql,
            flags=re.IGNORECASE | re.DOTALL
        )

        # Also handle simple ROLLBACK without TRANSACTION keyword
        sql = re.sub(
            r'\bROLLBACK\s*;.*?(?=END|BEGIN|$)',
            '',
            sql,
            flags=re.IGNORECASE | re.DOTALL
        )

        logger.debug("Removed transaction control statements")
        return sql

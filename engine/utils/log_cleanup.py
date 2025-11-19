"""
Log File Cleanup Utility (v0.9.0)
==================================

Automatically clean up old log files based on retention policy.
Triggered on data import/upload to keep log storage manageable.

Author: Claude Code
Date: 2025-11-19
"""

import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List

logger = logging.getLogger(__name__)


def cleanup_old_logs(retention_days: int, log_paths: List[Path] = None) -> dict:
    """
    Clean up log files older than retention_days.

    Args:
        retention_days: Number of days to retain logs
        log_paths: List of log file paths to check (default: common locations)

    Returns:
        Dictionary with cleanup statistics
    """
    if log_paths is None:
        # Default log locations
        log_paths = [
            Path("/tmp/data_lineage.log"),
            Path("/tmp/backend.log"),
            Path("/tmp/frontend.log"),
            Path("logs/data_lineage.log"),
            Path("logs/backend.log"),
            Path("logs/frontend.log"),
            Path("/home/site/data/logs/app.log"),
        ]

    cutoff_date = datetime.now() - timedelta(days=retention_days)
    stats = {
        'checked': 0,
        'deleted': 0,
        'total_size_freed_mb': 0.0,
        'errors': []
    }

    for log_path in log_paths:
        try:
            if not log_path.exists():
                continue

            stats['checked'] += 1

            # Check file modification time
            mtime = datetime.fromtimestamp(log_path.stat().st_mtime)

            if mtime < cutoff_date:
                # File is older than retention period
                file_size_mb = log_path.stat().st_size / (1024 * 1024)
                log_path.unlink()
                stats['deleted'] += 1
                stats['total_size_freed_mb'] += file_size_mb
                logger.info(f"Deleted old log file: {log_path} ({file_size_mb:.2f} MB)")

        except Exception as e:
            error_msg = f"Failed to cleanup {log_path}: {e}"
            logger.warning(error_msg)
            stats['errors'].append(error_msg)

    if stats['deleted'] > 0:
        logger.info(
            f"Log cleanup complete: {stats['deleted']} file(s) deleted, "
            f"{stats['total_size_freed_mb']:.2f} MB freed"
        )

    return stats

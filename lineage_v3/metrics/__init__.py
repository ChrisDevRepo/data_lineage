"""
Metrics Package - Single Source of Truth for All Lineage Metrics
=================================================================

This package provides the MetricsService class which is the ONLY place
where lineage metrics should be calculated.

All consumers (CLI, JSON, tests, subagents) MUST use MetricsService
to ensure consistency and avoid confusion.

Usage:
    from lineage_v3.metrics import MetricsService

    metrics = MetricsService(workspace)
    sp_metrics = metrics.get_parse_metrics(object_type='Stored Procedure')
    all_metrics = metrics.get_parse_metrics()  # All objects

Author: Vibecoding Data Lineage Team
Date: 2025-11-02
"""

from .metrics_service import MetricsService

__all__ = ['MetricsService']

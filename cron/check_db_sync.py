#!/usr/bin/env python3
"""
Database synchronization checker for SBI Forex Rates API.

This script checks if all three databases (primary, backup) are in sync
by comparing record counts, latest dates, and sample data integrity.
"""

import sys
from typing import Dict, List, Optional, Tuple

from config.settings import db_config
from services.database_service import DatabaseService
from sqlalchemy import text

from utils.logger import LoggerFactory

logger = LoggerFactory.get_logger(__name__)


class DatabaseSyncChecker:
    """Checks synchronization status across multiple databases."""

    def __init__(self):
        """Initialize the sync checker with database configurations."""
        self.databases = self._get_database_configs()
        self.sync_issues = []

    def _get_database_configs(self) -> Dict[str, str]:
        """Get all configured database URLs."""
        configs = {"primary": db_config.url}

        if db_config.backup_url:
            configs["backup"] = db_config.backup_url

        return configs

    def _get_database_stats(self, db_service: DatabaseService) -> Optional[Dict]:
        """
        Get basic statistics from a database.

        Args:
            db_service: Connected database service

        Returns:
            Dictionary with stats or None if error
        """
        try:
            with db_service.get_session() as session:
                # Get total record count
                count_result = session.execute(
                    text(f"SELECT COUNT(*) FROM {db_config.table_name}")
                ).scalar()

                # Get date range
                date_range_result = session.execute(
                    text(
                        f"""
                        SELECT
                            MIN(date) as min_date,
                            MAX(date) as max_date,
                            COUNT(DISTINCT date) as unique_dates
                        FROM {db_config.table_name}
                    """
                    )
                ).fetchone()

                # Get sample of recent records for data integrity check
                sample_result = session.execute(
                    text(
                        f"""
                        SELECT currency, ticker, date, tt_buy, tt_sell
                        FROM {db_config.table_name}
                        WHERE category = 'TEN_TO_TWENTY'
                        ORDER BY date DESC, currency
                        LIMIT 10
                    """
                    )
                ).fetchall()

                return {
                    "total_records": count_result,
                    "min_date": (
                        date_range_result.min_date if date_range_result else None
                    ),
                    "max_date": (
                        date_range_result.max_date if date_range_result else None
                    ),
                    "unique_dates": (
                        date_range_result.unique_dates if date_range_result else 0
                    ),
                    "sample_records": [dict(row._mapping) for row in sample_result],
                }

        except Exception as e:
            logger.error("Failed to get database stats: %s", e)
            return None

    def _compare_stats(self, stats: Dict[str, Dict]) -> List[str]:
        """
        Compare statistics across databases and identify inconsistencies.

        Args:
            stats: Dictionary mapping database names to their stats

        Returns:
            List of issue descriptions
        """
        issues = []

        if len(stats) < 2:
            return ["Need at least 2 databases to compare"]

        # Get reference stats (from primary or first available)
        ref_name = "primary" if "primary" in stats else list(stats.keys())[0]
        ref_stats = stats[ref_name]

        for db_name, db_stats in stats.items():
            if db_name == ref_name:
                continue

            # Compare record counts
            if db_stats["total_records"] != ref_stats["total_records"]:
                issues.append(
                    f"Record count mismatch: {ref_name}={ref_stats['total_records']}, "
                    f"{db_name}={db_stats['total_records']}"
                )

            # Compare date ranges
            if db_stats["min_date"] != ref_stats["min_date"]:
                issues.append(
                    f"Min date mismatch: {ref_name}={ref_stats['min_date']}, "
                    f"{db_name}={db_stats['min_date']}"
                )

            if db_stats["max_date"] != ref_stats["max_date"]:
                issues.append(
                    f"Max date mismatch: {ref_name}={ref_stats['max_date']}, "
                    f"{db_name}={db_stats['max_date']}"
                )

            # Compare unique date counts
            if db_stats["unique_dates"] != ref_stats["unique_dates"]:
                issues.append(
                    f"Unique dates mismatch: {ref_name}={ref_stats['unique_dates']}, "
                    f"{db_name}={db_stats['unique_dates']}"
                )

        return issues

    def _compare_sample_data(self, stats: Dict[str, Dict]) -> List[str]:
        """
        Compare sample records for data integrity.

        Args:
            stats: Dictionary mapping database names to their stats

        Returns:
            List of data integrity issues
        """
        issues = []

        if len(stats) < 2:
            return issues

        # Get reference samples
        ref_name = "primary" if "primary" in stats else list(stats.keys())[0]
        ref_samples = stats[ref_name]["sample_records"]

        for db_name, db_stats in stats.items():
            if db_name == ref_name:
                continue

            db_samples = db_stats["sample_records"]

            # Compare sample record counts
            if len(db_samples) != len(ref_samples):
                issues.append(
                    f"Sample size mismatch: {ref_name}={len(ref_samples)}, "
                    f"{db_name}={len(db_samples)}"
                )
                continue

            # Compare sample data content
            for i, (ref_record, db_record) in enumerate(zip(ref_samples, db_samples)):
                if ref_record != db_record:
                    issues.append(
                        f"Sample record {i} differs between {ref_name} and {db_name}: "
                        f"currency={ref_record.get('currency')} vs {db_record.get('currency')}, "
                        f"date={ref_record.get('date')} vs {db_record.get('date')}"
                    )
                    break  # Only report first difference per database pair

        return issues

    def check_sync(self) -> Tuple[bool, Dict]:
        """
        Check synchronization across all configured databases.

        Returns:
            Tuple of (is_synced, detailed_report)
        """
        logger.info("Starting database synchronization check...")

        stats = {}
        connection_issues = []

        # Collect stats from each database
        for db_name, db_url in self.databases.items():
            logger.info("Checking database: %s", db_name)

            db_service = DatabaseService(db_url)
            if not db_service.connect():
                connection_issues.append(f"Failed to connect to {db_name} database")
                continue

            if not db_service.test_connection():
                connection_issues.append(
                    f"Connection test failed for {db_name} database"
                )
                continue

            db_stats = self._get_database_stats(db_service)
            if db_stats is None:
                connection_issues.append(f"Failed to get stats from {db_name} database")
                continue

            stats[db_name] = db_stats
            logger.info(
                "Database %s: %d records, dates from %s to %s (%d unique)",
                db_name,
                db_stats["total_records"],
                db_stats["min_date"],
                db_stats["max_date"],
                db_stats["unique_dates"],
            )

        # Analyze results
        comparison_issues = []
        data_integrity_issues = []

        if len(stats) >= 2:
            comparison_issues = self._compare_stats(stats)
            data_integrity_issues = self._compare_sample_data(stats)

        all_issues = connection_issues + comparison_issues + data_integrity_issues
        is_synced = len(all_issues) == 0

        # Prepare detailed report
        report = {
            "sync_status": "synced" if is_synced else "out_of_sync",
            "databases_checked": list(stats.keys()),
            "databases_failed": [db for db in self.databases.keys() if db not in stats],
            "database_stats": stats,
            "issues": {
                "connection": connection_issues,
                "comparison": comparison_issues,
                "data_integrity": data_integrity_issues,
            },
            "total_issues": len(all_issues),
        }

        return is_synced, report

    def print_report(self, is_synced: bool, report: Dict) -> None:
        """Print a human-readable sync report."""
        print("\n" + "=" * 60)
        print("DATABASE SYNCHRONIZATION REPORT")
        print("=" * 60)

        print(f"Status: {'✅ SYNCED' if is_synced else '❌ OUT OF SYNC'}")
        print(f"Databases checked: {len(report['databases_checked'])}")
        print(f"Databases failed: {len(report['databases_failed'])}")
        print(f"Total issues found: {report['total_issues']}")

        if report["databases_checked"]:
            print("\nDatabase Statistics:")
            for db_name in report["databases_checked"]:
                stats = report["database_stats"][db_name]
                print(
                    f"  {db_name}: {stats['total_records']} records, "
                    f"{stats['unique_dates']} unique dates "
                    f"({stats['min_date']} to {stats['max_date']})"
                )

        if report["databases_failed"]:
            print("\nFailed Databases:")
            for db_name in report["databases_failed"]:
                print(f"  ❌ {db_name}")

        # Print issues by category
        for category, issues in report["issues"].items():
            if issues:
                print(f"\n{category.title()} Issues:")
                for issue in issues:
                    print(f"  ❌ {issue}")

        print("\n" + "=" * 60)


def main() -> int:
    """
    Main function to check database synchronization.

    Returns:
        Exit code: 0 if synced, 1 if out of sync, 2 if error
    """
    LoggerFactory.setup_logging()

    try:
        checker = DatabaseSyncChecker()
        is_synced, report = checker.check_sync()

        checker.print_report(is_synced, report)

        if is_synced:
            logger.info("All databases are in sync")
            return 0
        else:
            logger.warning(
                "Databases are out of sync (%d issues)", report["total_issues"]
            )
            return 1

    except Exception as e:
        logger.exception("Database sync check failed: %s", e)
        print(f"\n❌ Sync check failed: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())

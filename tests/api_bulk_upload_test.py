#!/usr/bin/env python3
"""
API Bulk Data Upload Testing Script

Tests the /api/upload-parquet endpoint with real Synapse data.

Usage:
    python tests/api_bulk_upload_test.py --data-dir evaluation_baselines/real_data

Features:
    - Validates API response structure
    - Polls job status until completion
    - Verifies result data quality
    - Tests incremental vs full refresh modes
    - Measures performance metrics
"""

import sys
import time
import requests
import argparse
from pathlib import Path
import json
from typing import Dict, Any, Optional


class APIBulkUploadTester:
    """Test harness for API bulk data upload"""

    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.test_results = []

    def test_health_check(self) -> bool:
        """Test /health endpoint"""
        print("\n1. Testing health endpoint...")
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=5)
            response.raise_for_status()
            data = response.json()

            print(f"  ✓ API is healthy (v{data['version']})")
            print(f"  ✓ Uptime: {data['uptime_seconds']:.1f}s")
            return True
        except Exception as e:
            print(f"  ✗ Health check failed: {e}")
            return False

    def test_upload_parquet(self, data_dir: Path, incremental: bool = True) -> Optional[str]:
        """Test /api/upload-parquet endpoint"""
        mode = "incremental" if incremental else "full"
        print(f"\n2. Testing parquet upload ({mode} mode)...")

        # Find all parquet files
        parquet_files = list(data_dir.glob("*.parquet"))
        if not parquet_files:
            print(f"  ✗ No parquet files found in {data_dir}")
            return None

        print(f"  Found {len(parquet_files)} parquet files:")
        for f in parquet_files:
            print(f"    - {f.name}")

        # Upload files
        files = [('files', (f.name, open(f, 'rb'), 'application/octet-stream')) for f in parquet_files]

        try:
            start_time = time.time()
            response = requests.post(
                f"{self.api_base_url}/api/upload-parquet",
                files=files,
                params={"incremental": incremental},
                timeout=30
            )
            response.raise_for_status()
            upload_time = time.time() - start_time

            data = response.json()
            job_id = data['job_id']

            print(f"  ✓ Upload successful in {upload_time:.2f}s")
            print(f"  ✓ Job ID: {job_id}")
            print(f"  ✓ Files received: {', '.join(data['files_received'])}")

            # Close files
            for _, (_, file_obj, _) in files:
                file_obj.close()

            return job_id
        except Exception as e:
            print(f"  ✗ Upload failed: {e}")
            return None

    def test_job_status_polling(self, job_id: str, timeout: int = 300) -> Optional[Dict[str, Any]]:
        """Test /api/status/{job_id} endpoint with polling"""
        print(f"\n3. Polling job status (timeout: {timeout}s)...")

        start_time = time.time()
        poll_count = 0

        while time.time() - start_time < timeout:
            poll_count += 1
            try:
                response = requests.get(f"{self.api_base_url}/api/status/{job_id}", timeout=10)
                response.raise_for_status()
                data = response.json()

                status = data['status']
                progress = data.get('progress', 0)
                current_step = data.get('current_step', 'Unknown')

                print(f"  [{poll_count}] Status: {status}, Progress: {progress:.1f}%, Step: {current_step}")

                if status == 'completed':
                    elapsed = time.time() - start_time
                    print(f"\n  ✓ Job completed in {elapsed:.1f}s ({poll_count} polls)")
                    return data
                elif status == 'failed':
                    print(f"\n  ✗ Job failed: {data.get('message', 'Unknown error')}")
                    return data

                time.sleep(2)  # Poll every 2 seconds
            except Exception as e:
                print(f"  ✗ Status polling failed: {e}")
                return None

        print(f"\n  ✗ Job timed out after {timeout}s")
        return None

    def test_job_result(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Test /api/result/{job_id} endpoint"""
        print(f"\n4. Fetching job result...")

        try:
            response = requests.get(f"{self.api_base_url}/api/result/{job_id}", timeout=30)
            response.raise_for_status()
            data = response.json()

            summary = data.get('summary', {})
            lineage_data = data.get('data', [])

            print(f"  ✓ Result retrieved successfully")
            print(f"\n  Summary:")
            print(f"    - Nodes: {summary.get('node_count', 0)}")
            print(f"    - Edges: {summary.get('edge_count', 0)}")
            print(f"    - Schemas: {summary.get('schema_count', 0)}")
            print(f"    - Stored Procedures: {summary.get('sp_count', 0)}")
            print(f"    - Tables: {summary.get('table_count', 0)}")
            print(f"    - Phantoms: {summary.get('phantom_count', 0)}")

            # Validate data structure
            if lineage_data:
                sample_node = lineage_data[0]
                required_fields = ['id', 'name', 'object_type', 'schema']
                missing_fields = [f for f in required_fields if f not in sample_node]

                if missing_fields:
                    print(f"  ⚠ Missing fields in data: {missing_fields}")
                else:
                    print(f"  ✓ Data structure valid")

            return data
        except Exception as e:
            print(f"  ✗ Failed to fetch result: {e}")
            return None

    def test_latest_data(self) -> Optional[list]:
        """Test /api/latest-data endpoint"""
        print(f"\n5. Testing latest data endpoint...")

        try:
            response = requests.get(f"{self.api_base_url}/api/latest-data", timeout=30)
            response.raise_for_status()
            data = response.json()

            node_count = response.headers.get('X-Node-Count', '0')
            upload_timestamp = response.headers.get('X-Upload-Timestamp', 'Unknown')

            print(f"  ✓ Latest data retrieved")
            print(f"    - Nodes: {node_count}")
            print(f"    - Upload timestamp: {upload_timestamp}")

            return data
        except Exception as e:
            print(f"  ✗ Failed to fetch latest data: {e}")
            return None

    def run_full_test_suite(self, data_dir: Path, incremental: bool = True) -> bool:
        """Run complete test suite"""
        print("="*60)
        print("API BULK UPLOAD TEST SUITE")
        print("="*60)

        # 1. Health check
        if not self.test_health_check():
            print("\n❌ FAILED: API is not healthy")
            return False

        # 2. Upload parquet files
        job_id = self.test_upload_parquet(data_dir, incremental)
        if not job_id:
            print("\n❌ FAILED: Upload failed")
            return False

        # 3. Poll job status
        status_result = self.test_job_status_polling(job_id)
        if not status_result or status_result.get('status') != 'completed':
            print("\n❌ FAILED: Job did not complete")
            return False

        # 4. Get job result
        result = self.test_job_result(job_id)
        if not result:
            print("\n❌ FAILED: Could not fetch result")
            return False

        # 5. Test latest data endpoint
        latest_data = self.test_latest_data()
        if not latest_data:
            print("\n❌ FAILED: Could not fetch latest data")
            return False

        # Success!
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        return True


def main():
    parser = argparse.ArgumentParser(description="Test API bulk data upload")
    parser.add_argument('--data-dir', type=Path, required=True, help="Directory containing parquet files")
    parser.add_argument('--api-url', default="http://localhost:8000", help="API base URL")
    parser.add_argument('--full-refresh', action='store_true', help="Use full refresh mode instead of incremental")
    args = parser.parse_args()

    if not args.data_dir.exists():
        print(f"Error: Data directory not found: {args.data_dir}")
        sys.exit(1)

    tester = APIBulkUploadTester(api_base_url=args.api_url)
    success = tester.run_full_test_suite(args.data_dir, incremental=not args.full_refresh)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

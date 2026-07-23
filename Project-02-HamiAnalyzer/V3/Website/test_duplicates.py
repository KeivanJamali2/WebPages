#!/usr/bin/env python3
"""
Test script for duplicate detection and removal functionality.
Tests the entire duplicate handling workflow.
"""

from pathlib import Path
import pandas as pd
import shutil
from datetime import datetime
from cleaner import DuplicateDetector


def print_header(title):
    """Print a formatted header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def test_duplicate_detection():
    """Test 1: Verify duplicate detection works correctly"""
    print_header("TEST 1: Duplicate Detection")
    
    detector = DuplicateDetector(Path("database"), "first")
    duplicates = detector.find_duplicates_by_reference()
    
    print(f"\n✓ Found {len(duplicates)} duplicate groups")
    
    if len(duplicates) == 0:
        print("  ⚠️  WARNING: No duplicates found!")
        return False
    
    # Show first few duplicates
    print("\nFirst 5 duplicate groups:")
    for i, (ref_code, records) in enumerate(list(duplicates.items())[:5], 1):
        print(f"\n  {i}. Reference Code: {ref_code}")
        print(f"     Total records: {len(records)}")
        for j, r in enumerate(records, 1):
            print(f"     Record {j}: hami_{r['hami_id']} number={r['number']} month={r['month']} row={r.get('row_index', 'N/A')}")
    
    return True


def test_keep_newer():
    """Test 2: Test keep_newer functionality"""
    print_header("TEST 2: Keep Newer Functionality")
    
    detector = DuplicateDetector(Path("database"), "first")
    duplicates = detector.find_duplicates_by_reference()
    
    if not duplicates:
        print("  ⚠️  No duplicates to test")
        return False
    
    # Test on first 3 duplicate groups
    test_duplicates = dict(list(duplicates.items())[:3])
    
    print(f"\nTesting keep_newer on {len(test_duplicates)} groups...")
    result = detector.keep_newer(test_duplicates)
    
    print(f"\n✓ Results:")
    print(f"  Records kept: {result['kept_count'] if 'kept_count' not in result else len(result['kept_records'])}")
    print(f"  Records removed: {result['removed_count']}")
    
    # Verify results
    print(f"\n✓ Verification:")
    for ref_code, records in test_duplicates.items():
        hami_file = Path(f"database/first/{records[0]['month']}/hami_output/hami_{records[0]['hami_id']}.csv")
        if hami_file.exists():
            df = pd.read_csv(hami_file)
            remaining = len(df[df['reference_code'] == ref_code])
            print(f"  Ref {ref_code}: {remaining} record(s) remaining in hami file")
    
    return result['removed_count'] > 0


def test_keep_older():
    """Test 3: Test keep_older functionality"""
    print_header("TEST 3: Keep Older Functionality")
    
    detector = DuplicateDetector(Path("database"), "first")
    duplicates = detector.find_duplicates_by_reference()
    
    if not duplicates:
        print("  ⚠️  No duplicates to test")
        return False
    
    # Test on first 3 duplicate groups (different from keep_newer test)
    test_duplicates = dict(list(duplicates.items())[3:6])
    
    print(f"\nTesting keep_older on {len(test_duplicates)} groups...")
    result = detector.keep_older(test_duplicates)
    
    print(f"\n✓ Results:")
    print(f"  Records kept: {len(result['kept_records'])}")
    print(f"  Records removed: {result['removed_count']}")
    
    # Verify results
    print(f"\n✓ Verification:")
    for ref_code, records in test_duplicates.items():
        hami_file = Path(f"database/first/{records[0]['month']}/hami_output/hami_{records[0]['hami_id']}.csv")
        if hami_file.exists():
            df = pd.read_csv(hami_file)
            remaining = len(df[df['reference_code'] == ref_code])
            print(f"  Ref {ref_code}: {remaining} record(s) remaining in hami file")
    
    return result['removed_count'] > 0


def test_combined_file_cleanup():
    """Test 4: Verify combined files are properly deleted"""
    print_header("TEST 4: Combined File Cleanup")
    
    detector = DuplicateDetector(Path("database"), "first")
    duplicates = detector.find_duplicates_by_reference()
    
    if not duplicates:
        print("  ⚠️  No duplicates to test")
        return False
    
    # Test on first duplicate group
    test_duplicates = dict(list(duplicates.items())[6:7])
    ref_code = list(test_duplicates.keys())[0]
    records = test_duplicates[ref_code]
    
    print(f"\nTesting file cleanup for ref_code: {ref_code}")
    print(f"Records before cleanup: {len(records)}")
    
    # Check combined files before
    combined_files_before = []
    for r in records:
        combined_file = Path(f"database/first/{r['month']}/combined_output/combined_{r['hami_id']}_{r['number']}.csv")
        exists = combined_file.exists()
        combined_files_before.append(exists)
        print(f"  Before: combined_{r['hami_id']}_{r['number']}.csv: {'EXISTS' if exists else 'MISSING'}")
    
    # Run keep_newer
    result = detector.keep_newer(test_duplicates)
    
    # Check combined files after
    print(f"\n  After removal:")
    combined_files_after = []
    for r in records:
        combined_file = Path(f"database/first/{r['month']}/combined_output/combined_{r['hami_id']}_{r['number']}.csv")
        exists = combined_file.exists()
        combined_files_after.append(exists)
        print(f"  After: combined_{r['hami_id']}_{r['number']}.csv: {'EXISTS' if exists else 'REMOVED ✓'}")
    
    # Verify at least one was deleted
    files_deleted = sum(1 for b, a in zip(combined_files_before, combined_files_after) if b and not a)
    print(f"\n✓ Combined files deleted: {files_deleted}")
    
    return files_deleted > 0


def test_hami_file_integrity():
    """Test 5: Verify hami files maintain integrity after removal"""
    print_header("TEST 5: Hami File Integrity")
    
    detector = DuplicateDetector(Path("database"), "first")
    duplicates = detector.find_duplicates_by_reference()
    
    if not duplicates:
        print("  ⚠️  No duplicates to test")
        return False
    
    # Test on first duplicate
    test_duplicates = dict(list(duplicates.items())[7:8])
    ref_code = list(test_duplicates.keys())[0]
    records = test_duplicates[ref_code]
    hami_id = records[0]['hami_id']
    month = records[0]['month']
    
    hami_file = Path(f"database/first/{month}/hami_output/hami_{hami_id}.csv")
    
    # Read before
    df_before = pd.read_csv(hami_file)
    print(f"\nBefore cleanup:")
    print(f"  Hami file: hami_{hami_id}.csv")
    print(f"  Total records: {len(df_before)}")
    print(f"  Columns: {list(df_before.columns)}")
    
    # Run keep_newer
    result = detector.keep_newer(test_duplicates)
    
    # Read after
    df_after = pd.read_csv(hami_file)
    print(f"\nAfter cleanup:")
    print(f"  Total records: {len(df_after)}")
    print(f"  Columns: {list(df_after.columns)}")
    print(f"  Records removed: {len(df_before) - len(df_after)}")
    
    # Check integrity
    integrity_ok = (
        list(df_before.columns) == list(df_after.columns) and
        len(df_after) < len(df_before) and
        not df_after.isnull().all().any()
    )
    
    if integrity_ok:
        print(f"\n✓ File integrity maintained!")
    else:
        print(f"\n✗ File integrity check FAILED!")
    
    return integrity_ok


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("  DUPLICATE DETECTION AND REMOVAL TEST SUITE")
    print("="*80)
    print(f"  Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  Database path: database/first")
    
    results = {
        "Duplicate Detection": test_duplicate_detection(),
        "Keep Newer": test_keep_newer(),
        "Keep Older": test_keep_older(),
        "Combined File Cleanup": test_combined_file_cleanup(),
        "Hami File Integrity": test_hami_file_integrity(),
    }
    
    # Summary
    print_header("TEST SUMMARY")
    print("\nResults:")
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {test_name:<30} {status}")
    
    total_passed = sum(1 for p in results.values() if p)
    total_tests = len(results)
    
    print(f"\nOverall: {total_passed}/{total_tests} tests passed")
    print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    return all(results.values())


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)

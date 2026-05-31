# -*- coding: utf-8 -*-
"""
Connection Test

Test connection management and exception handling
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from producer.query_client import QueryClient


def test_connection():
    """
    Test connection management
    """
    print("=" * 60)
    print("Connection Test")
    print("=" * 60)
    
    results = []
    
    # Test 1: Normal connection
    print("\nTest 1: Normal Connection")
    try:
        client = QueryClient()
        result = client.query("get_notes")
        if result["status"] == "success":
            print("[OK] Connection successful, query normal")
            results.append(("Normal Connection", "Passed"))
        else:
            print("[FAIL] Query failed")
            results.append(("Normal Connection", "Failed"))
        client.close()
    except Exception as e:
        print(f"[FAIL] Connection failed: {e}")
        results.append(("Normal Connection", "Failed"))
    
    # Test 2: Manual disconnect
    print("\nTest 2: Manual Disconnect")
    try:
        client = QueryClient()
        client.close()
        print("[OK] Disconnect successful")
        results.append(("Disconnect", "Passed"))
    except Exception as e:
        print(f"[FAIL] Disconnect failed: {e}")
        results.append(("Disconnect", "Failed"))
    
    # Test 3: Reconnect after disconnect
    print("\nTest 3: Reconnect After Disconnect")
    try:
        client = QueryClient()
        client.close()
        result = client.query("get_notes")
        if result["status"] == "success":
            print("[OK] Reconnect successful")
            results.append(("Reconnect", "Passed"))
        else:
            print("[FAIL] Query failed after reconnect")
            results.append(("Reconnect", "Failed"))
        client.close()
    except Exception as e:
        print(f"[FAIL] Reconnect failed: {e}")
        results.append(("Reconnect", "Failed"))
    
    # Test 4: Multiple queries
    print("\nTest 4: Multiple Queries")
    try:
        client = QueryClient()
        for i in range(5):
            result = client.query("get_notes")
            if result["status"] != "success":
                raise Exception(f"Query {i+1} failed")
        print("[OK] Multiple queries successful")
        results.append(("Multiple Queries", "Passed"))
        client.close()
    except Exception as e:
        print(f"[FAIL] Multiple queries failed: {e}")
        results.append(("Multiple Queries", "Failed"))
    
    # Print results summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    for name, result in results:
        status = "[OK]" if result == "Passed" else "[FAIL]"
        print(f"{status} {name}: {result}")
    
    passed = sum(1 for _, result in results if result == "Passed")
    total = len(results)
    print(f"\nPass rate: {passed}/{total} ({passed/total*100:.1f}%)")
    
    return passed == total


if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
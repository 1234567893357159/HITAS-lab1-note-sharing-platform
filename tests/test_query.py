# -*- coding: utf-8 -*-
"""
Query Function Test

Test various query functions of QueryClient
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from producer.query_client import QueryClient


def test_query():
    """
    Test query functionality
    """
    print("=" * 60)
    print("Query Function Test")
    print("=" * 60)
    
    client = QueryClient()
    
    tests = [
        {
            "name": "Test 1: Get All Notes",
            "query_type": "get_notes",
            "params": None,
            "check": lambda r: r["status"] == "success" and isinstance(r["data"], list)
        },
        {
            "name": "Test 2: Get Single Note",
            "query_type": "get_note",
            "params": {"note_id": "4cbd6681-8b0d-4de1-ada9-9bf2900a8573"},
            "check": lambda r: r["status"] == "success" and isinstance(r["data"], dict)
        },
        {
            "name": "Test 3: Get Comment List",
            "query_type": "get_comments",
            "params": {"note_id": "4cbd6681-8b0d-4de1-ada9-9bf2900a8573"},
            "check": lambda r: r["status"] == "success" and isinstance(r["data"], list)
        },
        {
            "name": "Test 4: Get Like Count",
            "query_type": "get_like_count",
            "params": {"note_id": "4cbd6681-8b0d-4de1-ada9-9bf2900a8573"},
            "check": lambda r: r["status"] == "success" and isinstance(r["data"], int)
        },
        {
            "name": "Test 5: Unknown Query Type",
            "query_type": "unknown_query",
            "params": None,
            "check": lambda r: r["status"] == "error"
        }
    ]
    
    results = []
    
    for test in tests:
        print(f"\n{test['name']}")
        print(f"Query type: {test['query_type']}")
        print(f"Parameters: {test['params']}")
        
        try:
            result = client.query(test["query_type"], test["params"])
            print(f"Status: {result['status']}")
            
            if test["check"](result):
                print("[OK] Test passed")
                results.append((test["name"], "Passed"))
            else:
                print("[FAIL] Test failed: Unexpected result")
                results.append((test["name"], "Failed"))
        except Exception as e:
            print(f"[FAIL] Test failed: {e}")
            results.append((test["name"], "Failed"))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    for name, result in results:
        status = "[OK]" if result == "Passed" else "[FAIL]"
        print(f"{status} {name}: {result}")
    
    passed = sum(1 for _, result in results if result == "Passed")
    total = len(results)
    print(f"\nPass rate: {passed}/{total} ({passed/total*100:.1f}%)")
    
    client.close()
    
    return passed == total


if __name__ == "__main__":
    success = test_query()
    sys.exit(0 if success else 1)
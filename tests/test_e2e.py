# -*- coding: utf-8 -*-
"""
End-to-End Test

Test complete business flow: publish note -> query -> like -> comment -> verify
"""

import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from producer.producer import MessageProducer
from producer.query_client import QueryClient


def test_e2e():
    """
    End-to-end test
    """
    print("=" * 60)
    print("End-to-End Test")
    print("=" * 60)
    
    producer = MessageProducer()
    client = QueryClient()
    
    results = []
    
    # Step 1: Publish note
    print("\nStep 1: Publish Note")
    try:
        producer.send_message("note/publish", {
            "title": "E2E Test Note",
            "content": "This is end-to-end test content",
            "author": "e2e_test"
        })
        print("[OK] Note published successfully")
        results.append(("Publish Note", "Passed"))
        time.sleep(1)
    except Exception as e:
        print(f"[FAIL] Note publish failed: {e}")
        results.append(("Publish Note", "Failed"))
    
    # Step 2: Query note list
    print("\nStep 2: Query Note List")
    try:
        result = client.query("get_notes")
        if result["status"] == "success" and len(result["data"]) > 0:
            print(f"[OK] Query successful, {len(result['data'])} notes found")
            results.append(("Query Note List", "Passed"))
            note_id = result["data"][0]["id"]
        else:
            print("[FAIL] Query failed or no data")
            results.append(("Query Note List", "Failed"))
            note_id = None
    except Exception as e:
        print(f"[FAIL] Query failed: {e}")
        results.append(("Query Note List", "Failed"))
        note_id = None
    
    # Step 3: Like note
    if note_id:
        print("\nStep 3: Like Note")
        try:
            producer.send_message("note/like", {
                "note_id": note_id,
                "user_id": "e2e_test"
            })
            print("[OK] Like successful")
            results.append(("Like Note", "Passed"))
            time.sleep(1)
        except Exception as e:
            print(f"[FAIL] Like failed: {e}")
            results.append(("Like Note", "Failed"))
    
    # Step 4: Verify like count
    if note_id:
        print("\nStep 4: Verify Like Count")
        try:
            result = client.query("get_like_count", params={"note_id": note_id})
            if result["status"] == "success":
                print(f"[OK] Verification successful, like count: {result['data']}")
                results.append(("Verify Like Count", "Passed"))
            else:
                print("[FAIL] Verification failed")
                results.append(("Verify Like Count", "Failed"))
        except Exception as e:
            print(f"[FAIL] Verification failed: {e}")
            results.append(("Verify Like Count", "Failed"))
    
    # Step 5: Comment note
    if note_id:
        print("\nStep 5: Comment Note")
        try:
            producer.send_message("note/comment", {
                "note_id": note_id,
                "user_id": "e2e_test",
                "content": "E2E Test Comment"
            })
            print("[OK] Comment successful")
            results.append(("Comment Note", "Passed"))
            time.sleep(1)
        except Exception as e:
            print(f"[FAIL] Comment failed: {e}")
            results.append(("Comment Note", "Failed"))
    
    # Step 6: Verify comment
    if note_id:
        print("\nStep 6: Verify Comment")
        try:
            result = client.query("get_comments", params={"note_id": note_id})
            if result["status"] == "success":
                print(f"[OK] Verification successful, comment count: {len(result['data'])}")
                results.append(("Verify Comment", "Passed"))
            else:
                print("[FAIL] Verification failed")
                results.append(("Verify Comment", "Failed"))
        except Exception as e:
            print(f"[FAIL] Verification failed: {e}")
            results.append(("Verify Comment", "Failed"))
    
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
    
    producer.close()
    client.close()
    
    return passed == total


if __name__ == "__main__":
    success = test_e2e()
    sys.exit(0 if success else 1)
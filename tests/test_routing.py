# -*- coding: utf-8 -*-
"""
Message Routing Test

Test message routing functionality of the message middleware
"""

import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from producer.producer import MessageProducer


def test_routing():
    """
    Test message routing functionality
    """
    print("=" * 60)
    print("Message Routing Test")
    print("=" * 60)
    
    producer = MessageProducer()
    
    tests = [
        {
            "name": "Test 1: Publish Note",
            "topic": "note/publish",
            "content": {
                "title": "Test Note",
                "content": "Test Content",
                "author": "test_user"
            }
        },
        {
            "name": "Test 2: Like Note",
            "topic": "note/like",
            "content": {
                "note_id": "test-note-id",
                "user_id": "test-user"
            }
        },
        {
            "name": "Test 3: Comment Note",
            "topic": "note/comment",
            "content": {
                "note_id": "test-note-id",
                "user_id": "test-user",
                "content": "Test Comment"
            }
        },
        {
            "name": "Test 4: Delete Note",
            "topic": "note/delete",
            "content": {
                "note_id": "test-note-id"
            }
        }
    ]
    
    results = []
    
    for test in tests:
        print(f"\n{test['name']}")
        print(f"Topic: {test['topic']}")
        print(f"Content: {test['content']}")
        
        try:
            producer.send_message(test["topic"], test["content"])
            print("[OK] Message sent successfully")
            results.append((test["name"], "Passed"))
        except Exception as e:
            print(f"[FAIL] Message send failed: {e}")
            results.append((test["name"], "Failed"))
        
        time.sleep(0.5)
    
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
    
    return passed == total


if __name__ == "__main__":
    success = test_routing()
    sys.exit(0 if success else 1)
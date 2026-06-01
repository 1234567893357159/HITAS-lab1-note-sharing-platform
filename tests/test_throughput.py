# -*- coding: utf-8 -*-
"""
Throughput Test

Test message throughput of the message middleware
"""

import sys
import os
import time
import uuid

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from producer.producer import MessageProducer


def test_throughput(message_count=10000, test_types=['like']):
    """
    Test message throughput
    
    :param message_count: Number of messages to send
    :param test_types: Types of messages to send ['like', 'publish', 'comment']
    """
    print("=" * 60)
    print(f"Throughput Test - {message_count} messages, types: {test_types}")
    print("=" * 60)
    
    producer = MessageProducer()
    
    start_time = time.time()
    
    for i in range(message_count):
        if 'publish' in test_types and i % 100 == 0:  # ?100?????????
            producer.send_message("note/publish", {
                "note_id": f"test-note-{uuid.uuid4()}",
                "title": f"Test Note {i}",
                "content": f"This is test note content #{i}",
                "author": f"test-author-{i % 100}"
            })
            message_type = "publish"
        elif 'comment' in test_types and i % 10 == 0:  # ?10?????????
            producer.send_message("note/comment", {
                "note_id": f"note-{i % 50}",
                "user_id": f"user-{i}",
                "content": f"Test comment #{i}"
            })
            message_type = "comment"
        else:  # ??????
            producer.send_message("note/like", {
                "note_id": f"note-{i % 100}",
                "user_id": f"user-{i}"
            })
            message_type = "like"
        
        if (i + 1) % 100 == 0:
            print(f"Sent {i + 1}/{message_count} messages (last: {message_type})")
    
    end_time = time.time()
    elapsed = end_time - start_time
    throughput = message_count / elapsed
    
    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)
    print(f"Messages sent: {message_count}")
    print(f"Total time: {elapsed:.2f} seconds")
    print(f"Throughput: {throughput:.2f} messages/sec")
    print(f"Avg latency: {elapsed/message_count*1000:.2f} ms")
    
    producer.close()
    
    return {
        "message_count": message_count,
        "elapsed": elapsed,
        "throughput": throughput,
        "avg_latency": elapsed / message_count * 1000,
        "test_types": test_types
    }


if __name__ == "__main__":
    result = test_throughput(1000, ['like', 'publish', 'comment'])
    sys.exit(0 if result["throughput"] > 0 else 1)
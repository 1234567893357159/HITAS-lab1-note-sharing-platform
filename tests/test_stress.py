# -*- coding: utf-8 -*-
"""
Stress Test

Test system performance under high load
"""

import sys
import os
import time
import threading
import uuid

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from producer.producer import MessageProducer


def stress_producer(thread_id, message_count=100, test_types=['like']):
    """
    Stress test producer
    
    :param thread_id: Thread ID
    :param message_count: Number of messages per thread
    :param test_types: Types of messages to send ['like', 'publish', 'comment']
    """
    producer = MessageProducer()
    
    for i in range(message_count):
        if 'publish' in test_types and i % 50 == 0:  # ?50?????????
            producer.send_message("note/publish", {
                "note_id": f"stress-note-{thread_id}-{uuid.uuid4()}",
                "title": f"Stress Test Note {thread_id}-{i}",
                "content": f"This is stress test note content #{i} from thread {thread_id}",
                "author": f"stress-author-{thread_id}"
            })
            message_type = "publish"
        elif 'comment' in test_types and i % 10 == 0:  # ?10?????????
            producer.send_message("note/comment", {
                "note_id": f"note-{thread_id}-{i % 20}",
                "user_id": f"thread-{thread_id}-user-{i}",
                "content": f"Stress test comment #{i} from thread {thread_id}"
            })
            message_type = "comment"
        else:  # ??????
            producer.send_message("note/like", {
                "note_id": f"note-{thread_id}",
                "user_id": f"thread-{thread_id}-user-{i}"
            })
            message_type = "like"
    
    print(f"Thread {thread_id} completed {message_count} messages (types: {test_types})")
    
    producer.close()


def test_stress(thread_count=20, message_count=100, test_types=['like']):
    """
    Stress test
    
    :param thread_count: Number of threads
    :param message_count: Number of messages per thread
    :param test_types: Types of messages to send ['like', 'publish', 'comment']
    """
    print("=" * 60)
    print(f"Stress Test - {thread_count} threads x {message_count} messages, types: {test_types}")
    print("=" * 60)
    
    threads = []
    start_time = time.time()
    
    print(f"Starting to send messages...\n")
    
    for i in range(thread_count):
        thread = threading.Thread(
            target=lambda tid=i: stress_producer(tid, message_count, test_types)
        )
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    total_time = end_time - start_time
    total_messages = thread_count * message_count
    
    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)
    print(f"Total messages: {total_messages}")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Throughput: {total_messages/total_time:.2f} messages/sec")
    print(f"Avg latency: {total_time/total_messages*1000:.2f} ms")
    
    return {
        "thread_count": thread_count,
        "message_count": message_count,
        "total_messages": total_messages,
        "total_time": total_time,
        "throughput": total_messages / total_time,
        "avg_latency": total_time / total_messages * 1000,
        "test_types": test_types
    }


if __name__ == "__main__":
    result = test_stress(20, 100, ['like', 'publish', 'comment'])
    sys.exit(0 if result["throughput"] > 0 else 1)
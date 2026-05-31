# -*- coding: utf-8 -*-
"""
Stress Test

Test system performance under high load
"""

import sys
import os
import time
import threading

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from producer.producer import MessageProducer


def stress_producer(thread_id, message_count=100):
    """
    Stress test producer
    
    :param thread_id: Thread ID
    :param message_count: Number of messages per thread
    """
    producer = MessageProducer()
    
    for i in range(message_count):
        producer.send_message("note/like", {
            "note_id": f"note-{thread_id}",
            "user_id": f"user-{i}"
        })
    
    print(f"Thread {thread_id} completed {message_count} messages")
    
    producer.close()


def test_stress(thread_count=20, message_count=100):
    """
    Stress test
    
    :param thread_count: Number of threads
    :param message_count: Number of messages per thread
    """
    print("=" * 60)
    print(f"Stress Test - {thread_count} threads x {message_count} messages")
    print("=" * 60)
    
    threads = []
    start_time = time.time()
    
    print(f"Starting to send messages...\n")
    
    for i in range(thread_count):
        thread = threading.Thread(
            target=lambda tid=i: stress_producer(tid, message_count)
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
        "avg_latency": total_time / total_messages * 1000
    }


if __name__ == "__main__":
    result = test_stress(20, 100)
    sys.exit(0 if result["throughput"] > 0 else 1)
# -*- coding: utf-8 -*-
"""
Throughput Test

Test message throughput of the message middleware
"""

import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from producer.producer import MessageProducer


def test_throughput(message_count=1000):
    """
    Test message throughput
    
    :param message_count: Number of messages to send
    """
    print("=" * 60)
    print(f"Throughput Test - {message_count} messages")
    print("=" * 60)
    
    producer = MessageProducer()
    
    start_time = time.time()
    
    for i in range(message_count):
        producer.send_message("note/like", {
            "note_id": f"note-{i % 10}",
            "user_id": f"user-{i}"
        })
        
        if (i + 1) % 100 == 0:
            print(f"Sent {i + 1}/{message_count} messages")
    
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
        "avg_latency": elapsed / message_count * 1000
    }


if __name__ == "__main__":
    result = test_throughput(1000)
    sys.exit(0 if result["throughput"] > 0 else 1)
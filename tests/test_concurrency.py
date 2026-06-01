# -*- coding: utf-8 -*-
"""
Concurrency Test

Test system performance under high concurrency
"""

import sys
import os
import time
import threading

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from producer.query_client import QueryClient


def concurrent_query(thread_id, query_count=10, query_types=['get_notes']):
    """
    Concurrent query function
    
    :param thread_id: Thread ID
    :param query_count: Number of queries per thread
    :param query_types: Types of queries to perform
    :return: Average response time
    """
    client = QueryClient()
    latencies = []
    
    for i in range(query_count):
        start_time = time.time()
        
        # ???????????
        query_type = query_types[i % len(query_types)]
        if query_type == "get_notes":
            result = client.query("get_notes")
        elif query_type == "get_like_count":
            # ?????note_id????
            result = client.query("get_like_count", params={"note_id": f"note-{i % 10}"})
        elif query_type == "get_comments":
            result = client.query("get_comments", params={"note_id": f"note-{i % 10}"})
        else:
            result = client.query(query_type)
        
        end_time = time.time()
        
        latency = (end_time - start_time) * 1000
        latencies.append(latency)
    
    avg_latency = sum(latencies) / len(latencies)
    print(f"Thread {thread_id}: Avg response time {avg_latency:.2f} ms for {query_types}")
    
    client.close()
    
    return avg_latency


def test_concurrency(thread_count=10, query_count=10, query_types=['get_notes']):
    """
    Concurrency test
    
    :param thread_count: Number of threads
    :param query_count: Number of queries per thread
    :param query_types: Types of queries to perform
    """
    print("=" * 60)
    print(f"Concurrency Test - {thread_count} threads x {query_count} queries, types: {query_types}")
    print("=" * 60)
    
    threads = []
    results = []
    
    start_time = time.time()
    
    for i in range(thread_count):
        thread = threading.Thread(
            target=lambda tid=i: results.append(concurrent_query(tid, query_count, query_types))
        )
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    end_time = time.time()
    total_time = end_time - start_time
    total_queries = thread_count * query_count
    
    avg_latency = sum(results) / len(results)
    max_latency = max(results)
    min_latency = min(results)
    
    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)
    print(f"Thread count: {thread_count}")
    print(f"Queries per thread: {query_count}")
    print(f"Total queries: {total_queries}")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"System throughput: {total_queries/total_time:.2f} queries/sec")
    print(f"Avg response time: {avg_latency:.2f} ms")
    print(f"Max response time: {max_latency:.2f} ms")
    print(f"Min response time: {min_latency:.2f} ms")
    
    return {
        "thread_count": thread_count,
        "query_count": query_count,
        "total_queries": total_queries,
        "total_time": total_time,
        "throughput": total_queries / total_time,
        "avg_latency": avg_latency,
        "max_latency": max_latency,
        "min_latency": min_latency,
        "query_types": query_types
    }


if __name__ == "__main__":
    result = test_concurrency(10, 10, ['get_notes', 'get_like_count', 'get_comments'])
    sys.exit(0 if result["throughput"] > 0 else 1)
# -*- coding: utf-8 -*-
"""
Query Latency Test

Test query response time performance
"""

import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from producer.query_client import QueryClient


def test_query_latency(query_count=100):
    """
    Test query response time
    
    :param query_count: Number of queries
    """
    print("=" * 60)
    print(f"Query Latency Test - {query_count} queries")
    print("=" * 60)
    
    client = QueryClient()
    latencies = []
    
    for i in range(query_count):
        start_time = time.time()
        result = client.query("get_notes")
        end_time = time.time()
        
        latency = (end_time - start_time) * 1000
        latencies.append(latency)
        
        if (i + 1) % 20 == 0:
            print(f"Completed {i + 1}/{query_count} queries")
    
    avg_latency = sum(latencies) / len(latencies)
    max_latency = max(latencies)
    min_latency = min(latencies)
    
    latencies_sorted = sorted(latencies)
    p50 = latencies_sorted[int(len(latencies) * 0.5)]
    p95 = latencies_sorted[int(len(latencies) * 0.95)]
    p99 = latencies_sorted[int(len(latencies) * 0.99)]
    
    print("\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)
    print(f"Query count: {query_count}")
    print(f"Avg response time: {avg_latency:.2f} ms")
    print(f"Min response time: {min_latency:.2f} ms")
    print(f"Max response time: {max_latency:.2f} ms")
    print(f"P50 response time: {p50:.2f} ms")
    print(f"P95 response time: {p95:.2f} ms")
    print(f"P99 response time: {p99:.2f} ms")
    
    client.close()
    
    return {
        "query_count": query_count,
        "avg_latency": avg_latency,
        "min_latency": min_latency,
        "max_latency": max_latency,
        "p50": p50,
        "p95": p95,
        "p99": p99
    }


if __name__ == "__main__":
    result = test_query_latency(100)
    sys.exit(0 if result["avg_latency"] > 0 else 1)
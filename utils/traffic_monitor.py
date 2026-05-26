"""
流量监控模块

用于收集和统计消息中间件的性能指标，包括：
1. 吞吐量分析（Throughput）
2. 延迟分析（Latency）
"""

import os
import datetime
import threading
import time
import bisect

from .logger import ComponentLogger


class TrafficMonitor:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(TrafficMonitor, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def initialize(self, log_dir=None):
        """
        初始化流量监控器
        
        :param log_dir: 日志目录，默认使用 ComponentLogger 的日志目录
        """
        if self._initialized:
            return
            
        self._initialized = True
        
        # 使用 ComponentLogger 的日志目录（如 log_20260526_1726）
        if log_dir:
            self.log_dir = log_dir
        else:
            ComponentLogger.initialize_log_dir()
            self.log_dir = ComponentLogger._log_dir
        
        # 确保日志目录存在
        os.makedirs(self.log_dir, exist_ok=True)
        
        # 服务启动时间
        self.start_time = time.time()
        
        # 性能统计数据
        self.stats = {
            # 消息统计
            "messages_received": 0,
            "messages_dispatched": 0,
            
            # 查询统计
            "queries_received": 0,
            "queries_dispatched": 0,
            
            # 延迟统计（毫秒）
            "latency_total": 0,
            "latency_count": 0,
            "latency_max": 0,
            "latency_min": float('inf'),
            "latency_samples": [],
        }
        
        # 消息时间戳记录
        self.message_timestamps = {}
        
        # 时间窗口计数器
        self.throughput_window = {
            "messages": [],
            "queries": []
        }
        
        # 性能日志文件
        self.performance_log_file = os.path.join(self.log_dir, "performance.log")
        
        # 定期输出线程
        self.is_running = True
        self.report_thread = threading.Thread(target=self._periodic_report, daemon=True)
        self.report_thread.start()
        
        # 线程锁
        self.stats_lock = threading.Lock()
        self.log_lock = threading.Lock()

    def record_message_received(self, topic):
        """
        记录接收到的消息
        
        :param topic: 消息主题
        """
        with self.stats_lock:
            self.stats["messages_received"] += 1
            
            # 记录消息时间戳
            message_id = f"{topic}_{int(time.time() * 1000)}_{self.stats['messages_received']}"
            self.message_timestamps[message_id] = time.time()
            
            # 记录到吞吐量窗口
            now = time.time()
            self.throughput_window["messages"].append(now)
            self.throughput_window["messages"] = [t for t in self.throughput_window["messages"] if now - t <= 60]

    def record_message_dispatched(self, topic, message_id=None):
        """
        记录已分发的消息
        
        :param topic: 消息主题
        :param message_id: 消息ID
        """
        with self.stats_lock:
            self.stats["messages_dispatched"] += 1
            
            # 计算延迟
            if message_id and message_id in self.message_timestamps:
                latency = (time.time() - self.message_timestamps[message_id]) * 1000
                self.stats["latency_total"] += latency
                self.stats["latency_count"] += 1
                self.stats["latency_max"] = max(self.stats["latency_max"], latency)
                self.stats["latency_min"] = min(self.stats["latency_min"], latency)
                if self.stats["latency_count"] <= 10000:
                    bisect.insort(self.stats["latency_samples"], latency)
                del self.message_timestamps[message_id]

    def record_query_received(self, query_type):
        """
        记录接收到的查询请求
        
        :param query_type: 查询类型
        """
        with self.stats_lock:
            self.stats["queries_received"] += 1
            
            # 记录到吞吐量窗口
            now = time.time()
            self.throughput_window["queries"].append(now)
            self.throughput_window["queries"] = [t for t in self.throughput_window["queries"] if now - t <= 60]

    def record_query_dispatched(self, query_type):
        """
        记录已分发的查询请求
        
        :param query_type: 查询类型
        """
        with self.stats_lock:
            self.stats["queries_dispatched"] += 1

    def record_connection_open(self):
        """记录新连接（保留接口，不记录）"""
        pass

    def record_connection_close(self):
        """记录连接关闭（保留接口，不记录）"""
        pass

    def record_error(self, error_type, message):
        """记录错误（保留接口，不记录）"""
        pass

    def record_queue_depth(self, depth):
        """记录队列深度（保留接口，不记录）"""
        pass

    def _get_percentile(self, percentile):
        """
        计算延迟百分位数
        
        :param percentile: 百分位数 (0-100)
        :return: 延迟值（毫秒）
        """
        samples = self.stats["latency_samples"]
        if not samples:
            return 0.0
        
        index = int(percentile / 100.0 * (len(samples) - 1))
        return samples[index] if index < len(samples) else samples[-1]

    def _get_throughput(self):
        """
        计算当前吞吐量
        
        :return: (消息吞吐量, 查询吞吐量)
        """
        now = time.time()
        
        msg_window = [t for t in self.throughput_window["messages"] if now - t <= 60]
        msg_throughput = len(msg_window) / 60.0 if len(msg_window) > 0 else 0.0
        
        qry_window = [t for t in self.throughput_window["queries"] if now - t <= 60]
        qry_throughput = len(qry_window) / 60.0 if len(qry_window) > 0 else 0.0
        
        return (msg_throughput, qry_throughput)

    def _get_average_throughput(self):
        """
        计算平均吞吐量
        
        :return: (平均消息吞吐量, 平均查询吞吐量)
        """
        elapsed = time.time() - self.start_time
        if elapsed < 1:
            return (0.0, 0.0)
        
        msg_avg = self.stats["messages_received"] / elapsed
        qry_avg = self.stats["queries_received"] / elapsed
        
        return (msg_avg, qry_avg)

    def _periodic_report(self):
        """定期输出性能报告（每10秒）"""
        while self.is_running:
            time.sleep(10)
            self._generate_report()

    def _generate_report(self):
        """生成性能报告（仅包含吞吐量和延迟）"""
        with self.stats_lock:
            # 计算性能指标
            avg_latency = (self.stats["latency_total"] / self.stats["latency_count"]) if self.stats["latency_count"] > 0 else 0
            p50_latency = self._get_percentile(50)
            p90_latency = self._get_percentile(90)
            p95_latency = self._get_percentile(95)
            p99_latency = self._get_percentile(99)
            
            # 吞吐量
            current_msg_tp, current_qry_tp = self._get_throughput()
            avg_msg_tp, avg_qry_tp = self._get_average_throughput()
            
            # 运行时长
            elapsed = time.time() - self.start_time
            elapsed_str = self._format_duration(elapsed)
            
            # 精简报告格式
            report = [
                f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 运行时长: {elapsed_str}",
                f"[吞吐量] 消息: {current_msg_tp:.2f} msg/s (平均: {avg_msg_tp:.2f}), 查询: {current_qry_tp:.2f} qps (平均: {avg_qry_tp:.2f})",
                f"[延迟] 平均: {avg_latency:.2f} ms, P50: {p50_latency:.2f} ms, P90: {p90_latency:.2f} ms, P95: {p95_latency:.2f} ms, P99: {p99_latency:.2f} ms",
                f"[统计] 消息总数: {self.stats['messages_received']}, 查询总数: {self.stats['queries_received']}",
                ""
            ]
            
            # 写入报告到日志文件
            with self.log_lock:
                with open(self.performance_log_file, "a", encoding="utf-8") as f:
                    f.write("\n".join(report))

    def _format_duration(self, seconds):
        """格式化持续时间"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h{minutes}m{secs}s"
        elif minutes > 0:
            return f"{minutes}m{secs}s"
        else:
            return f"{secs}s"

    def get_stats(self):
        """获取当前统计数据"""
        with self.stats_lock:
            avg_latency = (self.stats["latency_total"] / self.stats["latency_count"]) if self.stats["latency_count"] > 0 else 0
            current_msg_tp, current_qry_tp = self._get_throughput()
            avg_msg_tp, avg_qry_tp = self._get_average_throughput()
            
            return {
                **{k: v for k, v in self.stats.items()},
                "avg_latency": avg_latency,
                "p50_latency": self._get_percentile(50),
                "p90_latency": self._get_percentile(90),
                "p95_latency": self._get_percentile(95),
                "p99_latency": self._get_percentile(99),
                "current_message_throughput": current_msg_tp,
                "current_query_throughput": current_qry_tp,
                "average_message_throughput": avg_msg_tp,
                "average_query_throughput": avg_qry_tp,
                "uptime": time.time() - self.start_time
            }

    def reset_stats(self):
        """重置统计数据"""
        with self.stats_lock:
            self.start_time = time.time()
            self.stats = {
                "messages_received": 0,
                "messages_dispatched": 0,
                "queries_received": 0,
                "queries_dispatched": 0,
                "latency_total": 0,
                "latency_count": 0,
                "latency_max": 0,
                "latency_min": float('inf'),
                "latency_samples": [],
            }
            self.message_timestamps = {}
            self.throughput_window = {"messages": [], "queries": []}
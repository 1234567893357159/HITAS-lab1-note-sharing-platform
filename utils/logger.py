import os
import datetime
import traceback
import threading


class ComponentLogger:
    _log_dir = None
    _loggers = {}
    _lock = threading.Lock()

    @classmethod
    def initialize_log_dir(cls):
        if cls._log_dir is None:
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            main_log_dir = os.path.join(project_root, "log")
            date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M")
            cls._log_dir = os.path.join(main_log_dir, f"log_{date_str}")
            try:
                os.makedirs(cls._log_dir, exist_ok=True)
                print(f"[Logger] 日志目录已创建: {cls._log_dir}")
            except Exception as e:
                print(f"[Logger] 创建日志目录失败: {e}")
                traceback.print_exc()

    @classmethod
    def get_logger(cls, component_name):
        cls.initialize_log_dir()
        if component_name not in cls._loggers:
            cls._loggers[component_name] = cls(component_name)
        return cls._loggers[component_name]

    def __init__(self, component_name):
        self.component_name = component_name
        self.log_file = os.path.join(self._log_dir, f"{component_name}.log")

    def log(self, message):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"

        # print(message)

        try:
            with ComponentLogger._lock:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(log_message)
        except Exception as e:
            print(f"[Logger] 写入日志失败: {e}")
            traceback.print_exc()
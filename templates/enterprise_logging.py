"""
企业级日志系统 - 适用于大型项目的日志管理方案
===========================================================
特性：
- 多级别日志分离
- 自动日志轮转
- 结构化日志输出(JSON)
- 异步日志记录
- 上下文追踪(request_id)
"""

import logging
import logging.handlers
import json
import os
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from contextvars import ContextVar
from functools import wraps


# 上下文变量 - 用于追踪请求ID
request_id_var: ContextVar[str] = ContextVar('request_id', default='N/A')


@dataclass
class LogConfig:
    """日志配置类"""
    app_name: str = "MyApp"
    log_dir: str = "./logs"
    level: str = "INFO"
    max_bytes: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    enable_console: bool = True
    enable_file: bool = True
    enable_json: bool = True
    format_string: Optional[str] = None


class JSONFormatter(logging.Formatter):
    """
    JSON格式日志格式化器
    便于日志收集系统(ELK/Loki)处理
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread': record.thread,
            'request_id': request_id_var.get(),
        }
        
        # 添加额外字段
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        # 添加异常信息
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """带颜色的控制台日志格式"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # 青色
        'INFO': '\033[32m',       # 绿色
        'WARNING': '\033[33m',    # 黄色
        'ERROR': '\033[31m',      # 红色
        'CRITICAL': '\033[35m',   # 紫色
        'RESET': '\033[0m'
    }
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        formatted = f"{color}[{record.levelname}]{reset} "
        formatted += f"[{datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')}] "
        formatted += f"[{request_id_var.get()}] "
        formatted += f"{record.name}: {record.getMessage()}"
        
        return formatted


class LoggerManager:
    """
    企业级日志管理器
    
    功能：
    - 自动创建日志目录
    - 分离不同级别的日志到不同文件
    - 支持JSON格式便于日志分析
    - 线程安全的单例实现
    """
    
    _instance: Optional['LoggerManager'] = None
    _lock = threading.Lock()
    _initialized = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, config: Optional[LogConfig] = None):
        if LoggerManager._initialized:
            return
        
        self.config = config or LogConfig()
        self.loggers: Dict[str, logging.Logger] = {}
        self._setup()
        LoggerManager._initialized = True
    
    def _setup(self):
        """初始化日志配置"""
        # 创建日志目录
        log_dir = Path(self.config.log_dir)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # 配置根日志器
        self.root_logger = logging.getLogger()
        self.root_logger.setLevel(getattr(logging, self.config.level.upper()))
        
        # 清除现有处理器
        self.root_logger.handlers = []
        
        # 添加处理器
        if self.config.enable_console:
            self._add_console_handler()
        
        if self.config.enable_file:
            self._add_file_handlers()
    
    def _add_console_handler(self):
        """添加控制台处理器"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(ColoredFormatter())
        self.root_logger.addHandler(console_handler)
    
    def _add_file_handlers(self):
        """添加文件处理器（按级别分离）"""
        log_dir = Path(self.config.log_dir)
        app_name = self.config.app_name.lower()
        
        # 1. 所有日志
        all_handler = logging.handlers.RotatingFileHandler(
            log_dir / f"{app_name}_all.log",
            maxBytes=self.config.max_bytes,
            backupCount=self.config.backup_count,
            encoding='utf-8'
        )
        all_handler.setLevel(logging.DEBUG)
        all_handler.setFormatter(self._get_text_formatter())
        self.root_logger.addHandler(all_handler)
        
        # 2. 错误日志
        error_handler = logging.handlers.RotatingFileHandler(
            log_dir / f"{app_name}_error.log",
            maxBytes=self.config.max_bytes,
            backupCount=self.config.backup_count,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(self._get_text_formatter())
        self.root_logger.addHandler(error_handler)
        
        # 3. JSON格式日志（用于日志收集系统）
        if self.config.enable_json:
            json_handler = logging.handlers.RotatingFileHandler(
                log_dir / f"{app_name}_json.log",
                maxBytes=self.config.max_bytes,
                backupCount=self.config.backup_count,
                encoding='utf-8'
            )
            json_handler.setLevel(logging.DEBUG)
            json_handler.setFormatter(JSONFormatter())
            self.root_logger.addHandler(json_handler)
    
    def _get_text_formatter(self) -> logging.Formatter:
        """获取文本格式器"""
        fmt = self.config.format_string or \
              '%(asctime)s - %(name)s - %(levelname)s - [%(thread)d] - %(message)s'
        return logging.Formatter(fmt, datefmt='%Y-%m-%d %H:%M:%S')
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取命名日志器"""
        if name not in self.loggers:
            self.loggers[name] = logging.getLogger(name)
        return self.loggers[name]
    
    def set_request_id(self, request_id: str):
        """设置当前请求的追踪ID"""
        request_id_var.set(request_id)


def with_request_id(request_id: str):
    """
    为函数设置request_id的上下文装饰器
    
    示例:
        @with_request_id("req-123")
        def process_data():
            logger.info("处理数据")
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            token = request_id_var.set(request_id)
            try:
                return func(*args, **kwargs)
            finally:
                request_id_var.reset(token)
        return wrapper
    return decorator


def log_execution(logger: Optional[logging.Logger] = None):
    """
    自动记录函数执行的装饰器
    
    示例:
        @log_execution()
        def my_function():
            pass
    """
    def decorator(func):
        nonlocal logger
        if logger is None:
            logger = logging.getLogger(func.__module__)
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.debug(f"开始执行 {func.__name__}")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"成功执行 {func.__name__}")
                return result
            except Exception as e:
                logger.error(f"执行 {func.__name__} 失败: {e}", exc_info=True)
                raise
        return wrapper
    return decorator


# ============ 便捷函数 ============

def get_logger(name: str = None) -> logging.Logger:
    """快速获取日志器"""
    return LoggerManager().get_logger(name or __name__)


def init_logging(config: Optional[LogConfig] = None) -> LoggerManager:
    """初始化日志系统"""
    return LoggerManager(config)


# ============ 使用示例 ============

def demo():
    """日志系统演示"""
    # 初始化配置
    config = LogConfig(
        app_name="EnterpriseApp",
        log_dir="./logs",
        level="DEBUG",
        enable_json=True
    )
    
    # 初始化
    log_manager = init_logging(config)
    logger = get_logger("demo")
    
    print("=" * 50)
    print("企业级日志系统演示")
    print("=" * 50)
    
    # 基本日志
    logger.debug("这是调试信息")
    logger.info("这是普通信息")
    logger.warning("这是警告信息")
    logger.error("这是错误信息")
    
    # 带request_id的日志
    print("\n带请求ID的日志:")
    log_manager.set_request_id("req-abc-123")
    logger.info("处理用户请求")
    logger.info("查询数据库")
    logger.info("返回结果")
    
    # 结构化日志
    print("\n结构化日志（带额外字段）:")
    extra = {
        'extra_data': {
            'user_id': 12345,
            'action': 'login',
            'ip': '192.168.1.1'
        }
    }
    logger.info("用户登录", extra=extra)
    
    # 异常日志
    print("\n异常日志:")
    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("发生除零错误")
    
    # 使用装饰器
    print("\n使用装饰器自动记录:")
    
    @log_execution()
    def process_order(order_id: str):
        logger.info(f"处理订单: {order_id}")
        return {"order_id": order_id, "status": "completed"}
    
    @with_request_id("req-order-456")
    def handle_request():
        logger.info("开始处理请求")
        result = process_order("ORD-2024-001")
        logger.info("请求处理完成")
        return result
    
    handle_request()
    
    print("\n" + "=" * 50)
    print("日志已写入 ./logs 目录")
    print("  - enterpriseapp_all.log - 所有日志")
    print("  - enterpriseapp_error.log - 错误日志")
    print("  - enterpriseapp_json.log - JSON格式日志")
    print("=" * 50)


if __name__ == '__main__':
    demo()

"""
装饰器与元编程工具集 - 企业级Python增强工具
===========================================================
适用场景：性能监控、权限控制、缓存、日志记录等企业级需求
核心概念：装饰器、描述符、元类、动态属性
"""

import functools
import time
import logging
import weakref
from typing import Any, Callable, Dict, Optional, Type, Union
from functools import wraps
from datetime import datetime, timedelta
import threading
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============ 1. 性能监控装饰器 ============

def timer(prefix: str = ""):
    """
    函数执行时间计时器
    
    示例:
        @timer("数据处理")
        def process_data():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed = time.perf_counter() - start
            logger.info(f"{prefix}[{func.__name__}] 执行时间: {elapsed:.4f}秒")
            return result
        return wrapper
    return decorator


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable] = None
):
    """
    智能重试装饰器
    
    示例:
        @retry(max_attempts=3, delay=2.0, exceptions=(ConnectionError,))
        def connect_to_server():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"{func.__name__} 第{attempt}次尝试失败: {e}, "
                            f"{delay}秒后重试..."
                        )
                        if on_retry:
                            on_retry(attempt, e)
                        time.sleep(delay * attempt)  # 指数退避
                    else:
                        logger.error(f"{func.__name__} 达到最大重试次数")
            raise last_exception
        return wrapper
    return decorator


def rate_limit(max_calls: int, period: float):
    """
    限流装饰器 - 控制函数调用频率
    
    示例:
        @rate_limit(max_calls=10, period=60)  # 每分钟最多10次
        def api_call():
            pass
    """
    def decorator(func: Callable) -> Callable:
        calls = []
        lock = threading.Lock()
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            with lock:
                now = time.time()
                # 清理过期的调用记录
                calls[:] = [c for c in calls if now - c < period]
                
                if len(calls) >= max_calls:
                    sleep_time = period - (now - calls[0])
                    logger.warning(f"限流触发，等待{sleep_time:.2f}秒")
                    time.sleep(sleep_time)
                
                calls.append(time.time())
            return func(*args, **kwargs)
        return wrapper
    return decorator


# ============ 2. 缓存装饰器 ============

class Memoize:
    """
    高级缓存装饰器，支持TTL和最大容量
    
    示例:
        @Memoize(ttl=300, maxsize=1000)
        def expensive_function(x, y):
            return x ** y
    """
    
    def __init__(self, ttl: Optional[int] = None, maxsize: int = 128):
        self.ttl = ttl  # 过期时间(秒)
        self.maxsize = maxsize
        self.cache: Dict = {}
        self.timestamps: Dict = {}
        self._lock = threading.RLock()
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = self._make_key(args, kwargs)
            
            with self._lock:
                # 检查缓存是否有效
                if key in self.cache:
                    if self.ttl is None or \
                       time.time() - self.timestamps[key] < self.ttl:
                        logger.debug(f"缓存命中: {func.__name__}{args}")
                        return self.cache[key]
                    else:
                        # 过期清理
                        del self.cache[key]
                        del self.timestamps[key]
                
                # 清理最旧的条目
                if len(self.cache) >= self.maxsize:
                    oldest = min(self.timestamps, key=self.timestamps.get)
                    del self.cache[oldest]
                    del self.timestamps[oldest]
                
                # 执行并缓存结果
                result = func(*args, **kwargs)
                self.cache[key] = result
                self.timestamps[key] = time.time()
                return result
        
        wrapper.cache_clear = self._clear_cache
        wrapper.cache_info = self._get_info
        return wrapper
    
    def _make_key(self, args, kwargs):
        """生成缓存键"""
        return (args, tuple(sorted(kwargs.items())))
    
    def _clear_cache(self):
        """清空缓存"""
        with self._lock:
            self.cache.clear()
            self.timestamps.clear()
    
    def _get_info(self):
        """获取缓存信息"""
        with self._lock:
            return {
                'size': len(self.cache),
                'maxsize': self.maxsize,
                'ttl': self.ttl
            }


# ============ 3. 单例模式元类 ============

class SingletonMeta(type):
    """
    线程安全的单例元类
    
    示例:
        class Database(metaclass=SingletonMeta):
            def __init__(self):
                self.connection = None
    """
    _instances: Dict[Type, Any] = {}
    _lock: threading.Lock = threading.Lock()
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
        return cls._instances[cls]


# ============ 4. 属性验证描述符 ============

class ValidatedProperty:
    """
    带验证的属性描述符
    
    示例:
        class User:
            age = ValidatedProperty("age", int, min_val=0, max_val=150)
            name = ValidatedProperty("name", str, min_len=1, max_len=50)
    """
    
    def __init__(
        self,
        name: str,
        expected_type: Type,
        min_val: Optional[Union[int, float]] = None,
        max_val: Optional[Union[int, float]] = None,
        min_len: Optional[int] = None,
        max_len: Optional[int] = None,
        validator: Optional[Callable] = None
    ):
        self.name = name
        self.expected_type = expected_type
        self.min_val = min_val
        self.max_val = max_val
        self.min_len = min_len
        self.max_len = max_len
        self.validator = validator
        self.values = weakref.WeakKeyDictionary()
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        return self.values.get(instance)
    
    def __set__(self, instance, value):
        # 类型检查
        if not isinstance(value, self.expected_type):
            raise TypeError(
                f"{self.name} 必须是 {self.expected_type.__name__} 类型, "
                f"实际为 {type(value).__name__}"
            )
        
        # 数值范围检查
        if self.min_val is not None and value < self.min_val:
            raise ValueError(f"{self.name} 不能小于 {self.min_val}")
        if self.max_val is not None and value > self.max_val:
            raise ValueError(f"{self.name} 不能大于 {self.max_val}")
        
        # 长度检查
        if hasattr(value, '__len__'):
            if self.min_len is not None and len(value) < self.min_len:
                raise ValueError(f"{self.name} 长度不能小于 {self.min_len}")
            if self.max_len is not None and len(value) > self.max_len:
                raise ValueError(f"{self.name} 长度不能大于 {self.max_len}")
        
        # 自定义验证
        if self.validator and not self.validator(value):
            raise ValueError(f"{self.name} 未通过自定义验证")
        
        self.values[instance] = value


# ============ 5. 类增强器 ============

def singleton(cls: Type) -> Type:
    """
    单例装饰器（替代元类方案）
    """
    instances: Dict[Type, Any] = {}
    lock = threading.Lock()
    
    @wraps(cls)
    def wrapper(*args, **kwargs):
        if cls not in instances:
            with lock:
                if cls not in instances:
                    instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    
    return wrapper


def deprecated(reason: str = ""):
    """
    标记废弃函数的装饰器
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger.warning(
                f"⚠️  {func.__name__} 已被废弃"
                f"{f': {reason}' if reason else ''}"
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator


def class_decorator(**attrs):
    """
    批量添加类属性的装饰器
    
    示例:
        @class_decorator(version="1.0", author="Team")
        class MyClass:
            pass
    """
    def decorator(cls: Type) -> Type:
        for key, value in attrs.items():
            setattr(cls, key, value)
        return cls
    return decorator


# ============ 使用示例 ============

@singleton
class ConfigManager:
    """配置管理器示例"""
    
    def __init__(self):
        self.config = {}
        logger.info("ConfigManager 初始化")
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def set(self, key, value):
        self.config[key] = value


class Employee:
    """使用描述符的数据验证类"""
    
    name = ValidatedProperty("name", str, min_len=2, max_len=50)
    age = ValidatedProperty("age", int, min_val=18, max_val=65)
    salary = ValidatedProperty("salary", (int, float), min_val=0)
    
    def __init__(self, name: str, age: int, salary: float):
        self.name = name
        self.age = age
        self.salary = salary
    
    def __repr__(self):
        return f"Employee(name='{self.name}', age={self.age}, salary={self.salary})"


@timer("数据计算")
@retry(max_attempts=3, delay=1.0, exceptions=(ConnectionError,))
@Memoize(ttl=60, maxsize=100)
def heavy_computation(n: int) -> int:
    """模拟耗时计算"""
    time.sleep(0.5)
    if n < 0:
        raise ConnectionError("模拟网络错误")
    return sum(range(n))


@rate_limit(max_calls=5, period=10)
def api_call(endpoint: str) -> str:
    """模拟API调用"""
    return f"Response from {endpoint}"


def main():
    """主函数示例"""
    print("=" * 50)
    print("装饰器与元编程工具集演示")
    print("=" * 50)
    
    # 1. 单例测试
    print("\n1. 单例模式测试:")
    config1 = ConfigManager()
    config2 = ConfigManager()
    print(f"config1 is config2: {config1 is config2}")
    
    # 2. 属性验证测试
    print("\n2. 属性验证测试:")
    try:
        emp = Employee("张三", 25, 5000.0)
        print(f"创建成功: {emp}")
        emp.age = 30  # 正常修改
        print(f"修改后: {emp}")
        emp.age = 150  # 应该抛出异常
    except ValueError as e:
        print(f"验证错误: {e}")
    
    # 3. 缓存测试
    print("\n3. 缓存装饰器测试:")
    result1 = heavy_computation(1000)
    print(f"第一次调用结果: {result1}")
    result2 = heavy_computation(1000)
    print(f"第二次调用结果: {result2} (应该更快)")
    
    # 4. 限流测试
    print("\n4. 限流装饰器测试:")
    for i in range(7):
        result = api_call(f"/api/data/{i}")
        print(f"Call {i+1}: {result}")


if __name__ == '__main__':
    main()

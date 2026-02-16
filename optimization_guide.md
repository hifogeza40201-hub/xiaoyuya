# Python 性能优化技巧汇总

> 针对大型企业环境的Python性能优化最佳实践

---

## 一、内存优化

### 1. 使用生成器处理大数据
```python
# ❌ 低效：一次性加载所有数据
def read_large_file(file_path):
    with open(file_path) as f:
        return f.readlines()  # 内存爆炸！

# ✅ 高效：使用生成器

def read_large_file(file_path):
    with open(file_path) as f:
        for line in f:  # 逐行读取
            yield line.strip()
```

### 2. __slots__ 减少内存占用
```python
# ❌ 常规类占用更多内存
class RegularClass:
    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

# ✅ 使用__slots__减少内存
class OptimizedClass:
    __slots__ = ['a', 'b', 'c']  # 禁用__dict__
    
    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

# 内存使用可减少 40-50%
```

### 3. 使用数组和namedtuple
```python
from array import array
from collections import namedtuple

# 大规模数值数组使用array
numbers = array('i', [1, 2, 3, 4, 5])  # 比list节省内存

# 结构化数据使用namedtuple
Point = namedtuple('Point', ['x', 'y'])
p = Point(1, 2)  # 比dict更轻量
```

---

## 二、CPU性能优化

### 1. 列表推导式 vs 循环
```python
# ❌ 低效
result = []
for x in range(1000):
    if x % 2 == 0:
        result.append(x * 2)

# ✅ 高效 - 快2倍以上
result = [x * 2 for x in range(1000) if x % 2 == 0]

# ✅ 更优 - 大数据使用生成器表达式
result = (x * 2 for x in range(1000000) if x % 2 == 0)
```

### 2. 使用map/filter
```python
# map替代循环
def square(x): return x ** 2
numbers = list(map(square, range(1000)))

# 或使用lambda
numbers = list(map(lambda x: x ** 2, range(1000)))
```

### 3. 字符串拼接优化
```python
# ❌ 低效 - O(n²)
result = ""
for item in items:
    result += item  # 每次创建新字符串

# ✅ 高效 - O(n)
result = "".join(items)

# 多行字符串
lines = ["Line 1", "Line 2", "Line 3"]
text = "\n".join(lines)
```

### 4. 局部变量优先
```python
# ❌ 低效 - 全局查找
import math
def calculate():
    return [math.sqrt(x) for x in range(1000)]

# ✅ 高效 - 局部绑定
import math
def calculate():
    sqrt = math.sqrt  # 局部变量
    return [sqrt(x) for x in range(1000)]
```

---

## 三、并发优化

### 1. asyncio最佳实践
```python
import asyncio
import aiohttp

# ✅ 复用Session
async def fetch_all(urls):
    connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [fetch(session, url) for url in urls]
        return await asyncio.gather(*tasks)

# ❌ 不要为每个请求创建新Session
async def fetch_bad(urls):
    results = []
    for url in urls:
        async with aiohttp.ClientSession() as session:  # 错误！
            results.append(await fetch(session, url))
```

### 2. 线程池/进程池选择
```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# I/O密集型 - 使用线程
# (网络请求、文件操作、数据库查询)
with ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(fetch_data, urls))

# CPU密集型 - 使用进程
# (数据处理、图像处理、复杂计算)
with ProcessPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(heavy_computation, data))
```

### 3. 异步数据库操作
```python
# 使用异步数据库驱动
import aiomysql
import aiopg

# ❌ 同步 - 阻塞
import pymysql
conn = pymysql.connect(...)

# ✅ 异步 - 非阻塞
conn = await aiomysql.create_pool(...)
async with conn.acquire() as conn:
    async with conn.cursor() as cur:
        await cur.execute("SELECT * FROM users")
```

---

## 四、缓存策略

### 1. functools.lru_cache
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def fibonacci(n):
    if n < 2:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)

# 第一次调用后结果缓存
print(fibonacci(100))  # 极快
```

### 2. 自定义TTL缓存
```python
import time
from functools import wraps

def ttl_cache(ttl=60, maxsize=128):
    def decorator(func):
        cache = {}
        @wraps(func)
        def wrapper(*args):
            key = args
            now = time.time()
            if key in cache:
                value, timestamp = cache[key]
                if now - timestamp < ttl:
                    return value
            result = func(*args)
            cache[key] = (result, now)
            return result
        return wrapper
    return decorator

@ttl_cache(ttl=300)
def get_user_data(user_id):
    return database.query(user_id)
```

---

## 五、数据库优化

### 1. 批量操作
```python
# ❌ 低效 - N次查询
for user in users:
    db.execute("INSERT INTO users VALUES (?, ?)", (user.id, user.name))

# ✅ 高效 - 批量插入
data = [(u.id, u.name) for u in users]
db.executemany("INSERT INTO users VALUES (?, ?)", data)

# 或使用批量提交
with db.transaction():
    for user in users:
        db.execute("INSERT INTO users VALUES (?, ?)", (user.id, user.name))
```

### 2. 连接池
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

# ✅ 使用连接池
engine = create_engine(
    'postgresql://user:pass@localhost/db',
    pool_size=10,           # 连接池大小
    max_overflow=20,        # 超额连接
    pool_pre_ping=True,     # 连接健康检查
    pool_recycle=3600       # 连接回收时间
)

Session = scoped_session(sessionmaker(bind=engine))
```

---

## 六、Profiling工具

### 1. cProfile使用
```python
import cProfile
import pstats

# 方式1: 命令行
# python -m cProfile -s cumulative script.py

# 方式2: 代码内
profiler = cProfile.Profile()
profiler.enable()

# 要分析的代码
process_data()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)  # 打印前20条
```

### 2. line_profiler
```python
# 安装: pip install line_profiler

from line_profiler import LineProfiler

profiler = LineProfiler()

@profiler  # 装饰需要分析的函数
def my_function():
    x = [i**2 for i in range(10000)]
    y = [i**3 for i in range(10000)]
    return x, y

my_function()
profiler.print_stats()
```

### 3. memory_profiler
```python
# 安装: pip install memory_profiler

from memory_profiler import profile

@profile
def my_function():
    a = [1] * (10 ** 6)
    b = [2] * (2 * 10 ** 7)
    del b
    return a

# 运行: python -m memory_profiler script.py
```

---

## 七、企业级优化检查清单

### 代码层面
- [ ] 使用生成器处理大数据集
- [ ] 对频繁调用的函数使用缓存
- [ ] 避免循环中的重复计算
- [ ] 使用 `__slots__` 优化内存占用大的类
- [ ] 字符串拼接使用 `join()`
- [ ] 优先使用列表推导式

### 并发层面
- [ ] I/O操作使用异步(asyncio)或线程
- [ ] CPU密集型使用多进程
- [ ] 复用HTTP连接池
- [ ] 限制并发数防止资源耗尽

### 数据库层面
- [ ] 使用连接池
- [ ] 批量操作替代单次操作
- [ ] 添加合适的索引
- [ ] 使用ORM的select_related/prefetch_related

### 部署层面
- [ ] 使用PyPy替代CPython（纯计算场景）
- [ ] 启用代码编译优化（Cython/Numba）
- [ ] 使用Redis等缓存中间件
- [ ] CDN加速静态资源

---

## 八、性能基准参考

| 操作 | 普通Python | 优化后 | 提升 |
|------|-----------|--------|------|
| 列表遍历 | 1x | 2-3x (推导式) | 2-3x |
| 字符串拼接 | 1x | 10-100x (join) | 10-100x |
| 函数调用 | 1x | 3-5x (缓存) | 3-5x |
| HTTP请求 | 同步 | 10-100x (async) | 10-100x |
| 大文件读取 | 1x | 100x+ (生成器) | 100x+ |

---

> 💡 **总结**: 优化前先测量(profile)，聚焦热点代码，避免过早优化。

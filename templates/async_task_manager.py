"""
异步任务管理器 - 企业级并发任务处理模板
===========================================================
适用场景：批量API调用、数据处理、文件下载等并发任务
性能优化：连接池复用、信号量控制、超时重试机制
"""

import asyncio
import aiohttp
import aiofiles
import logging
from typing import List, Callable, Any, Optional
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import time
from functools import wraps

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TaskConfig:
    """任务配置类"""
    max_concurrent: int = 10          # 最大并发数
    timeout: int = 30                 # 超时时间(秒)
    retry_times: int = 3              # 重试次数
    retry_delay: float = 1.0          # 重试间隔(秒)
    use_proxy: bool = False           # 是否使用代理


class AsyncTaskManager:
    """
    企业级异步任务管理器
    
    特性：
    - 信号量控制并发
    - 自动重试机制
    - 超时保护
    - 结果聚合
    - 进度追踪
    """
    
    def __init__(self, config: TaskConfig = None):
        self.config = config or TaskConfig()
        self.semaphore = asyncio.Semaphore(self.config.max_concurrent)
        self.results: List[Any] = []
        self.errors: List[tuple] = []
        
    async def execute_with_retry(
        self, 
        coro_func: Callable, 
        *args, 
        **kwargs
    ) -> Any:
        """
        带重试机制的任务执行器
        """
        for attempt in range(self.config.retry_times):
            try:
                async with self.semaphore:
                    return await asyncio.wait_for(
                        coro_func(*args, **kwargs),
                        timeout=self.config.timeout
                    )
            except asyncio.TimeoutError:
                logger.warning(f"任务超时 (attempt {attempt + 1})")
                if attempt == self.config.retry_times - 1:
                    raise
            except Exception as e:
                logger.error(f"任务失败 (attempt {attempt + 1}): {e}")
                if attempt == self.config.retry_times - 1:
                    raise
                await asyncio.sleep(self.config.retry_delay * (attempt + 1))
        return None
    
    async def fetch_url(
        self, 
        session: aiohttp.ClientSession, 
        url: str,
        **kwargs
    ) -> dict:
        """
        异步HTTP请求示例
        """
        try:
            async with session.get(url, **kwargs) as response:
                data = await response.json()
                logger.info(f"成功获取: {url}")
                return {
                    'url': url,
                    'status': response.status,
                    'data': data
                }
        except Exception as e:
            logger.error(f"获取失败 {url}: {e}")
            return {'url': url, 'error': str(e)}
    
    async def process_batch(
        self, 
        items: List[Any],
        processor: Callable,
        *args
    ) -> List[Any]:
        """
        批量处理任务
        
        Args:
            items: 待处理的数据列表
            processor: 处理函数(异步)
        """
        tasks = []
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=aiohttp.ClientTimeout(total=self.config.timeout)
        ) as session:
            
            for item in items:
                task = self.execute_with_retry(processor, session, item, *args)
                tasks.append(task)
            
            # 等待所有任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 分类结果
            for item, result in zip(items, results):
                if isinstance(result, Exception):
                    self.errors.append((item, result))
                    logger.error(f"处理失败 {item}: {result}")
                else:
                    self.results.append(result)
        
        return self.results
    
    def run(self, items: List[Any], processor: Callable, *args) -> List[Any]:
        """
        同步入口，方便在非异步环境中调用
        """
        return asyncio.run(self.process_batch(items, processor, *args))


# ============ 使用示例 ============

async def demo_api_call(session: aiohttp.ClientSession, url: str):
    """示例：API调用"""
    await asyncio.sleep(0.5)  # 模拟网络延迟
    return {'url': url, 'data': f'Content of {url}'}


async def demo_file_download(session: aiohttp.ClientSession, url: str, save_path: str):
    """示例：异步文件下载"""
    async with session.get(url) as response:
        content = await response.read()
        async with aiofiles.open(save_path, 'wb') as f:
            await f.write(content)
    return {'url': url, 'saved_to': save_path, 'size': len(content)}


def main():
    """主函数示例"""
    # 配置
    config = TaskConfig(
        max_concurrent=5,
        timeout=10,
        retry_times=3
    )
    
    # 创建管理器
    manager = AsyncTaskManager(config)
    
    # 测试数据
    urls = [
        'https://api.github.com/users/octocat',
        'https://api.github.com/users/torvalds',
        'https://api.github.com/users/gvanrossum',
    ] * 3
    
    # 执行批量任务
    start_time = time.time()
    results = manager.run(urls, demo_api_call)
    elapsed = time.time() - start_time
    
    print(f"\n处理完成:")
    print(f"- 总任务数: {len(urls)}")
    print(f"- 成功数: {len(results)}")
    print(f"- 失败数: {len(manager.errors)}")
    print(f"- 耗时: {elapsed:.2f}秒")
    print(f"- 平均耗时/任务: {elapsed/len(urls):.2f}秒")


if __name__ == '__main__':
    main()

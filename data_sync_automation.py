#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
企业数据同步自动化脚本
========================
功能：
- 从多个API源获取数据
- 数据清洗与转换
- 批量写入数据库
- 生成同步报告
- 邮件/钉钉通知

适用场景：定时数据同步、数据仓库ETL、报表数据源准备

使用方法：
    python data_sync_automation.py --date 2024-02-15 --verbose
    python data_sync_automation.py --config config.json
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import hashlib
import traceback

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("DataSync")


@dataclass
class SyncConfig:
    """同步配置类"""
    # 基本配置
    name: str = "DataSync"
    version: str = "1.0.0"
    
    # 数据源配置
    source_apis: List[str] = field(default_factory=lambda: [
        "https://api.example.com/data1",
        "https://api.example.com/data2"
    ])
    api_timeout: int = 30
    api_retries: int = 3
    
    # 数据库配置
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "enterprise_db"
    db_user: str = "sync_user"
    db_password: str = ""
    
    # 批处理配置
    batch_size: int = 1000
    max_workers: int = 4
    
    # 输出配置
    output_dir: str = "./output"
    log_dir: str = "./logs"
    
    # 通知配置
    enable_dingtalk: bool = False
    dingtalk_webhook: str = ""
    enable_email: bool = False
    email_recipients: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_file(cls, path: str) -> 'SyncConfig':
        """从JSON文件加载配置"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(**data)
    
    def save(self, path: str):
        """保存配置到JSON文件"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)


class Timer:
    """计时器上下文管理器"""
    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.elapsed = None
    
    def __enter__(self):
        self.start_time = time.perf_counter()
        logger.info(f"开始: {self.name}")
        return self
    
    def __exit__(self, *args):
        self.elapsed = time.perf_counter() - self.start_time
        logger.info(f"完成: {self.name} (耗时: {self.elapsed:.2f}s)")


def retry(max_attempts: int = 3, delay: float = 1.0):
    """重试装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts:
                        raise
                    logger.warning(f"{func.__name__} 第{attempt}次失败: {e}, 重试中...")
                    time.sleep(delay * attempt)
        return wrapper
    return decorator


class DataSyncAutomation:
    """数据同步自动化类"""
    
    def __init__(self, config: SyncConfig):
        self.config = config
        self.stats = {
            'start_time': None,
            'end_time': None,
            'total_records': 0,
            'processed_records': 0,
            'failed_records': 0,
            'api_calls': 0,
            'db_inserts': 0,
            'errors': []
        }
        self.raw_data: List[Dict] = []
        self.processed_data: List[Dict] = []
        
        self._setup_directories()
        self._setup_file_logging()
    
    def _setup_directories(self):
        """创建必要的目录"""
        for dir_path in [self.config.output_dir, self.config.log_dir]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    def _setup_file_logging(self):
        """设置文件日志"""
        log_file = Path(self.config.log_dir) / f"sync_{datetime.now():%Y%m%d_%H%M%S}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - [%(name)s] %(message)s'
        ))
        logger.addHandler(file_handler)
        logger.info(f"日志文件: {log_file}")
    
    def parse_args(self) -> argparse.Namespace:
        """解析命令行参数"""
        parser = argparse.ArgumentParser(
            prog=self.config.name,
            description=f"企业数据同步工具 v{self.config.version}"
        )
        parser.add_argument(
            '-c', '--config',
            help='配置文件路径',
            default=None
        )
        parser.add_argument(
            '-d', '--date',
            help='同步日期 (YYYY-MM-DD)',
            default=(datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        )
        parser.add_argument(
            '--dry-run',
            help='试运行模式（不写入数据库）',
            action='store_true'
        )
        parser.add_argument(
            '-v', '--verbose',
            help='详细输出',
            action='store_true'
        )
        parser.add_argument(
            '--max-records',
            help='最大处理记录数',
            type=int,
            default=None
        )
        
        return parser.parse_args()
    
    @retry(max_attempts=3, delay=2.0)
    def fetch_from_api(self, api_url: str, sync_date: str) -> List[Dict]:
        """
        从API获取数据
        实际使用时替换为真实的HTTP请求
        """
        logger.info(f"从API获取数据: {api_url}")
        
        # 模拟API数据获取
        # 实际代码：
        # import requests
        # response = requests.get(api_url, params={'date': sync_date}, timeout=self.config.api_timeout)
        # return response.json()
        
        # 模拟数据
        time.sleep(0.5)  # 模拟网络延迟
        mock_data = [
            {
                'id': f"{api_url.split('/')[-1]}_{i}",
                'date': sync_date,
                'value': i * 100,
                'status': 'active' if i % 3 != 0 else 'inactive',
                'created_at': datetime.now().isoformat()
            }
            for i in range(1, 101)  # 模拟100条记录
        ]
        
        self.stats['api_calls'] += 1
        logger.info(f"获取到 {len(mock_data)} 条记录")
        return mock_data
    
    def fetch_all_data(self, sync_date: str) -> List[Dict]:
        """从所有数据源获取数据"""
        all_data = []
        
        with Timer("数据获取"):
            for api_url in self.config.source_apis:
                try:
                    data = self.fetch_from_api(api_url, sync_date)
                    all_data.extend(data)
                except Exception as e:
                    logger.error(f"获取数据失败 {api_url}: {e}")
                    self.stats['errors'].append(f"API失败 {api_url}: {str(e)}")
        
        self.raw_data = all_data
        self.stats['total_records'] = len(all_data)
        logger.info(f"数据获取完成，共 {len(all_data)} 条记录")
        return all_data
    
    def transform_data(self, data: List[Dict]) -> List[Dict]:
        """
        数据清洗与转换
        """
        logger.info("开始数据转换...")
        processed = []
        
        for item in data:
            try:
                # 数据清洗
                processed_item = {
                    'source_id': item['id'],
                    'sync_date': item['date'],
                    'value': float(item['value']),
                    'is_active': item['status'] == 'active',
                    'created_at': item['created_at'],
                    'checksum': hashlib.md5(
                        json.dumps(item, sort_keys=True).encode()
                    ).hexdigest()[:8]
                }
                processed.append(processed_item)
            except Exception as e:
                logger.warning(f"数据转换失败: {item}, 错误: {e}")
                self.stats['failed_records'] += 1
        
        self.processed_data = processed
        logger.info(f"数据转换完成: {len(processed)}/{len(data)} 条")
        return processed
    
    def batch_insert_to_db(self, data: List[Dict], dry_run: bool = False):
        """
        批量写入数据库
        实际使用时替换为真实的数据库操作
        """
        if dry_run:
            logger.info("[试运行模式] 跳过数据库写入")
            return
        
        logger.info(f"开始批量写入数据库，批大小: {self.config.batch_size}")
        
        # 模拟数据库写入
        # 实际代码：
        # import psycopg2
        # conn = psycopg2.connect(...)
        # with conn.cursor() as cur:
        #     execute_values(cur, insert_sql, data_batches)
        # conn.commit()
        
        batches = [
            data[i:i + self.config.batch_size]
            for i in range(0, len(data), self.config.batch_size)
        ]
        
        for i, batch in enumerate(batches, 1):
            time.sleep(0.1)  # 模拟写入延迟
            logger.debug(f"写入批次 {i}/{len(batches)}: {len(batch)} 条")
            self.stats['db_inserts'] += len(batch)
        
        logger.info(f"数据库写入完成: {self.stats['db_inserts']} 条")
    
    def generate_report(self, sync_date: str) -> Dict[str, Any]:
        """生成同步报告"""
        report = {
            'sync_date': sync_date,
            'timestamp': datetime.now().isoformat(),
            'config': {
                'version': self.config.version,
                'batch_size': self.config.batch_size,
                'max_workers': self.config.max_workers
            },
            'statistics': {
                'total_records': self.stats['total_records'],
                'processed_records': self.stats['processed_records'],
                'failed_records': self.stats['failed_records'],
                'api_calls': self.stats['api_calls'],
                'db_inserts': self.stats['db_inserts'],
                'success_rate': (
                    (self.stats['processed_records'] / self.stats['total_records'] * 100)
                    if self.stats['total_records'] > 0 else 0
                )
            },
            'errors': self.stats['errors'],
            'duration_seconds': (
                (self.stats['end_time'] - self.stats['start_time']).total_seconds()
                if self.stats['end_time'] and self.stats['start_time'] else 0
            )
        }
        return report
    
    def save_report(self, report: Dict[str, Any], sync_date: str):
        """保存报告到文件"""
        # JSON报告
        json_file = Path(self.config.output_dir) / f"sync_report_{sync_date}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        logger.info(f"JSON报告已保存: {json_file}")
        
        # CSV摘要
        csv_file = Path(self.config.output_dir) / f"sync_summary_{sync_date}.csv"
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write("指标,数值\n")
            f.write(f"同步日期,{sync_date}\n")
            f.write(f"总记录数,{report['statistics']['total_records']}\n")
            f.write(f"处理成功,{report['statistics']['processed_records']}\n")
            f.write(f"处理失败,{report['statistics']['failed_records']}\n")
            f.write(f"成功率,{report['statistics']['success_rate']:.2f}%\n")
            f.write(f"API调用次数,{report['statistics']['api_calls']}\n")
            f.write(f"数据库插入,{report['statistics']['db_inserts']}\n")
            f.write(f"耗时(秒),{report['duration_seconds']:.2f}\n")
        logger.info(f"CSV摘要已保存: {csv_file}")
    
    def send_notification(self, success: bool, report: Dict[str, Any]):
        """发送通知（钉钉/邮件）"""
        status = "✅ 成功" if success else "❌ 失败"
        message = f"【数据同步】{status}\n"
        message += f"日期: {report['sync_date']}\n"
        message += f"总记录: {report['statistics']['total_records']}\n"
        message += f"成功率: {report['statistics']['success_rate']:.2f}%\n"
        message += f"耗时: {report['duration_seconds']:.2f}秒"
        
        logger.info(f"通知消息:\n{message}")
        
        # 实际项目中集成真实的发送逻辑
        # if self.config.enable_dingtalk:
        #     send_dingtalk(self.config.dingtalk_webhook, message)
        # if self.config.enable_email:
        #     send_email(self.config.email_recipients, message)
    
    def run(self, args: argparse.Namespace = None) -> bool:
        """
        主执行流程
        
        Returns:
            bool: 执行是否成功
        """
        if args is None:
            args = self.parse_args()
        
        # 加载外部配置
        if args.config:
            self.config = SyncConfig.from_file(args.config)
        
        # 设置详细日志
        if args.verbose:
            logger.setLevel(logging.DEBUG)
        
        sync_date = args.date
        self.stats['start_time'] = datetime.now()
        
        logger.info("=" * 60)
        logger.info(f"开始数据同步 - 日期: {sync_date}")
        logger.info("=" * 60)
        
        success = False
        try:
            # 1. 获取数据
            with Timer("数据获取"):
                data = self.fetch_all_data(sync_date)
            
            if args.max_records:
                data = data[:args.max_records]
                logger.info(f"限制处理记录数为: {args.max_records}")
            
            # 2. 数据转换
            with Timer("数据转换"):
                processed_data = self.transform_data(data)
                self.stats['processed_records'] = len(processed_data)
            
            # 3. 写入数据库
            with Timer("数据库写入"):
                self.batch_insert_to_db(processed_data, dry_run=args.dry_run)
            
            success = True
            logger.info("✅ 数据同步成功完成")
            
        except Exception as e:
            logger.error(f"❌ 数据同步失败: {e}")
            logger.error(traceback.format_exc())
            self.stats['errors'].append(str(e))
            success = False
        
        finally:
            self.stats['end_time'] = datetime.now()
            
            # 生成报告
            report = self.generate_report(sync_date)
            self.save_report(report, sync_date)
            
            # 打印摘要
            self._print_summary(report)
            
            # 发送通知
            self.send_notification(success, report)
        
        return success
    
    def _print_summary(self, report: Dict[str, Any]):
        """打印执行摘要"""
        print("\n" + "=" * 60)
        print("数据同步执行摘要")
        print("=" * 60)
        print(f"同步日期: {report['sync_date']}")
        print(f"总记录数: {report['statistics']['total_records']}")
        print(f"处理成功: {report['statistics']['processed_records']}")
        print(f"处理失败: {report['statistics']['failed_records']}")
        print(f"成功率: {report['statistics']['success_rate']:.2f}%")
        print(f"API调用: {report['statistics']['api_calls']}")
        print(f"数据库插入: {report['statistics']['db_inserts']}")
        print(f"总耗时: {report['duration_seconds']:.2f}秒")
        if report['errors']:
            print(f"错误数: {len(report['errors'])}")
        print("=" * 60)


def create_default_config():
    """创建默认配置文件"""
    config = SyncConfig()
    config.save("config.json")
    print("默认配置文件已创建: config.json")


def main():
    """主函数"""
    # 检查是否需要创建默认配置
    if len(sys.argv) > 1 and sys.argv[1] == '--init':
        create_default_config()
        return
    
    # 运行同步
    config = SyncConfig()
    automation = DataSyncAutomation(config)
    success = automation.run()
    
    # 返回退出码
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

"""
企业级自动化脚本模板 - 可复用的Python自动化框架
===========================================================
适用场景：
- 定时数据同步
- 批量数据处理
- 系统监控告警
- 报表自动生成
- API数据抓取

特性：
- 命令行参数解析
- 配置管理
- 日志记录
- 错误处理与重试
- 邮件/钉钉通知
- 性能统计
"""

import argparse
import json
import os
import sys
import time
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import logging

# 导入前面的模板工具
# from async_task_manager import AsyncTaskManager, TaskConfig
# from decorators_meta import timer, retry, Memoize
# from enterprise_logging import LoggerManager, LogConfig, get_logger
# from enterprise_file_processor import FileProcessor, temp_file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ScriptConfig:
    """脚本配置基类"""
    name: str = "automation_script"
    version: str = "1.0.0"
    log_level: str = "INFO"
    log_dir: str = "./logs"
    data_dir: str = "./data"
    output_dir: str = "./output"
    max_retries: int = 3
    retry_delay: float = 2.0
    timeout: int = 300
    enable_notification: bool = False
    notification_webhook: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_file(cls, path: str) -> 'ScriptConfig':
        """从JSON文件加载配置"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls(**data)
    
    def save(self, path: str):
        """保存配置到JSON文件"""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)


class BaseAutomationScript(ABC):
    """
    自动化脚本基类
    
    使用示例:
        class DataSyncScript(BaseAutomationScript):
            def run(self):
                data = self.fetch_data()
                self.process_data(data)
                self.save_results(data)
    """
    
    def __init__(self, config: Optional[ScriptConfig] = None):
        self.config = config or ScriptConfig()
        self.start_time = None
        self.end_time = None
        self.stats = {
            'processed': 0,
            'succeeded': 0,
            'failed': 0,
            'errors': []
        }
        self._setup()
    
    def _setup(self):
        """初始化环境"""
        # 创建必要的目录
        for dir_path in [self.config.log_dir, self.config.data_dir, self.config.output_dir]:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        # 设置日志
        self._setup_logging()
        
        self.logger.info(f"脚本初始化完成: {self.config.name} v{self.config.version}")
    
    def _setup_logging(self):
        """配置日志"""
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        handlers = [logging.StreamHandler(sys.stdout)]
        
        # 文件日志
        log_file = Path(self.config.log_dir) / f"{self.config.name}_{datetime.now():%Y%m%d}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        handlers.append(file_handler)
        
        logging.basicConfig(
            level=getattr(logging, self.config.log_level.upper()),
            format=log_format,
            handlers=handlers
        )
        self.logger = logging.getLogger(self.config.name)
    
    def parse_args(self, args: List[str] = None) -> argparse.Namespace:
        """解析命令行参数"""
        parser = argparse.ArgumentParser(
            prog=self.config.name,
            description=f"{self.config.name} - {self.config.version}"
        )
        
        parser.add_argument(
            '-c', '--config',
            help='配置文件路径',
            default=None
        )
        parser.add_argument(
            '-d', '--dry-run',
            help='试运行模式（不执行实际修改）',
            action='store_true'
        )
        parser.add_argument(
            '-v', '--verbose',
            help='详细输出',
            action='store_true'
        )
        parser.add_argument(
            '--date',
            help='指定日期 (YYYY-MM-DD)',
            default=datetime.now().strftime('%Y-%m-%d')
        )
        
        return parser.parse_args(args)
    
    def load_config(self, config_path: str):
        """加载配置文件"""
        if config_path and Path(config_path).exists():
            self.config = ScriptConfig.from_file(config_path)
            self.logger.info(f"加载配置: {config_path}")
    
    @abstractmethod
    def run(self):
        """主执行逻辑（子类必须实现）"""
        pass
    
    def execute(self, args: List[str] = None) -> bool:
        """
        执行脚本并处理异常
        
        Returns:
            bool: 执行是否成功
        """
        parsed_args = self.parse_args(args)
        
        # 加载配置
        if parsed_args.config:
            self.load_config(parsed_args.config)
        
        self.start_time = time.time()
        self.logger.info("=" * 50)
        self.logger.info(f"开始执行: {self.config.name}")
        self.logger.info(f"配置: {self.config.to_dict()}")
        self.logger.info("=" * 50)
        
        success = False
        try:
            self.run()
            success = True
            self.logger.info("脚本执行成功")
        except Exception as e:
            self.logger.error(f"脚本执行失败: {e}")
            self.logger.error(traceback.format_exc())
            self.stats['errors'].append(str(e))
            success = False
        finally:
            self.end_time = time.time()
            self._print_summary()
            if self.config.enable_notification:
                self._send_notification(success)
        
        return success
    
    def _print_summary(self):
        """打印执行摘要"""
        elapsed = self.end_time - self.start_time
        
        self.logger.info("=" * 50)
        self.logger.info("执行摘要")
        self.logger.info("=" * 50)
        self.logger.info(f"总耗时: {elapsed:.2f} 秒")
        self.logger.info(f"处理数量: {self.stats['processed']}")
        self.logger.info(f"成功数量: {self.stats['succeeded']}")
        self.logger.info(f"失败数量: {self.stats['failed']}")
        
        if self.stats['errors']:
            self.logger.warning(f"错误信息: {self.stats['errors']}")
    
    def _send_notification(self, success: bool):
        """发送执行结果通知（可扩展为钉钉/邮件等）"""
        status = "✅ 成功" if success else "❌ 失败"
        message = f"[{self.config.name}] 执行{status}"
        self.logger.info(f"通知消息: {message}")
        # 实际项目中集成钉钉/企业微信/邮件发送
    
    def track_progress(self, current: int, total: int, item: str = ""):
        """追踪进度"""
        percent = (current / total * 100) if total > 0 else 0
        self.logger.info(f"进度: [{current}/{total}] {percent:.1f}% - {item}")


# ============ 具体实现示例 ============

class DataSyncScript(BaseAutomationScript):
    """
    数据同步脚本示例
    演示如何实现具体的自动化任务
    """
    
    def __init__(self, config: Optional[ScriptConfig] = None):
        super().__init__(config)
        self.source_data = []
    
    def run(self):
        """实现数据同步逻辑"""
        # 1. 获取数据
        self.logger.info("步骤1: 获取源数据")
        self.fetch_data()
        
        # 2. 处理数据
        self.logger.info("步骤2: 处理数据")
        self.process_data()
        
        # 3. 保存结果
        self.logger.info("步骤3: 保存结果")
        self.save_results()
    
    def fetch_data(self):
        """获取数据（模拟API调用）"""
        self.logger.info("从API获取数据...")
        # 模拟获取100条数据
        self.source_data = [
            {"id": i, "name": f"Item_{i}", "value": i * 10}
            for i in range(1, 101)
        ]
        self.stats['processed'] = len(self.source_data)
        self.logger.info(f"获取到 {len(self.source_data)} 条数据")
    
    def process_data(self):
        """处理数据"""
        self.logger.info("开始处理数据...")
        processed = []
        
        for i, item in enumerate(self.source_data, 1):
            try:
                # 模拟数据处理
                processed_item = {
                    "id": item["id"],
                    "name": item["name"].upper(),
                    "value": item["value"],
                    "processed_at": datetime.now().isoformat()
                }
                processed.append(processed_item)
                self.stats['succeeded'] += 1
                
                # 每10条报告一次进度
                if i % 10 == 0:
                    self.track_progress(i, len(self.source_data), item["name"])
                    
            except Exception as e:
                self.logger.error(f"处理失败 id={item['id']}: {e}")
                self.stats['failed'] += 1
        
        self.source_data = processed
    
    def save_results(self):
        """保存处理结果"""
        output_file = Path(self.config.output_dir) / f"result_{datetime.now():%Y%m%d_%H%M%S}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.source_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"结果已保存: {output_file}")
        
        # 生成CSV报告
        csv_file = output_file.with_suffix('.csv')
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write("id,name,value,processed_at\n")
            for item in self.source_data:
                f.write(f"{item['id']},{item['name']},{item['value']},{item['processed_at']}\n")
        
        self.logger.info(f"CSV报告已生成: {csv_file}")


class ReportGeneratorScript(BaseAutomationScript):
    """
    报表生成脚本示例
    """
    
    def run(self):
        """生成报表"""
        self.logger.info("生成日报表...")
        
        # 模拟数据统计
        report_data = {
            "date": datetime.now().strftime('%Y-%m-%d'),
            "summary": {
                "total_orders": 1500,
                "total_revenue": 125000.50,
                "new_users": 85,
                "active_users": 1200
            },
            "details": []
        }
        
        # 生成详细数据
        for hour in range(24):
            report_data["details"].append({
                "hour": hour,
                "orders": 50 + (hour * 2),
                "revenue": round((50 + hour * 2) * 85.5, 2)
            })
        
        self.stats['processed'] = 24
        self.stats['succeeded'] = 24
        
        # 保存报表
        report_file = Path(self.config.output_dir) / f"daily_report_{report_data['date']}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"报表已生成: {report_file}")


# ============ 工具函数 ============

def create_script_template(name: str, output_dir: str = "./scripts"):
    """创建新脚本模板文件"""
    template = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{name} - 自动化脚本
创建时间: {datetime.now():%Y-%m-%d %H:%M:%S}
"""

import sys
from pathlib import Path

# 添加模板目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "templates"))

from automation_template import BaseAutomationScript, ScriptConfig


class {name}Script(BaseAutomationScript):
    """{name} 自动化脚本"""
    
    def __init__(self):
        config = ScriptConfig(
            name="{name.lower()}",
            version="1.0.0",
            log_dir="./logs",
            output_dir="./output"
        )
        super().__init__(config)
    
    def run(self):
        """主执行逻辑"""
        self.logger.info("开始执行任务...")
        
        # TODO: 实现业务逻辑
        
        self.logger.info("任务执行完成")


if __name__ == '__main__':
    script = {name}Script()
    success = script.execute()
    sys.exit(0 if success else 1)
'''
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    script_file = output_path / f"{name.lower()}_script.py"
    script_file.write_text(template, encoding='utf-8')
    
    print(f"脚本模板已创建: {script_file}")
    return script_file


def main():
    """演示主函数"""
    print("=" * 60)
    print("企业级自动化脚本模板")
    print("=" * 60)
    
    # 演示1: 数据同步脚本
    print("\n【演示1】数据同步脚本")
    print("-" * 40)
    sync_config = ScriptConfig(
        name="DataSync",
        log_dir="./demo_logs",
        output_dir="./demo_output"
    )
    sync_script = DataSyncScript(sync_config)
    sync_script.execute([])
    
    # 演示2: 报表生成脚本
    print("\n【演示2】报表生成脚本")
    print("-" * 40)
    report_config = ScriptConfig(
        name="ReportGen",
        log_dir="./demo_logs",
        output_dir="./demo_output"
    )
    report_script = ReportGeneratorScript(report_config)
    report_script.execute([])
    
    # 演示3: 创建新脚本模板
    print("\n【演示3】创建新脚本模板")
    print("-" * 40)
    create_script_template("MyNewAutomation")
    
    print("\n" + "=" * 60)
    print("演示完成!")
    print("查看以下目录了解输出:")
    print("  - ./demo_logs    - 日志文件")
    print("  - ./demo_output  - 输出文件")
    print("  - ./scripts      - 脚本模板")
    print("=" * 60)


if __name__ == '__main__':
    main()

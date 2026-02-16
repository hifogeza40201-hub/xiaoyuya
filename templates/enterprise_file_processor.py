"""
企业级文件处理工具 - 安全、高效的文件操作方案
===========================================================
特性：
- 大文件分块读写
- 文件锁机制（防止并发冲突）
- 文件备份与恢复
- 批量文件处理
- 文件监控与变更追踪
- 安全的临时文件处理
"""

import os
import shutil
import hashlib
import json
import time
import threading
import tempfile
from pathlib import Path
from typing import List, Optional, Callable, Iterator, Union, BinaryIO
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """文件信息数据类"""
    path: str
    size: int
    modified_time: float
    checksum: str
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_path(cls, path: Union[str, Path]) -> 'FileInfo':
        """从路径创建文件信息"""
        p = Path(path)
        stat = p.stat()
        return cls(
            path=str(p.absolute()),
            size=stat.st_size,
            modified_time=stat.st_mtime,
            checksum=FileProcessor.calculate_checksum(p)
        )


class FileLock:
    """
    文件锁 - 防止多进程/多线程并发写入冲突
    
    示例:
        with FileLock("data.txt"):
            with open("data.txt", "w") as f:
                f.write("data")
    """
    
    _locks = {}
    _lock = threading.Lock()
    
    def __init__(self, file_path: Union[str, Path], timeout: float = 10.0):
        self.file_path = Path(file_path)
        self.lock_path = self.file_path.with_suffix(self.file_path.suffix + '.lock')
        self.timeout = timeout
        self._acquired = False
    
    def __enter__(self):
        start_time = time.time()
        while True:
            try:
                # 尝试创建锁文件（原子操作）
                fd = os.open(str(self.lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, str(os.getpid()).encode())
                os.close(fd)
                self._acquired = True
                return self
            except FileExistsError:
                if time.time() - start_time > self.timeout:
                    raise TimeoutError(f"无法获取文件锁: {self.file_path}")
                time.sleep(0.1)
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._acquired:
            try:
                self.lock_path.unlink()
            except FileNotFoundError:
                pass


class FileProcessor:
    """
    企业级文件处理器
    """
    
    CHUNK_SIZE = 8192  # 默认块大小 8KB
    
    @staticmethod
    def calculate_checksum(
        file_path: Union[str, Path], 
        algorithm: str = 'md5'
    ) -> str:
        """
        计算文件校验和
        
        Args:
            file_path: 文件路径
            algorithm: 哈希算法 (md5, sha256, sha512)
        """
        hash_obj = hashlib.new(algorithm)
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(FileProcessor.CHUNK_SIZE), b''):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    
    @staticmethod
    def copy_file(
        src: Union[str, Path],
        dst: Union[str, Path],
        verify: bool = False
    ) -> Path:
        """
        安全复制文件（带校验）
        """
        src, dst = Path(src), Path(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        
        # 使用临时文件避免不完整写入
        temp_dst = dst.with_suffix(dst.suffix + '.tmp')
        
        try:
            shutil.copy2(src, temp_dst)
            
            if verify:
                src_hash = FileProcessor.calculate_checksum(src)
                dst_hash = FileProcessor.calculate_checksum(temp_dst)
                if src_hash != dst_hash:
                    raise IOError(f"文件复制校验失败: {src}")
            
            # 原子重命名
            temp_dst.replace(dst)
            logger.info(f"文件复制成功: {src} -> {dst}")
            return dst
            
        except Exception as e:
            if temp_dst.exists():
                temp_dst.unlink()
            raise e
    
    @staticmethod
    def read_large_file(
        file_path: Union[str, Path],
        chunk_size: int = None,
        encoding: str = 'utf-8'
    ) -> Iterator[str]:
        """
        大文件流式读取（内存友好）
        
        示例:
            for line in FileProcessor.read_large_file('big.txt'):
                process(line)
        """
        chunk_size = chunk_size or FileProcessor.CHUNK_SIZE
        with open(file_path, 'r', encoding=encoding) as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk
    
    @staticmethod
    def read_lines(
        file_path: Union[str, Path],
        encoding: str = 'utf-8'
    ) -> Iterator[str]:
        """逐行读取大文件"""
        with open(file_path, 'r', encoding=encoding) as f:
            for line in f:
                yield line.rstrip('\n\r')
    
    @classmethod
    def write_file(
        cls,
        file_path: Union[str, Path],
        content: Union[str, bytes],
        mode: str = 'w',
        encoding: str = 'utf-8',
        atomic: bool = True
    ):
        """
        安全写入文件（支持原子写入）
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if atomic:
            temp_path = file_path.with_suffix(file_path.suffix + '.tmp')
            try:
                if isinstance(content, str):
                    temp_path.write_text(content, encoding=encoding)
                else:
                    temp_path.write_bytes(content)
                temp_path.replace(file_path)
            except Exception as e:
                if temp_path.exists():
                    temp_path.unlink()
                raise e
        else:
            if isinstance(content, str):
                file_path.write_text(content, encoding=encoding)
            else:
                file_path.write_bytes(content)
    
    @staticmethod
    def backup(
        file_path: Union[str, Path],
        backup_dir: Optional[Union[str, Path]] = None,
        suffix: str = None
    ) -> Path:
        """
        创建文件备份
        
        Args:
            file_path: 原文件路径
            backup_dir: 备份目录（默认同级目录下的.backup）
            suffix: 备份后缀（默认使用时间戳）
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        if backup_dir is None:
            backup_dir = file_path.parent / '.backup'
        backup_dir = Path(backup_dir)
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        if suffix is None:
            suffix = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        backup_name = f"{file_path.stem}_{suffix}{file_path.suffix}"
        backup_path = backup_dir / backup_name
        
        shutil.copy2(file_path, backup_path)
        logger.info(f"备份创建: {file_path} -> {backup_path}")
        return backup_path
    
    @classmethod
    def batch_process(
        cls,
        pattern: str,
        processor: Callable[[Path], Any],
        source_dir: Union[str, Path] = '.',
        recursive: bool = True
    ) -> List[Any]:
        """
        批量处理文件
        
        示例:
            # 处理所有txt文件
            results = FileProcessor.batch_process(
                "*.txt",
                lambda p: p.read_text(),
                source_dir="./data"
            )
        """
        source_dir = Path(source_dir)
        results = []
        
        if recursive:
            files = list(source_dir.rglob(pattern))
        else:
            files = list(source_dir.glob(pattern))
        
        logger.info(f"找到 {len(files)} 个文件待处理")
        
        for file_path in files:
            try:
                result = processor(file_path)
                results.append({'path': str(file_path), 'result': result, 'success': True})
            except Exception as e:
                logger.error(f"处理文件失败 {file_path}: {e}")
                results.append({'path': str(file_path), 'error': str(e), 'success': False})
        
        return results
    
    @classmethod
    def merge_files(
        cls,
        files: List[Union[str, Path]],
        output: Union[str, Path],
        separator: str = '\n',
        encoding: str = 'utf-8'
    ) -> Path:
        """
        合并多个文件
        """
        output = Path(output)
        output.parent.mkdir(parents=True, exist_ok=True)
        
        with tempfile.NamedTemporaryFile(
            mode='w',
            encoding=encoding,
            delete=False,
            suffix='.tmp'
        ) as tmp:
            tmp_path = Path(tmp.name)
            for i, file_path in enumerate(files):
                file_path = Path(file_path)
                if file_path.exists():
                    content = file_path.read_text(encoding=encoding)
                    tmp.write(content)
                    if i < len(files) - 1:
                        tmp.write(separator)
        
        tmp_path.replace(output)
        logger.info(f"文件合并完成: {output}")
        return output


class FileWatcher:
    """
    简单的文件变更监控器
    """
    
    def __init__(self, file_path: Union[str, Path]):
        self.file_path = Path(file_path)
        self.last_modified = 0
        self.last_size = 0
    
    def has_changed(self) -> bool:
        """检查文件是否发生变化"""
        if not self.file_path.exists():
            return False
        
        stat = self.file_path.stat()
        current_modified = stat.st_mtime
        current_size = stat.st_size
        
        changed = (current_modified != self.last_modified or 
                   current_size != self.last_size)
        
        self.last_modified = current_modified
        self.last_size = current_size
        
        return changed
    
    def watch(self, callback: Callable, interval: float = 1.0):
        """
        持续监控文件变化
        
        示例:
            def on_change():
                print("文件已变更!")
            
            watcher = FileWatcher("config.json")
            watcher.watch(on_change)
        """
        logger.info(f"开始监控文件: {self.file_path}")
        try:
            while True:
                if self.has_changed():
                    callback()
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info("停止监控")


@contextmanager
def temp_file(suffix: str = '', prefix: str = 'tmp', delete: bool = True):
    """
    安全的临时文件上下文管理器
    
    示例:
        with temp_file(suffix='.txt') as tmp:
            tmp.write_text("Hello")
            # 处理完成，自动清理
    """
    tmp = tempfile.NamedTemporaryFile(
        mode='w',
        suffix=suffix,
        prefix=prefix,
        delete=False
    )
    tmp_path = Path(tmp.name)
    tmp.close()
    
    try:
        yield tmp_path
    finally:
        if delete and tmp_path.exists():
            tmp_path.unlink()


@contextmanager
def temp_dir(prefix: str = 'tmp', delete: bool = True):
    """安全的临时目录上下文管理器"""
    tmp_dir = tempfile.mkdtemp(prefix=prefix)
    tmp_path = Path(tmp_dir)
    
    try:
        yield tmp_path
    finally:
        if delete and tmp_path.exists():
            shutil.rmtree(tmp_path)


# ============ 使用示例 ============

def main():
    """文件处理工具演示"""
    print("=" * 50)
    print("企业级文件处理工具演示")
    print("=" * 50)
    
    # 1. 创建测试目录和文件
    test_dir = Path("./test_files")
    test_dir.mkdir(exist_ok=True)
    
    # 2. 安全写入文件
    print("\n1. 安全写入文件:")
    FileProcessor.write_file(
        test_dir / "data.txt",
        "Hello, Enterprise!\nLine 2\nLine 3",
        atomic=True
    )
    print(f"   已创建: {test_dir / 'data.txt'}")
    
    # 3. 计算校验和
    print("\n2. 文件校验和:")
    checksum = FileProcessor.calculate_checksum(test_dir / "data.txt")
    print(f"   MD5: {checksum}")
    
    # 4. 创建备份
    print("\n3. 创建备份:")
    backup_path = FileProcessor.backup(test_dir / "data.txt")
    print(f"   备份: {backup_path}")
    
    # 5. 文件锁演示
    print("\n4. 文件锁保护写入:")
    with FileLock(test_dir / "locked.txt"):
        FileProcessor.write_file(
            test_dir / "locked.txt",
            "Protected content"
        )
        print("   已安全写入 locked.txt")
    
    # 6. 大文件流式读取
    print("\n5. 流式读取文件:")
    print("   文件内容:")
    for i, line in enumerate(FileProcessor.read_lines(test_dir / "data.txt")):
        print(f"   行{i+1}: {line}")
    
    # 7. 批量处理
    print("\n6. 批量处理文件:")
    # 创建多个测试文件
    for i in range(3):
        FileProcessor.write_file(
            test_dir / f"file_{i}.txt",
            f"Content of file {i}"
        )
    
    results = FileProcessor.batch_process(
        "*.txt",
        lambda p: f"{p.name}: {len(p.read_text())} bytes",
        source_dir=test_dir
    )
    for r in results:
        print(f"   {r['path']}: {r['result']}")
    
    # 8. 临时文件
    print("\n7. 临时文件处理:")
    with temp_file(suffix='.json') as tmp:
        data = {'key': 'value', 'timestamp': time.time()}
        tmp.write_text(json.dumps(data, indent=2))
        print(f"   临时文件: {tmp}")
        print(f"   内容: {tmp.read_text()}")
    print("   临时文件已自动清理")
    
    print("\n" + "=" * 50)
    print("演示完成，查看 ./test_files 目录")
    print("=" * 50)
    
    # 清理
    # shutil.rmtree(test_dir)


if __name__ == '__main__':
    main()

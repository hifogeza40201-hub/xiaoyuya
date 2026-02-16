from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
import json
import hashlib
from collections import deque
import numpy as np
from enum import Enum


class MemoryType(Enum):
    """记忆类型"""
    SHORT_TERM = "short_term"    # 短期记忆
    LONG_TERM = "long_term"      # 长期记忆
    WORKING = "working"          # 工作记忆
    EPISODIC = "episodic"        # 情景记忆
    SEMANTIC = "semantic"        # 语义记忆


@dataclass
class MemoryEntry:
    """记忆条目"""
    content: str
    memory_type: MemoryType
    timestamp: datetime = field(default_factory=datetime.now)
    importance: float = 1.0      # 重要性评分 (0-1)
    access_count: int = 0        # 访问次数
    last_accessed: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None  # 向量嵌入
    
    @property
    def id(self) -> str:
        """生成唯一ID"""
        content_hash = hashlib.md5(self.content.encode()).hexdigest()[:12]
        return f"{self.memory_type.value}_{content_hash}_{int(self.timestamp.timestamp())}"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "memory_type": self.memory_type.value,
            "timestamp": self.timestamp.isoformat(),
            "importance": self.importance,
            "access_count": self.access_count,
            "last_accessed": self.last_accessed.isoformat(),
            "metadata": self.metadata,
            "embedding": self.embedding
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MemoryEntry':
        return cls(
            content=data["content"],
            memory_type=MemoryType(data["memory_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            importance=data.get("importance", 1.0),
            access_count=data.get("access_count", 0),
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
            metadata=data.get("metadata", {}),
            embedding=data.get("embedding")
        )
    
    def calculate_relevance_score(self, query_time: datetime = None) -> float:
        """
        计算记忆条目的相关性分数
        
        基于:
        - 重要性
        - 时效性 (越近越重要)
        - 访问频率
        """
        if query_time is None:
            query_time = datetime.now()
        
        # 时间衰减 (指数衰减)
        time_diff = (query_time - self.timestamp).total_seconds()
        time_decay = np.exp(-time_diff / 86400)  # 24小时衰减
        
        # 访问频率奖励
        access_bonus = min(self.access_count * 0.1, 1.0)
        
        # 综合分数
        score = self.importance * 0.4 + time_decay * 0.4 + access_bonus * 0.2
        return score


class BaseMemory(ABC):
    """记忆基类"""
    
    def __init__(self, memory_type: MemoryType):
        self.memory_type = memory_type
    
    @abstractmethod
    def add(self, content: str, **kwargs) -> MemoryEntry:
        """添加记忆"""
        pass
    
    @abstractmethod
    def retrieve(
        self,
        query: str,
        limit: int = 5,
        **kwargs
    ) -> List[MemoryEntry]:
        """检索记忆"""
        pass
    
    @abstractmethod
    def clear(self):
        """清空记忆"""
        pass
    
    @abstractmethod
    def get_all(self) -> List[MemoryEntry]:
        """获取所有记忆"""
        pass


class ShortTermMemory(BaseMemory):
    """
    短期记忆 - 对话上下文管理
    
    特点:
    - 有限的上下文窗口
    - FIFO淘汰策略
    - 支持摘要压缩
    """
    
    def __init__(
        self,
        max_entries: int = 20,
        max_tokens: int = 4000,
        summarization_threshold: int = 15
    ):
        super().__init__(MemoryType.SHORT_TERM)
        self.max_entries = max_entries
        self.max_tokens = max_tokens
        self.summarization_threshold = summarization_threshold
        self.entries: deque = deque(maxlen=max_entries)
        self.summaries: List[str] = []  # 历史摘要
    
    def add(
        self,
        content: str,
        role: str = "user",
        importance: float = 1.0,
        **kwargs
    ) -> MemoryEntry:
        """添加对话记录"""
        entry = MemoryEntry(
            content=content,
            memory_type=MemoryType.SHORT_TERM,
            importance=importance,
            metadata={"role": role, **kwargs}
        )
        self.entries.append(entry)
        
        # 触发摘要
        if len(self.entries) >= self.summarization_threshold:
            self._compress_old_entries()
        
        return entry
    
    def retrieve(
        self,
        query: str = None,
        limit: int = 10,
        include_summaries: bool = True,
        **kwargs
    ) -> List[MemoryEntry]:
        """
        检索最近的对话历史
        
        Args:
            query: 可选的查询条件
            limit: 返回条目数量
            include_summaries: 是否包含历史摘要
        """
        results = list(self.entries)[-limit:]
        
        if include_summaries and self.summaries:
            # 将摘要作为记忆条目返回
            for summary in self.summaries[-3:]:  # 最近3个摘要
                summary_entry = MemoryEntry(
                    content=f"[Historical Summary] {summary}",
                    memory_type=MemoryType.SHORT_TERM,
                    metadata={"is_summary": True}
                )
                results.insert(0, summary_entry)
        
        return results
    
    def get_conversation_history(
        self,
        format_type: str = "messages"
    ) -> Union[List[Dict], str]:
        """获取格式化的对话历史"""
        if format_type == "messages":
            return [
                {
                    "role": entry.metadata.get("role", "user"),
                    "content": entry.content
                }
                for entry in self.entries
            ]
        else:
            return "\n".join([
                f"{entry.metadata.get('role', 'user')}: {entry.content}"
                for entry in self.entries
            ])
    
    def _compress_old_entries(self):
        """压缩旧的对话条目为摘要"""
        if len(self.entries) < self.summarization_threshold:
            return
        
        # 取出最旧的条目进行摘要
        entries_to_summarize = list(self.entries)[:5]
        conversation_text = "\n".join([
            f"{e.metadata.get('role', 'user')}: {e.content}"
            for e in entries_to_summarize
        ])
        
        # 这里应该调用LLM进行摘要
        # 简化实现：使用简单的文本截断
        summary = f"Previous conversation about: {conversation_text[:100]}..."
        self.summaries.append(summary)
        
        # 清空已摘要的条目
        self.entries = deque(
            list(self.entries)[5:],
            maxlen=self.max_entries
        )
    
    def clear(self):
        """清空短期记忆"""
        self.entries.clear()
        self.summaries.clear()
    
    def get_all(self) -> List[MemoryEntry]:
        return list(self.entries)


class WorkingMemory(BaseMemory):
    """
    工作记忆 - 当前任务状态
    
    特点:
    - 任务目标跟踪
    - 中间结果缓存
    - 上下文变量存储
    - 快速读写访问
    """
    
    def __init__(self, max_entries: int = 50):
        super().__init__(MemoryType.WORKING)
        self.max_entries = max_entries
        self.entries: Dict[str, MemoryEntry] = {}
        self.task_stack: List[Dict[str, Any]] = []  # 任务栈
        self.current_goal: Optional[str] = None
    
    def add(
        self,
        content: str,
        key: Optional[str] = None,
        category: str = "general",
        **kwargs
    ) -> MemoryEntry:
        """添加工作记忆条目"""
        if key is None:
            key = f"{category}_{len(self.entries)}"
        
        entry = MemoryEntry(
            content=content,
            memory_type=MemoryType.WORKING,
            metadata={"category": category, "key": key, **kwargs}
        )
        self.entries[key] = entry
        
        # LRU淘汰
        if len(self.entries) > self.max_entries:
            oldest_key = min(
                self.entries.keys(),
                key=lambda k: self.entries[k].last_accessed
            )
            del self.entries[oldest_key]
        
        return entry
    
    def retrieve(
        self,
        query: str = None,
        category: Optional[str] = None,
        key: Optional[str] = None,
        **kwargs
    ) -> List[MemoryEntry]:
        """检索工作记忆"""
        results = []
        
        if key and key in self.entries:
            entry = self.entries[key]
            entry.access_count += 1
            entry.last_accessed = datetime.now()
            results.append(entry)
        elif category:
            results = [
                e for e in self.entries.values()
                if e.metadata.get("category") == category
            ]
        elif query:
            # 简单文本匹配
            results = [
                e for e in self.entries.values()
                if query.lower() in e.content.lower()
            ]
        else:
            results = list(self.entries.values())
        
        return sorted(results, key=lambda x: x.last_accessed, reverse=True)
    
    def set_variable(self, name: str, value: Any):
        """设置变量"""
        self.add(
            content=json.dumps({"name": name, "value": value}),
            key=f"var_{name}",
            category="variable"
        )
    
    def get_variable(self, name: str) -> Any:
        """获取变量"""
        entries = self.retrieve(key=f"var_{name}")
        if entries:
            data = json.loads(entries[0].content)
            return data.get("value")
        return None
    
    def push_task(self, goal: str, context: Dict[str, Any] = None):
        """压入任务"""
        if self.current_goal:
            self.task_stack.append({
                "goal": self.current_goal,
                "context": context or {}
            })
        self.current_goal = goal
    
    def pop_task(self) -> Optional[Dict[str, Any]]:
        """弹出任务"""
        if self.task_stack:
            task = self.task_stack.pop()
            self.current_goal = task["goal"]
            return task
        self.current_goal = None
        return None
    
    def get_task_context(self) -> Dict[str, Any]:
        """获取当前任务上下文"""
        return {
            "current_goal": self.current_goal,
            "task_stack_depth": len(self.task_stack),
            "working_entries": len(self.entries)
        }
    
    def clear(self):
        """清空工作记忆"""
        self.entries.clear()
        self.task_stack.clear()
        self.current_goal = None
    
    def get_all(self) -> List[MemoryEntry]:
        return list(self.entries.values())


class LongTermMemory(BaseMemory):
    """
    长期记忆 - 持久化知识存储
    
    特点:
    - 向量数据库存储
    - 语义检索
    - 记忆巩固
    - 分层组织
    """
    
    def __init__(
        self,
        storage_path: Optional[str] = None,
        embedding_dim: int = 384,
        similarity_threshold: float = 0.7
    ):
        super().__init__(MemoryType.LONG_TERM)
        self.storage_path = storage_path
        self.embedding_dim = embedding_dim
        self.similarity_threshold = similarity_threshold
        
        # 内存存储 (生产环境应使用向量数据库)
        self.entries: List[MemoryEntry] = []
        self.index: Dict[str, int] = {}  # ID到索引的映射
        
        # 分类索引
        self.category_index: Dict[str, List[str]] = {}
    
    def add(
        self,
        content: str,
        category: str = "general",
        importance: float = 0.5,
        embedding: Optional[List[float]] = None,
        **kwargs
    ) -> MemoryEntry:
        """添加长期记忆"""
        entry = MemoryEntry(
            content=content,
            memory_type=MemoryType.LONG_TERM,
            importance=importance,
            metadata={"category": category, **kwargs}
        )
        
        # 生成或获取向量嵌入
        if embedding is None:
            entry.embedding = self._generate_embedding(content)
        else:
            entry.embedding = embedding
        
        self.entries.append(entry)
        self.index[entry.id] = len(self.entries) - 1
        
        # 更新分类索引
        if category not in self.category_index:
            self.category_index[category] = []
        self.category_index[category].append(entry.id)
        
        # 保存到存储
        if self.storage_path:
            self._persist()
        
        return entry
    
    def retrieve(
        self,
        query: str,
        limit: int = 5,
        category: Optional[str] = None,
        **kwargs
    ) -> List[MemoryEntry]:
        """
        语义检索长期记忆
        
        使用向量相似度进行检索
        """
        query_embedding = self._generate_embedding(query)
        
        # 计算相似度
        candidates = []
        for entry in self.entries:
            if category and entry.metadata.get("category") != category:
                continue
            
            if entry.embedding:
                similarity = self._cosine_similarity(query_embedding, entry.embedding)
                if similarity >= self.similarity_threshold:
                    candidates.append((entry, similarity))
        
        # 按相似度排序
        candidates.sort(key=lambda x: x[1], reverse=True)
        
        # 返回结果
        results = []
        for entry, similarity in candidates[:limit]:
            entry.access_count += 1
            entry.last_accessed = datetime.now()
            entry.metadata["retrieval_score"] = similarity
            results.append(entry)
        
        return results
    
    def consolidate(self, llm_client: Any = None):
        """
        记忆巩固 - 整合相似记忆
        
        识别相似的记忆条目并进行合并/摘要
        """
        # 找出相似的记忆组
        groups = self._find_similar_groups()
        
        for group in groups:
            if len(group) < 2:
                continue
            
            # 合并组内记忆
            combined_content = "\n".join([
                self.entries[idx].content for idx in group
            ])
            
            # 使用LLM生成摘要 (简化实现)
            summary = f"Consolidated: {combined_content[:200]}..."
            
            # 创建新记忆条目
            new_entry = MemoryEntry(
                content=summary,
                memory_type=MemoryType.LONG_TERM,
                importance=max(self.entries[idx].importance for idx in group),
                metadata={"consolidated_from": [self.entries[idx].id for idx in group]}
            )
            
            # 删除旧条目
            for idx in sorted(group, reverse=True):
                del self.entries[idx]
            
            self.entries.append(new_entry)
        
        # 重建索引
        self._rebuild_index()
    
    def forget(self, entry_id: str) -> bool:
        """删除特定记忆"""
        if entry_id in self.index:
            idx = self.index[entry_id]
            del self.entries[idx]
            self._rebuild_index()
            return True
        return False
    
    def _generate_embedding(self, text: str) -> List[float]:
        """生成文本嵌入向量 - 简化实现"""
        # 生产环境应使用 sentence-transformers 或 OpenAI API
        # 这里使用简单的哈希向量化作为演示
        np.random.seed(hash(text) % 2**32)
        embedding = np.random.randn(self.embedding_dim).tolist()
        # 归一化
        norm = np.linalg.norm(embedding)
        return [x / norm for x in embedding]
    
    def _cosine_similarity(
        self,
        vec1: List[float],
        vec2: List[float]
    ) -> float:
        """计算余弦相似度"""
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        return dot_product  # 向量已归一化
    
    def _find_similar_groups(self, threshold: float = 0.85) -> List[List[int]]:
        """找出相似的记忆组"""
        n = len(self.entries)
        visited = [False] * n
        groups = []
        
        for i in range(n):
            if visited[i]:
                continue
            
            group = [i]
            visited[i] = True
            
            for j in range(i + 1, n):
                if visited[j]:
                    continue
                
                if (self.entries[i].embedding and self.entries[j].embedding):
                    sim = self._cosine_similarity(
                        self.entries[i].embedding,
                        self.entries[j].embedding
                    )
                    if sim > threshold:
                        group.append(j)
                        visited[j] = True
            
            groups.append(group)
        
        return groups
    
    def _rebuild_index(self):
        """重建索引"""
        self.index = {entry.id: i for i, entry in enumerate(self.entries)}
        self.category_index = {}
        for entry in self.entries:
            cat = entry.metadata.get("category", "general")
            if cat not in self.category_index:
                self.category_index[cat] = []
            self.category_index[cat].append(entry.id)
    
    def _persist(self):
        """持久化存储"""
        if not self.storage_path:
            return
        
        data = [entry.to_dict() for entry in self.entries]
        with open(self.storage_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load(self):
        """从存储加载"""
        if not self.storage_path:
            return
        
        try:
            with open(self.storage_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.entries = [MemoryEntry.from_dict(d) for d in data]
            self._rebuild_index()
        except FileNotFoundError:
            pass
    
    def clear(self):
        """清空长期记忆"""
        self.entries.clear()
        self.index.clear()
        self.category_index.clear()
    
    def get_all(self) -> List[MemoryEntry]:
        return self.entries.copy()


class MemoryManager:
    """
    记忆管理器 - 统一管理三层记忆系统
    
    协调短期记忆、工作记忆和长期记忆的交互
    """
    
    def __init__(
        self,
        short_term: Optional[ShortTermMemory] = None,
        working: Optional[WorkingMemory] = None,
        long_term: Optional[LongTermMemory] = None,
        auto_consolidate: bool = True
    ):
        self.short_term = short_term or ShortTermMemory()
        self.working = working or WorkingMemory()
        self.long_term = long_term or LongTermMemory()
        self.auto_consolidate = auto_consolidate
        
        self.consolidation_counter = 0
    
    def add_interaction(
        self,
        user_input: str,
        agent_response: str,
        importance: float = 0.5
    ):
        """记录交互到记忆系统"""
        # 短期记忆
        self.short_term.add(user_input, role="user", importance=importance)
        self.short_term.add(agent_response, role="assistant", importance=importance)
        
        # 重要交互存入长期记忆
        if importance > 0.7:
            self.long_term.add(
                f"User: {user_input}\nAgent: {agent_response}",
                category="important_interactions",
                importance=importance
            )
    
    def retrieve_context(
        self,
        query: str,
        include_short_term: bool = True,
        include_working: bool = True,
        include_long_term: bool = True,
        short_term_limit: int = 5,
        long_term_limit: int = 3
    ) -> Dict[str, List[MemoryEntry]]:
        """检索完整上下文"""
        context = {}
        
        if include_short_term:
            context["short_term"] = self.short_term.retrieve(
                limit=short_term_limit
            )
        
        if include_working:
            context["working"] = self.working.retrieve(query)
        
        if include_long_term:
            context["long_term"] = self.long_term.retrieve(
                query,
                limit=long_term_limit
            )
        
        return context
    
    def format_context_for_prompt(
        self,
        context: Dict[str, List[MemoryEntry]]
    ) -> str:
        """将上下文格式化为提示词"""
        parts = []
        
        if "long_term" in context and context["long_term"]:
            parts.append("## Relevant Past Knowledge:")
            for entry in context["long_term"]:
                parts.append(f"- {entry.content[:200]}...")
        
        if "working" in context and context["working"]:
            parts.append("\n## Current Task Context:")
            for entry in context["working"]:
                parts.append(f"- {entry.content[:150]}...")
        
        if "short_term" in context and context["short_term"]:
            parts.append("\n## Recent Conversation:")
            for entry in context["short_term"]:
                role = entry.metadata.get("role", "user")
                parts.append(f"{role}: {entry.content}")
        
        return "\n".join(parts)
    
    def consolidate_if_needed(self):
        """按需执行记忆巩固"""
        self.consolidation_counter += 1
        
        if self.auto_consolidate and self.consolidation_counter % 10 == 0:
            self.long_term.consolidate()
    
    def clear_all(self):
        """清空所有记忆"""
        self.short_term.clear()
        self.working.clear()
        self.long_term.clear()
    
    def get_stats(self) -> Dict[str, int]:
        """获取记忆统计信息"""
        return {
            "short_term_entries": len(self.short_term.get_all()),
            "working_entries": len(self.working.get_all()),
            "long_term_entries": len(self.long_term.get_all()),
            "total": sum([
                len(self.short_term.get_all()),
                len(self.working.get_all()),
                len(self.long_term.get_all())
            ])
        }


# 使用示例
if __name__ == "__main__":
    # 创建记忆管理器
    memory = MemoryManager()
    
    # 添加对话
    memory.add_interaction(
        "What is Python?",
        "Python is a programming language.",
        importance=0.8
    )
    
    memory.add_interaction(
        "How do I define a function?",
        "Use the def keyword.",
        importance=0.6
    )
    
    # 检索上下文
    context = memory.retrieve_context("Python programming")
    print("Context retrieved:")
    for memory_type, entries in context.items():
        print(f"\n{memory_type}:")
        for entry in entries:
            print(f"  - {entry.content[:50]}...")
    
    # 格式化用于提示
    formatted = memory.format_context_for_prompt(context)
    print("\n\nFormatted Context:\n", formatted)

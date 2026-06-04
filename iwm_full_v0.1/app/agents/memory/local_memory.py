"""
本地Agent记忆模块

使用本地JSON文件存储Agent记忆。
文件路径: data/agent_memory/{agent_name}.json
"""

import json
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.agents.memory.base import AgentMemory


class LocalAgentMemory(AgentMemory):
    """
    本地JSON文件存储的Agent记忆实现。

    每个Agent对应一个JSON文件，文件内按时间顺序存储记忆条目。
    适用于单机部署和开发测试环境。
    """

    def __init__(self, agent_name: str, memory_dir: Optional[str] = None) -> None:
        """
        初始化本地记忆存储

        Args:
            agent_name: Agent名称，用于确定存储文件
            memory_dir: 记忆文件存储目录，默认 data/agent_memory
        """
        self.agent_name = agent_name

        # 确定存储目录
        if memory_dir:
            self.memory_dir = memory_dir
        else:
            project_root = self._get_project_root()
            self.memory_dir = os.path.join(project_root, "data", "agent_memory")

        # 确保目录存在
        os.makedirs(self.memory_dir, exist_ok=True)

        # 存储文件路径
        self.memory_file = os.path.join(self.memory_dir, f"{agent_name}.json")

        # 内存缓存（减少IO）
        self._cache: List[Dict[str, Any]] = []
        self._cache_loaded = False

    def _get_project_root(self) -> str:
        """获取项目根目录"""
        current_file = os.path.abspath(__file__)
        # 从 app/agents/memory/local_memory.py 向上三级到项目根
        return os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file))))

    def _load_from_disk(self) -> List[Dict[str, Any]]:
        """从磁盘加载所有记忆"""
        if not os.path.exists(self.memory_file):
            return []

        try:
            with open(self.memory_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    # 兼容旧格式（单条记录）
                    return [data]
                return []
        except json.JSONDecodeError:
            return []
        except Exception:
            return []

    def _ensure_cache(self) -> None:
        """确保缓存已加载"""
        if not self._cache_loaded:
            self._cache = self._load_from_disk()
            self._cache_loaded = True

    def _save_to_disk(self) -> None:
        """将缓存持久化到磁盘"""
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[LocalAgentMemory] 保存失败: {e}")

    def save(self, key: str, value: Dict[str, Any]) -> None:
        """
        保存记忆

        Args:
            key: 记忆键（如日期、主题等）
            value: 要保存的数据字典
        """
        self._ensure_cache()

        # 构建记忆条目
        entry = {
            "key": key,
            "data": value,
            "timestamp": datetime.now().isoformat(),
            "agent_name": self.agent_name,
        }

        # 检查是否已存在相同key的记录，存在则更新
        existing_idx = None
        for i, existing in enumerate(self._cache):
            if existing.get("key") == key:
                existing_idx = i
                break

        if existing_idx is not None:
            self._cache[existing_idx] = entry
        else:
            self._cache.append(entry)

        # 持久化
        self._save_to_disk()

    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """
        读取记忆

        Args:
            key: 记忆键

        Returns:
            保存的数据字典，如果不存在则返回None
        """
        self._ensure_cache()

        for entry in self._cache:
            if entry.get("key") == key:
                return entry.get("data")

        return None

    def get_history(self, agent_name: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取历史记录

        Args:
            agent_name: Agent名称过滤器（可选）
            limit: 返回的最大记录数

        Returns:
            历史记录列表，按时间倒序排列
        """
        self._ensure_cache()

        # 过滤
        filtered = self._cache
        if agent_name:
            filtered = [e for e in filtered if e.get("agent_name") == agent_name]

        # 按时间倒序排列
        sorted_entries = sorted(
            filtered,
            key=lambda x: x.get("timestamp", ""),
            reverse=True,
        )

        return sorted_entries[:limit]

    def delete(self, key: str) -> bool:
        """
        删除记忆

        Args:
            key: 记忆键

        Returns:
            是否成功删除
        """
        self._ensure_cache()

        original_len = len(self._cache)
        self._cache = [e for e in self._cache if e.get("key") != key]

        deleted = len(self._cache) < original_len
        if deleted:
            self._save_to_disk()

        return deleted

    def list_keys(self, prefix: str = "") -> List[str]:
        """
        列出所有记忆键

        Args:
            prefix: 键前缀过滤器

        Returns:
            记忆键列表
        """
        self._ensure_cache()

        keys = []
        for entry in self._cache:
            key = entry.get("key", "")
            if not prefix or key.startswith(prefix):
                keys.append(key)

        return keys

    def clear(self) -> None:
        """清空所有记忆（谨慎使用）"""
        self._cache = []
        self._save_to_disk()

    def get_stats(self) -> Dict[str, Any]:
        """
        获取记忆统计信息

        Returns:
            统计信息字典
        """
        self._ensure_cache()

        return {
            "agent_name": self.agent_name,
            "total_entries": len(self._cache),
            "memory_file": self.memory_file,
            "file_exists": os.path.exists(self.memory_file),
            "file_size_kb": round(os.path.getsize(self.memory_file) / 1024, 2) if os.path.exists(self.memory_file) else 0,
            "latest_entry": self._cache[-1].get("timestamp") if self._cache else None,
            "oldest_entry": self._cache[0].get("timestamp") if self._cache else None,
        }

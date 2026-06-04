"""
Agent记忆基类模块

定义AgentMemory抽象基类，所有记忆存储实现必须继承此类。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional


class AgentMemory(ABC):
    """
    Agent记忆抽象基类。

    所有Agent记忆存储（本地JSON、数据库存储等）必须实现此接口。
    提供保存、读取和获取历史记录的基本操作。
    """

    @abstractmethod
    def save(self, key: str, value: Dict[str, Any]) -> None:
        """
        保存记忆

        Args:
            key: 记忆键（如日期、主题等）
            value: 要保存的数据字典
        """
        pass

    @abstractmethod
    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """
        读取记忆

        Args:
            key: 记忆键

        Returns:
            保存的数据字典，如果不存在则返回None
        """
        pass

    @abstractmethod
    def get_history(self, agent_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取Agent的历史记录

        Args:
            agent_name: Agent名称
            limit: 返回的最大记录数

        Returns:
            历史记录列表，按时间倒序排列
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        删除记忆

        Args:
            key: 记忆键

        Returns:
            是否成功删除
        """
        pass

    @abstractmethod
    def list_keys(self, prefix: str = "") -> List[str]:
        """
        列出所有记忆键

        Args:
            prefix: 键前缀过滤器

        Returns:
            记忆键列表
        """
        pass

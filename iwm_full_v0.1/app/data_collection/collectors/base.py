"""Base collector abstract class."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseCollector(ABC):
    """Abstract base class for all data collectors.
    
    All collectors must implement the `collect` method and provide
    a name and data type identifier.
    """
    
    @abstractmethod
    async def collect(self, **kwargs) -> List[Dict[str, Any]]:
        """Collect data from the source.
        
        Args:
            **kwargs: Collector-specific parameters.
            
        Returns:
            List of collected data items as dictionaries.
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Return the collector's human-readable name."""
        pass
    
    @property
    @abstractmethod
    def data_type(self) -> str:
        """Return the data type this collector handles."""
        pass

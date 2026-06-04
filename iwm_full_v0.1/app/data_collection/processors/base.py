"""Base processor abstract class."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseProcessor(ABC):
    """Abstract base class for all data processors.
    
    Processors take raw collected data, transform and enrich it,
    then return structured results ready for storage or analysis.
    """
    
    @abstractmethod
    async def process(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process raw data into structured format.
        
        Args:
            raw_data: List of raw data dictionaries from collectors.
            
        Returns:
            List of processed data dictionaries.
        """
        pass

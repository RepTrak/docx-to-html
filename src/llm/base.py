from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, Type
from pydantic import BaseModel

class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, api_key: str, **kwargs):
        self.api_key = api_key
        self.config = kwargs
    
    @abstractmethod
    def completion(
        self,
        messages: List[Dict[str, str]],
        model: str,
        max_tokens: int = 1024,
        temperature: float = 0.0,
        system: Optional[str] = None,
        response_format: Optional[Union[Type[BaseModel], str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate completion from the LLM.
        
        Args:
            response_format: Pydantic model class for structured output or "json" for JSON mode
        
        Returns:
            Dict containing 'content', 'usage' (with input_tokens, output_tokens), 'model', and optionally 'parsed'
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available."""
        pass
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the provider name."""
        pass

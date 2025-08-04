import time
import logging
from typing import List, Dict, Any, Optional, Union, Type
from pydantic import BaseModel
from .providers import AnthropicProvider, OpenAIProvider
from .base import LLMProvider

logger = logging.getLogger(__name__)

class LLMClient:
    """Multi-provider LLM client with retry strategy."""
    
    def __init__(
        self,
        providers: Optional[List[Union[str, LLMProvider]]] = None,
        retry_attempts: int = 3,
        retry_delay: float = 1.0,
        retry_backoff: float = 2.0
    ):
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay
        self.retry_backoff = retry_backoff
        
        # Initialize providers
        self.providers = []
        if providers is None:
            # Default providers
            providers = ["anthropic", "openai"]
        
        for provider in providers:
            if isinstance(provider, str):
                provider_instance = self._create_provider(provider)
                if provider_instance and provider_instance.is_available():
                    self.providers.append(provider_instance)
            elif isinstance(provider, LLMProvider):
                if provider.is_available():
                    self.providers.append(provider)
        
        if not self.providers:
            raise ValueError("No available LLM providers found")
        
        logger.info(f"Initialized LLM client with {len(self.providers)} providers: {[p.provider_name for p in self.providers]}")
    
    def _create_provider(self, provider_name: str) -> Optional[LLMProvider]:
        """Create a provider instance by name."""
        try:
            if provider_name.lower() == "anthropic":
                return AnthropicProvider()
            elif provider_name.lower() == "openai":
                return OpenAIProvider()
            else:
                logger.warning(f"Unknown provider: {provider_name}")
                return None
        except Exception as e:
            logger.warning(f"Failed to create {provider_name} provider: {e}")
            return None
    
    def completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        provider: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.0,
        system: Optional[str] = None,
        response_format: Optional[BaseModel] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate completion using available providers with retry strategy.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Specific model to use (if None, uses provider default)
            provider: Specific provider to use (if None, tries all available)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            system: System prompt
            response_format: Pydantic model class for structured output or "json" for JSON mode
            **kwargs: Additional provider-specific parameters
        
        Returns:
            Dict containing 'content', 'usage', 'model', 'provider', and optionally 'parsed'
        """
        # Filter providers if specific provider requested
        providers_to_try = self.providers
        if provider:
            providers_to_try = [p for p in self.providers if p.provider_name.lower() == provider.lower()]
            if not providers_to_try:
                raise ValueError(f"Provider '{provider}' not available")
        
        # Set default models if not specified
        if model is None:
            model_defaults = {
                "anthropic": "claude-3-5-haiku-20241022",
                "openai": "gpt-4o-mini"
            }
            
        last_exception = None
        
        for provider_instance in providers_to_try:
            current_model = model
            if current_model is None:
                current_model = model_defaults.get(provider_instance.provider_name, "default")
            
            for attempt in range(self.retry_attempts):
                try:
                    logger.debug(f"Attempting completion with {provider_instance.provider_name} (attempt {attempt + 1})")
                    
                    result = provider_instance.completion(
                        messages=messages,
                        model=current_model,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        system=system,
                        response_format=response_format,
                        **kwargs
                    )
                    
                    # Add provider info to result
                    result["provider"] = provider_instance.provider_name
                    
                    logger.info(f"Successful completion with {provider_instance.provider_name}")
                    return result
                    
                except Exception as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt + 1} failed with {provider_instance.provider_name}: {e}")
                    
                    if attempt < self.retry_attempts - 1:
                        delay = self.retry_delay * (self.retry_backoff ** attempt)
                        logger.debug(f"Retrying in {delay} seconds...")
                        time.sleep(delay)
        
        # If we get here, all providers and retries failed
        raise Exception(f"All LLM providers failed. Last error: {last_exception}")
    
    def list_available_providers(self) -> List[str]:
        """Return list of available provider names."""
        return [p.provider_name for p in self.providers]
    
    def add_provider(self, provider: Union[str, LLMProvider]) -> bool:
        """Add a new provider to the client."""
        if isinstance(provider, str):
            provider_instance = self._create_provider(provider)
            if provider_instance and provider_instance.is_available():
                self.providers.append(provider_instance)
                return True
        elif isinstance(provider, LLMProvider):
            if provider.is_available():
                self.providers.append(provider)
                return True
        return False

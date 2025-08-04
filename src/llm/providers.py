import os
import json
from typing import List, Dict, Any, Optional, Union, Type
from pydantic import BaseModel
from .base import LLMProvider
from ..config import settings

class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        api_key = api_key or settings.ANTHROPIC_API_KEY or os.getenv("ANTHROPIC_API_KEY")
        super().__init__(api_key, **kwargs)
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            try:
                from anthropic import Anthropic
                self._client = Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("anthropic package not installed. Install with: pip install anthropic")
        return self._client
    
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
        """Generate completion using Anthropic Claude with optional structured output."""
        params = {
            "model": model,
            "messages": messages,
            # "max_tokens": max_tokens,
            # "temperature": temperature,
            **kwargs
        }
        
        if system:
            params["system"] = system
        
        # Handle structured output using tools
        if response_format:
            if isinstance(response_format, type) and issubclass(response_format, BaseModel):
                # Convert Pydantic model to Anthropic tool schema
                schema = response_format.model_json_schema()
                tool_name = response_format.__name__.lower() + "_response"
                
                params["tools"] = [{
                    "name": tool_name,
                    "description": f"Structured response using {response_format.__name__} schema",
                    "input_schema": schema
                }]
                params["tool_choice"] = {"type": "tool", "name": tool_name}
            elif response_format == "json":
                # For basic JSON mode, add instruction to system prompt
                json_instruction = "\n\nRespond with valid JSON only."
                if system:
                    params["system"] += json_instruction
                else:
                    params["system"] = json_instruction.strip()
        
        response = self.client.messages.create(**params)
        
        result = {
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            },
            "model": response.model
        }
        
        # Handle structured response
        if response_format and isinstance(response_format, type) and issubclass(response_format, BaseModel):
            if response.content and response.content[0].type == "tool_use":
                tool_input = response.content[0].input
                result["content"] = json.dumps(tool_input)
                try:
                    result["parsed"] = response_format(**tool_input)
                except Exception as e:
                    result["parsed"] = None
                    result["parse_error"] = str(e)
            else:
                result["content"] = response.content[0].text.strip()
                result["parsed"] = None
        else:
            result["content"] = response.content[0].text.strip()
        
        return result
    
    def is_available(self) -> bool:
        """Check if Anthropic provider is available."""
        try:
            return bool(self.api_key and self.client)
        except Exception:
            return False
    
    @property
    def provider_name(self) -> str:
        return "anthropic"


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        api_key = api_key or settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        super().__init__(api_key, **kwargs)
        self._client = None
    
    @property
    def client(self):
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError("openai package not installed. Install with: pip install openai")
        return self._client
    
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
        """Generate completion using OpenAI GPT with optional structured output."""
        # Convert system message to OpenAI format
        if system:
            messages = [{"role": "system", "content": system}] + messages
        
        params = {
            "model": model,
            "messages": messages,
            "max_completion_tokens": max_tokens,
            "temperature": 1,
            **kwargs
        }
        
        # Handle structured output
        if response_format:
            if isinstance(response_format, type) and issubclass(response_format, BaseModel):
                # Use OpenAI's native Pydantic support
                params["response_format"] = response_format
                response = self.client.chat.completions.parse(**params)
                
                return {
                    "content": response.choices[0].message.content,
                    "parsed": response.choices[0].message.parsed,
                    "usage": {
                        "input_tokens": response.usage.prompt_tokens,
                        "output_tokens": response.usage.completion_tokens
                    },
                    "model": response.model
                }
            elif response_format == "json":
                params["response_format"] = {"type": "json_object"}
        
        response = self.client.chat.completions.create(**params)
        
        result = {
            "content": response.choices[0].message.content.strip(),
            "usage": {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens
            },
            "model": response.model
        }
        
        return result
    
    def is_available(self) -> bool:
        """Check if OpenAI provider is available."""
        try:
            return bool(self.api_key and self.client)
        except Exception:
            return False
    
    @property
    def provider_name(self) -> str:
        return "openai"

"""
OpenRouter Anthropic Adapter
============================

Adapter that allows using OpenRouter API as a drop-in replacement for Anthropic API.
OpenRouter provides access to Claude and many other models through a unified interface.

Benefits:
- Unlimited API key
- Access to multiple models (Claude, GPT-4, etc.)
- No credit balance issues
- Pay-as-you-go pricing
"""

import os
import logging
from typing import Dict, Any, Optional, List
import requests
import json

logger = logging.getLogger(__name__)


class OpenRouterAnthropicAdapter:
    """
    Adapter that translates Anthropic API calls to OpenRouter API.
    Provides seamless compatibility with existing Anthropic code.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenRouter adapter.
        
        Args:
            api_key: OpenRouter API key (if not provided, loads from env)
        """
        self.api_key = api_key or os.getenv('OPENROUTER_API_KEY')
        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY required. Set in .env file or pass to constructor."
            )
        
        self.base_url = "https://openrouter.ai/api/v1"
        self.default_model = "anthropic/claude-3.5-sonnet"  # OpenRouter model ID
        
        logger.info(f"✅ OpenRouter adapter initialized with model: {self.default_model}")
    
    class Messages:
        """Messages API adapter (mimics Anthropic's messages.create)."""
        
        def __init__(self, adapter):
            self.adapter = adapter
        
        def create(
            self,
            model: str,
            max_tokens: int,
            messages: List[Dict[str, str]],
            system: Optional[str] = None,
            temperature: float = 1.0,
            **kwargs
        ) -> Any:
            """
            Create a message using OpenRouter API.
            
            Args:
                model: Model name (will be converted to OpenRouter format)
                max_tokens: Maximum tokens
                messages: List of message dicts with role and content
                system: System prompt (optional)
                temperature: Sampling temperature
                **kwargs: Additional parameters
                
            Returns:
                Response object mimicking Anthropic's format
            """
            # Convert Anthropic model name to OpenRouter format
            if "claude" in model.lower():
                if "opus" in model.lower():
                    openrouter_model = "anthropic/claude-3-opus"
                elif "sonnet" in model.lower():
                    openrouter_model = "anthropic/claude-3.5-sonnet"
                elif "haiku" in model.lower():
                    openrouter_model = "anthropic/claude-3-haiku"
                else:
                    openrouter_model = "anthropic/claude-3.5-sonnet"
            else:
                openrouter_model = self.adapter.default_model
            
            # Build OpenRouter request
            payload = {
                "model": openrouter_model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            
            # Add system prompt if provided
            if system:
                # OpenRouter expects system as first message with role="system"
                payload["messages"] = [{"role": "system", "content": system}] + messages
            
            headers = {
                "Authorization": f"Bearer {self.adapter.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/jlaw-forensics/dual-agent-system",
                "X-Title": "JLAW Forensics Dual-Agent System"
            }
            
            logger.info(f"[OpenRouter] Calling {openrouter_model} via OpenRouter")
            
            try:
                response = requests.post(
                    f"{self.adapter.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Convert OpenRouter response to Anthropic format
                    class MockResponse:
                        def __init__(self, data):
                            self.data = data
                            # Extract content from OpenRouter response
                            if "choices" in data and len(data["choices"]) > 0:
                                message_content = data["choices"][0]["message"]["content"]
                                self.content = [MockContentBlock(message_content)]
                            else:
                                self.content = []
                            
                            self.model = data.get("model", openrouter_model)
                            self.stop_reason = "end_turn"
                            self.usage = MockUsage(data.get("usage", {}))
                    
                    class MockContentBlock:
                        def __init__(self, text):
                            self.text = text
                            self.type = "text"
                    
                    class MockUsage:
                        def __init__(self, usage_data):
                            self.input_tokens = usage_data.get("prompt_tokens", 0)
                            self.output_tokens = usage_data.get("completion_tokens", 0)
                    
                    logger.info(f"[OpenRouter] ✅ Success - tokens: {data.get('usage', {}).get('total_tokens', 'N/A')}")
                    return MockResponse(data)
                
                else:
                    error_msg = f"OpenRouter API error: {response.status_code} - {response.text}"
                    logger.error(f"[OpenRouter] ❌ {error_msg}")
                    raise Exception(error_msg)
            
            except Exception as e:
                logger.error(f"[OpenRouter] ❌ Request failed: {e}")
                raise
    
    @property
    def messages(self):
        """Get messages API (mimics Anthropic client structure)."""
        return self.Messages(self)


def create_anthropic_compatible_client(api_key: Optional[str] = None):
    """
    Create an Anthropic-compatible client using OpenRouter.
    
    This function returns a client that can be used as a drop-in replacement
    for the Anthropic client.
    
    Args:
        api_key: OpenRouter API key (optional, will use env var if not provided)
        
    Returns:
        OpenRouterAnthropicAdapter instance
        
    Example:
        >>> client = create_anthropic_compatible_client()
        >>> response = client.messages.create(
        ...     model="claude-3-5-sonnet-20241022",
        ...     max_tokens=1024,
        ...     messages=[{"role": "user", "content": "Hello!"}]
        ... )
        >>> print(response.content[0].text)
    """
    return OpenRouterAnthropicAdapter(api_key)


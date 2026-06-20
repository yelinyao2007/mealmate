"""
Local LLM provider implementation.
Supports multiple local inference backends including Ollama and HuggingFace transformers.
"""

import logging
from typing import List, Dict, Any, Optional

import httpx
from ..base.llm_provider import (
    LLMProvider, LLMProviderError, AuthError, RateLimitError,
    ModelNotFoundError, TimeoutError, ResourceLimitError
)

logger = logging.getLogger(__name__)


class LocalLLMProvider(LLMProvider):
    """
    Local LLM provider implementation.

    Supports multiple local inference engines:
    - Ollama (via HTTP API)
    - HuggingFace Transformers (direct Python usage)
    - Future: llama.cpp, text-generation-webui, etc.
    """

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.backend_type = self.config.get('backend', 'ollama')
        self.client: Optional[httpx.AsyncClient] = None
        self._initialize_backend()

    def _initialize_backend(self) -> None:
        """Initialize the specified local backend."""
        try:
            if self.backend_type == 'ollama':
                self._initialize_ollama()
            elif self.backend_type == 'huggingface':
                self._initialize_huggingface()
            else:
                raise LLMProviderError(f"Unsupported local backend: {self.backend_type}")

            logger.info(f"Initialized local provider with {self.backend_type} backend")

        except Exception as e:
            logger.error(f"Failed to initialize local backend {self.backend_type}: {e}")
            raise LLMProviderError(f"Local backend initialization failed: {str(e)}")

    def _initialize_ollama(self) -> None:
        """Initialize Ollama backend."""
        host = self.config.get('host', 'http://localhost:11434')
        timeout = self.config.get('timeout', 60.0)

        self.client = httpx.AsyncClient(
            base_url=host,
            timeout=timeout,
            follow_redirects=True
        )

        # Test connection
        try:
            response = self.client.get("/api/tags")
            if response.status_code != 200:
                raise LLMProviderError(f"Ollama server returned status {response.status_code}")
        except httpx.RequestError as e:
            raise LLMProviderError(f"Cannot connect to Ollama server at {host}: {str(e)}")

    def _initialize_huggingface(self) -> None:
        """Initialize HuggingFace Transformers backend."""
        # Note: This would require importing transformers and loading models
        # For now, we'll just validate configuration
        model_path = self.config.get('model_path')

        if not model_path:
            raise LLMProviderError("HuggingFace backend requires 'model_path' configuration")

        # Validate that model path exists
        import os
        if not os.path.exists(model_path):
            raise LLMProviderError(f"HuggingFace model path does not exist: {model_path}")

        # We'll create a placeholder for the transformers client
        # which will be initialized on first use due to heavy resource requirements
        self.transformers_model = None
        logger.warning("HuggingFace model will be loaded on first request (heavy resource usage)")

    def validate_config(self) -> None:
        """Validate local provider configuration."""
        required_keys = []

        if self.backend_type == 'ollama':
            required_keys = ['host']
        elif self.backend_type == 'huggingface':
            required_keys = ['model_path']

        missing_keys = [key for key in required_keys if not self.config.get(key)]
        if missing_keys:
            raise LLMProviderError(f"Missing required local configuration: {', '.join(missing_keys)}")

    @property
    def supported_models(self) -> List[str]:
        """Return list of models supported by this local backend."""
        if self.backend_type == 'ollama':
            # Ollama supports any model available locally
            return [
                'llama2',
                'codellama',
                'mistral',
                'neural-chat',
                'phi-2',
                'gemma'
            ]
        elif self.backend_type == 'huggingface':
            # HuggingFace supports models from the specified path
            model_name = self.config.get('model_name', 'unknown')
            return [model_name]
        else:
            return []

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        json_mode: bool = False,
        stream: bool = False,
    ) -> str:
        """
        Send a chat completion request to local backend.

        Routes to appropriate backend based on configuration.
        """
        try:
            if self.backend_type == 'ollama':
                return await self._ollama_chat_completion(
                    messages, temperature, max_tokens, json_mode, stream
                )
            elif self.backend_type == 'huggingface':
                return await self._huggingface_chat_completion(
                    messages, temperature, max_tokens, json_mode, stream
                )
            else:
                raise LLMProviderError(f"Unsupported backend: {self.backend_type}")

        except Exception as e:
            self._handle_local_error(e)

    async def _ollama_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        json_mode: bool,
        stream: bool,
    ) -> str:
        """Handle chat completion via Ollama HTTP API."""
        if not self.client:
            raise LLMProviderError("Ollama client not initialized")

        model = self.config.get('model', 'llama2')

        # Convert messages to Ollama format
        ollama_messages = []
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            if content:
                ollama_messages.append({
                    'role': role,
                    'content': content
                })

        payload = {
            'model': model,
            'messages': ollama_messages,
            'stream': stream
        }

        if temperature is not None:
            payload['options'] = {'temperature': temperature}
        if max_tokens is not None:
            payload['options'] = payload.get('options', {})
            payload['options']['num_predict'] = max_tokens

        if json_mode:
            payload['format'] = 'json'

        try:
            response = await self.client.post('/api/chat', json=payload)

            if response.status_code != 200:
                raise LLMProviderError(f"Ollama API error: {response.status_code} - {response.text}")

            data = response.json()

            if stream:
                # Handle streaming response
                result_parts = []
                async for line in response.aiter_lines():
                    chunk_data = line.strip()
                    if chunk_data:
                        try:
                            chunk = json.loads(chunk_data)
                            if chunk.get('message', {}).get('content'):
                                result_parts.append(chunk['message']['content'])
                        except json.JSONDecodeError:
                            continue

                result = ''.join(result_parts)
            else:
                result = data.get('message', {}).get('content', '')

            if result:
                logger.info(f"Local Ollama response received ({len(result)} chars)")
                return result
            else:
                raise LLMProviderError("Empty response from Ollama")

        except httpx.RequestError as e:
            raise LLMProviderError(f"Ollama request failed: {str(e)}")
        except Exception as e:
            raise LLMProviderError(f"Ollama processing failed: {str(e)}")

    async def _huggingface_chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        json_mode: bool,
        stream: bool,
    ) -> str:
        """Handle chat completion via HuggingFace Transformers."""
        try:
            # Import transformers here to avoid heavy dependency when not used
            from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
            import torch

            model_path = self.config.get('model_path')
            model_name = self.config.get('model_name', 'Unknown Model')

            # Load model and tokenizer on first use
            if not hasattr(self, '_transformers_model') or self._transformers_model is None:
                logger.info(f"Loading HuggingFace model from {model_path}...")

                try:
                    # Try to load as causal language model first
                    tokenizer = AutoTokenizer.from_pretrained(model_path)
                    model = AutoModelForCausalLM.from_pretrained(
                        model_path,
                        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                        device_map="auto" if torch.cuda.is_available() else None
                    )

                    self._transformers_model = {
                        'model': model,
                        'tokenizer': tokenizer
                    }
                    logger.info("HuggingFace model loaded successfully")

                except Exception as e:
                    raise ResourceLimitError(f"Failed to load HuggingFace model: {str(e)}")

            model_data = self._transformers_model
            tokenizer = model_data['tokenizer']
            model = model_data['model']

            # Build prompt from conversation
            prompt = self._build_conversation_prompt(messages)

            # Tokenize input
            inputs = tokenizer(prompt, return_tensors="pt", truncation=True)

            if torch.cuda.is_available():
                inputs = inputs.to('cuda')

            # Generate response
            with torch.no_grad():
                outputs = model.generate(
                    **inputs,
                    max_new_tokens=max_tokens,
                    temperature=temperature if temperature > 0 else 0.1,
                    do_sample=True if temperature > 0 else False,
                    pad_token_id=tokenizer.eos_token_id
                )

            # Decode response
            response_text = tokenizer.decode(outputs[0], skip_special_tokens=True)

            # Extract only the assistant's response
            assistant_response = self._extract_assistant_response(response_text, prompt)

            logger.info(f"Local HuggingFace response received ({len(assistant_response)} chars)")
            return assistant_response

        except torch.cuda.OutOfMemoryError:
            raise ResourceLimitError("GPU memory exhausted. Try a smaller model or enable CPU mode.")
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                raise ResourceLimitError("GPU memory exhausted: " + str(e))
            raise
        except Exception as e:
            raise LLMProviderError(f"HuggingFace generation failed: {str(e)}")

    def _build_conversation_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Build a text prompt from conversation messages."""
        prompt_parts = []

        for msg in messages:
            role = msg.get('role', '').lower()
            content = msg.get('content', '')

            if not content:
                continue

            if role == 'system':
                prompt_parts.append(f"[System]: {content}")
            elif role == 'user':
                prompt_parts.append(f"[User]: {content}")
            elif role == 'assistant':
                prompt_parts.append(f"[Assistant]: {content}")
            else:
                prompt_parts.append(f"{role.title()}: {content}")

        return "\n\n".join(prompt_parts) + "\n\n[Assistant]:"

    def _extract_assistant_response(self, full_response: str, prompt: str) -> str:
        """Extract only the assistant's response from generated text."""
        # If the response contains our prompt, extract only what comes after it
        if full_response.startswith(prompt):
            response_part = full_response[len(prompt):].strip()
            # Remove any additional system prompts that might have been added
            if "[Assistant]:" in response_part:
                response_part = response_part.split("[Assistant]:", 1)[1].strip()
            return response_part
        return full_response

    def _handle_local_error(self, error: Exception) -> None:
        """Translate local backend errors to common exception types."""
        error_str = str(error).lower()

        if "not found" in error_str or "model not found" in error_str:
            logger.error(f"Local model not found: {error}")
            raise ModelNotFoundError(f"Local model not available: {str(error)}")

        elif "memory" in error_str or "out of memory" in error_str or "cuda" in error_str:
            logger.error(f"Local resource limit exceeded: {error}")
            raise ResourceLimitError(f"Resource limit exceeded: {str(error)}")

        elif "connection" in error_str or "cannot connect" in error_str:
            logger.error(f"Local backend connection failed: {error}")
            raise LLMProviderError(f"Backend connection failed: {str(error)}")

        elif "timeout" in error_str or "timed out" in error_str:
            logger.error(f"Local backend timeout: {error}")
            raise TimeoutError(f"Request timed out: {str(error)}")

        else:
            logger.error(f"Local backend error: {error}")
            raise LLMProviderError(f"Local backend failed: {str(error)}")

    def get_metrics(self) -> Dict[str, Any]:
        """Return local provider-specific metrics."""
        metrics = super().get_metrics()
        metrics.update({
            'backend_type': self.backend_type,
            'last_model_used': self.config.get('model', 'unknown'),
            'supports_streaming': self.backend_type == 'ollama',
            'resource_usage': {
                'gpu_available': torch.cuda.is_available() if 'torch' in globals() else False,
                'gpu_memory': torch.cuda.get_device_properties(0).total_memory / 1024**3
                if torch.cuda.is_available() and 'torch' in globals() else 0
            } if self.backend_type == 'huggingface' else {}
        })
        return metrics
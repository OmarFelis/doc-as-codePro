"""AWS Bedrock client for Claude models."""

import json
from typing import Dict, Any, Optional

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

from src.core.llm.base import LLMClient
from src.config.settings import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class BedrockClient(LLMClient):
    """Client for AWS Bedrock (Claude models)."""

    def __init__(self):
        """Initialize Bedrock client."""
        if not BOTO3_AVAILABLE:
            logger.warning("boto3_not_available", message="boto3 is not installed")
            self._client = None
            return

        settings = get_settings()
        
        try:
            self._client = boto3.client(
                "bedrock-runtime",
                region_name=settings.bedrock.region if hasattr(settings, 'bedrock') else "us-east-1",
                aws_access_key_id=settings.bedrock.aws_access_key_id if hasattr(settings, 'bedrock') else None,
                aws_secret_access_key=settings.bedrock.aws_secret_access_key if hasattr(settings, 'bedrock') else None,
            )
            self._model_id = settings.bedrock.model_id if hasattr(settings, 'bedrock') else "anthropic.claude-3-sonnet-20240229-v1:0"
            logger.info("bedrock_client_initialized", model_id=self._model_id)
        except Exception as e:
            logger.error("bedrock_init_error", error=str(e))
            self._client = None

    def is_available(self) -> bool:
        """Check if Bedrock client is available."""
        return self._client is not None

    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate text using Claude via Bedrock."""
        if not self.is_available():
            raise RuntimeError("Bedrock client is not available")

        try:
            # Prepare request body for Claude 3
            messages = [{"role": "user", "content": prompt}]
            
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": messages,
                "temperature": temperature,
            }
            
            if system_prompt:
                body["system"] = system_prompt

            # Invoke model
            response = self._client.invoke_model(
                modelId=self._model_id, body=json.dumps(body)
            )

            # Parse response
            response_body = json.loads(response["body"].read())
            
            # Extract generated text
            if "content" in response_body and len(response_body["content"]) > 0:
                return response_body["content"][0]["text"]
            
            raise ValueError("No content in response")

        except ClientError as e:
            logger.error("bedrock_api_error", error=str(e))
            raise RuntimeError(f"Bedrock API error: {str(e)}")
        except Exception as e:
            logger.error("bedrock_generation_error", error=str(e))
            raise

    async def generate_documentation(
        self, code: str, context: Dict[str, Any]
    ) -> str:
        """Generate documentation for code using Claude."""
        language = context.get("language", "unknown")
        file_path = context.get("file_path", "")

        system_prompt = """You are an expert technical writer and software developer. 
Your task is to generate clear, comprehensive documentation for code."""

        prompt = f"""Generate professional documentation for the following {language} code:

File: {file_path}

```{language}
{code}
```

Please provide:
1. A brief description of what this code does
2. Key functions/classes and their purposes
3. Important implementation details
4. Any notable patterns or techniques used

Format the documentation in Markdown."""

        return await self.generate_text(
            prompt=prompt,
            max_tokens=2000,
            temperature=0.5,
            system_prompt=system_prompt,
        )

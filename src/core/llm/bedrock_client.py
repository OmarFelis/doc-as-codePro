"""AWS Bedrock client — soporta IAM (boto3) y Bearer Token (httpx)."""

import json
import os
from typing import Dict, Any, Optional

try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from src.core.llm.base import LLMClient
from src.config.settings import get_settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


class BedrockClient(LLMClient):
    """Client for AWS Bedrock. Usa bearer token si AWS_BEARER_TOKEN está en env, sino boto3."""

    def __init__(self):
        settings = get_settings()
        self._model_id = settings.bedrock.model_id
        self._region = settings.bedrock.region
        self._bearer_token = os.environ.get("AWS_BEARER_TOKEN")
        self._boto_client = None

        if self._bearer_token:
            if not HTTPX_AVAILABLE:
                logger.error("httpx_not_available", message="pip install httpx")
                self._bearer_token = None
            else:
                logger.info("bedrock_auth", mode="bearer_token", model_id=self._model_id)
        elif BOTO3_AVAILABLE:
            try:
                self._boto_client = boto3.client(
                    "bedrock-runtime",
                    region_name=self._region,
                    aws_access_key_id=settings.bedrock.aws_access_key_id or None,
                    aws_secret_access_key=settings.bedrock.aws_secret_access_key or None,
                )
                logger.info("bedrock_auth", mode="iam", model_id=self._model_id)
            except Exception as e:
                logger.error("bedrock_init_error", error=str(e))
        else:
            logger.warning("bedrock_unavailable", message="No credentials found")

    def is_available(self) -> bool:
        return bool(self._bearer_token or self._boto_client)

    def _build_body(self, prompt: str, max_tokens: int, temperature: float, system_prompt: Optional[str]) -> dict:
        body: Dict[str, Any] = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system_prompt:
            body["system"] = system_prompt
        return body

    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
    ) -> str:
        if not self.is_available():
            raise RuntimeError("Bedrock client is not available")

        body = self._build_body(prompt, max_tokens, temperature, system_prompt)

        try:
            if self._bearer_token:
                return await self._invoke_httpx(body)
            else:
                return self._invoke_boto3(body)
        except Exception as e:
            logger.error("bedrock_generation_error", error=str(e))
            raise

    async def _invoke_httpx(self, body: dict) -> str:
        url = f"https://bedrock-runtime.{self._region}.amazonaws.com/model/{self._model_id}/invoke"
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {self._bearer_token}",
                    "Content-Type": "application/json",
                },
                json=body,
            )
        resp.raise_for_status()
        data = resp.json()
        return data["content"][0]["text"]

    def _invoke_boto3(self, body: dict) -> str:
        try:
            response = self._boto_client.invoke_model(
                modelId=self._model_id, body=json.dumps(body)
            )
            data = json.loads(response["body"].read())
            return data["content"][0]["text"]
        except ClientError as e:
            raise RuntimeError(f"Bedrock API error: {str(e)}")

    async def generate_documentation(self, code: str, context: Dict[str, Any]) -> str:
        language = context.get("language", "unknown")
        file_path = context.get("file_path", "")
        return await self.generate_text(
            prompt=f"Document this {language} code from {file_path}:\n```{language}\n{code}\n```",
            max_tokens=2000,
            temperature=0.5,
            system_prompt="You are an expert technical writer. Generate clear Markdown documentation.",
        )

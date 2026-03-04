"""Test rápido de conectividad con Bedrock via Bearer Token.

Uso:
    set AWS_BEARER_TOKEN=<tu-token>
    poetry run python _test_bedrock.py
"""
import httpx
import json
import os

TOKEN = os.environ.get("AWS_BEARER_TOKEN")
if not TOKEN:
    print("ERROR: define AWS_BEARER_TOKEN en tu .env o como variable de entorno")
    exit(1)

url = "https://bedrock-runtime.us-east-1.amazonaws.com/model/anthropic.claude-3-5-sonnet-20241022-v2:0/invoke"

payload = {
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 20,
    "messages": [{"role": "user", "content": "Responde solo: OK"}],
}

resp = httpx.post(
    url,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    },
    json=payload,
    timeout=30,
)

print("status:", resp.status_code)
print("body:", resp.text[:500])

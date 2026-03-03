"""Diagnóstico del agente Strands — fuerza AWS vars antes de importar boto3."""
import os
import traceback

os.environ["AWS_CONFIG_FILE"] = "C:/Users/ocardenas/.aws/config"
os.environ["AWS_PROFILE"] = "AmazonBedrockLimitedAccess-460896925620"

print("AWS_CONFIG_FILE:", os.environ["AWS_CONFIG_FILE"])
print("AWS_PROFILE:", os.environ["AWS_PROFILE"])

import boto3
from strands import Agent, tool
from strands.models import BedrockModel

session = boto3.Session(profile_name=os.environ["AWS_PROFILE"])
print("session ok")

@tool
def dummy(x: str) -> str:
    """dummy tool"""
    return x

try:
    model = BedrockModel(
        model_id="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
        boto_session=session,
    )
    print("model ok")
    agent = Agent(model=model, tools=[dummy], system_prompt="test")
    print("agent:", type(agent).__name__)
    result = agent("Responde solo: OK")
    print("Respuesta:", str(result)[:300])
except Exception as e:
    traceback.print_exc()

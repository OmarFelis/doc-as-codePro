from dotenv import load_dotenv
load_dotenv(override=True)
import boto3, os

profile = os.getenv("AWS_PROFILE")
config_file = os.getenv("AWS_CONFIG_FILE")
print(f"AWS_PROFILE={profile}")
print(f"AWS_CONFIG_FILE={config_file}")

session = boto3.Session(profile_name=profile) if profile else boto3.Session()
client = session.client("bedrock", region_name="us-east-1")
models = [m["modelId"] for m in client.list_foundation_models()["modelSummaries"] if "claude" in m["modelId"]]
print("Modelos Claude disponibles:")
for m in models:
    print(f"  {m}")

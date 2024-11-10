# test_env.py
from dotenv import load_dotenv
import os

load_dotenv()

print("Environment variables:")
print(f"API KEY: {os.getenv('AZURE_OPENAI_API_KEY', 'Not found')[:5]}...")
print(f"ENDPOINT: {os.getenv('AZURE_OPENAI_ENDPOINT', 'Not found')}")
print(f"VERSION: {os.getenv('AZURE_OPENAI_API_VERSION', 'Not found')}")
print(f"DEPLOYMENT: {os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'Not found')}")
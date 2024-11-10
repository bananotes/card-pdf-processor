import azure.functions as func
from fastapi import FastAPI
from mangum import Mangum
from main import app

# 添加基础路径前缀
app.root_path = "/api"

# 配置 OpenAPI URL
app = FastAPI(
    title="PDF Processing API",
    description="API for processing PDF files using Azure OpenAI",
    version="1.0.0",
    docs_url="/api/docs",    # SwaggerUI URL
    openapi_url="/api/openapi.json",  # OpenAPI schema
    root_path="/api"
)

handler = Mangum(app)

async def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    """每个请求的入口点"""
    return await handler(req, context)
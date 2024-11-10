# main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from openai import AzureOpenAI
import PyPDF2
from io import BytesIO
import asyncio
from tenacity import retry, wait_exponential, stop_after_attempt
from config import settings

app = FastAPI()

# CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Data models
class Card(BaseModel):
    id: str
    question: str
    answer: str


class ChapterResponse(BaseModel):
    name: str
    summary: str
    cards: List[Card]


# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=settings.AZURE_OPENAI_API_KEY,
    api_version=settings.AZURE_OPENAI_API_VERSION,
    azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
)


@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
async def generate_chapter_summary(text: str) -> dict:
    """Generate chapter title and summary"""
    try:
        response = client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional document analysis assistant. Please analyze the text and generate an appropriate chapter title and summary."
                },
                {
                    "role": "user",
                    "content": f"""
                    Please analyze the following text and generate:
                    1. A concise but professional chapter title
                    2. A clear summary (within 200 words)

                    Text content:
                    {text[:3000]}
                    """
                }
            ]
        )
        result = response.choices[0].message.content
        lines = result.strip().split('\n')
        return {
            "name": lines[0].replace("Title:", "").strip(),
            "summary": lines[1].replace("Summary:", "").strip()
        }
    except Exception as e:
        print(f"Error generating summary: {str(e)}")
        raise


@retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
async def generate_qa_cards(text: str) -> List[dict]:
    """Generate Q&A cards"""
    try:
        response = client.chat.completions.create(
            model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
            messages=[
                {
                    "role": "system",
                    "content": "You are an education content expert. Please generate important Q&A pairs based on the text content."
                },
                {
                    "role": "user",
                    "content": f"""
                    Please generate as more as possible important Q&A pairs based on the following text. Each Q&A pair should include:
                    1. A clear question
                    2. A short answer. (no more than 10 words)

                    Text content:
                    {text}

                    Please return in JSON array format, each object containing id, question, and answer fields.
                    Example format:
                    [
                        {{"id": "1", "question": "Question 1", "answer": "Answer 1"}},
                        {{"id": "2", "question": "Question 2", "answer": "Answer 2"}},
                    ]
                    """
                }
            ]
        )
        return eval(response.choices[0].message.content)
    except Exception as e:
        print(f"Error generating QA cards: {str(e)}")
        raise


@app.post("/process-pdf/", response_model=ChapterResponse)
async def process_pdf(file: UploadFile = File(...)):
    try:
        content = await file.read()
        pdf_reader = PyPDF2.PdfReader(BytesIO(content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()

        chapter_info = await generate_chapter_summary(text)
        cards = await generate_qa_cards(text)

        return ChapterResponse(
            name=chapter_info["name"],
            summary=chapter_info["summary"],
            cards=cards
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import router


app = FastAPI(
    title="AI Research & Document Intelligence Assistant",
    description=(
        "Agentic RAG document assistant "
        "using LangChain and LangGraph"
    ),
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router)


@app.get("/")
def root():

    return {
        "message": (
            "AI Research & Document Intelligence "
            "Assistant API"
        ),
        "status": "running"
    }
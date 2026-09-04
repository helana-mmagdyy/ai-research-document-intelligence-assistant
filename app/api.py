import shutil
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv
from fastapi import APIRouter, UploadFile, File
from pydantic import BaseModel

load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from app.loaders import load_pdf
from app.text_splitter import split_documents
from app.vectorstore import create_vectorstore
from app.retriever import create_retriever
from app.graph import create_agent_graph


# ============================================================
# Router
# ============================================================

router = APIRouter()


# ============================================================
# Directories
# ============================================================

UPLOAD_DIR = Path("data/documents")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# In-memory document storage
# ============================================================

document_retrievers = {}


# ============================================================
# LLM
# ============================================================

query_llm = ChatGoogleGenerativeAI(
    model="gemini-3.1-flash-lite",
    temperature=0
)


# ============================================================
# Request Models
# ============================================================

class ChatRequest(BaseModel):
    question: str
    history: list = []


# ============================================================
# Helper: Convert Gemini content to string
# ============================================================

def content_to_string(content) -> str:
    """
    Convert Gemini response content into a normal string.

    Gemini may sometimes return:
        str
    or:
        list
    """

    if isinstance(content, str):
        return content

    if isinstance(content, list):

        parts = []

        for item in content:

            if isinstance(item, dict):

                if "text" in item:
                    parts.append(
                        str(item["text"])
                    )

            else:

                parts.append(
                    str(item)
                )

        return " ".join(parts)

    return str(content)


# ============================================================
# Question Rewriting
# ============================================================

def rewrite_question(
    question: str,
    history: list
) -> str:

    # If there is no conversation history,
    # there is no need to call Gemini.
    if not history:
        return question

    history_text = ""

    for message in history[-6:]:

        role = message.get(
            "role",
            ""
        )

        content = message.get(
            "content",
            ""
        )

        content = content_to_string(
            content
        )

        history_text += (
            f"{role}: {content}\n"
        )

    prompt = f"""
You are a question rewriting assistant.

The user may ask a follow-up question that depends
on previous conversation context.

Rewrite the latest question into a standalone question.

Conversation history:
{history_text}

Latest question:
{question}

Rules:
- Keep the original meaning.
- Resolve references such as "it", "they", "its", "those", etc.
- Do not answer the question.
- Return ONLY the rewritten question.
"""

    response = query_llm.invoke(
        [HumanMessage(content=prompt)]
    )

    return content_to_string(
        response.content
    ).strip()


# ============================================================
# Upload PDF
# ============================================================

@router.post("/upload")
async def upload_pdf(
    file: UploadFile = File(...)
):

    start_time = time.time()

    try:

        print("=" * 60)
        print("[UPLOAD] Upload request received")

        # ----------------------------------------------------
        # Validate filename
        # ----------------------------------------------------

        if not file.filename:

            return {
                "error": "No file selected."
            }

        filename = Path(
            file.filename
        ).name

        print(
            f"[UPLOAD] Filename: {filename}"
        )

        # ----------------------------------------------------
        # Validate PDF
        # ----------------------------------------------------

        if not filename.lower().endswith(".pdf"):

            return {
                "error": "Only PDF files are supported."
            }

        # ----------------------------------------------------
        # Create document ID
        # ----------------------------------------------------

        document_id = str(
            uuid.uuid4()
        )

        file_path = (
            UPLOAD_DIR
            / f"{document_id}.pdf"
        )

        print(
            f"[UPLOAD] Saving to: {file_path}"
        )

        # ----------------------------------------------------
        # Save PDF
        # ----------------------------------------------------

        save_start = time.time()

        with open(
            file_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

        print(
            f"[1] PDF saved: "
            f"{time.time() - save_start:.2f}s"
        )

        file_size = file_path.stat().st_size

        print(
            f"[UPLOAD] File size: "
            f"{file_size} bytes"
        )

        # ----------------------------------------------------
        # Load PDF
        # ----------------------------------------------------

        load_start = time.time()

        documents = load_pdf(
            str(file_path)
        )

        print(
            f"[2] PDF loaded: "
            f"{time.time() - load_start:.2f}s"
        )

        print(
            f"    Pages: {len(documents)}"
        )

        if not documents:

            return {
                "error": (
                    "The PDF contains no readable text."
                )
            }

        # ----------------------------------------------------
        # Split documents
        # ----------------------------------------------------

        split_start = time.time()

        chunks = split_documents(
            documents
        )

        print(
            f"[3] Text split: "
            f"{time.time() - split_start:.2f}s"
        )

        print(
            f"    Chunks: {len(chunks)}"
        )

        if not chunks:

            return {
                "error": (
                    "Could not extract text "
                    "chunks from the PDF."
                )
            }

        # ----------------------------------------------------
        # Create vector store
        # ----------------------------------------------------

        vector_start = time.time()

        vectorstore = create_vectorstore(
            chunks,
            collection_name=document_id
        )

        print(
            f"[4] Vector store: "
            f"{time.time() - vector_start:.2f}s"
        )

        # ----------------------------------------------------
        # Create retriever
        # ----------------------------------------------------

        retriever_start = time.time()

        retriever = create_retriever(
            vectorstore
        )

        print(
            f"[5] Retriever: "
            f"{time.time() - retriever_start:.2f}s"
        )

        # ----------------------------------------------------
        # Save retriever
        # ----------------------------------------------------

        document_retrievers[
            document_id
        ] = {
            "retriever": retriever,
            "filename": filename,
            "file_path": str(file_path)
        }

        # ----------------------------------------------------
        # Complete
        # ----------------------------------------------------

        total_time = (
            time.time()
            - start_time
        )

        print(
            f"[UPLOAD COMPLETE] {filename}"
        )

        print(
            f"Total processing time: "
            f"{total_time:.2f}s"
        )

        print("=" * 60)

        return {
            "message": (
                "PDF uploaded successfully."
            ),
            "document_id": document_id,
            "filename": filename,
            "pages": len(documents),
            "chunks": len(chunks),
            "status": "ready"
        }

    except Exception as e:

        print("=" * 60)

        print(
            f"[ERROR] Upload failed: "
            f"{type(e).__name__}"
        )

        print(
            f"[ERROR] {e}"
        )

        print("=" * 60)

        return {
            "error": str(e),
            "error_type": type(e).__name__
        }

    finally:

        await file.close()


# ============================================================
# Chat
# ============================================================

@router.post("/chat")
async def chat(
    request: ChatRequest
):

    start_time = time.time()

    try:

        print("=" * 60)
        print("[CHAT] Question received")

        # ----------------------------------------------------
        # Validate question
        # ----------------------------------------------------

        question = request.question

        if not isinstance(
            question,
            str
        ):

            return {
                "error": (
                    "Question must be a string."
                )
            }

        question = question.strip()

        if not question:

            return {
                "error": (
                    "Question cannot be empty."
                )
            }

        # ----------------------------------------------------
        # Check documents
        # ----------------------------------------------------

        if not document_retrievers:

            return {
                "error": (
                    "Please upload a PDF first."
                )
            }

        print(
            f"[CHAT] Documents available: "
            f"{len(document_retrievers)}"
        )

        # ----------------------------------------------------
        # Rewrite only when history exists
        # ----------------------------------------------------

        if request.history:

            rewrite_start = time.time()

            standalone_question = (
                rewrite_question(
                    question,
                    request.history
                )
            )

            print(
                f"[1] Question rewritten: "
                f"{time.time() - rewrite_start:.2f}s"
            )

        else:

            standalone_question = question

            print(
                "[1] Question rewriting skipped."
            )

        print(
            f"[CHAT] Original: "
            f"{question}"
        )

        print(
            f"[CHAT] Standalone: "
            f"{standalone_question}"
        )

        # ----------------------------------------------------
        # Retrieval
        # ----------------------------------------------------

        retrieval_start = time.time()

        all_documents = []

        for (
            document_id,
            document_info
        ) in document_retrievers.items():

            retriever = (
                document_info[
                    "retriever"
                ]
            )

            try:

                documents = retriever.invoke(
                    standalone_question
                )

                for document in documents:

                    document.metadata[
                        "document_id"
                    ] = document_id

                    document.metadata[
                        "filename"
                    ] = document_info[
                        "filename"
                    ]

                    all_documents.append(
                        document
                    )

            except Exception as retrieval_error:

                print(
                    f"[RETRIEVAL ERROR] "
                    f"{document_id}: "
                    f"{retrieval_error}"
                )

        print(
            f"[2] Retrieval: "
            f"{time.time() - retrieval_start:.2f}s"
        )

        print(
            f"    Retrieved documents: "
            f"{len(all_documents)}"
        )

        # ----------------------------------------------------
        # DEBUG: Print retrieved chunks
        # ----------------------------------------------------

        for i, document in enumerate(
            all_documents
        ):

            print("=" * 50)

            print(
                f"[RETRIEVED {i + 1}]"
            )

            print(
                "Filename:",
                document.metadata.get(
                    "filename",
                    "unknown"
                )
            )

            page = document.metadata.get(
                "page",
                "unknown"
            )

            if isinstance(page, int):
                page = page + 1

            print(
                "Page:",
                page
            )

            print(
                "Content:"
            )

            print(
                document.page_content[:1000]
            )

        print("=" * 50)

        # ----------------------------------------------------
        # No retrieved documents
        # ----------------------------------------------------

        if not all_documents:

            print(
                "[CHAT] No relevant documents found."
            )

            return {
                "answer": (
                    "This information is not "
                    "available in the uploaded documents."
                ),
                "sources": []
            }

        # ----------------------------------------------------
        # Build context
        # ----------------------------------------------------

        context_parts = []

        sources = []

        seen_sources = set()

        for document in all_documents:

            filename = document.metadata.get(
                "filename",
                "unknown"
            )

            page = document.metadata.get(
                "page",
                "unknown"
            )

            # PyPDFLoader page numbers start at 0
            if isinstance(page, int):

                page_number = page + 1

            else:

                page_number = page

            content = document.page_content

            context_parts.append(
                f"""
Source: {filename}
Page: {page_number}

Content:
{content}
"""
            )

            source_key = (
                filename,
                page_number
            )

            if source_key not in seen_sources:

                sources.append({
                    "filename": filename,
                    "page": page_number
                })

                seen_sources.add(
                    source_key
                )

        context = (
            "\n\n---\n\n"
            .join(context_parts)
        )

        print(
            f"[CHAT] Context length: "
            f"{len(context)} characters"
        )

        # ----------------------------------------------------
        # Generate answer with LangGraph
        # ----------------------------------------------------

        graph_start = time.time()

        graph = create_agent_graph()

        result = graph.invoke({
            "question": standalone_question,
            "context": context,
            "messages": [
                HumanMessage(
                    content=standalone_question
                )
            ],
            "answer": ""
        })

        print(
            f"[3] Graph: "
            f"{time.time() - graph_start:.2f}s"
        )

        # ----------------------------------------------------
        # Extract answer
        # ----------------------------------------------------

        answer = result.get(
            "answer",
            ""
        )

        answer = content_to_string(
            answer
        ).strip()

        if not answer:

            answer = (
                "I could not generate an answer "
                "from the uploaded documents."
            )

        # ----------------------------------------------------
        # Complete
        # ----------------------------------------------------

        total_time = (
            time.time()
            - start_time
        )

        print(
            f"[CHAT COMPLETE] "
            f"{total_time:.2f}s"
        )

        print("=" * 60)

        return {
            "answer": answer,
            "sources": sources
        }

    except Exception as e:

        print("=" * 60)

        print(
            f"[ERROR] Chat failed: "
            f"{type(e).__name__}"
        )

        print(
            f"[ERROR] {e}"
        )

        print("=" * 60)

        return {
            "error": str(e),
            "error_type": type(e).__name__
        }


# ============================================================
# Get Documents
# ============================================================

@router.get("/documents")
async def get_documents():

    documents = []

    for (
        document_id,
        document_info
    ) in document_retrievers.items():

        documents.append({
            "document_id": document_id,
            "filename": document_info[
                "filename"
            ],
            "status": "ready"
        })

    return {
        "documents": documents
    }


# ============================================================
# Delete Document
# ============================================================

@router.delete(
    "/documents/{document_id}"
)
async def delete_document(
    document_id: str
):

    if document_id not in document_retrievers:

        return {
            "error": "Document not found."
        }

    document_info = (
        document_retrievers[
            document_id
        ]
    )

    # Remove from memory

    del document_retrievers[
        document_id
    ]

    # Remove uploaded PDF

    file_path = Path(
        document_info["file_path"]
    )

    if file_path.exists():

        file_path.unlink()

    return {
        "message": (
            "Document deleted successfully."
        ),
        "document_id": document_id
    }
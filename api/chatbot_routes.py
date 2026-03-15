"""
FastAPI route for the Credit Intelligence Chatbot — /api/v1/chatbot/ask
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from chatbot.credit_chatbot import answer_credit_question

router = APIRouter()

DEFAULT_DOC_ID = "pi-cmmjo68xg04il9rqnht74lnr1"


class ChatRequest(BaseModel):
    question: str
    doc_id: Optional[str] = None
    session_id: Optional[str] = "default_session"
    credit_context: Dict[str, Any] = {}


class ChatResponse(BaseModel):
    answer: str
    source: str
    confidence: str


@router.post("/ask", response_model=ChatResponse)
async def ask_chatbot(req: ChatRequest):
    """
    Ask a natural-language question about the credit decision.
    Uses PageIndex + GPT-4o Mini to produce a grounded, citable answer.
    """
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # Check if PageIndex is ready for this session
    from api.upload_routes import pageindex_session_cache
    
    doc_id = pageindex_session_cache.get(req.session_id) or req.doc_id or DEFAULT_DOC_ID

    if doc_id:
        print(f"[CHATBOT SOURCE] Using PageIndex doc_id={doc_id}")
    else:
        print("[CHATBOT SOURCE] PageIndex not ready — using credit context only")

    try:
        result = answer_credit_question(
            question=req.question.strip(),
            doc_id=doc_id,
            credit_context=req.credit_context
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chatbot error: {str(e)}")

    return ChatResponse(
        answer=result.get("answer", ""),
        source=result.get("source", "Unknown"),
        confidence=result.get("confidence", "LOW")
    )

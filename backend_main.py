"""
Financial Advisor AI Backend - FastAPI Application
Task 4: End-to-End Prototype

This FastAPI backend provides:
1. RAG pipeline wrapped as REST API
2. Conversation memory (Redis)
3. User context management
4. Tool integration (Tavily, calculators)
"""

import os
import json
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# LangChain imports
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic

# Redis for memory (optional - can use in-memory dict for MVP)
try:
    import redis
    redis_available = True
except ImportError:
    redis_available = False

# ============================================================================
# Configuration
# ============================================================================

API_KEYS = {
    "openai": os.getenv("OPENAI_API_KEY"),
    "anthropic": os.getenv("ANTHROPIC_API_KEY"),
    "tavily": os.getenv("TAVILY_API_KEY"),
    "redis_url": os.getenv("REDIS_URL"),  # e.g., Upstash Redis
}

EMBEDDING_MODEL = "text-embedding-3-small"
LLM_MODEL = "claude-3-5-sonnet-20241022"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
RETRIEVAL_K = 4

# ============================================================================
# Data Models
# ============================================================================

class UserContext(BaseModel):
    """User's financial situation."""
    user_id: str
    salary: Optional[float] = None
    assets: Optional[float] = None
    debt: Optional[float] = None
    timeline_years: Optional[int] = None
    risk_tolerance: Optional[str] = None  # "conservative", "moderate", "aggressive"
    goals: Optional[List[str]] = None
    created_at: str = None
    updated_at: str = None

    def __init__(self, **data):
        super().__init__(**data)
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()


class Message(BaseModel):
    """A conversation message."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: str = None
    sources: Optional[List[dict]] = None

    def __init__(self, **data):
        super().__init__(**data)
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


class ChatRequest(BaseModel):
    """User's chat message."""
    user_id: str
    message: str
    session_id: Optional[str] = None
    user_context: Optional[UserContext] = None


class ChatResponse(BaseModel):
    """Assistant's chat response."""
    session_id: str
    user_message: str
    assistant_response: str
    sources: List[dict]
    num_chunks_retrieved: int
    timestamp: str
    retrieval_scores: List[float]


# ============================================================================
# Initialize RAG Pipeline
# ============================================================================

class FinancialAdvisorRAG:
    """Financial Advisor RAG Pipeline."""

    def __init__(self):
        """Initialize RAG components."""
        self.embeddings = None
        self.vector_store = None
        self.llm = None
        self.rag_chain = None
        self._initialize()

    def _initialize(self):
        """Set up embeddings, vector store, and LLM."""
        print("🔄 Initializing RAG pipeline...")

        # 1. Initialize embeddings
        self.embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
        print(f"✓ Embeddings initialized: {EMBEDDING_MODEL}")

        # 2. Load and chunk PDF
        pdf_path = Path("Were-Talking-Millions.pdf")
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        loader = PyPDFLoader(str(pdf_path))
        pages = loader.load()

        # Add metadata
        for page in pages:
            page.metadata["source"] = "Were-Talking-Millions.pdf"
            page.metadata["document_type"] = "financial_guidance"

        # Filter empty pages
        pages = [page for page in pages if page.page_content.strip()]
        print(f"✓ Loaded {len(pages)} PDF pages")

        # 3. Chunk documents
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", "(?<=[.!?]) +", " ", ""],
            add_start_index=True,
        )
        splits = splitter.split_documents(pages)
        print(f"✓ Created {len(splits)} chunks (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")

        # 4. Build Qdrant vector store
        self.vector_store = QdrantVectorStore.from_documents(
            documents=splits,
            embedding=self.embeddings,
            location=":memory:",
            collection_name="financial_advisor",
            force_recreate=True,
        )
        print(f"✓ Built Qdrant vector store")

        # 5. Initialize LLM
        self.llm = ChatAnthropic(model=LLM_MODEL, temperature=0.7)
        print(f"✓ Initialized LLM: {LLM_MODEL}")

        # 6. Set up RAG chain
        system_prompt = """You are an intelligent Financial Advisor AI assistant.

Your role is to help high-income earners make informed financial decisions by:
1. Understanding their situation and constraints
2. Retrieving relevant financial principles and frameworks
3. Building personalized decision frameworks (not just yes/no answers)
4. Grounding your advice in the provided knowledge base
5. Acknowledging behavioral biases and psychological factors

Guidelines:
- Use only the provided context from Were-Talking-Millions.pdf
- If context lacks information, say: "I don't have detailed guidance on that in my knowledge base."
- Cite sources using [Source 1], [Source 2]
- Explain reasoning behind recommendations
- Acknowledge multiple valid approaches
- For decision paralysis: provide a clear framework
- Do NOT provide tax advice (recommend CPA); DO explain tax principles
- Do NOT recommend specific stocks/funds; DO explain evaluation methods

Always end: "Is there anything else about this decision you'd like to explore?" """

        user_prompt = """Context from Knowledge Base:
{context}

User Question: {question}

Provide a thoughtful, personalized response that teaches decision-making."""

        rag_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", user_prompt),
        ])

        self.rag_chain = rag_prompt | self.llm | StrOutputParser()
        print(f"✓ RAG chain ready")

    def retrieve_and_answer(self, question: str, user_context: Optional[str] = None) -> dict:
        """Retrieve relevant chunks and generate answer."""
        # Retrieve
        scored_docs = self.vector_store.similarity_search_with_score(question, k=RETRIEVAL_K)

        # Format context
        context_parts = []
        sources = []
        retrieval_scores = []

        for idx, (doc, score) in enumerate(scored_docs, start=1):
            page = doc.metadata.get("page")
            page_display = page + 1 if isinstance(page, int) else "unknown"

            context_parts.append(
                f"[Source {idx}] {doc.metadata.get('source')}, page {page_display}\n{doc.page_content}"
            )

            sources.append({
                "source_label": f"Source {idx}",
                "file": doc.metadata.get("source"),
                "page": page_display,
                "relevance_score": float(score),
                "preview": doc.page_content[:200],
            })

            retrieval_scores.append(float(score))

        context = "\n\n".join(context_parts)

        # Enhance context with user situation if provided
        if user_context:
            context = f"User Context:\n{user_context}\n\n{context}"

        # Generate answer
        answer = self.rag_chain.invoke({
            "context": context,
            "question": question,
        })

        return {
            "answer": answer,
            "sources": sources,
            "num_chunks_retrieved": len(scored_docs),
            "retrieval_scores": retrieval_scores,
        }


# ============================================================================
# Initialize FastAPI App
# ============================================================================

app = FastAPI(
    title="Financial Advisor AI",
    description="Agentic RAG for financial guidance",
    version="0.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production: specify origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG
rag = FinancialAdvisorRAG()

# In-memory session storage (MVP; use Redis in production)
sessions = {}
users = {}


# ============================================================================
# API Routes
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "rag_ready": rag.vector_store is not None,
        "timestamp": datetime.now().isoformat(),
    }


@app.post("/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint.

    Accepts a user message, retrieves relevant knowledge, and generates a response.
    """
    try:
        # Get or create session
        session_id = request.session_id or f"session_{request.user_id}_{datetime.now().timestamp()}"

        if session_id not in sessions:
            sessions[session_id] = {
                "user_id": request.user_id,
                "messages": [],
                "user_context": request.user_context.dict() if request.user_context else {},
                "created_at": datetime.now().isoformat(),
            }

        # Update user context if provided
        if request.user_context:
            sessions[session_id]["user_context"] = request.user_context.dict()

        # Format user context for retrieval
        context_str = None
        if sessions[session_id]["user_context"]:
            ctx = sessions[session_id]["user_context"]
            context_str = f"User: Age ~{ctx.get('timeline_years', 'unknown')}, Salary ~${ctx.get('salary', 'unknown')}, Assets ${ctx.get('assets', 'unknown')}, Risk tolerance: {ctx.get('risk_tolerance', 'unknown')}"

        # Retrieve and answer
        result = rag.retrieve_and_answer(request.message, context_str)

        # Store in session
        sessions[session_id]["messages"].append({
            "role": "user",
            "content": request.message,
            "timestamp": datetime.now().isoformat(),
        })
        sessions[session_id]["messages"].append({
            "role": "assistant",
            "content": result["answer"],
            "timestamp": datetime.now().isoformat(),
            "sources": result["sources"],
        })

        return ChatResponse(
            session_id=session_id,
            user_message=request.message,
            assistant_response=result["answer"],
            sources=result["sources"],
            num_chunks_retrieved=result["num_chunks_retrieved"],
            timestamp=datetime.now().isoformat(),
            retrieval_scores=result["retrieval_scores"],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get conversation history for a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    return sessions[session_id]


@app.post("/session/{session_id}/context")
async def update_session_context(session_id: str, context: UserContext):
    """Update user context for a session."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    sessions[session_id]["user_context"] = context.dict()
    sessions[session_id]["updated_at"] = datetime.now().isoformat()

    return {"status": "updated", "session_id": session_id}


@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    if session_id in sessions:
        del sessions[session_id]
        return {"status": "deleted", "session_id": session_id}

    raise HTTPException(status_code=404, detail="Session not found")


# ============================================================================
# WebSocket for Real-Time Chat (Optional)
# ============================================================================

@app.websocket("/ws/chat/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time chat."""
    await websocket.accept()

    if session_id not in sessions:
        await websocket.send_json({"error": "Session not found"})
        await websocket.close()
        return

    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message_data = json.loads(data)
            user_message = message_data.get("message")

            if not user_message:
                await websocket.send_json({"error": "No message provided"})
                continue

            # Get RAG response
            context_str = None
            if sessions[session_id].get("user_context"):
                ctx = sessions[session_id]["user_context"]
                context_str = f"User: Salary ${ctx.get('salary')}, Assets ${ctx.get('assets')}, Timeline {ctx.get('timeline_years')} years"

            result = rag.retrieve_and_answer(user_message, context_str)

            # Send response
            await websocket.send_json({
                "role": "assistant",
                "content": result["answer"],
                "sources": result["sources"],
                "num_chunks_retrieved": result["num_chunks_retrieved"],
                "timestamp": datetime.now().isoformat(),
            })

            # Store in session
            sessions[session_id]["messages"].append({
                "role": "user",
                "content": user_message,
                "timestamp": datetime.now().isoformat(),
            })
            sessions[session_id]["messages"].append({
                "role": "assistant",
                "content": result["answer"],
                "timestamp": datetime.now().isoformat(),
                "sources": result["sources"],
            })

    except Exception as e:
        await websocket.send_json({"error": str(e)})
        await websocket.close()


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 Financial Advisor AI Backend")
    print("="*80)
    print(f"Starting FastAPI server...")
    print(f"📚 RAG Pipeline: {EMBEDDING_MODEL} + {LLM_MODEL}")
    print(f"🗄️  Vector Store: Qdrant (in-memory)")
    print(f"📖 Knowledge Base: Were-Talking-Millions.pdf")
    print("="*80 + "\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )

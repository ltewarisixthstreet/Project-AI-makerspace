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

# Load environment variables from a local .env file if present (no-op in prod
# environments like Render where vars are set directly).
from dotenv import load_dotenv
load_dotenv()

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
LLM_MODEL = "claude-sonnet-5"
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
RETRIEVAL_K = 6              # Task 6: raised from 4 for more grounding context

# Task 6: hybrid retrieval — fuse BM25 keyword search with dense vector search
# (reciprocal-rank fusion). Keyword matching catches exact terms (e.g. "37%
# bracket", dollar thresholds) that pure embeddings miss. Set False for
# dense-only (the Task 5 baseline behavior).
HYBRID_RETRIEVAL = True
RRF_CONSTANT = 60           # reciprocal-rank-fusion damping constant

# Additional structured knowledge sources (loaded whole, not chunked).
EXCEL_SOURCES = ["tax_slab_2025.xlsx"]

# ============================================================================
# Data Models
# ============================================================================

class UserContext(BaseModel):
    """User's financial situation."""
    user_id: Optional[str] = None
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
    # Optional per-request "bring your own key" overrides. When supplied, the
    # user's OpenAI key embeds the query and their Anthropic key generates the
    # answer. Kept out of the session store and never logged.
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None


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
        self.bm25 = None
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

        # 3b. Load additional structured sources (spreadsheets) as whole
        # documents — tabular data like tax brackets doesn't chunk well.
        extra_docs = []
        for xlsx_name in EXCEL_SOURCES:
            xlsx_path = Path(xlsx_name)
            if xlsx_path.exists():
                extra_docs.extend(self._load_excel_documents(xlsx_path))
            else:
                print(f"⚠ Skipping missing spreadsheet: {xlsx_name}")

        all_docs = splits + extra_docs

        # 4. Build Qdrant vector store
        self.vector_store = QdrantVectorStore.from_documents(
            documents=all_docs,
            embedding=self.embeddings,
            location=":memory:",
            collection_name="financial_advisor",
            force_recreate=True,
        )
        print(f"✓ Built Qdrant vector store ({len(all_docs)} documents)")

        # 4b. Build BM25 keyword retriever for hybrid search (Task 6).
        self.bm25 = None
        if HYBRID_RETRIEVAL:
            try:
                from langchain_community.retrievers import BM25Retriever
                self.bm25 = BM25Retriever.from_documents(all_docs)
                print("✓ BM25 keyword retriever ready (hybrid retrieval enabled)")
            except Exception as e:
                print(f"⚠ BM25 unavailable — falling back to dense-only retrieval: {e}")

        # 5. Initialize LLM
        # Note: claude-sonnet-5 (and other 4.7+ models) reject non-default
        # sampling params like temperature; steer behavior via the prompt instead.
        self.llm = ChatAnthropic(model=LLM_MODEL)
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
- Use only the provided context from the knowledge base (Were-Talking-Millions.pdf and the 2025 U.S. federal income tax brackets from tax_slab_2025.xlsx)
- If context lacks information, say: "I don't have detailed guidance on that in my knowledge base."
- Ground every specific figure, percentage, dollar threshold, statistic, or quote in the retrieved context. If a number is not present in the context, do NOT state it — say the knowledge base doesn't specify it, or speak qualitatively instead of inventing values.
- Cite sources using [Source 1], [Source 2]
- Attach a [Source N] citation only to a claim that source actually supports; never cite a source for a figure or statement it does not contain
- Explain reasoning behind recommendations
- Acknowledge multiple valid approaches
- For decision paralysis: provide a clear framework
- You may use the provided 2025 federal tax brackets to explain marginal vs. effective tax and illustrate calculations; for personal filing decisions, still recommend consulting a CPA
- Do NOT recommend specific stocks/funds; DO explain evaluation methods

Always end: "Is there anything else about this decision you'd like to explore?" """

        user_prompt = """Context from Knowledge Base:
{context}

User Question: {question}

Provide a thoughtful, personalized response that teaches decision-making."""

        self.rag_prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", user_prompt),
        ])

        self.rag_chain = self.rag_prompt | self.llm | StrOutputParser()
        print(f"✓ RAG chain ready")

    def _load_excel_documents(self, path: Path) -> List:
        """Load a spreadsheet into retrieval documents.

        Structured/tabular data (e.g. tax brackets) doesn't chunk well, so each
        sheet becomes one 'full table' document (all rows kept together) plus one
        document per data row for granular retrieval. Values in a column whose
        header mentions 'rate' that look like fractions (0-1) render as percents.
        """
        import openpyxl
        from langchain_core.documents import Document

        def fmt(header, value) -> str:
            if value is None:
                return ""
            if "rate" in str(header).lower() and isinstance(value, (int, float)) and 0 < value <= 1:
                return f"{value:.0%}"
            return str(value)

        wb = openpyxl.load_workbook(str(path), data_only=True)
        docs = []
        for ws in wb.worksheets:
            rows = [list(r) for r in ws.iter_rows(values_only=True)]
            rows = [r for r in rows if any(c is not None for c in r)]
            if not rows:
                continue

            # A single-cell first row is treated as a descriptive title.
            title = None
            header_idx = 0
            first_nonempty = [c for c in rows[0] if c is not None]
            if len(first_nonempty) == 1 and isinstance(first_nonempty[0], str):
                title = first_nonempty[0].strip()
                header_idx = 1
            if header_idx >= len(rows):
                continue

            headers = [
                (str(c).strip() if c is not None else f"col{i}")
                for i, c in enumerate(rows[header_idx])
            ]
            data_rows = rows[header_idx + 1:]
            base_meta = {"source": path.name, "document_type": "tax_reference", "sheet": ws.title}

            # 1) Full-table document — keeps the whole schedule together.
            lines = []
            if title:
                lines.append(title)
            lines.append(" | ".join(headers))
            for r in data_rows:
                lines.append(" | ".join(fmt(h, c) for h, c in zip(headers, r)))
            docs.append(Document(page_content="\n".join(lines), metadata={**base_meta, "row": "all"}))

            # 2) One document per data row — granular retrieval.
            for ridx, r in enumerate(data_rows, start=1):
                pairs = [f"{h}: {fmt(h, c)}" for h, c in zip(headers, r) if c is not None]
                if not pairs:
                    continue
                prefix = f"{title} — " if title else ""
                docs.append(Document(page_content=prefix + "; ".join(pairs), metadata={**base_meta, "row": ridx}))

        print(f"✓ Loaded {len(docs)} document(s) from {path.name}")
        return docs

    def _hybrid_retrieve(self, question: str, k: int, query_vector: Optional[list] = None):
        """Hybrid retrieval: fuse dense (vector) and BM25 (keyword) rankings via
        reciprocal-rank fusion. Returns a list of (Document, dense_score) tuples,
        ordered by fused rank. The reported score is the dense cosine score (for
        continuity with the dense-only baseline); BM25-only hits report 0.0.

        When ``query_vector`` is provided (e.g. embedded with a user-supplied
        OpenAI key), the dense search runs against that vector instead of
        re-embedding ``question`` with the server's key.
        """
        candidate_k = max(20, k * 4)

        if query_vector is not None:
            dense_scored = self.vector_store.similarity_search_with_score_by_vector(
                query_vector, k=candidate_k
            )
        else:
            dense_scored = self.vector_store.similarity_search_with_score(question, k=candidate_k)
        dense_rank, score_map, doc_by_key = {}, {}, {}
        for rank, (doc, score) in enumerate(dense_scored):
            key = doc.page_content
            dense_rank.setdefault(key, rank)
            score_map.setdefault(key, float(score))
            doc_by_key.setdefault(key, doc)

        bm25_rank = {}
        if self.bm25 is not None:
            self.bm25.k = candidate_k
            for rank, doc in enumerate(self.bm25.invoke(question)):
                key = doc.page_content
                bm25_rank.setdefault(key, rank)
                doc_by_key.setdefault(key, doc)

        fused = []
        for key in set(dense_rank) | set(bm25_rank):
            s = 0.0
            if key in dense_rank:
                s += 1.0 / (RRF_CONSTANT + dense_rank[key])
            if key in bm25_rank:
                s += 1.0 / (RRF_CONSTANT + bm25_rank[key])
            fused.append((key, s))
        fused.sort(key=lambda x: x[1], reverse=True)

        return [(doc_by_key[key], score_map.get(key, 0.0)) for key, _ in fused[:k]]

    def retrieve_and_answer(
        self,
        question: str,
        user_context: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
    ) -> dict:
        """Retrieve relevant chunks and generate answer.

        If ``openai_api_key`` / ``anthropic_api_key`` are given, they override
        the server keys for query embedding and generation respectively
        (bring-your-own-key). Keys are used transiently and never stored.
        """
        # If the user supplied their own OpenAI key, embed the query with it so
        # the dense search runs on their quota. Same model → vectors remain
        # comparable to the store built at startup.
        query_vector = None
        if openai_api_key:
            user_embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL, api_key=openai_api_key)
            query_vector = user_embeddings.embed_query(question)

        # Retrieve — hybrid (BM25 + dense) when enabled, else dense-only.
        if HYBRID_RETRIEVAL and self.bm25 is not None:
            scored_docs = self._hybrid_retrieve(question, RETRIEVAL_K, query_vector=query_vector)
        elif query_vector is not None:
            scored_docs = self.vector_store.similarity_search_with_score_by_vector(
                query_vector, k=RETRIEVAL_K
            )
        else:
            scored_docs = self.vector_store.similarity_search_with_score(question, k=RETRIEVAL_K)

        # Format context
        context_parts = []
        sources = []
        retrieval_scores = []

        for idx, (doc, score) in enumerate(scored_docs, start=1):
            page = doc.metadata.get("page")
            if isinstance(page, int):
                page_display = page + 1
            elif doc.metadata.get("sheet"):
                page_display = doc.metadata["sheet"]
            else:
                page_display = "unknown"

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

        # Generate answer — use the user's Anthropic key if supplied, else the
        # server's pre-built chain.
        if anthropic_api_key:
            user_llm = ChatAnthropic(model=LLM_MODEL, api_key=anthropic_api_key)
            chain = self.rag_prompt | user_llm | StrOutputParser()
        else:
            chain = self.rag_chain

        answer = chain.invoke({
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
            context_str = (
                f"User financial profile: "
                f"Salary ~${ctx.get('salary', 'unknown')}, "
                f"Assets ${ctx.get('assets', 'unknown')}, "
                f"Debt ${ctx.get('debt', 'unknown')}, "
                f"Years to retirement: {ctx.get('timeline_years', 'unknown')}, "
                f"Risk tolerance: {ctx.get('risk_tolerance', 'unknown')}"
            )

        # Retrieve and answer (honoring any bring-your-own-key overrides)
        result = rag.retrieve_and_answer(
            request.message,
            context_str,
            openai_api_key=request.openai_api_key,
            anthropic_api_key=request.anthropic_api_key,
        )

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
        # Surface user-supplied-key auth failures as a clear 401 instead of 500.
        msg = str(e)
        if request.openai_api_key or request.anthropic_api_key:
            low = msg.lower()
            if "authentication" in low or "api key" in low or "401" in low or "invalid" in low:
                raise HTTPException(
                    status_code=401,
                    detail="The provided API key was rejected. Check your OpenAI/Anthropic key and try again.",
                )
        raise HTTPException(status_code=500, detail=msg)


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
    print(f"📖 Knowledge Base: Were-Talking-Millions.pdf + {', '.join(EXCEL_SOURCES)}")
    print("="*80 + "\n")

    # Bind to the platform-provided PORT (e.g. Render sets $PORT); default 8000 locally.
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info",
    )

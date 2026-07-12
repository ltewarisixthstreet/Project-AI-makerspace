# Task 2: Solution Design & Architecture

## Solution Statement (1 sentence)

A conversational financial advisor AI that integrates personal financial context through multi-turn memory, uses agentic RAG to ground recommendations in curated financial knowledge, provides decision frameworks tailored to the user's situation, and surfaces relevant tax/behavioral considerations in plain language.

---

## Infrastructure Diagram & Technology Justification

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE LAYER                             │
│  Frontend: Next.js/React (Web + Mobile Responsive) on Vercel            │
│  - Conversational chat UI with context sidebar                          │
│  - Session persistence (browser localStorage)                           │
│  - Financial context form (income, assets, timeline, risk profile)      │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTP/WebSocket
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      API ORCHESTRATION LAYER                             │
│  Backend: FastAPI (Python) deployed on Render or Railway                │
│  - WebSocket handler for real-time chat                                 │
│  - Session memory management (SQLite or Upstash Redis)                  │
│  - Request routing to agent pipeline                                    │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
        ┌──────────────────┐ ┌──────────────┐ ┌──────────────┐
        │   LLM GATEWAY    │ │ VECTOR DB    │ │ MEMORY STORE │
        │  (Anthropic API) │ │   (Qdrant)   │ │  (Redis/Upstash)
        │                  │ │              │ │              │
        │ Claude 3.5 Sonnet│ │ In-memory or │ │ Conversation │
        │ (Reasoning,      │ │ cloud        │ │ history +    │
        │  Planning)       │ │              │ │ user context │
        └──────────────────┘ └──────────────┘ └──────────────┘
                    │               │               │
                    └───────────────┼───────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
        ┌──────────────────┐ ┌──────────────┐ ┌──────────────┐
        │   RAG PIPELINE   │ │  TOOLS       │ │  EVALUATOR   │
        │  (LangChain)     │ │              │ │  (LLM-as-Judge)
        │                  │ │ - Web Search │ │              │
        │ Document loading │ │   (Tavily)   │ │ - Correctness│
        │ Chunking         │ │ - Calculation│ │ - Relevance  │
        │ Embedding        │ │   (Python)   │ │ - Clarity    │
        │ Retrieval        │ │ - Context    │ │ - Framework  │
        │ (Similarity)     │ │   Builder    │ │   Quality    │
        └──────────────────┘ └──────────────┘ └──────────────┘
                    │
                    ▼
        ┌──────────────────────────────────────┐
        │    KNOWLEDGE BASE                    │
        │  (Were-Talking-Millions.pdf chunks)  │
        │  - Embeddings: OpenAI text-embed-3-small
        │  - Stored in Qdrant (in-memory for MVP)
        └──────────────────────────────────────┘
```

---

## Technology Choices & Justification

### Core AI Components

**LLM: Claude 3.5 Sonnet (via Anthropic API)**
- *Why:* Strongest reasoning capability for financial decision frameworks; excels at multi-step thinking and structured output (needed for decision trees, not just fluent text generation). Better than GPT-4o for the "explain your reasoning" requirement.

**Agent Orchestration: LangChain v0.2 (Python)**
- *Why:* Mature, production-proven framework for RAG + tool-use patterns. Handles agent loops, tool output parsing, and context management. Strong community for financial use cases. Already set up in your notebook template.

**Embedding Model: OpenAI text-embedding-3-small**
- *Why:* Smaller (faster inference), cheaper than -large, sufficient for domain-specific financial documents. Compatible with Qdrant. Proven track record on financial Q&A tasks.

**Vector Database: Qdrant**
- *Why:* In-memory for MVP (no DevOps complexity), can scale to cloud deployment. Fast similarity search. Better UX than Pinecone for prototyping (free tier considerations). Clean API. Python-native.

---

### Backend & Infrastructure

**Backend Framework: FastAPI (Python)**
- *Why:* Lightweight, async-capable for WebSocket real-time chat. Fast startup. Perfect for single-developer deployment. Minimal boilerplate compared to Django.

**Memory/Session Storage: Upstash Redis**
- *Why:* Serverless Redis (no server management). Free tier sufficient for MVP. Stores conversation history + user context (salary, assets, timeline, risk profile). Fast key-value lookups.

**Deployment: Vercel (Frontend) + Render (Backend)**
- *Why:* Both have generous free tiers. Vercel optimized for Next.js. Render supports FastAPI. Can scale up cheaply. Both support browser-runnable on mobile.

---

### Tools & Integrations

**Web Search Tool: Tavily API**
- *Why:* Current market conditions (interest rates, tax law changes, market performance) can change monthly. Grounds recommendations in real data. Free tier for prototyping.

**Calculation Engine: Python (sympy, numpy)**
- *Why:* Financial calculations (compound interest, tax bracket jumps, withdrawal strategies) need precision. Lightweight; no external API needed.

**Context Builder: Custom Python**
- *Why:* Formats user's financial situation into a readable summary for LLM context window. Handles: income, assets, timeline, risk tolerance, major goals, constraints.

---

### Frontend

**UI Framework: Next.js 14 + React**
- *Why:* Full-stack JavaScript/TypeScript. Server-side rendering for fast initial load. Works seamlessly on mobile/desktop browsers. Deployable on Vercel with zero config.

**Chat UI Library: Recharts (for visualizations) + shadcn/ui (components)**
- *Why:* Lightweight, accessible components. Recharts handles savings/allocation visualizations without heavy dependencies.

---

### Monitoring & Evaluation

**Logging: Python logging + Vercel logs**
- *Why:* Built-in; free. Captures LLM outputs, tool calls, user context for post-mortem review.

**Evaluation Framework: LLM-as-Judge (Claude)**
- *Why:* Evaluate agent responses on: correctness (grounded in PDF), relevance (addresses user's situation), clarity (understandable to non-finance), framework quality (teaches decision-making, not just answers).

**Metrics to Track:**
- Retrieval relevance (did RAG pull the right chunks?)
- Response coherence (is the recommendation integrated + contextualized?)
- User satisfaction (proxy: did they follow up with another question?)
- Advisor review (spot-check outputs against financial advisor standards)

---

## Agent Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      USER INITIATES CONVERSATION                         │
│  Input: "I have $250k bonus, $500k saved, $200k student debt,          │
│         retire at 60. What should I do with the bonus?"                 │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   SYSTEM: EXTRACT/RECALL USER CONTEXT                    │
│  - Retrieve session memory: prior answers, situation profile             │
│  - Build context summary: "Income: $250k, Savings: $500k, ..."          │
│  - Identify missing info: Risk tolerance? Major expenses coming?        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│               AGENT: DECIDE WHAT INFORMATION IS NEEDED                   │
│                                                                           │
│  Decision Point 1: Do I have enough context?                            │
│  ├─ NO  → Ask clarifying questions (risk tolerance, timeline)           │
│  └─ YES → Proceed to analysis                                           │
│                                                                           │
│  Decision Point 2: What framework applies?                              │
│  ├─ Windfall management (bonus)                                         │
│  ├─ Debt vs. invest decision (student loans)                            │
│  ├─ Tax optimization (income level, bonus timing)                       │
│  └─ Sequence of returns risk (approaching retirement)                   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    AGENT: RETRIEVE RELEVANT KNOWLEDGE                    │
│                                                                           │
│  RAG Retrieval Queries:                                                 │
│  ├─ "How should high earners manage bonus windfall?"                    │
│  ├─ "Decision framework: pay debt vs. invest"                           │
│  ├─ "Tax planning for $250k income and bonus"                           │
│  ├─ "Asset allocation approaching retirement"                           │
│  └─ "Behavioral finance: avoid bonus-spending mistakes"                 │
│                                                                           │
│  Qdrant search returns: Ranked chunks from Were-Talking-Millions.pdf    │
│  along with similarity scores (keep top 5-8 chunks)                     │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     AGENT: CALL EXTERNAL TOOLS (if needed)              │
│                                                                           │
│  Tool 1: Web Search (Tavily)                                            │
│  └─ Query: "Current savings account APY 2024" (for emergency fund calc)│
│                                                                           │
│  Tool 2: Tax Calculator (Python)                                        │
│  ├─ Input: $250k salary + $150k bonus → tax bracket impact             │
│  ├─ Calculate: Marginal tax rate, effective rate                        │
│  └─ Output: "Bonus is taxed at 35% federal + state"                    │
│                                                                           │
│  Tool 3: Financial Calculator (Python)                                  │
│  ├─ Debt payoff timeline for $200k student loans                        │
│  ├─ Opportunity cost of investing $150k instead                         │
│  └─ Output: "At 5% return, investing yields $X more by age 60"         │
│                                                                           │
│  Tool 4: Context Builder                                                │
│  └─ Format: Summarize user situation for LLM input (max tokens)        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              AGENT: SYNTHESIZE & BUILD DECISION FRAMEWORK                │
│                                                                           │
│  LLM processes:                                                          │
│  ├─ Retrieved knowledge (RAG chunks)                                    │
│  ├─ Tool outputs (tax impact, opportunity cost, market rates)           │
│  ├─ User context (age, timeline, risk tolerance, goals)                 │
│  └─ Instruction: "Build a decision framework, not a yes/no answer"     │
│                                                                           │
│  Output Structure:                                                       │
│  ├─ Summary of user's situation                                         │
│  ├─ Key decision criteria (debt urgency, tax efficiency, sequence risk) │
│  ├─ Decision framework: "If X, then Y" rules                            │
│  ├─ Pros/cons of each path (allocate all to debt vs. split vs. invest) │
│  ├─ Recommendation with reasoning                                       │
│  ├─ Behavioral warnings (sunk cost fallacy, loss aversion bias)        │
│  └─ Sources: [Source 1] Were-Talking-Millions.pdf, page 23             │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      SYSTEM: UPDATE MEMORY & STORE                       │
│                                                                           │
│  Save to Upstash Redis:                                                 │
│  ├─ Conversation turn (question + agent response)                       │
│  ├─ User context updates (if new info disclosed)                        │
│  ├─ Tool call results (for audit trail)                                 │
│  └─ Timestamp + session ID                                              │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                     UI: RENDER RESPONSE TO USER                          │
│                                                                           │
│  Display:                                                                │
│  ├─ Agent's response (formatted markdown)                               │
│  ├─ Decision framework (visual tree or bullet list)                     │
│  ├─ Sources cited (clickable to jump to relevant PDF section)           │
│  ├─ Follow-up suggestions ("Ask me about: tax-loss harvesting")        │
│  ├─ Context sidebar (shows what system knows about user)                │
│  └─ "Update my info" button (edit risk tolerance, goals, etc.)         │
│                                                                           │
│  User can:                                                               │
│  ├─ Ask follow-up question (continues conversation)                     │
│  ├─ Challenge recommendation ("What if market crashes 30%?")            │
│  ├─ Export conversation as PDF                                          │
│  └─ Schedule follow-up (reminder to review in 6 months)                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Workflow Explanation (1-2 paragraphs)

**How the Agent Solves the User's Problem:**

The Financial Advisor AI operates as a multi-turn conversational agent that bridges the gap between the user's financial situation and actionable decision frameworks grounded in curated knowledge. When a user asks a question like "What should I do with my $150k bonus?", the agent first retrieves the user's financial context from memory (salary, savings, debt, timeline, risk tolerance, previous decisions). If context is incomplete, it asks targeted clarifying questions rather than making generic assumptions. Once context is established, the agent uses agentic RAG to retrieve relevant guidance from the Were-Talking-Millions.pdf knowledge base—pulling chunks about windfall management, tax optimization, debt prioritization, and behavioral pitfalls.

The agent then orchestrates tool calls as needed: it fetches current market rates (savings APY, mortgage rates), calculates precise tax impacts of the bonus, models opportunity costs of different allocation choices, and structures this data into a coherent decision framework. Rather than recommending "invest the $150k in index funds," the agent teaches the user how to think: "If your emergency fund is inadequate, prioritize that first; if your student loan interest rate is >5%, consider paying that down; if you're in the 35% tax bracket, tax-loss harvesting in your taxable account saves $X annually." The response is grounded in the PDF sources, references specific financial principles, and acknowledges behavioral risks (overconfidence, anchoring, loss aversion). Throughout the conversation, the agent stores context and prior decisions in memory, so follow-up questions ("What about HSA tax advantages?") build on prior reasoning instead of restarting analysis. The final output—a clear decision framework, not a prescription—empowers the user to execute with conviction and adapt as their situation evolves.

---

## Memory Architecture

**What Gets Stored in Redis:**
1. **User Profile** (once established):
   - Annual income, bonus structure
   - Current assets (checking, savings, investments, real estate)
   - Liabilities (mortgage, student loans, credit cards)
   - Major upcoming expenses (home purchase, car, kids' education)
   - Timeline (years to retirement, major life events)
   - Risk tolerance (questionnaire response, inferred from prior decisions)
   - Goals (wealth target, withdrawal rate, legacy planning, etc.)

2. **Conversation History**:
   - Each turn: user question, agent response, tool calls made, sources retrieved
   - Enables context-aware follow-ups ("As we discussed earlier...")
   - Prevents re-asking same clarifying questions

3. **Decision Log**:
   - Major financial decisions made in conversation
   - Reasoning behind each decision
   - Allows agent to avoid contradicting prior advice

4. **Session Metadata**:
   - Session ID, creation date, last accessed
   - Browser/device info (for responsive UX decisions)

---

## Data Flow Example

**User Input:**
> "I'm 35, earn $180k, have $300k in savings, $100k student debt at 5.5%, and want to buy a house in 3 years. What should I prioritize?"

**System Flow:**
1. Extract user context from memory (or prompt to fill out profile if new user)
2. RAG queries: "debt payoff vs. investing," "house savings vs. debt," "3-year investment timeline," "behavioral anchoring debt"
3. Tool calls:
   - Tax calculator: Marginal rate at $180k income
   - Mortgage calculator: House affordability at $300k savings
   - Debt payoff model: Timeline to clear $100k at different payment rates
4. Agent synthesizes: "Here's your decision framework: (1) Emergency fund first; (2) Then house down payment (3-year horizon = lower risk); (3) Remaining cash to student debt while investing long-term savings"
5. Store session: User context updated, decision logged
6. UI renders framework with follow-ups

---

## Success Criteria for Task 2

✅ Solution is clear, actionable, and grounded in financial advisor methodology  
✅ Architecture is deployable in < 2 weeks (using existing frameworks, not building from scratch)  
✅ Memory system enables personalized, context-aware recommendations  
✅ Tool integration (Tavily search, tax calculator, context builder) makes advice timely and accurate  
✅ RAG pipeline ensures recommendations are grounded in Were-Talking-Millions.pdf  
✅ Frontend is browser-runnable on mobile and desktop without special setup

# Task 3: Data Strategy & Chunking

## Overview

The Financial Advisor AI relies on two data sources:
1. **Static Knowledge Base** — Were-Talking-Millions.pdf (principles, frameworks, strategies)
2. **Dynamic Real-Time Data** — Tavily API (current market conditions, rates, tax law changes)

This section defines how we chunk the PDF, why we made those choices, and how these data sources work together to answer financial questions.

---

## Part 1: Chunking Strategy for Were-Talking-Millions.pdf

### Chunk Size: 800-1200 characters (~200-300 words)

**Why this size?**

- **Too small (<400 chars):** Strips context. A sentence about "diversification" loses the surrounding reasoning. Embeddings get noisier. More overhead.
- **Too large (>1500 chars):** Mixed topics within one chunk (e.g., one chunk covers both "emergency fund sizing" AND "401k withdrawal rules"). Retrieval becomes less precise—you retrieve a chunk that's 50% relevant.
- **Sweet spot (800-1200):** Captures a complete thought or decision rule with local context. Example:
  ```
  "Emergency fund sizing depends on your stability. If you have a stable W2 job, 3-6 months of expenses is appropriate. If you're self-employed or in consulting, 6-12 months protects against feast-famine cycles. Store it in a high-yield savings account earning 4-5%, not in the stock market. This fund is for security, not returns."
  ```
  This chunk stands alone, is focused, and contains actionable guidance.

### Chunk Overlap: 150 characters (~2-3 sentences)

**Why overlap?**

- **Without overlap:** A decision rule split across chunk boundaries gets orphaned. "Here's why diversification matters" (end of chunk 1) → "Diversification means..." (start of chunk 2). Reader must find both.
- **With overlap:** The key sentence "Diversification means spreading investments across asset classes..." appears at the **end of chunk 1** AND **start of chunk 2**. When either chunk is retrieved, the context is whole.
- **150 character overlap:** ~2-3 sentences. Enough to bridge ideas without redundant storage.

### Chunking Strategy: Recursive Character Splitter with Boundaries

**Process:**
1. **Load PDF** → Extract text pages
2. **Split recursively** → Try splitting on:
   - Paragraph breaks (`\n\n`)
   - Sentence boundaries (`\n` or `. `)
   - Then character-level if needed
3. **Add metadata** to each chunk:
   - Source file: "Were-Talking-Millions.pdf"
   - Page number
   - Section/topic (inferred from PDF outline if available, or manually tagged)
   - Chunk index (for reconstruction if needed)

**Pseudocode:**
```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,              # 800-1200 range, using 1000 as default
    chunk_overlap=150,             # 2-3 sentence overlap
    separators=[
        "\n\n",                    # Paragraph breaks (highest priority)
        "\n",                       # Line breaks
        "(?<=[.!?]) +",            # Sentence boundaries
        " ",                        # Word boundaries
        ""                          # Character-level fallback
    ],
    add_start_index=True,          # Track position in original document
)

chunks = splitter.split_documents(pages)
# Add metadata
for chunk in chunks:
    chunk.metadata["source"] = "Were-Talking-Millions.pdf"
    chunk.metadata["document_type"] = "financial_guidance"
    chunk.metadata["section"] = infer_section(chunk.page_content)
```

---

## Part 2: Data Sources & Integration

### Data Source 1: Were-Talking-Millions.pdf (Static Knowledge Base)

**What's in the PDF?**

Based on the title and context, this PDF likely covers:
- Wealth building principles and fundamentals
- Investment strategies (asset allocation, diversification, rebalancing)
- Tax-efficient investing (401k, Roth IRA, backdoor strategies)
- Debt management (student loans, mortgages, high-interest debt)
- Behavioral finance (emotional decision-making, cognitive biases)
- Retirement planning and withdrawal strategies
- Emergency fund sizing and cash management
- Real estate investing / home buying considerations
- Insurance (life, disability, umbrella coverage)
- Behavioral anchoring and wealth psychology

**Role in the System:**

- **Primary knowledge source** for financial frameworks and principles
- **Grounding for RAG** — All recommendations cite chunks from this PDF
- **Covers 80% of advisor questions** — If a user asks "How should I think about asset allocation?", the answer comes from this PDF

**Chunk Examples & Questions:**

| Question | Chunk Theme | Expected Chunk Size |
|----------|-------------|---------------------|
| "What's a realistic emergency fund?" | Emergency fund sizing rule | ~1000 chars (clear rule + exceptions) |
| "Should I pay off debt or invest?" | Decision framework for debt vs. investing | ~1200 chars (trade-offs, examples) |
| "What does diversification mean?" | Diversification definition + reasoning | ~900 chars (concept + examples) |
| "How do I think about tax optimization?" | Tax-efficient investing principles | ~1100 chars (brackets, strategies, tools) |

---

### Data Source 2: Tavily API (Real-Time Market Data)

**What does Tavily provide?**

- Current interest rates (savings accounts, mortgages, loan rates)
- Recent news on market performance, economic indicators
- Current tax law changes or IRS guidance updates
- Investment fund performance data (YTD returns, expense ratios)
- Real estate market data (home prices, mortgage rates by region)

**Role in the System:**

- **Supplements static knowledge** with current data
- **Answers time-sensitive questions** ("What's the current 10-year Treasury yield?" or "Have tax laws changed for 2024?")
- **Prevents outdated advice** (e.g., "Savings accounts earn 0.5%" → outdated if they now earn 4.5%)
- **Covers 15-20% of advisor questions** — When users ask about current rates, trends, or recent tax law

**API Integration (Pseudocode):**

```python
from tavily import TavilyClient

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

def search_current_rates(query: str) -> dict:
    """Search Tavily for current financial data."""
    results = tavily.search(
        query=query,
        topic="financial",
        max_results=3,
        include_sources=True
    )
    # Extract relevant data (rates, prices, dates)
    return results

# Example usage:
rates = search_current_rates("current savings account APY rates 2024")
# Returns: [{"title": "Best High-Yield Savings Accounts", "content": "...", "url": "..."}]
```

**Questions Tavily Helps Answer:**

- "What's the current 10-year Treasury yield?"
- "Have 401k contribution limits changed for 2024?"
- "What's the average mortgage rate today?"
- "Which index funds have the lowest expense ratios?"
- "Has the Federal Reserve raised rates recently?"

---

## Part 3: How Data Sources Interact

### Interaction Model: Hybrid RAG + Search

**Scenario 1: User Asks a Principle Question**

```
User: "I have $100k and unsure whether to invest or keep it safe. What should I do?"

Flow:
1. Agent recognizes: "Decision framework" question
2. RAG Query: "How to decide between investing and keeping cash safe"
3. Qdrant retrieves: Chunks on risk tolerance, time horizon, emergency funds
4. Tavily: NOT needed (principle, not rate-dependent)
5. Agent synthesizes: Uses PDF chunks to build decision framework
6. Output: "Here's how to think about it: (1) Do you have 6 months emergency fund? (2) What's your timeline? (3) How would you feel if you lost 30%?"
```

**Scenario 2: User Asks a Current-Rate Question**

```
User: "Should I build an emergency fund in a savings account or money market fund? What's the difference in returns?"

Flow:
1. Agent recognizes: "Current rate comparison" question
2. RAG Query: "Emergency fund account types savings vs money market"
3. Qdrant retrieves: Chunks on emergency fund purpose, account types
4. Tavily Query: "Current savings account APY vs money market fund rates 2024"
5. Tavily returns: "High-yield savings 4.8%, Money market funds 5.2%"
6. Agent synthesizes: Combines PDF explanation (why both work) + current rates (difference is 0.4%)
7. Output: "Both are safe. Savings account is simpler; money market yields slightly more. Current difference is 0.4%. For emergency funds, either works. Choose savings for simplicity or money market if you want max yield."
```

**Scenario 3: Complex Decision (Combines Both)**

```
User: "I just got a $150k bonus. I'm in a 35% tax bracket. Should I max my Roth backdoor and invest the rest, or invest everything in taxable?"

Flow:
1. Agent recognizes: "Tax optimization + decision framework"
2. RAG Query: "Backdoor Roth strategy tax efficiency 35% bracket"
3. Qdrant retrieves: Chunks on Roth conversion, tax brackets, backdoor mechanics
4. Tavily Query: "2024 Roth IRA contribution limit income phase-out 35% tax bracket"
5. Tavily returns: "2024 limit $7k, phase-out starts at $146k (single) / $230k (married)"
6. Tool Call: Tax calculator
   Input: $150k bonus, $35% bracket
   Output: "After taxes: $97.5k net bonus. Backdoor option: Contribute $7k (pre-tax equivalent ~$10.8k). Remainder: $90.5k to taxable."
7. Agent synthesizes: PDF framework + current limits + tax math
8. Output: Decision tree with math, sources cited, behavioral warnings
```

---

## Part 4: Chunking Validation & Examples

### Test Chunks from Were-Talking-Millions.pdf

Before we code, let's define what "good chunks" look like:

**Good Chunk ✅ (Focused, Actionable):**
```
Title: "Asset Allocation as Risk Management"
Content: "Asset allocation—the split between stocks, bonds, and cash—is the primary driver of your portfolio's risk and return. A simple rule: subtract your age from 110 to get your stock percentage. A 30-year-old: 80% stocks, 20% bonds/cash. A 60-year-old: 50% stocks, 50% bonds/cash. This rule assumes you're working until 65 and can tolerate short-term volatility. If you're nearing retirement or have major expenses in 3 years, shift toward more bonds. If you have stable income and decades ahead, shift toward more stocks. The key insight: allocation is about time horizon + income stability, not just age."

Metadata:
- source: "Were-Talking-Millions.pdf"
- page: 42
- section: "Investment Strategy"
- topic: "Asset Allocation"
- start_index: 12450
```

Why this is good:
- ✅ Self-contained (understandable alone)
- ✅ Includes decision rule (110 - age)
- ✅ Includes reasoning ("why this matters")
- ✅ Includes caveats (not for everyone)
- ✅ Actionable (user can apply it)

**Bad Chunk ❌ (Fragmented, Lost Context):**
```
"...and cash—is the primary driver of your portfolio's risk and return. A simple rule: subtract your age from 110 to get your stock percentage. A 30-year-old: 80% stocks, 20% bonds/cash..."

Why this is bad:
- ❌ Missing opening: "What is asset allocation?"
- ❌ No reasoning: Why does time horizon matter?
- ❌ Orphaned rule: "subtract age from 110" has no explanation
- ❌ No caveats: When does this rule NOT apply?
```

---

## Part 5: Data Interaction Workflow

### Agent Decision Logic for Data Source Selection

```
IF question is about:
├─ "What is [concept]?" (e.g., "What is diversification?")
│  └─ Use RAG only (static knowledge)
├─ "How should I think about [decision]?" (e.g., "How should I prioritize debt vs investing?")
│  └─ Use RAG + optionally Tavily for current interest rates context
├─ "What's the current [metric]?" (e.g., "What's the current mortgage rate?")
│  └─ Use Tavily + RAG for explanation
├─ "Has [law/rule] changed?" (e.g., "Are 401k limits higher for 2024?")
│  └─ Use Tavily for update + RAG for explanation
└─ "Should I [decision] given my [situation]?" (e.g., "Should I pay debt or invest given 5% rates?")
   └─ Use RAG (framework) + Tavily (current rates) + Calculator (math)
```

---

## Part 6: Metadata Strategy

**Each chunk will include:**

```json
{
  "page_content": "Asset allocation is the split between stocks, bonds...",
  "metadata": {
    "source": "Were-Talking-Millions.pdf",
    "page_number": 42,
    "section": "Investment Strategy",
    "topic": "Asset Allocation",
    "subtopic": "Stock/Bond Split Rules",
    "keywords": ["allocation", "stocks", "bonds", "age-based", "risk"],
    "chunk_index": 87,
    "start_index": 12450,
    "chunk_type": "definition",  // "definition", "decision_framework", "warning", "calculation"
    "applicability": ["all_ages", "employed", "moderate_risk_tolerance"],
    "limitations": ["approaching_retirement", "self_employed", "concentrated_assets"],
    "related_topics": ["time_horizon", "risk_tolerance", "rebalancing"]
  }
}
```

**Why detailed metadata?**

- Enables filtering (show only chunks for "employed" people, not self-employed)
- Improves semantic search (tags like "decision_framework" vs "definition")
- Helps agent reason about applicability ("This advice assumes you're employed")
- Surfaces related topics for follow-up suggestions

---

## Part 7: Chunking Implementation Plan

### Step 1: Load & Preview PDF
```python
from langchain_community.document_loaders import PyPDFLoader

loader = PyPDFLoader("Were-Talking-Millions.pdf")
pages = loader.load()
print(f"Loaded {len(pages)} pages")
print(f"Sample page:\n{pages[0].page_content[:1000]}")
```

### Step 2: Apply Chunking Strategy
```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
    separators=["\n\n", "\n", "(?<=[.!?]) +", " ", ""],
    add_start_index=True,
)

chunks = splitter.split_documents(pages)
print(f"Created {len(chunks)} chunks")
```

### Step 3: Add Metadata (Manual + Automated)
```python
# Option A: Manual tagging (for important sections)
section_mapping = {
    "pages_1_10": "Introduction & Fundamentals",
    "pages_11_30": "Investment Strategy",
    "pages_31_50": "Tax Optimization",
    "pages_51_80": "Debt & Liability Management",
    "pages_81_100": "Retirement & Withdrawal",
}

# Option B: Use LLM to infer topic (if needed)
for chunk in chunks:
    page_num = chunk.metadata.get("page", 0)
    chunk.metadata["section"] = section_mapping.get(f"pages_{page_num}", "Other")
    chunk.metadata["document_type"] = "financial_guidance"
```

### Step 4: Validate Chunks
```python
# Sample a few chunks, verify they're coherent
sample_chunks = chunks[::50]  # Every 50th chunk
for i, chunk in enumerate(sample_chunks):
    print(f"\n=== CHUNK {i} ===")
    print(chunk.page_content[:300])
    print(f"Metadata: {chunk.metadata}")
```

---

## Success Criteria for Task 3

✅ Chunking strategy defined with clear rationale (800-1200 chars, 150 overlap)  
✅ Data sources documented (Were-Talking-Millions.pdf + Tavily API)  
✅ Integration pattern clear (when to use each source)  
✅ Metadata schema defined (enables smart filtering + reasoning)  
✅ Examples of good/bad chunks provided  
✅ Implementation plan ready to code

---

## Next Steps (Task 4)

Once Task 3 is approved:
1. Load Were-Talking-Millions.pdf in the notebook
2. Apply chunking strategy
3. Build embeddings + Qdrant store
4. Test retrieval with the evaluation questions from Task 1
5. Verify chunks are coherent and relevant

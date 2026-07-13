# Financial Advisor RAG - Evaluation Baseline

- Target: `http://localhost:8000`
- Cases: **15**  |  Judge: `claude-opus-4-8`

## Aggregate metrics

| Metric | Score |
|---|---|
| Groundedness (1-5) | 3.6 |
| Relevance (1-5) | 5 |
| Framework quality (1-5, in-scope) | 5 |
| Citations (1-5) | 3.53 |
| Retrieval source-hit rate | 1.0 |
| Avg top retrieval score | 0.5 |
| Out-of-scope handled correctly | 3/3 |
| Avg latency (s) | 13.09 |

## Per-question results

| ID | Cat | Ground | Rel | Frwk | Cite | Scope | Src hit | Top | Lat(s) |
|---|---|---|---|---|---|---|---|---|---|
| alloc-horizon | general | 2 | 5 | 5 | 3 | na | Y | 0.605 | 13.16 |
| debt-vs-invest | general | 5 | 5 | 5 | 5 | na | Y | 0.495 | 13.44 |
| emergency-fund | general | 5 | 5 | 5 | 4 | na | Y | 0.427 | 10.33 |
| diversification | general | 3 | 5 | 5 | 4 | na | Y | 0.536 | 17.3 |
| market-crash-behavior | general | 4 | 5 | 5 | 4 | na | Y | 0.566 | 14.14 |
| bonus-deploy | general | 4 | 5 | 5 | 4 | na | Y | 0.439 | 18.9 |
| stock-picking-strategy | general | 2 | 5 | 5 | 3 | na | Y | 0.583 | 15.53 |
| tax-marginal-150k | tax | 3 | 5 | 5 | 3 | na | Y | 0.599 | 11.86 |
| tax-effective-vs-marginal | tax | 3 | 5 | 5 | 4 | na | Y | 0.546 | 13.97 |
| tax-progressive-90k | tax | 5 | 5 | 5 | 4 | na | Y | 0.57 | 13.02 |
| tax-top-bracket | tax | 5 | 5 | 5 | 4 | na | Y | 0.601 | 10.66 |
| roth-vs-taxable | combo | 2 | 5 | 5 | 2 | na | Y | 0.581 | 17.12 |
| oos-stock-pick | out_of_scope | 3 | 5 | 5 | 4 | correct | Y | 0.477 | 12.96 |
| oos-crypto | out_of_scope | 3 | 5 | 5 | 4 | correct | Y | 0.36 | 10.58 |
| oos-unrelated | out_of_scope | 5 | 5 | 3 | 1 | correct | Y | 0.174 | 3.41 |

## Judge rationales

- **alloc-horizon**: The answer teaches an excellent decision framework directly relevant to the question, but it fabricates specific quotes and numbers not present in the retrieved sources — the '25 years from retirement' quote, the Vanguard 2065 fund at 11%, and the 'before they are about 40' language are not supported by the provided snippets, which only mention glide paths, a '2030 fund,' and small-cap value. Citations are formatted well but attach to unsupported claims, undermining groundedness.
- **debt-vs-invest**: The answer honestly acknowledges the sources don't directly address the tradeoff, then builds a solid decision framework (guaranteed vs expected return, time horizon, foundation, psychology) while only citing sources for claims they actually support. No hallucinated numbers and appropriate redirect to a professional.
- **emergency-fund**: The assistant honestly flagged that the sources don't cover emergency funds, then provided a sound general framework (3-6 months, liquidity/safety vehicles) clearly labeled as external knowledge to verify, avoiding hallucinated citations. Citations are used appropriately for the tangential source claims, though the tax connection is a slight stretch.
- **diversification**: The answer teaches a strong decision framework with appropriate citations, but several specifics are hallucinated or embellished beyond the sources: the '40-year' comparison in Source 4 compares three diversifying stock types, not S&P 500 vs. others; the 'nine other pools,' '11th bond fund,' and detailed 10-fund structure are not supported by the retrieved snippets, which don't enumerate these. Relevance and framework quality are excellent.
- **market-crash-behavior**: The answer builds a strong behavioral framework well-grounded in the V-shaped market timing narrative from the sources, with appropriate citations. The '$1 million' figure is somewhat inferred from the book's title/theme rather than clearly stated in the retrieved excerpts, a minor groundedness concern, but overall the response is accurate and directly useful.
- **bonus-deploy**: The answer delivers a thorough, well-sequenced decision framework covering debt, emergency fund, tax-advantaged accounts, and investing, with a behavioral note. It cites sources appropriately, though it extrapolates figures (e.g., '$1.2 million' extra, '20-30% boost') beyond what the terse snippets clearly support and stretches Sources 3-4 somewhat; it does transparently flag gaps in its knowledge base.
- **stock-picking-strategy**: The answer teaches an excellent decision framework and directly addresses the question, but it fabricates numerous specific figures not supported by the fragmentary sources — the $10,000-to-$3M Microsoft example, '16 years to break even,' the '4% of companies / 96% like Treasury bills / 1-in-25' study, and the S&P 500 details are not present in the retrieved snippets, which are truncated. Citations are attached but many point to sources that don't actually contain the claimed data.
- **tax-marginal-150k**: Correctly identifies the 24% bracket and range, and teaches marginal vs effective rate excellently. However, the 24% and 12% bracket boundaries aren't actually in the retrieved sources (which are garbled/missing), so the tax breakdown table numbers are partly unsupported/inferred, and citing [Source 1] for the 24% claim is inaccurate since that source doesn't contain the 24% row.
- **tax-effective-vs-marginal**: The concept explanation and use of cited brackets (10%, 32%, 35%) is well-grounded, but the example uses 12% ($48,475), 22%, and 24% bracket thresholds that are not present in the retrieved sources (which were truncated), so those figures are partly unsupported/hallucinated. Otherwise highly relevant, teaches a strong marginal-vs-effective framework, and cites sources appropriately.
- **tax-progressive-90k**: Math is correct and matches the exact 2025 thresholds in the sources (10% to 11925, 12% to 48475, 22% to 103350), with accurate bracket sums and effective rate. The 24% at 103351 boundary is a minor inference not fully in retrieved sources but consistent. Strong marginal-vs-effective framework; citations present though could be more granular.
- **tax-top-bracket**: Correctly states $626,351 threshold from the sources and cites them; the intermediate brackets (22%, 24%) shown in the table aren't in the retrieved sources but the core answer and top-bracket claim are well grounded, and it teaches a strong marginal vs. effective framework.
- **roth-vs-taxable**: The framework and relevance are excellent, but the answer fabricates quotes attributed to sources—the retrieved snippets never contain lines like 'put as much money as you can into tax-advantaged accounts' or 'tax rates will be much higher in 40 years,' so multiple [Source] citations are unsupported/hallucinated, dragging down groundedness and citation accuracy.
- **oos-stock-pick**: Correctly declines to pick a stock and teaches a robust diversification/value framework with citations. However, several specific figures (Microsoft $10k to $3M, S&P P/E 21.9, 11.1% vs 9.9% returns, $50B large-cap avg, target date fund detail) are not clearly supported by the truncated retrieved snippets, suggesting some fabricated or unverifiable numbers.
- **oos-crypto**: Appropriately declined the speculative prediction and redirected to a strong decision framework with citations. However, the '~4%' figure claimed as from Source 1 is not actually supported by the retrieved text (which mentions 10% annual growth, not the 4% concentration stat), a minor hallucination that lowers groundedness.
- **oos-unrelated**: The answer correctly declines the out-of-scope weather question and redirects to financial topics. No citations needed since it appropriately refused, and it doesn't hallucinate any facts.

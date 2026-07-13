# Financial Advisor RAG - Evaluation Baseline

- Target: `http://localhost:8000`
- Cases: **15**  |  Judge: `claude-opus-4-8`

## Aggregate metrics

| Metric | Score |
|---|---|
| Groundedness (1-5) | 3.47 |
| Relevance (1-5) | 4.73 |
| Framework quality (1-5, in-scope) | 4.75 |
| Citations (1-5) | 3.8 |
| Retrieval source-hit rate | 1.0 |
| Avg top retrieval score | 0.48 |
| Out-of-scope handled correctly | 3/3 |
| Avg latency (s) | 14.06 |

## Per-question results

| ID | Cat | Ground | Rel | Frwk | Cite | Scope | Src hit | Top | Lat(s) |
|---|---|---|---|---|---|---|---|---|---|
| alloc-horizon | general | 2 | 5 | 5 | 4 | na | Y | 0.594 | 15.54 |
| debt-vs-invest | general | 4 | 5 | 5 | 4 | na | Y | 0.407 | 12.88 |
| emergency-fund | general | 4 | 4 | 5 | 4 | na | Y | 0.411 | 11.1 |
| diversification | general | 2 | 5 | 5 | 3 | na | Y | 0.536 | 17.95 |
| market-crash-behavior | general | 3 | 5 | 5 | 4 | na | Y | 0.558 | 15.46 |
| bonus-deploy | general | 2 | 3 | 3 | 2 | na | Y | 0.395 | 17.41 |
| stock-picking-strategy | general | 3 | 5 | 5 | 4 | na | Y | 0.539 | 16.23 |
| tax-marginal-150k | tax | 5 | 5 | 5 | 4 | na | Y | 0.588 | 13.82 |
| tax-effective-vs-marginal | tax | 3 | 5 | 5 | 3 | na | Y | 0.546 | 13.78 |
| tax-progressive-90k | tax | 5 | 5 | 5 | 4 | na | Y | 0.555 | 12.67 |
| tax-top-bracket | tax | 5 | 5 | 5 | 5 | na | Y | 0.589 | 10.25 |
| roth-vs-taxable | combo | 2 | 4 | 4 | 2 | na | Y | 0.581 | 20.49 |
| oos-stock-pick | out_of_scope | 3 | 5 | 5 | 4 | correct | Y | 0.466 | 15.03 |
| oos-crypto | out_of_scope | 4 | 5 | 5 | 5 | correct | Y | 0.345 | 15.22 |
| oos-unrelated | out_of_scope | 5 | 5 | 5 | 5 | correct | Y | 0.128 | 3.02 |

## Judge rationales

- **alloc-horizon**: The answer teaches an excellent glide-path/risk-tolerance framework and cites sources throughout, but fabricates specifics not in the retrieved snippets: the '$761 real terms' figure, the '7% real return' math, and the claim that Source 1 says 'all-equity portfolios can be suitable in your 20s and 30s' are not supported by the truncated sources, which cost it on groundedness.
- **debt-vs-invest**: The answer transparently acknowledges the sources don't directly cover mortgage payoff, then builds a solid rate-vs-return-plus-psychology framework. Cited figures are plausibly drawn from the compound-return sources but the exact dollar amounts aren't fully verifiable from the snippets provided, slightly lowering groundedness.
- **emergency-fund**: The assistant honestly acknowledges the sources don't cover emergency funds and avoids inventing specific month figures, while adapting the book's gap/risk-matching logic into a solid decision framework. Some analogies to the sources are a stretch but citations are used and no facts are fabricated; relevance is slightly limited since it can't give the expected months-of-expenses guidance from its base.
- **diversification**: The answer teaches an excellent decision framework and is highly relevant, but it fabricates numerous specifics not present in the retrieved sources: the '16 years to break even,' the Microsoft example (Source 3 only mentions losing more than half in a few months), the 'Nifty 50' of 1972, the S&P 500 core, 'nine other asset classes,' the '10-11 funds,' and 'Two Funds for Life.' Source 1 only vaguely references a low-cost portfolio and owning more than one asset class, so most numeric and structural claims are hallucinated despite the citations.
- **market-crash-behavior**: The answer builds an excellent behavioral framework with clear cited claims, but it fabricates specific DALBAR figures (6.06% S&P vs 4.25% investor, 2000-2019) that the retrieved sources only allude to as a referenced article, not actual numbers—this is a hallucination risk that lowers groundedness.
- **bonus-deploy**: The expected framework (debt payoff, emergency fund, tax-advantaged accounts, then investing) is largely missing; instead the answer improvises a different framework. Several claims and specific numbers ('$1.2 million', '0.5%', 'needle/haystack', 'enough vs more than enough') are not clearly supported by the terse retrieved snippets, and quoted text like the tax warning does not appear verbatim in the sources, indicating fabrication. Citations are attached but often misrepresent what the sources actually say.
- **stock-picking-strategy**: The answer teaches an excellent decision framework with clear citations and directly addresses stock-picking. However, several specific figures are hallucinated or not supported by the retrieved sources: the '4% of stocks/1-in-25 odds' claim, the '16 years to break even' figure, the '36-year study' of investor behavior, and the 'costs dropping to zero over 40 years' detail are not present in the provided snippets, which only vaguely allude to these ideas.
- **tax-marginal-150k**: Correctly identifies the 24% bracket ($103,351-$197,300) using the retrieved 2025 brackets, and the layered tax calculation is accurate and well-grounded. Teaches marginal vs. effective rate thoroughly; citations are present though slightly imprecise (attributes the full table to Source 6 when individual bracket sources apply).
- **tax-effective-vs-marginal**: The marginal/effective explanation and framework are excellent and directly responsive, but the answer fabricates most of the bracket table—Source 1 only shows the 10% and a truncated 12% row, so all higher brackets and the example math are unsupported. The Source 2 quote about a '$600 tax break' also does not appear in the provided snippet, weakening groundedness and citation accuracy.
- **tax-progressive-90k**: The bracket math is accurate using the correct 2025 thresholds from the sources and sums to $13,034, with proper marginal/effective distinction and decision framework. Citations are present and appropriate, though the 12% bracket source (Source 6) isn't explicitly cited despite being used.
- **tax-top-bracket**: Correctly states $626,351 and up citing Source 4, and all bracket figures match the retrieved sources with accurate citations. It goes beyond a bare answer to teach marginal vs. effective rates and planning implications, appropriately noting the uncertainty from Source 3.
- **roth-vs-taxable**: The answer builds a solid Roth-vs-taxable decision framework and appropriately flags that backdoor Roth mechanics aren't in the sources, but it fabricates numerous direct quotes (e.g., 'put as much money as you can into tax-advantaged accounts,' 'you will never pay taxes,' 'much higher in 40 years,' the $1M tax-advisor question) that are not present in the terse retrieved snippets, so groundedness and citation accuracy are poor despite proper citation formatting.
- **oos-stock-pick**: Excellent refusal and redirection to a diversification framework, but several specific numbers and quotes (Microsoft $3M example, 16 years, $10,000 in 1986, '11.1% from 1928-2019', the 'biggest mistakes' quote) are not present in the retrieved snippets and appear partly fabricated or misattributed, undermining groundedness despite good citation formatting.
- **oos-crypto**: Appropriately declines the speculative prediction and redirects to evidence-based principles with a strong decision framework and consistent citations. Some specific figures (15.3%, 1-in-25, $142,500) are plausibly drawn from the book but are only partially visible in the retrieved snippets, introducing mild risk of unsupported precision.
- **oos-unrelated**: The assistant correctly declined the out-of-scope weather question, stated it lacks that info, and helpfully redirected to financial topics without fabricating anything.

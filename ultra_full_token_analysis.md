# ULTRA Full Token Analysis

Generated: 2026-06-28

## Executive Summary

- I could not recover raw `brand-outreach-worker` session transcripts from `query_build_sessions`, the WSL OpenCode `session` table, Mac `~/.opencode`, or Windows project/session-log searches, so this is the task-approved fallback analysis: DeepSeek June 2026 usage CSVs plus 20 executed ULTRA sample instructions.
- The June 27-28 ULTRA batch consumed `9,784` requests, `763.25M` input tokens, and `4.35M` output tokens for `$10.5239` total. Input was `88.4%` of spend; output was only `11.6%`.
- The stored final notes are tiny: the 20-sample average is `32.05` tokens. By contrast, the batch average was about `78,010` input tokens and `445` output tokens per request. Optimizing `execution_notes` alone attacks the wrong layer.
- The dominant cost driver is a very large fixed request payload plus repeated rereading of accumulated tool context. A realistic next-flight target is about `$0.0094/brand` instead of about `$0.0247/brand` if you shrink the fixed tool payload, summarize tool results, and cap workers at `15` turns.

## Method And Limits

### Sources used

- `~/Downloads/usage_data_2026_6/amount-2026-6.csv`
- `~/Downloads/usage_data_2026_6/cost-2026-6.csv`
- `~/armada/ultra_token_waste_analysis.md` for the existing 20-sample ULTRA instruction set
- `agents/brand-outreach-worker.yaml` for the live worker prompt design

### Transcript retrieval attempts

- `custodian_query_build_sessions` for `fba-command-center` on 2026-06-27 through 2026-06-28 with `brand-outreach-worker` searches: no worker sessions returned
- Global OpenCode session DB search: only `build`, `reconciler`, and `armada-foreman` sessions surfaced for that window
- Mac filesystem search under `~/.opencode` and `~/armada`: artifacts present, no raw worker transcript logs
- Windows repo and user-profile searches for `.opencode*`, `.jsonl`, `.log`, and worker strings: no raw worker logs found
- WSL OpenCode DB and adjacent storage inspection: indexed sessions existed, but no recoverable raw `brand-outreach-worker` transcript set surfaced

### Important limitation

- Because turn-by-turn worker transcripts were not retrievable, all per-session turn curves, tool frequencies, and waste rates below are modeled from the exact DeepSeek token ledger plus the worker prompt/tool design, not directly measured from raw session transcripts.

## Full Cost Baseline

### June 2026 monthly DeepSeek totals

| Bucket | Tokens | Cost |
| --- | ---: | ---: |
| Input cache miss | `74,402,592` | `$10.4164` |
| Input cache hit | `1,102,175,872` | `$3.0861` |
| Output | `7,228,351` | `$2.0239` |
| Total | `1,183,806,815` | `$15.5264` |

### Why the prior framing understated input cost

- The task brief's `"$10.42 input vs $2.02 output"` matches only **input cache misses** vs output.
- Full input cost for June is actually `'$13.50'` when cache-hit rereads are included: `$10.4164 + $3.0861 = $13.5025`.
- So full input spend is about `6.67x` output spend, not `5.16x`.

## June 27-28 ULTRA Flight Ledger

| Metric | Value |
| --- | ---: |
| Requests | `9,784` |
| Input cache miss tokens | `52,240,456` |
| Input cache hit tokens | `711,009,024` |
| Total input tokens | `763,249,480` |
| Output tokens | `4,354,965` |
| Total tokens | `767,604,445` |
| Input cache miss cost | `$7.3137` |
| Input cache hit cost | `$1.9908` |
| Output cost | `$1.2194` |
| Total cost | `$10.5239` |

### Direct flight averages

| Metric | Value |
| --- | ---: |
| Avg input tokens / request | `78,010` |
| Avg output tokens / request | `445` |
| Avg new miss tokens / request | `5,339` |
| Avg total cost / request | `$0.001076` |

## Primary Normalization

- I use the task brief's established `~23 requests/brand` as the primary normalization because it aligns with the observed June 27-28 spend and gives about `425.39` implied worker sessions for the batch (`9,784 / 23`).
- Cross-check: `EE-418` reported `584` executed ULTRA instructions in the fresh range. If I normalize by all `584`, the implied per-brand cost falls to `$0.0180`, which does **not** match the task brief's `~$0.023/brand`. I therefore treat `584` as an upper-bound contamination check, not the primary denominator.

### Primary per-session estimate

| Metric | Value |
| --- | ---: |
| Implied sessions in the batch | `425.39` |
| Requests / session | `23` |
| Input tokens / session | `1,794,229` |
| Output tokens / session | `10,238` |
| Total cost / session | `$0.02474` |

## Per-Session Table

These 20 instructions are the executed ULTRA sample already established in `ultra_token_waste_analysis.md`. Because raw transcripts were unavailable, request/input/output/cost columns use the batch-average fallback estimate above.

| AI | Brand | Final Note Tokens | Est. Requests | Est. Input Tokens | Est. Output Tokens | Est. Cost | Flag |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| `AI-81928` | Good Smile Company | `45` | `23` | `1.79M` | `10.2K` | `$0.0247` | - |
| `AI-81993` | RADA | `32` | `23` | `1.79M` | `10.2K` | `$0.0247` | - |
| `AI-82058` | Kuat | `30` | `23` | `1.79M` | `10.2K` | `$0.0247` | - |
| `AI-82253` | Astragon | `31` | `23` | `1.79M` | `10.2K` | `$0.0247` | - |
| `AI-82318` | Miracle-Gro | `34` | `23` | `1.79M` | `10.2K` | `$0.0247` | Output references Dyson |
| `AI-82383` | Denso | `33` | `23` | `1.79M` | `10.2K` | `$0.0247` | Output references HyCraft |
| `AI-82578` | Suncloud | `44` | `23` | `1.79M` | `10.2K` | `$0.0247` | - |
| `AI-82643` | Nite Ize | `41` | `23` | `1.79M` | `10.2K` | `$0.0247` | - |
| `AI-82708` | Greenlee | `36` | `23` | `1.79M` | `10.2K` | `$0.0247` | - |
| `AI-82903` | Enforcer | `37` | `23` | `1.79M` | `10.2K` | `$0.0247` | - |
| `AI-82968` | Mister Landscaper | `30` | `23` | `1.79M` | `10.2K` | `$0.0247` | - |
| `AI-82923` | Gemini Sound | `23` | `23` | `1.79M` | `10.2K` | `$0.0247` | - |
| `AI-82934` | Hilton Herbs | `27` | `23` | `1.79M` | `10.2K` | `$0.0247` | - |
| `AI-82945` | Jim Dunlop | `31` | `23` | `1.79M` | `10.2K` | `$0.0247` | - |
| `AI-82956` | LO Ink Specialties | `26` | `23` | `1.79M` | `10.2K` | `$0.0247` | - |
| `AI-82969` | MOCINNA | `32` | `23` | `1.79M` | `10.2K` | `$0.0247` | - |
| `AI-82981` | Nicole Home Collection | `26` | `23` | `1.79M` | `10.2K` | `$0.0247` | - |
| `AI-82993` | PetSport | `28` | `23` | `1.79M` | `10.2K` | `$0.0247` | - |
| `AI-83006` | REGA | `26` | `23` | `1.79M` | `10.2K` | `$0.0247` | - |
| `AI-83019` | Shell Rotella | `29` | `23` | `1.79M` | `10.2K` | `$0.0247` | - |

## What The 20-Sample Set Proves

- Average stored final note: `32.05` tokens
- Largest stored final note: `45` tokens
- Smallest stored final note: `23` tokens
- Estimated live output per worker session: `10,238` tokens

### Practical meaning

- The persisted `execution_notes` are only about `0.31%` of modeled live output (`32.05 / 10,238`).
- So `EE-434` was measuring the tail receipt, not the real session bill.
- Two of the twenty sampled outputs (`10%`) contain brand/output mismatches severe enough to flag quality drift, not just verbosity.

## Context Growth Model

Under the primary `23 requests/brand` normalization, the June 27-28 ledger implies:

- A **fixed request floor** of about `33,214` input tokens per request
- About `4,072` new tokens added per turn on average
- A visible worker prompt lower bound of only about `1,990` tokens (`7,960` chars / `4`), which means most of the fixed floor is hidden tool/function-call payload, not the human-written worker instructions

### Plot-ready average input curve

| Turn | Est. Input Tokens |
| ---: | ---: |
| 1 | `33,214` |
| 2 | `37,287` |
| 3 | `41,359` |
| 4 | `45,431` |
| 5 | `49,504` |
| 6 | `53,576` |
| 7 | `57,648` |
| 8 | `61,721` |
| 9 | `65,793` |
| 10 | `69,865` |
| 11 | `73,938` |
| 12 | `78,010` |
| 13 | `82,082` |
| 14 | `86,155` |
| 15 | `90,227` |
| 16 | `94,299` |
| 17 | `98,372` |
| 18 | `102,444` |
| 19 | `106,516` |
| 20 | `110,589` |
| 21 | `114,661` |
| 22 | `118,733` |
| 23 | `122,806` |

### Cross-check model using all 584 executed ULTRA instructions

- Avg requests / session: `16.75`
- Implied fixed request floor: `66,567` input tokens
- Implied new tokens added / turn: `1,453`

That cross-check changes the exact split, but it **does not** change the conclusion: a huge fixed prompt/tool payload is dominating cost.

## Token Budget Breakdown

Primary-model decomposition of the full June 27-28 batch (`767.60M` total tokens):

| Bucket | Tokens | Share |
| --- | ---: | ---: |
| Fixed prompt/tool payload repeated across requests | `324.97M` | `42.34%` |
| New dynamic context added during work | `38.11M` | `4.96%` |
| Reread of accumulated dynamic history/tool results | `400.17M` | `52.13%` |
| Assistant output | `4.35M` | `0.57%` |

### What this means

- The human-readable worker prompt itself is a small part of the fixed floor: about `19.47M` tokens across the batch, only `2.54%` of total tokens.
- The remaining fixed floor, about `39.80%` of total tokens, is almost certainly hidden tool schema / function-call metadata / runtime wrapper overhead.
- The biggest single bucket is not new research, but **rereading previously accumulated context**.

## Tool Call Inventory

Exact per-session tool inventories were not recoverable without raw transcripts. The worker configuration still lets us establish a hard minimum:

### Exposed tools

- `web_search`
- `browser_use`
- `call_project_tool`

### Minimum planned actions from the worker prompt

- `web_search`: `9` minimum
  - `1` Faire search
  - `5` wholesale/dealer/distributor searches
  - `3` marketplace-policy searches
- `call_project_tool`: `3` mandatory
  - `query_passing_products`
  - `search_flywheel`
  - `upsert_flywheel_artifact`
- `call_project_tool`: `+1` optional
  - `upsert_flywheel_link` if a relevant subject already exists
- `browser_use`: conditional, but likely used when search snippets were not enough

### Implication

- The architecture bakes in `12-13` tool actions **before** retries, detours, or extra browsing.
- That makes the session overhead structurally high even when the worker is behaving perfectly.

## Waste Signals

### What I can measure directly

- `2 / 20` sampled final outputs (`10%`) had brand/output mismatches (`Miracle-Gro -> Dyson`, `Denso -> HyCraft`).
- Earlier reconcile evidence from the same worker family on 2026-06-27 also showed artifact-write failures (`502` / zero-byte outputs), which are classic wasted turns.

### What I cannot measure directly

- Exact retry counts
- Exact redundant searches
- Exact failed-tool turn share
- Exact browser/page payload sizes per turn

### Conservative waste estimate

- **Hard lower bound:** `10%` session-level QA failure in the 20-sample set
- **Estimated wasted-turn band:** `8-15%`, with the caveat that this is inferred, not transcript-measured
- **Structural overhead floor:** `12-13` planned tool actions per session even without mistakes

## Top 3 Cost Drivers

### 1. Hidden fixed request payload

- Inferred at about `33.2K` tokens per request under the primary model
- Visible written worker prompt is only about `2.0K` tokens
- Conclusion: tool schemas / wrappers / function-call metadata are the real fixed-cost problem

### 2. Rereading accumulated context

- `400.17M` tokens, `52.13%` of all June 27-28 tokens
- This is the largest single bucket in the entire batch

### 3. Too many mandated round trips

- Minimum worker design already requires `9` searches plus `3-4` project-tool calls
- That pushes sessions toward the task brief's `~23` requests even before retries or extra browsing

## Optimization Recommendations

### 1. Replace the broad tool surface with narrower worker-specific tools

- Wrap `query_passing_products`, `search_flywheel`, artifact write, and optional link creation behind one or two purpose-built tools
- Biggest likely win: slash the hidden tool-schema payload
- Modeled savings if the fixed payload is cut `50%`: cost drops from `$0.0247` to about `$0.0214` per brand

### 2. Summarize tool results before they re-enter context

- Return compact fielded results from search / browsing instead of full verbose page text whenever possible
- Favor extracted facts over rich browser transcripts
- Modeled savings if dynamic context is cut `50%`: cost drops to about `$0.0172` per brand

### 3. Cap sessions at 15 turns and force an early structured verdict

- The current design tolerates too many rounds of search, browse, reflect, and write
- A hard turn cap forces the worker to stop exploring and commit to a structured output earlier
- Modeled savings at a `15`-turn cap alone: cost drops to about `$0.0168` per brand

### 4. Pre-fetch known brand context outside the worker

- Inject `query_passing_products` and existing flywheel subject matches before the worker starts
- That removes at least two project-tool calls and shortens the first-turn payload

### 5. Split research from recording

- Run a short research worker first
- Then run a tiny recorder / linker phase with narrow tools and narrow output
- This prevents the heavy research context from contaminating the artifact-write phase

## Projected Cost After Optimizations

### Single-change scenarios

| Scenario | Est. Cost / Brand |
| --- | ---: |
| Current modeled baseline | `$0.0247` |
| 50% fixed payload cut only | `$0.0214` |
| 50% dynamic-context cut only | `$0.0172` |
| 15-turn cap only | `$0.0168` |

### Combined realistic target

| Scenario | Est. Cost / Brand | Reduction |
| --- | ---: | ---: |
| 15-turn cap + 50% fixed payload cut + 50% dynamic-context cut | `$0.0094` | `-62%` |
| 12-turn cap + 50% fixed payload cut + 50% dynamic-context cut | `$0.0078` | `-69%` |

### Recommended planning number for the next flight

- Use **`$0.009-$0.012 per brand`** as the realistic next-flight target band if the worker is slimmed and turn-capped.

## Bottom Line

- The real ULTRA spend problem is **not** verbose persisted notes.
- The real problem is a heavy hidden request envelope plus repeated rereading of tool-rich context across too many turns.
- Shortening `execution_notes` barely matters.
- Slimmer tool payloads, summarized tool returns, and shorter sessions are where the actual money is.

## Appendix: Raw Sample Anchors

Because the worker transcripts were unavailable, exact per-session tool-call lists could not be reconstructed. This appendix records the 20 sample anchors actually used.

| AI | Brand | Stored Final Note Tokens | Anomaly |
| --- | --- | ---: | --- |
| `AI-81928` | Good Smile Company | `45` | - |
| `AI-81993` | RADA | `32` | - |
| `AI-82058` | Kuat | `30` | - |
| `AI-82253` | Astragon | `31` | - |
| `AI-82318` | Miracle-Gro | `34` | Output references Dyson |
| `AI-82383` | Denso | `33` | Output references HyCraft |
| `AI-82578` | Suncloud | `44` | - |
| `AI-82643` | Nite Ize | `41` | - |
| `AI-82708` | Greenlee | `36` | - |
| `AI-82903` | Enforcer | `37` | - |
| `AI-82968` | Mister Landscaper | `30` | - |
| `AI-82923` | Gemini Sound | `23` | - |
| `AI-82934` | Hilton Herbs | `27` | - |
| `AI-82945` | Jim Dunlop | `31` | - |
| `AI-82956` | LO Ink Specialties | `26` | - |
| `AI-82969` | MOCINNA | `32` | - |
| `AI-82981` | Nicole Home Collection | `26` | - |
| `AI-82993` | PetSport | `28` | - |
| `AI-83006` | REGA | `26` | - |
| `AI-83019` | Shell Rotella | `29` | - |

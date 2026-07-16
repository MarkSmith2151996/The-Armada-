# browse_page Impact Audit for v2 ULTRA Flight

## Scope

- Custodian dispatches reviewed: `D-V2-F1`, `D-V2-F3`, `D-V2-F4`, `D-V2-F5`, `D-V2-F6`
- Executed workers in scope: `608`
- Local telemetry source: `/Users/tubslamanna/armada/node.db`
- Telemetry window used for local `tool_results`: `2026-06-30 00:00:00` through `2026-07-01 23:59:59`

## Executive Summary

The v2 flight does **not** appear to have sent workers 34K-character `browse_page` payloads at scale.

What the data shows instead:

- `browse_page` was widely used in v2: `522 / 608` executed workers had at least one local browse call in telemetry.
- Successful browse responses were usually around the old visible cap, not the feared 34K payload size:
  - `3034` successful browse calls in the time window
  - average stored token estimate: `1002.1`
  - average JSON result size: `4006.3` chars
  - `2232 / 3034` successful calls explicitly say `4000 characters returned`
- Only `16` calls exceeded the expected `1250`-token baseline, across `8` AI sessions. Total excess over baseline from those outliers was only `12,147` tokens.
- The biggest local rows were `17,036` and `16,965` JSON chars, but those same rows report only `4000 characters returned`, meaning the extra size came from JSON framing / escaped Unicode / ARIA formatting, not 34K of model-visible content.
- Verdict quality does **not** show evidence that browse users were harmed relative to non-browse workers. In fact, the opposite trend appears in the real browse-usage cohort.

Bottom line: the main v2 problem was browse reliability/noise in a minority of cases, not systemic 34K token bloat. A targeted re-run of browse-failure/noise cases is justified; a blanket re-run of all 608 brands is not supported by the evidence.

## 1. Local Telemetry: browse_page Size Audit

Top local `browse_page` rows by stored JSON size:

| session_id | result_size | summary_size | created_at |
| --- | ---: | ---: | --- |
| AI-83615 | 17036 | 89 | 2026-06-30 23:33:43 |
| AI-83615 | 16965 | 75 | 2026-06-30 23:32:32 |
| AI-83934 | 9022 | 61 | 2026-07-01 06:02:50 |
| AI-83615 | 8526 | 68 | 2026-06-30 23:31:36 |
| AI-83746 | 7444 | 70 | 2026-06-30 23:39:09 |
| AI-83303 | 7335 | 59 | 2026-06-30 23:33:03 |
| AI-83290 | 7300 | 70 | 2026-06-30 22:23:01 |
| AI-83605 | 6858 | 87 | 2026-06-30 22:26:54 |

Aggregate browse telemetry for the v2 time window:

- Total browse calls logged: `3954`
- Distinct sessions with browse calls: `623`
- Average stored result size: `3107.1` chars
- Minimum stored result size: `66` chars
- Maximum stored result size: `17036` chars
- Calls with stored result size `>= 30000`: `0`
- Calls with stored result size `5000-29999`: `14`
- Calls with stored result size `< 5000`: `3940`

Successful browse calls only:

- Successful browse calls: `3034`
- Successful browse sessions: `534`
- Average token estimate: `1002.1`
- Min token estimate: `56`
- Max token estimate: `4259`
- Average stored JSON size: `4006.3` chars
- Calls whose summary explicitly says `4000 characters returned`: `2232`

Interpretation:

- The local store does **not** show worker-facing 34K browse payloads.
- The dominant behavior was a capped `~4000`-character response.
- Some stored rows are much larger than 4K because the JSON wraps escaped ARIA text, especially on non-ASCII pages, but that is not equivalent to 34K of prompt-visible content.

## 2. Custodian Execution Notes Review

Workers with `browse_page` explicitly mentioned in execution notes: `38`

Those notes are heavily biased toward problematic cases, because workers usually only mention `browse_page` when it failed, timed out, or materially affected the verdict.

Counts from those note mentions:

- Mention `browse_page`: `38`
- Mention browse failure / timeout / HTTP2 / Cloudflare / tool failure markers: `27`
- Mention `TOOL_FAILED`: `6`
- Mention `asyncio.run` failures: `7`
- Mention timeout: `13`
- Mention HTTP/2 errors: `2`
- Mention Cloudflare blocks: `5`
- Mention explicit truncation / token-limit symptoms: `3`
- Explicitly describe browse success (`completed without timeout`): `1`

Representative note patterns:

- Failure: `browse_page tool failed with asyncio.run() error`
- Failure: `browse_page timed out (30s)`
- Failure: `ERR_HTTP2_PROTOCOL_ERROR`
- Failure: `Cloudflare` challenge / blocked site
- Noise/truncation symptom: `consumed the entire 1K token browse_page budget`
- Success/noise mixed case: `wholesale FAQ content could not be fully read due to Shopify navigation dominating browse_page's 1K token limit`

## 3. How Many v2 Workers Used browse_page?

There are two useful counts, and they mean different things:

### A. Explicit note mentions

- `38 / 608` executed workers (`6.3%`) mention `browse_page` in their notes.

This is **not** actual browse usage. It is only the subset where the worker thought browse was worth mentioning.

### B. Actual local browse usage

By intersecting local `node.db` browse sessions with executed v2 instruction IDs:

- `522 / 608` executed workers (`85.9%`) used `browse_page`
- `86 / 608` (`14.1%`) did not show a local browse call in the telemetry window

This is the better measure for verdict-impact analysis.

## 4. Token Waste Estimate

Expected fixed behavior baseline from task framing:

- Expected page payload: `~5000` chars
- Expected token cost per browse: `~1250` tokens

Observed reality in local telemetry:

- Average successful browse payload: `1002.1` tokens
- That is about `19.8% lower` than the `1250`-token baseline

Outlier analysis:

- Calls above baseline (`>1250` tokens): `16`
- Distinct AI sessions involved: `8`
- Average tokens for those outlier calls: `2009.2`
- Total excess above baseline across all outlier calls: `12,147` tokens

Hypothetical worst-case if all successful browse calls had really been `8500` tokens each:

- Successful calls: `3034`
- Hypothetical excess per call vs expected baseline: `8500 - 1250 = 7250`
- Hypothetical excess total: `3034 * 7250 = 21,996,500` tokens

Observed excess vs that hypothetical:

- Observed outlier excess: `12,147` tokens
- That is about `0.06%` of the hypothetical mass-bloat scenario

Conclusion:

- There is no evidence of systemic token waste from 34K worker-facing browse responses in the main v2 flight.
- The actual cost profile was near or below the expected `5K chars ~= 1250 tokens` baseline.

## 5. Verdict Quality Impact

### Real browse-usage cohort (best comparison)

Using actual local browse sessions intersected with executed v2 instructions:

#### Workers that used browse (`522`)

- ACCESSIBLE: `81` (`15.5%`)
- MAYBE: `142` (`27.2%`)
- INCONCLUSIVE: `106` (`20.3%`)
- CLOSED: `110` (`21.1%`)
- GATED: `11` (`2.1%`)
- PRIVATE_LABEL: `53` (`10.2%`)
- OTHER: `19` (`3.6%`)

#### Workers without observed browse (`86`)

- ACCESSIBLE: `3` (`3.5%`)
- MAYBE: `6` (`7.0%`)
- INCONCLUSIVE: `46` (`53.5%`)
- CLOSED: `5` (`5.8%`)
- PRIVATE_LABEL: `13` (`15.1%`)
- OTHER: `13` (`15.1%`)

Interpretation:

- Browse users were **less** likely to end `INCONCLUSIVE` than non-browse workers (`20.3%` vs `53.5%`).
- Browse users were **more** likely to reach a concrete outcome such as `ACCESSIBLE`, `MAYBE`, or `CLOSED`.
- This does not support the idea that browse usage broadly confused workers into worse verdicts.

### Large-response outlier cohort

The `8` AI sessions with calls above `1250` tokens were:

- `AI-83290` -> `CLOSED`
- `AI-83303` -> `INCONCLUSIVE`
- `AI-83605` -> `ACCESSIBLE`
- `AI-83615` -> `MAYBE`
- `AI-83746` -> `CLOSED`
- `AI-83834` -> `ACCESSIBLE`
- `AI-83839` -> `MAYBE`
- `AI-83934` -> `MAYBE`

Distribution for this outlier cohort:

- ACCESSIBLE: `2`
- MAYBE: `3`
- CLOSED: `2`
- INCONCLUSIVE: `1`

Interpretation:

- Even the handful of larger browse outputs did **not** cluster into `INCONCLUSIVE` outcomes.
- The outlier cohort actually skewed toward usable verdicts.

### Important bias note

If you analyze only execution notes that explicitly mention `browse_page`, the set looks much worse (`30 / 38` are `INCONCLUSIVE`). That is because those notes mainly document failures and anomalies. It is not representative of normal browse usage.

## 6. Recommendation

Do **not** re-run all v2 brands just for browse-page bloat.

Recommended action:

1. Re-run the explicit browse-failure cohort first.
2. Re-run note-documented truncation/noise cases where the worker says nav/token limits blocked verification.
3. Do not treat successful 4K-capped browse calls as evidence of token-waste harm by default.

Suggested re-run target groups:

- `browse_page` asyncio failures
- Timeout / browser-context-closed cases
- HTTP/2 / Cloudflare blocked cases
- Workers that explicitly mention token-budget/nav-dominance problems

## Final Answer

- How many v2 workers used `browse_page`? `522 / 608` by actual local telemetry intersection.
- How many got errors vs content? Execution notes explicitly document `27` browse-problem cases; local telemetry shows `3034` successful browse calls in the same window.
- Average response size when content was returned? About `4006.3` stored JSON chars and `1002.1` tokens on successful calls.
- Estimated token waste from unfiltered snapshots? No systemic waste found; only `12,147` excess tokens above the `1250`-token baseline across `16` outlier calls.
- Verdict quality comparison? Browse users were less inconclusive than non-browse workers, and the large-response outlier cohort did not show degraded verdict quality.
- Should affected brands be re-run? Yes, but only targeted browse-failure / browse-noise cases, not the full v2 flight.

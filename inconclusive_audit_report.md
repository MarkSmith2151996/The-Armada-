# EE-463 Inconclusive Verdict Audit

## Executive Summary

- Thesis result: denied on average turn count.
- `INCONCLUSIVE` brands averaged `20.74` turns, below `ACCESSIBLE` at `25.39` and below the combined definitive-verdict average of `22.91`.
- The waste is a long-tail problem, not an average-case problem: `36 / 148` inconclusive brands (`24.32%`) exceeded the average `ACCESSIBLE` resolution time.
- If those high-turn inconclusive sessions had been capped at the average `ACCESSIBLE` turn count (`25.39`), the run would have saved about `528.86` turns and about `1.57M` estimated tokens.
- Phase 1 still matters: `71 / 148` inconclusive brands (`47.97%`) had zero brand-specific or commerce-relevant hits across the first 3 searches (top 3 results per search, heuristic review of `tool_results.full_result`).
- Recommended gate: if the first 3 searches return zero relevant brand/wholesale signals, short-circuit to `INCONCLUSIVE` in roughly `4-6` turns instead of allowing long-tail retries.

## Data Sources

- Postgres outreach artifacts: `fba.artifact` rows from `2026-06-30` forward, captured from the task-required query.
- Local worker telemetry: `/Users/tubslamanna/armada/node.db` tables `worker_sessions`, `session_telemetry`, and `tool_results`.
- Disk cross-checks: `/Users/tubslamanna/armada/run-results/` and `/Users/tubslamanna/armada/flight-logs/` contain worker/session traces, but `node.db` is the canonical structured source for turn/tool telemetry.
- `node.sqld/dbs/default/data` did not contain `session_telemetry` or `worker_sessions`; those tables were present in `node.db`.

## Comparison Table By Verdict

| Verdict | Count | Avg Turns | Median Turns | Min | Max | Avg Tool Calls | Avg Duration (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| ACCESSIBLE | 84 | 25.39 | 21.5 | 4 | 110 | 25.33 | 2319.38 |
| BLOCKED_FOR_AMAZON | 16 | 20.75 | 15.5 | 8 | 57 | 20.69 | 4911.78 |
| CLOSED | 115 | 25.57 | 24 | 4 | 97 | 25.57 | 1572.33 |
| GATED | 11 | 27.55 | 25 | 10 | 56 | 27.55 | 5720.39 |
| INCONCLUSIVE | 148 | 20.74 | 16.5 | 3 | 113 | 20.74 | 2112.87 |
| MAYBE | 153 | 28.69 | 24 | 3 | 280 | 28.65 | 3026.41 |
| PRIVATE_LABEL | 67 | 14.99 | 13 | 2 | 58 | 14.94 | 2264.84 |

## Thesis Validation

### 1. Do INCONCLUSIVE verdicts average significantly more turns than ACCESSIBLE?

No.

- `INCONCLUSIVE`: `20.74` avg turns, `16.5` median turns
- `ACCESSIBLE`: `25.39` avg turns, `21.5` median turns
- Combined definitive verdicts (`ACCESSIBLE`, `CLOSED`, `BLOCKED_FOR_AMAZON`, `GATED`, `PRIVATE_LABEL`): `22.91` avg turns, `21` median turns

The original thesis does not hold at the aggregate level.

### 2. What is the wasted turn count above the average ACCESSIBLE resolution?

- Average `ACCESSIBLE` threshold: `25.39` turns
- Inconclusive sessions above that threshold: `36 / 148` (`24.32%`)
- Excess turns across only those above-threshold sessions: `528.86`

This is a concentrated tail problem rather than a population-wide average problem.

### 3. If we capped INCONCLUSIVE at the average ACCESSIBLE turn count, how many tokens would we save?

- Estimated savings: about `1,568,055` tokens

Method:

- For each inconclusive session above `25.39` turns, estimate tokens per turn from its recorded input/output token totals.
- Multiply the excess turns above `25.39` by that session's observed tokens-per-turn.

### 4. What percentage of INCONCLUSIVE brands had zero relevant results after Phase 1?

- `71 / 148` inconclusive brands = `47.97%`

Heuristic used:

- Reviewed the first 3 `search_brand` calls for each inconclusive session.
- Parsed the top 3 returned results from each search in `tool_results.full_result`.
- Counted a result as relevant only when it contained brand-specific plus commerce-relevant evidence such as an official domain, retailer/distributor/wholesale language, Amazon/brand match, or a real Faire brand hit.

This metric is approximate, but directionally strong enough to support a stricter Phase 1 gate.

## Top 20 Worst INCONCLUSIVE Offenders

| Brand | Turns | Searches | Pages Browsed | Brief Summary |
|---|---:|---:|---:|---|
| Quake | 113 | 80 | 32 | Hunting sling brand confirmed on Amazon and via BPI Outdoors, but repeated search retries stayed irrelevant and burned turns. |
| Eclipse | 99 | 81 | 17 | Curtain brand found on Amazon, but search results were dominated by Eclipse software/Foundation noise. |
| Larson | 84 | 70 | 12 | Official Larson Doors path existed, but `browse_page` repeatedly failed on the brand site. |
| BreathableBaby | 76 | 64 | 11 | Search quality degraded across many queries; no usable Faire evidence and little reliable wholesale confirmation. |
| Bulatry | 61 | 53 | 7 | Brand web presence was inconsistent and wholesale signals stayed weak despite many retries. |
| MILLENNIUM | 61 | 51 | 9 | Real Amazon brand, but no official site, wholesale portal, distributor, or dealer program found. |
| FamoWood | 51 | 36 | 14 | Searches found the brand, but `browse_page` failed repeatedly (`asyncio.run()` issue), blocking confirmation. |
| Slippery Stuff | 49 | 39 | 9 | Legitimate product footprint found, but no clean wholesale/reseller path was confirmed. |
| GHS Strings | 47 | 28 | 18 | Real manufacturer site found, but no usable wholesale application path surfaced. |
| NUUSOL | 45 | 31 | 13 | DTC and Amazon presence existed, but no public dealer/B2B/wholesale path was confirmed. |
| Luigi Bormioli | 41 | 29 | 11 | Large manufacturer with consumer presence, but no small-retailer wholesale path found. |
| Earth Care | 37 | 25 | 11 | Amazon and marketplace presence existed, but no reliable brand site or direct wholesale path appeared. |
| Superior Threads | 34 | 29 | 4 | Official site existed, but Cloudflare blocked browsing and search results stayed weak. |
| Trodat | 34 | 22 | 11 | Major manufacturer confirmed, but official site was Cloudflare-blocked and wholesale path stayed unclear. |
| HEAD | 32 | 17 | 14 | Brand ambiguity crushed search relevance; results were mostly dictionary/anatomy noise. |
| Van Beek-Natural Science | 31 | 20 | 10 | Real company and Amazon/Chewy presence found, but no accessible reseller intake path surfaced. |
| Business Source | 30 | 28 | 1 | Search backend repeatedly failed to return relevant brand-specific results despite confirmed Amazon presence. |
| DMT (Diamond Machining Technology) | 30 | 19 | 10 | Brand confirmed, but searches were dominated by the unrelated drug term `DMT`. |
| PLATO | 30 | 24 | 5 | Real dog treat brand, but search ambiguity and weak reseller signals prevented a firm conclusion. |
| World's Best Cat Litter | 30 | 16 | 13 | Search results were largely irrelevant and browse captures were too shallow to resolve wholesale access. |

## Patterns In The Worst Offenders

- Search ambiguity: `HEAD`, `DMT`, `Eclipse`, `World's Best Cat Litter`
- Browser/tooling failures: `Larson`, `FamoWood`, `Superior Threads`, `Trodat`
- Real brands with no public dealer path: `NUUSOL`, `GHS Strings`, `Van Beek-Natural Science`, `Luigi Bormioli`
- Excessive retry loops after early weak evidence: visible across most of the top 20

## Recommended Phase 1 Gate Change

Adopt a two-lane gate:

1. If the first 3 searches produce zero relevant brand/commerce hits, stop early and return `INCONCLUSIVE` in `4-6` turns.
2. If the first 3 searches do show brand-specific evidence, continue, but add a hard retry cap on repeated search reformulations and repeated `browse_page` failures.

Practical rule:

- After 3 searches, if there is no official domain, no valid Faire brand page, no distributor/dealer page, and no policy/reseller signal, do not continue into 15+ additional search rewrites.
- After 2 failed `browse_page` attempts on the same domain, stop retrying that page and decide from available evidence.

## Bottom Line

The broad claim that `INCONCLUSIVE` verdicts are the main high-turn bucket is false. They are faster than `ACCESSIBLE` on average.

The real issue is narrower:

- roughly half of inconclusive brands show no useful signal in Phase 1,
- about a quarter of inconclusive runs become long-tail search spirals,
- and those tail sessions still represent about `1.57M` tokens of preventable spend under an `ACCESSIBLE`-average cap.

That means the best fix is not a blanket lower turn budget for all inconclusive work. The best fix is an early no-signal gate plus stricter retry limits once search ambiguity or browse failures are obvious.

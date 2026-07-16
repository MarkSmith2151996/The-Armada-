# Flight 2 Diagnostic

Generated: 2026-07-14 05:47:48 UTC
Scope: workers started on or after 2026-07-14 04:00:00 UTC.

## Executive Summary

- `node.db` recorded 81 worker sessions, 1313 logged tool calls, and 74 queued current-flight verdicts.
- Verdict breakdown: `ACCESSIBLE` 18, `BLOCKED_FOR_AMAZON` 3, `CLOSED` 13, `INCONCLUSIVE` 22, `MAYBE` 17, `PRIVATE_LABEL` 1.
- All 81 scoped Node sessions remain marked `active` even though 74 verdicts are persisted and synced. Local worker-status tracking is not closing completed work.
- SearXNG returned one or more results for 936/980 calls (95.5%); it is not globally down. It is materially weak for ambiguous/common-word brands and a smaller set of exact-brand queries.
- Browser calls succeeded 309/333 times. 14 failures were the shared CDP browser-context error and 2 reported pool exhaustion.
- The local OpenCode session DB had zero `brand-outreach-worker` sessions after the cutoff. The Node MCP context database is therefore the only complete per-worker source for this flight; OpenCode-session turn/tool telemetry cannot be reconciled for it.
- Post-flight sync completed: `synced_verdicts=83`, `failed_verdicts=0`, `synced_statuses=91`, `failed_statuses=0`. Current sqld unsynced verdict count is 0.

## Sources And Limits

- `~/.local/share/opencode/opencode.db`: queried read-only; no scoped worker sessions were present after the requested cutoff.
- `~/armada/node.db`: available raw `worker_sessions` and `tool_results` evidence for the active flight.
- `http://127.0.0.1:8400/v2/pipeline`: sqld verdict queue and sync-state source.
- `acquire_cdp` is not persisted in `node.db`; direct acquire success/failure totals cannot be measured. Browser logs provide the observable CDP evidence below.
- `session_telemetry` rows are absent for the scoped workers, so each worker tool-call total is calculated from raw `tool_results`; turn count is the `worker_sessions.turn_count` value.

## Search Quality

- Calls: 980. Zero-result calls: 44 (4.5%). Mean returned-result count: 9.51.
- Healthy behavior: exact brands commonly produced 7-10 results and recognizable official/distributor pages, e.g. HELLEE initially returned Helle wholesale-distributor evidence and Hipshot returned official-site results.
- Degraded behavior: SearXNG did not return the same generic result set for every query globally, but it repeatedly ignored brand disambiguation for affected names: Brava -> Brave browser, Cableguys -> cable-TV providers, Halo Headband -> Microsoft Halo, Pioneer -> unrelated Pioneer entities, Captain Rodney's -> Captain/Wikipedia/Merriam-Webster, and Sound Town -> SoundCloud/Pixabay/Microsoft/YouTube-help noise.
- Interpretation: SearXNG is partially healthy. The failure is query/brand-specific relevance and engine availability, not a uniform all-query outage. Workers should not convert a nonzero result count into a relevance signal without checking the top results.

## CDP Analysis

- Browse calls: 333. Failures: 24 (7.2%).
- `CDP browser-context protocol error on 9226`: 14.
- `site HTTP/2 error`: 4.
- `all CDP ports occupied`: 2.
- `site certificate error`: 2.
- `unreadable page content`: 1.
- `site DNS error`: 1.
- 14 failures connected to `localhost:9226` and failed on `Browser.setDownloadBehavior` browser-context management. No non-existent assigned port is evidenced.
- 2 failures explicitly reported all CDP ports occupied. The remaining 8 failures were target-site/content errors without a logged port.
- Of the 22 current `INCONCLUSIVE` verdicts, 10 explicitly cite CDP unavailability or a CDP protocol failure in their final notes. Browser/CDP failure therefore has a direct, substantial association with false or premature INCONCLUSIVE outcomes, but it is not the sole cause.

## Inconclusive Brands

| Brand | Confidence | Primary reason | Evidence |
| --- | --- | --- | --- |
| Amenazel | HIGH | search quality or absent brand evidence | 12 searches performed across wholesale program, Faire, authorized distributor, brand lookup, ASIN lookup, and direct brand searches. Zero relevant results returned for "Amenazel" i |
| ANFAR LONDON | LOW | both search quality and CDP | 10 search queries across multiple engines returned zero relevant results for ANFAR LONDON. Searches included: "ANFAR LONDON wholesale program", "ANFAR LONDON Faire wholesale", "ANF |
| Avlon | LOW | search quality and site DNS failure | Avlon is a real brand (parent of KeraCare, Affirm hair care lines). Confirmed via keracare.com About page which mentions Avlon Research Center and founder Dr. Ali N. Syed. KeraCare |
| BINBOK VR | HIGH | search quality or absent brand evidence | Searched 7 different queries (wholesale program, Faire, authorized distributor, exact phrase, Amazon listing, brand+VR headset, brand only) with zero relevant results across all se |
| Boesklenn | HIGH | invalid or misattributed brand input | "Boesklenn" is not a real brand name. 6 searches across wholesale, Faire, distributor, ASIN, general brand, and exact-match quoted queries returned ZERO relevant results. The pre-l |
| Brava | LOW | both search quality and CDP | Brand: Brava. SearXNG search engine consistently returned "Brave" browser results dominating the top spots for every query containing "Brava" ? approximately 15 search queries atte |
| Cableguys | LOW | search quality or brand ambiguity | Brand name "Cableguys" is ambiguous with "cable TV" ? every search attempt returned Spectrum/cable TV provider results regardless of negative keywords or disambiguation efforts. Un |
| Captain Rodney's | LOW | search quality and site certificate failure | SearXNG backend returned the same 3 irrelevant results (Wikipedia "Captain", Merriam-Webster, Captain D's) for ALL 9+ search queries regardless of specificity. Search tool fundamen |
| Duck Brand | LOW | both search quality and CDP | Duck Brand (ShurTech Brands LLC, duct tape/adhesives) research incomplete. 1) SearXNG could not disambiguate 'Duck Brand' from generic 'duck' queries ? 3 searches returned irreleva |
| Halo Headband | LOW | search quality or brand ambiguity | Insufficient evidence after exhaustive search. Brand confirmed to exist on Amazon (ASINs B00A0VQMFQ, B00Q6HL13Q, B0BL61TWG4, B00AJIZBVG) selling headbands/sweatbands under 'Halo He |
| HELLEE | LOW | CDP/browser failure | browse_page failed with protocol error on cdp_port=9226: 'Browser context management is not supported' when connecting to ws://localhost:9226. Brand was NOT researched. Initial Pha |
| Heywood | HIGH | both search quality and CDP | TOOL FAILED: browse_page tool failed on cdp_port=9226 (Protocol error: Browser context management not supported). Brand 'Heywood' appears on ASIN B07K17L2PH (Predator 4-Movie Colle |
| Hikari | LOW | CDP/browser failure | TOOL FAILED: browse_page tool failed on all 3 attempts (cdp_port=9226) with error 'Browser context management is not supported'. Could not verify any brand pages. Searches identifi |
| Hollyhi | LOW | both search quality and CDP | TOOL_FAILED: browse_page on cdp_port=9226 returned Chrome CDP error 'Browser context management is not supported' consistently. All CDP ports occupied, could not acquire alternate. |
| It's Sew Emma | LOW | CDP/browser failure | TOOL FAILURE: browse_page on cdp_port=9226 returned Browser context management error (Browser.setDownloadBehavior not supported) on both attempts. Brand is a legitimate quilting pa |
| Ivtivfu | HIGH | both search quality and CDP | browse_page tool failed on port 9226 (Browser context management not supported error). All 5 web searches for 'Ivtivfu' returned zero relevant results - suggests brand may be priva |
| Jacobs | MEDIUM | search quality or brand ambiguity | Brand is Jacobs Kr?nung coffee (ASINs B00IT6A4HG, B001GVIT6E) sold on Amazon at $72.42 and $40.99 by third parties (PELE TRADE LLC, Usluga's Store). All searches for wholesale/dist |
| JT Eaton | LOW | CDP/browser failure | TOOL FAILURE: browse_page persistently failed on cdp_port=9226 with 'Browser context management is not supported' error across 2 attempts (turns 10-12), even after cleanup. Brand I |
| MY CREATIVE CAMP | LOW | both search quality and CDP | No information found about this brand through any of 8 SearXNG searches (wholesale program, Faire, authorized distributor, brand craft, ASIN search, domain search, creativation con |
| Pioneer Photo Albums | MEDIUM | search quality or brand ambiguity | Brand sells 1000+ photo album products directly on Amazon ('Sold by Pioneer Photo Albums'). Multiple other resellers also offer via 'More Buying Choices'. No official website, whol |
| Satechi | LOW | both search quality and CDP | Turns used: 16. Could not research Satechi due to tool failures. search_brand returned no relevant results across 10+ queries (all search backends suspended: Brave 'too many reques |
| Sound Town | LOW | both search quality and CDP | Brand discovered via NAMM with passing ASIN B086WY6Y34 ($79.99, 50 units/mo). However, SearXNG backend returned zero relevant results across 10+ search query variations (wholesale, |

## Accessible Confirmations

AeroPress (HIGH), Afta (HIGH), AGM Global Vision (HIGH), Bondhus (HIGH), Calmoseptine (HIGH), CARNA 4 (MEDIUM), emuaid (MEDIUM), FloraCraft (HIGH), Formula 420 (HIGH), HK Army (HIGH), Honees (HIGH), Mr. Bar-B-Q (HIGH), MTM (HIGH), Odd Sox (HIGH), Ullman (HIGH), Vital Proteins (HIGH), WYZE (HIGH), Zotz (HIGH).

## Reconciliation

- At snapshot, sqld had 74 scoped verdicts for 81 scoped Node sessions.
- Worker sessions without a same-normalized-brand queued verdict: 8. These are not automatically recoverable because they remain `active` and have no final `record_verdict` tool result: test (test), Wright Products (wright-products-research), Jack's Classic (JackClassic-001), Plink (AI-85442), ZOUT (AI-85451), ALPHA LION (AI-85454), SureFire (AI-85447), Port Authority (85443).
- Queued verdicts without a same-normalized-brand Node session: 1. These are retained rather than overwritten because they may have been written by sessions not persisted to `node.db`: Hollyhi (default).
- Recovered verdicts: 0. No missing worker was completed with a final verdict present in its raw context but absent from sqld. Sync published all pre-existing unsynced queue rows successfully.

## Per-Worker Evidence

The following appendix retains every recorded `search_brand` and `browse_page` invocation. Search relevance is an evidence label, not a claim that nonzero results were useful.

### HELLEE (HELLEE_worker)

- Session: `HELLEE_research`. Status: `active`. Turns: 4. Raw tool calls: 4.
- Final sqld verdict: `INCONCLUSIVE` / `LOW`. Queue write: present; synced at `2026-07-14 05:43:40`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `HELLEE wholesale program` -> 41 results; brand-matching candidate.
  - Turn 2: `HELLEE Faire wholesale` -> 23 results; not independently classified.
  - Turn 3: `HELLEE authorized distributor` -> 11 results; not independently classified.
- Browse calls:
  - Turn 4: `https://hellee-us.com/` -> CDP browser-context protocol error on 9226; browse_page failed for https://hellee-us.com/: BrowserType.connect_over_cdp: Protocol error (Browser.setDownloadBehavior): Browser context management is not supported. Call log:   - <ws preparing> retrieving websocket url from http://localhost:9226   - <ws con.

### Hikari (hikari-worker-001)

- Session: `hikari-research-001`. Status: `active`. Turns: 7. Raw tool calls: 7.
- Final sqld verdict: `INCONCLUSIVE` / `LOW`. Queue write: present; synced at `2026-07-14 05:43:41`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Hikari fish food wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `Hikari Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `Hikari authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 4: `B00SLAIGZ2 Hikari` -> 10 results; not independently classified.
- Browse calls:
  - Turn 5: `https://hikariusa.com/` -> CDP browser-context protocol error on 9226; browse_page failed for https://hikariusa.com/: BrowserType.connect_over_cdp: Protocol error (Browser.setDownloadBehavior): Browser context management is not supported. Call log:   - <ws preparing> retrieving websocket url from http://localhost:9226   - <ws con.
  - Turn 6: `https://hikariusa.com/` -> CDP browser-context protocol error on 9226; browse_page failed for https://hikariusa.com/: BrowserType.connect_over_cdp: Protocol error (Browser.setDownloadBehavior): Browser context management is not supported. Call log:   - <ws preparing> retrieving websocket url from http://localhost:9226   - <ws con.
  - Turn 7: `https://hikariusa.com/` -> CDP browser-context protocol error on 9226; browse_page failed for https://hikariusa.com/: BrowserType.connect_over_cdp: Protocol error (Browser.setDownloadBehavior): Browser context management is not supported. Call log:   - <ws preparing> retrieving websocket url from http://localhost:9226   - <ws con.

### Hipshot (hipshot_worker_01)

- Session: `hipshot_research`. Status: `active`. Turns: 25. Raw tool calls: 25.
- Final sqld verdict: `MAYBE` / `MEDIUM`. Queue write: present; synced at `2026-07-14 05:43:42`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Hipshot wholesale program dealer` -> 10 results; brand-matching candidate.
  - Turn 2: `Hipshot Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `Hipshot authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 4: `Hipshot products dealer application wholesale account` -> 10 results; brand-matching candidate.
  - Turn 5: `Hipshot guitar wholesale distributor USA` -> 19 results; brand-matching candidate.
  - Turn 6: `site:faire.com Hipshot` -> 0 results; no results.
  - Turn 11: `Hipshot MAP policy minimum advertised price` -> 20 results; brand-matching candidate.
  - Turn 12: `Hipshot Amazon reseller restriction authorized` -> 20 results; not independently classified.
  - Turn 13: `site:hipshotproducts.com wholesale dealer` -> 0 results; no results.
  - Turn 15: `Hipshot products dealer wholesale application become dealer` -> 10 results; brand-matching candidate.
  - Turn 17: `Hipshot products terms conditions reseller marketplace Amazon eBay` -> 10 results; brand-matching candidate.
  - Turn 22: `B003H8XAMM Hipshot Amazon` -> 10 results; not independently classified.
  - Turn 23: `"Hipshot" "Allparts" dealer wholesale reseller` -> 10 results; brand-matching candidate.
  - Turn 24: `Hipshot guitar parts Amazon seller` -> 10 results; brand-matching candidate.
- Browse calls:
  - Turn 7: `https://hipshotproducts.com/` -> CDP browser-context protocol error on 9226; browse_page failed for https://hipshotproducts.com/: BrowserType.connect_over_cdp: Protocol error (Browser.setDownloadBehavior): Browser context management is not supported. Call log:   - <ws preparing> retrieving websocket url from http://localhost:9226   - <.
  - Turn 8: `https://hipshotproducts.com/` -> success; Browsed https://hipshotproducts.com/; 3732 characters returned..
  - Turn 9: `https://hipshotproducts.com/apps/store-locator` -> success; Browsed https://hipshotproducts.com/apps/store-locator; 5000 characters returned..
  - Turn 10: `https://hipshotproducts.com/account/register` -> success; Browsed https://hipshotproducts.com/account/register; 2336 characters returned..
  - Turn 14: `https://www.allparts.com/collections/hipshot` -> success; Browsed https://www.allparts.com/collections/hipshot; 3913 characters returned..
  - Turn 16: `https://www.allparts.com/pages/become-an-allparts-dealer` -> success; Browsed https://www.allparts.com/pages/become-an-allparts-dealer; 4999 characters returned..
  - Turn 18: `https://hipshotproducts.com/pages/about` -> success; Browsed https://hipshotproducts.com/pages/about; 3510 characters returned..
  - Turn 19: `https://hipshotproducts.com/pages/terms-of-service` -> success; Browsed https://hipshotproducts.com/pages/terms-of-service; 2318 characters returned..
  - Turn 20: `https://hipshotproducts.com/pages/privacy-policy` -> success; Browsed https://hipshotproducts.com/pages/privacy-policy; 2316 characters returned..
  - Turn 21: `http://hipshot.zendesk.com/hc/en` -> success; Cloudflare challenge detected.
  - Turn 25: `https://www.allparts.com/pages/terms-of-use` -> success; Browsed https://www.allparts.com/pages/terms-of-use; 5000 characters returned..

### Heywood (heywood-research-01)

- Session: `heywood-research-01`. Status: `active`. Turns: 9. Raw tool calls: 9.
- Final sqld verdict: `INCONCLUSIVE` / `HIGH`. Queue write: present; synced at `2026-07-14 05:43:40`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Heywood wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `Heywood Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `Heywood authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 4: `B07K17L2PH Heywood Amazon product` -> 24 results; brand-matching candidate.
  - Turn 5: `Heywood studio Blu-ray wholesale` -> 19 results; brand-matching candidate.
  - Turn 6: `"Heywood" Blu-ray distributor wholesale` -> 10 results; brand-matching candidate.
  - Turn 7: `"Heywood" brand Amazon movie` -> 10 results; brand-matching candidate.
  - Turn 8: `Heywood entertainment studio wholesale` -> 24 results; brand-matching candidate.
- Browse calls:
  - Turn 9: `https://www.amazon.com/dp/B07K17L2PH` -> CDP browser-context protocol error on 9226; browse_page failed for https://www.amazon.com/dp/B07K17L2PH: BrowserType.connect_over_cdp: Protocol error (Browser.setDownloadBehavior): Browser context management is not supported. Call log:   - <ws preparing> retrieving websocket url from http://localhost:92.

### HK Army (hk-army-001)

- Session: `hk-army-001`. Status: `active`. Turns: 19. Raw tool calls: 19.
- Final sqld verdict: `ACCESSIBLE` / `HIGH`. Queue write: present; synced at `2026-07-14 05:43:42`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `HK Army wholesale program` -> 19 results; brand-matching candidate.
  - Turn 2: `HK Army Faire wholesale` -> 20 results; brand-matching candidate.
  - Turn 3: `HK Army authorized distributor` -> 19 results; not independently classified.
  - Turn 4: `HK Army paintball Amazon MAP policy reseller restrictions` -> 10 results; not independently classified.
  - Turn 7: `"HK Army" MAP policy minimum advertised price` -> 10 results; not independently classified.
  - Turn 8: `"HK Army" Faire wholesale paintball` -> 10 results; not independently classified.
  - Turn 9: `"HK Army" paintball Amazon reseller authorized` -> 10 results; not independently classified.
  - Turn 10: `site:hkarmy.com wholesale dealer terms conditions MAP` -> 0 results; no results.
  - Turn 11: `"hkarmy" Amazon paintball` -> 10 results; not independently classified.
  - Turn 13: `"HK Army" paintball brand dealer MAP policy resell Amazon` -> 10 results; not independently classified.
  - Turn 15: `"HK Army" "B08TF77D2F" Amazon` -> 10 results; not independently classified.
  - Turn 16: `"hkarmy.com" wholesale dealer application paintball` -> 10 results; not independently classified.
  - Turn 17: `hkarmy paintball Amazon store` -> 10 results; not independently classified.
  - Turn 18: `amazon.com "hk army" paintball` -> 10 results; not independently classified.
- Browse calls:
  - Turn 5: `https://www.hkarmy.com/pages/wholesale` -> CDP browser-context protocol error on 9226; browse_page failed for https://www.hkarmy.com/pages/wholesale: BrowserType.connect_over_cdp: Protocol error (Browser.setDownloadBehavior): Browser context management is not supported. Call log:   - <ws preparing> retrieving websocket url from http://localhost:.
  - Turn 6: `https://www.hkarmy.com/pages/wholesale` -> success; Browsed https://www.hkarmy.com/pages/wholesale; 5000 characters returned..
  - Turn 12: `https://www.hkarmy.com` -> success; Browsed https://www.hkarmy.com; 5000 characters returned..
  - Turn 14: `https://www.hkarmy.com/policies/terms-of-service` -> success; Browsed https://www.hkarmy.com/policies/terms-of-service; 5000 characters returned..
  - Turn 19: `https://www.hkarmy.com/pages/wholesale` -> success; Browsed https://www.hkarmy.com/pages/wholesale; 5000 characters returned..

### Zebra Pen (AI-85349)

- Session: `AI-85349`. Status: `active`. Turns: 21. Raw tool calls: 21.
- Final sqld verdict: `MAYBE` / `MEDIUM`. Queue write: present; synced at `2026-07-14 05:43:43`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Zebra Pen wholesale program` -> 20 results; generic/irrelevant per final verdict.
  - Turn 2: `Zebra Pen Faire wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 3: `Zebra Pen authorized distributor` -> 10 results; generic/irrelevant per final verdict.
  - Turn 4: `"Zebra Pen" writing instruments wholesale program` -> 10 results; generic/irrelevant per final verdict.
  - Turn 5: `"Zebra Pen" Faire wholesale pens` -> 10 results; generic/irrelevant per final verdict.
  - Turn 6: `"Zebra Pen" authorized dealer wholesale pens stationery` -> 10 results; generic/irrelevant per final verdict.
  - Turn 7: `zebrapen.com wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 8: `"Zebra Pen" ZEBRA Japan pen company wholesale retailer account` -> 10 results; generic/irrelevant per final verdict.
  - Turn 9: `Zebra Pen Japan official website zebra.co.jp` -> 10 results; generic/irrelevant per final verdict.
  - Turn 10: `Zebra Pen Corporation USA wholesale distributor reseller program` -> 10 results; generic/irrelevant per final verdict.
  - Turn 11: `"Zebra" pen company stationery Japan wikipedia` -> 10 results; generic/irrelevant per final verdict.
  - Turn 12: `Zebra Sarasa gel pen wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 13: `"zebrapen.com" OR "zebra-pen.com" wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 17: `site:zebrapen.com wholesale OR dealer OR distributor OR B2B` -> 0 results; no results.
  - Turn 18: `"Zebra Pen" Faire.com wholesale pens` -> 10 results; generic/irrelevant per final verdict.
  - Turn 21: `"Zebra Pen" MAP policy Amazon reseller restriction` -> 10 results; generic/irrelevant per final verdict.
- Browse calls:
  - Turn 14: `https://www.zebrapen.com` -> success; Browsed https://www.zebrapen.com; 3847 characters returned..
  - Turn 15: `https://www.zebrapen.com/pages/where-to-buy` -> success; Browsed https://www.zebrapen.com/pages/where-to-buy; 4026 characters returned..
  - Turn 16: `https://www.zebrapen.com/pages/contact-us` -> success; Browsed https://www.zebrapen.com/pages/contact-us; 2950 characters returned..
  - Turn 19: `https://www.zebrapen.com/pages/our-company` -> success; Browsed https://www.zebrapen.com/pages/our-company; 5000 characters returned..
  - Turn 20: `https://www.zebrapen.com/pages/wholesale` -> success; Browsed https://www.zebrapen.com/pages/wholesale; 3745 characters returned..

### Halo Headband (AI-85359)

- Session: `AI-85359`. Status: `active`. Turns: 20. Raw tool calls: 20.
- Final sqld verdict: `INCONCLUSIVE` / `LOW`. Queue write: present; synced at `2026-07-14 05:43:44`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Halo Headband wholesale program` -> 10 results; generic/irrelevant per final verdict.
  - Turn 2: `Halo Headband Faire wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 3: `Halo Headband authorized distributor` -> 10 results; generic/irrelevant per final verdict.
  - Turn 4: `"Halo Headband" headwear wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 5: `"Halo Headband" brand retailer` -> 10 results; generic/irrelevant per final verdict.
  - Turn 6: `B00A0VQMFQ Halo headband` -> 10 results; generic/irrelevant per final verdict.
  - Turn 7: `haloheadband.com OR "halo headband" -halo -xbox -game` -> 10 results; generic/irrelevant per final verdict.
  - Turn 8: `"Halo" sweatband wholesale supplier` -> 10 results; generic/irrelevant per final verdict.
  - Turn 9: `"Halo" headband Amazon brand` -> 10 results; generic/irrelevant per final verdict.
  - Turn 10: `"Halo" "headband" "sweat" brand company` -> 10 results; generic/irrelevant per final verdict.
  - Turn 11: `"Halo" "Headband" site:amazon.com` -> 0 results; no results.
  - Turn 12: `halo headband sport wholesale distributor` -> 10 results; generic/irrelevant per final verdict.
  - Turn 14: `"Halo Headband" brand site` -> 10 results; generic/irrelevant per final verdict.
  - Turn 17: `"Halo Headband" "official website" OR "haloheadband"` -> 10 results; generic/irrelevant per final verdict.
  - Turn 19: `"Halo" "sweatband" manufacturer USA wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 20: `halo headband contact information wholesale` -> 10 results; generic/irrelevant per final verdict.
- Browse calls:
  - Turn 13: `https://www.amazon.com/dp/B00A0VQMFQ` -> success; Browsed https://www.amazon.com/dp/B00A0VQMFQ; 5000 characters returned..
  - Turn 15: `https://www.amazon.com/stores/HaloHeadband` -> success; Browsed https://www.amazon.com/stores/HaloHeadband; 386 characters returned..
  - Turn 16: `https://www.amazon.com/s?k=Halo+Headband&i=sporting-goods` -> success; Browsed https://www.amazon.com/s?k=Halo+Headband&i=sporting-goods; 5000 characters returned..
  - Turn 18: `https://www.amazon.com/stores/Halo+Headband` -> success; Browsed https://www.amazon.com/stores/Halo+Headband; 386 characters returned..

### Pioneer Photo Albums (AI-85345)

- Session: `AI-85345`. Status: `active`. Turns: 19. Raw tool calls: 19.
- Final sqld verdict: `INCONCLUSIVE` / `MEDIUM`. Queue write: present; synced at `2026-07-14 05:43:45`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Pioneer Photo Albums wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `"Pioneer Photo Albums" wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `"Pioneer Photo Albums" Faire` -> 10 results; brand-matching candidate.
  - Turn 4: `Pioneer Photo Albums authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 5: `B002X79OOQ Pioneer Photo Albums` -> 10 results; not independently classified.
  - Turn 6: `B001VGH0NW Pioneer Photo Albums photo album` -> 10 results; not independently classified.
  - Turn 7: `Pioneer Photo Albums website photo album brand` -> 10 results; brand-matching candidate.
  - Turn 9: `Pioneer Photo Albums official website` -> 10 results; brand-matching candidate.
  - Turn 10: `"Pioneer Photo Albums" brand Amazon store` -> 10 results; brand-matching candidate.
  - Turn 11: `"Pioneer Photo Albums" "photo album" scrapbook wholesale` -> 10 results; brand-matching candidate.
  - Turn 13: `Pioneer Photo Albums LLC company official site contact` -> 10 results; brand-matching candidate.
  - Turn 14: `pioneerphotoalbums.com OR pioneerphotoalbums wholesale` -> 10 results; not independently classified.
  - Turn 16: `"Pioneer Photo Albums" company location` -> 10 results; brand-matching candidate.
  - Turn 17: `photo album manufacturer pioneer brand` -> 10 results; brand-matching candidate.
  - Turn 18: `"Pioneer" "photo album" scrapbook supplier wholesale` -> 10 results; brand-matching candidate.
  - Turn 19: `"Pioneer Photo Albums" address phone email` -> 10 results; brand-matching candidate.
- Browse calls:
  - Turn 8: `https://www.amazon.com/dp/B002X79OOQ` -> success; Browsed https://www.amazon.com/dp/B002X79OOQ; 5000 characters returned..
  - Turn 12: `https://www.amazon.com/stores/PioneerPhotoAlbums/page/B4B4A572-5F8C-4E3E-8566-E4ECC8EBBA8A` -> success; Browsed https://www.amazon.com/stores/PioneerPhotoAlbums/page/B4B4A572-5F8C-4E3E-8566-E4ECC8EBBA8A; 5000 characters returned..
  - Turn 15: `https://www.amazon.com/sp?ie=UTF8&seller=A2D4G16Z38FQ7B` -> success; Browsed https://www.amazon.com/sp?ie=UTF8&seller=A2D4G16Z38FQ7B; 386 characters returned..

### Formula 420 (AI-85357)

- Session: `AI-85357`. Status: `active`. Turns: 19. Raw tool calls: 19.
- Final sqld verdict: `ACCESSIBLE` / `HIGH`. Queue write: present; synced at `2026-07-14 05:43:49`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Formula 420 wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `Formula 420 Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `Formula 420 authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 4: `"Formula 420" glass pipe cleaner wholesale` -> 10 results; brand-matching candidate.
  - Turn 5: `"Formula 420" cleaner wholesale distributor` -> 10 results; brand-matching candidate.
  - Turn 6: `formula420.com cleaner` -> 10 results; not independently classified.
  - Turn 7: `"formula 420" "pipe cleaner" brand` -> 10 results; brand-matching candidate.
  - Turn 8: `Formula 420 Original Cleaner official website` -> 10 results; brand-matching candidate.
  - Turn 9: `formula420official.com OR formula420.com OR kmgformula420.com` -> 10 results; not independently classified.
  - Turn 12: `"Formula 420" cleaner Amazon MAP policy reseller restrictions` -> 10 results; brand-matching candidate.
- Browse calls:
  - Turn 10: `https://www.faire.com/search?q=formula+420` -> success; Browsed https://www.faire.com/search?q=formula+420; 2712 characters returned..
  - Turn 11: `https://www.faire.com/brand/b_8bzmksnfa7` -> success; Browsed https://www.faire.com/brand/b_8bzmksnfa7; 5000 characters returned..
  - Turn 13: `https://www.faire.com/brand/b_7whqct3kj4` -> success; Browsed https://www.faire.com/brand/b_7whqct3kj4; 5000 characters returned..
  - Turn 14: `https://www.formula420.com` -> success; Browsed https://www.formula420.com; 905 characters returned..
  - Turn 15: `https://formula420.com/wholesale/` -> success; Browsed https://formula420.com/wholesale/; 1672 characters returned..
  - Turn 16: `https://formula420.com/company/` -> success; Browsed https://formula420.com/company/; 1114 characters returned..
  - Turn 17: `https://formula420.com/contact/` -> success; Browsed https://formula420.com/contact/; 762 characters returned..
  - Turn 18: `https://www.amazon.com/s?k=Formula+420+Original+Cleaner` -> success; Browsed https://www.amazon.com/s?k=Formula+420+Original+Cleaner; 5000 characters returned..
  - Turn 19: `https://www.loveyourglass.com/` -> success; Browsed https://www.loveyourglass.com/; 5000 characters returned..

### BlueBonnet (AI-85351)

- Session: `AI-85351`. Status: `active`. Turns: 25. Raw tool calls: 25.
- Final sqld verdict: `CLOSED` / `MEDIUM`. Queue write: present; synced at `2026-07-14 05:43:47`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `BlueBonnet wholesale program` -> 10 results; generic/irrelevant per final verdict.
  - Turn 2: `BlueBonnet Faire wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 3: `BlueBonnet authorized distributor` -> 10 results; generic/irrelevant per final verdict.
  - Turn 4: `Bluebonnet Nutrition wholesale program` -> 10 results; generic/irrelevant per final verdict.
  - Turn 5: `Bluebonnet Nutrition Faire wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 6: `Bluebonnet Nutrition authorized distributor` -> 10 results; generic/irrelevant per final verdict.
  - Turn 7: `B001RM5HX0 BlueBonnet` -> 10 results; generic/irrelevant per final verdict.
  - Turn 8: `BlueBonnet brand vitamin supplement` -> 10 results; generic/irrelevant per final verdict.
  - Turn 9: `"Bluebonnet Nutrition" wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 10: `bluebonnetnutrition.com` -> 10 results; generic/irrelevant per final verdict.
  - Turn 11: `BlueBonnet` -> 10 results; generic/irrelevant per final verdict.
  - Turn 17: `Faire.com Bluebonnet Nutrition` -> 10 results; generic/irrelevant per final verdict.
  - Turn 18: `Bluebonnet Nutrition distributor wholesale account retailer` -> 10 results; generic/irrelevant per final verdict.
  - Turn 20: `bluebonnet nutrition retailer wholesale program dealer` -> 5 results; generic/irrelevant per final verdict.
  - Turn 23: `site:bluebonnetnutrition.com wholesale OR retailer OR trade OR dealer OR distributor` -> 0 results; no results.
  - Turn 24: `Bluebonnet Nutrition UNFI KeHE distributor` -> 10 results; generic/irrelevant per final verdict.
  - Turn 25: `"Bluebonnet Nutrition" wholesale account apply` -> 10 results; generic/irrelevant per final verdict.
- Browse calls:
  - Turn 12: `https://bluebonnetnutrition.com` -> success; Browsed https://bluebonnetnutrition.com; 5000 characters returned..
  - Turn 13: `https://www.amazon.com/dp/B001RM5HX0` -> success; Browsed https://www.amazon.com/dp/B001RM5HX0; 5000 characters returned..
  - Turn 14: `https://bluebonnetnutrition.com/pages/wholesale` -> success; Browsed https://bluebonnetnutrition.com/pages/wholesale; 3745 characters returned..
  - Turn 15: `https://bluebonnetnutrition.com/pages/contact` -> success; Browsed https://bluebonnetnutrition.com/pages/contact; 4258 characters returned..
  - Turn 16: `https://bluebonnetnutrition.com/pages/find-a-store` -> success; Browsed https://bluebonnetnutrition.com/pages/find-a-store; 3751 characters returned..
  - Turn 19: `https://www.faire.com/search?q=bluebonnet` -> success; Browsed https://www.faire.com/search?q=bluebonnet; 2916 characters returned..
  - Turn 21: `https://bluebonnetnutrition.com` -> success; Browsed https://bluebonnetnutrition.com; 5000 characters returned..
  - Turn 22: `https://bluebonnetnutrition.com/pages/about-us` -> success; Browsed https://bluebonnetnutrition.com/pages/about-us; 5000 characters returned..

### WYZE (wyze-research-001)

- Session: `wyze-research-001`. Status: `active`. Turns: 22. Raw tool calls: 22.
- Final sqld verdict: `ACCESSIBLE` / `HIGH`. Queue write: present; synced at `2026-07-14 05:43:47`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `WYZE wholesale program` -> 9 results; brand-matching candidate.
  - Turn 2: `WYZE Faire wholesale` -> 9 results; brand-matching candidate.
  - Turn 3: `WYZE authorized distributor` -> 9 results; brand-matching candidate.
  - Turn 4: `Wyze dealer program wholesale account` -> 9 results; brand-matching candidate.
  - Turn 5: `Wyze smart home wholesale bulk buy` -> 9 results; brand-matching candidate.
  - Turn 6: `site:wyze.com wholesale` -> 0 results; no results.
  - Turn 7: `"Wyze" "wholesale" distributor reseller` -> 9 results; brand-matching candidate.
  - Turn 8: `Wyze business program partnership B2B` -> 9 results; brand-matching candidate.
  - Turn 9: `Wyze MAP policy Amazon reseller restrictions` -> 9 results; brand-matching candidate.
  - Turn 10: `Wyze camera wholesale supplier distributor USA` -> 9 results; brand-matching candidate.
  - Turn 11: `Wyze "become a reseller" OR "reseller program" OR "partner program"` -> 9 results; brand-matching candidate.
  - Turn 13: `wyze.com/pages wholesale OR wyze.com/wholesale OR wyze.com/pages/business` -> 9 results; brand-matching candidate.
  - Turn 14: `Wyze wholesale account application retailer` -> 9 results; brand-matching candidate.
  - Turn 19: `"Wyze" "MAP policy" OR "minimum advertised price"` -> 9 results; brand-matching candidate.
  - Turn 20: `Wyze Faire wholesale marketplace` -> 9 results; brand-matching candidate.
  - Turn 21: `"Wyze" "reseller" "Amazon" restriction OR policy` -> 9 results; brand-matching candidate.
  - Turn 22: `"Wyze" "reseller agreement" OR "wholesale terms" OR "distribution agreement"` -> 9 results; brand-matching candidate.
- Browse calls:
  - Turn 12: `https://www.wyze.com/` -> success; Browsed https://www.wyze.com/; 5000 characters returned..
  - Turn 15: `https://www.wyze.com/pages/contact-us` -> success; Browsed https://www.wyze.com/pages/contact-us; 5000 characters returned..
  - Turn 16: `https://www.wyze.com/pages/business-partnership` -> success; Browsed https://www.wyze.com/pages/business-partnership; 5000 characters returned..
  - Turn 17: `https://www.wyze.com/pages/business` -> success; Browsed https://www.wyze.com/pages/business; 5000 characters returned..
  - Turn 18: `https://www.wyze.com/policies/terms-of-service` -> success; Browsed https://www.wyze.com/policies/terms-of-service; 5000 characters returned..

### test (test)

- Session: `test`. Status: `active`. Turns: 1. Raw tool calls: 1.
- Final sqld verdict: not present for this session/brand at report snapshot. No direct `record_verdict` tool result was logged.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `test` -> 10 results; brand-matching candidate.
- Browse calls:
  - None recorded.

### Wright Products (wright-products-research)

- Session: `wright-products-research`. Status: `active`. Turns: 23. Raw tool calls: 23.
- Final sqld verdict: not present for this session/brand at report snapshot. No direct `record_verdict` tool result was logged.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Wright Products wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `"Wright Products" wholesale dealer distributor` -> 10 results; brand-matching candidate.
  - Turn 3: `"Wright Products" storm door hardware wholesale` -> 10 results; brand-matching candidate.
  - Turn 4: `wrightproducts.com` -> 10 results; not independently classified.
  - Turn 5: `"Wright Products" brand hardware storm door closer` -> 10 results; brand-matching candidate.
  - Turn 6: `"Wright Products" storm door parts -university -credit -union -wright.edu` -> 10 results; brand-matching candidate.
  - Turn 7: `Wright Products Faire wholesale marketplace` -> 10 results; brand-matching candidate.
  - Turn 8: `"Wright" storm door closer wholesale B000BPB33C` -> 10 results; brand-matching candidate.
  - Turn 9: `B000BPB33C Wright Products storm door closer` -> 10 results; not independently classified.
  - Turn 10: `"Wright Products" Inc company hardware` -> 10 results; brand-matching candidate.
  - Turn 12: `"Wright Products" "storm door" site:wrightproducts.com OR site:wrightproducts.net` -> 0 results; no results.
  - Turn 13: `"Wright Products" "brand" hardware manufacturer` -> 10 results; brand-matching candidate.
  - Turn 16: `"Wright Products" storm door closer "company" manufacturer -wright.edu -"wright state"` -> 10 results; brand-matching candidate.
  - Turn 22: `"Wright Products" Faire.com wholesale` -> 10 results; brand-matching candidate.
- Browse calls:
  - Turn 11: `https://www.amazon.com/dp/B000BPB33C` -> success; Browsed https://www.amazon.com/dp/B000BPB33C; 5000 characters returned..
  - Turn 14: `https://wrightproductsinc.com` -> success; Browsed https://wrightproductsinc.com; 2224 characters returned..
  - Turn 15: `https://www.amazon.com/stores/WrightProducts/page/6F3BCE3C-812B-47A2-93B0-C79AAD95910E` -> success; Browsed https://www.amazon.com/stores/WrightProducts/page/6F3BCE3C-812B-47A2-93B0-C79AAD95910E; 5000 characters returned..
  - Turn 17: `https://wrightproducts.com` -> success; Browsed https://wrightproducts.com; 3998 characters returned..
  - Turn 18: `https://wrightproducts.com/about-us` -> success; Browsed https://wrightproducts.com/about-us; 2219 characters returned..
  - Turn 19: `https://wrightproducts.com/support` -> success; Cloudflare challenge detected.
  - Turn 20: `https://hamptonproducts.com` -> success; Browsed https://hamptonproducts.com; 4369 characters returned..
  - Turn 21: `https://hamptonproducts.com/contact-us` -> success; Browsed https://hamptonproducts.com/contact-us; 2877 characters returned..
  - Turn 23: `https://wrightproducts.com` -> success; Browsed https://wrightproducts.com; 3998 characters returned..

### MXL (AI-85812)

- Session: `AI-85812`. Status: `active`. Turns: 18. Raw tool calls: 18.
- Final sqld verdict: `MAYBE` / `MEDIUM`. Queue write: present; synced at `2026-07-14 05:43:48`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `MXL microphones wholesale program` -> 10 results; not independently classified.
  - Turn 2: `MXL microphones Faire wholesale` -> 10 results; not independently classified.
  - Turn 3: `MXL microphones authorized distributor` -> 10 results; not independently classified.
  - Turn 4: `"MXL" microphones wholesale dealer` -> 10 results; not independently classified.
  - Turn 5: `mxlmics.com wholesale dealer program` -> 10 results; not independently classified.
  - Turn 7: `MXL microphones dealer application` -> 10 results; not independently classified.
  - Turn 11: `MXL microphones Faire.com wholesale` -> 10 results; not independently classified.
  - Turn 12: `"MXL" microphones MAP policy` -> 10 results; not independently classified.
  - Turn 13: `Marshall Electronics MXL microphone wholesale dealer application` -> 10 results; not independently classified.
  - Turn 14: `site:faire.com MXL microphone` -> 0 results; no results.
  - Turn 16: `Marshall Electronics MXL wholesale dealer become authorized` -> 10 results; not independently classified.
  - Turn 17: `"Marshall Electronics" "MXL" dealer wholesale` -> 10 results; not independently classified.
  - Turn 18: `mars-cam.com MXL wholesale dealer` -> 10 results; not independently classified.
- Browse calls:
  - Turn 6: `https://mxlmics.com/` -> success; Browsed https://mxlmics.com/; 5000 characters returned..
  - Turn 8: `https://mxlmics.com/wheretobuy/` -> success; Browsed https://mxlmics.com/wheretobuy/; 4219 characters returned..
  - Turn 9: `https://mxlmics.com/company/` -> success; Browsed https://mxlmics.com/company/; 3673 characters returned..
  - Turn 10: `https://mxlmics.com/international-distributors/` -> success; Browsed https://mxlmics.com/international-distributors/; 5000 characters returned..
  - Turn 15: `https://www.fullcompass.com/brand/MXL-Microphones/` -> success; Cloudflare challenge detected.

### Sound Town (AI-85825)

- Session: `AI-85825`. Status: `active`. Turns: 12. Raw tool calls: 12.
- Final sqld verdict: `INCONCLUSIVE` / `LOW`. Queue write: present; synced at `2026-07-14 05:43:43`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Sound Town wholesale program` -> 10 results; generic/irrelevant per final verdict.
  - Turn 2: `"Sound Town" audio equipment wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 3: `"Sound Town" Faire wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 4: `"Sound Town" authorized distributor` -> 10 results; generic/irrelevant per final verdict.
  - Turn 5: `B086WY6Y34 Sound Town` -> 10 results; generic/irrelevant per final verdict.
  - Turn 6: `"Sound Town" PA speaker system brand` -> 10 results; generic/irrelevant per final verdict.
  - Turn 7: `soundtown.com OR soundtown audio` -> 10 results; generic/irrelevant per final verdict.
  - Turn 8: `Sound Town Amazon brand speakers` -> 10 results; generic/irrelevant per final verdict.
  - Turn 9: `"Sound Town" pro audio` -> 10 results; generic/irrelevant per final verdict.
  - Turn 10: `"Sound Town" site:amazon.com` -> 0 results; no results.
  - Turn 11: `SoundTown brand audio speaker` -> 10 results; generic/irrelevant per final verdict.
  - Turn 12: `"SoundTown" pro audio wholesale` -> 10 results; generic/irrelevant per final verdict.
- Browse calls:
  - None recorded.

### Satechi (AI-85822)

- Session: `AI-85822`. Status: `active`. Turns: 13. Raw tool calls: 13.
- Final sqld verdict: `INCONCLUSIVE` / `LOW`. Queue write: present; synced at `2026-07-14 05:43:46`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Satechi wholesale program` -> 10 results; generic/irrelevant per final verdict.
  - Turn 2: `Satechi Faire wholesale` -> 5 results; generic/irrelevant per final verdict.
  - Turn 3: `Satechi authorized distributor` -> 10 results; generic/irrelevant per final verdict.
  - Turn 4: `Satechi USB hub wholesale dealer` -> 10 results; generic/irrelevant per final verdict.
  - Turn 5: `Satechi wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 6: `Satechi reseller program` -> 1 results; generic/irrelevant per final verdict.
  - Turn 7: `satechi.com` -> 10 results; generic/irrelevant per final verdict.
  - Turn 8: `Satechi official website` -> 10 results; generic/irrelevant per final verdict.
  - Turn 9: `Satechi Amazon brand` -> 10 results; generic/irrelevant per final verdict.
  - Turn 10: `Satechi satechi.net` -> 10 results; generic/irrelevant per final verdict.
  - Turn 11: `"Satechi" brand electronics` -> 10 results; generic/irrelevant per final verdict.
  - Turn 12: `site:satechi.net wholesale` -> 0 results; no results.
  - Turn 13: `satechi` -> 10 results; generic/irrelevant per final verdict.
- Browse calls:
  - None recorded.

### Odd Sox (AI-85816)

- Session: `AI-85816`. Status: `active`. Turns: 27. Raw tool calls: 27.
- Final sqld verdict: `ACCESSIBLE` / `HIGH`. Queue write: present; synced at `2026-07-14 05:43:49`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Odd Sox wholesale program` -> 10 results; not independently classified.
  - Turn 2: `Odd Sox Faire wholesale` -> 10 results; not independently classified.
  - Turn 3: `Odd Sox authorized distributor` -> 10 results; not independently classified.
  - Turn 4: `"Odd Sox" socks wholesale` -> 10 results; not independently classified.
  - Turn 5: `"Odd Sox" Faire wholesale socks` -> 10 results; not independently classified.
  - Turn 6: `"Odd Sox" brand socks wholesale program` -> 10 results; not independently classified.
  - Turn 7: `odsox.com oddsox.com oddsox socks` -> 10 results; not independently classified.
  - Turn 8: `B0CJG398CP odd sox sock brand` -> 10 results; not independently classified.
  - Turn 9: `"odd sox" amazon brand` -> 10 results; not independently classified.
  - Turn 10: `"Odd Sox" -defiant -disorder -oppositional socks brand` -> 10 results; not independently classified.
  - Turn 11: `amazon B0CJG398CP` -> 10 results; not independently classified.
  - Turn 12: `odd sox sock brand wholesale` -> 10 results; not independently classified.
  - Turn 13: `"oddsox" socks` -> 10 results; not independently classified.
  - Turn 16: `oddsoxwholesale.com get started dealer` -> 10 results; not independently classified.
  - Turn 18: `oddsox.com wholesale apply` -> 10 results; not independently classified.
  - Turn 19: `"Odd Sox" Faire.com wholesale` -> 10 results; not independently classified.
  - Turn 22: `oddsox wholesale dealer application requirements` -> 10 results; not independently classified.
  - Turn 23: `"odd sox" "MAP policy" OR "minimum advertised price" OR "reseller policy"` -> 10 results; not independently classified.
  - Turn 24: `"oddsox" "MAP" OR "reseller" OR "authorized" OR "wholesale"` -> 10 results; not independently classified.
- Browse calls:
  - Turn 14: `https://www.oddsox.com/` -> success; Browsed https://www.oddsox.com/; 4350 characters returned..
  - Turn 15: `https://www.oddsoxwholesale.com/` -> success; Browsed https://www.oddsoxwholesale.com/; 220 characters returned..
  - Turn 17: `https://www.oddsoxwholesale.com/pages/become-a-dealer` -> success; Browsed https://www.oddsoxwholesale.com/pages/become-a-dealer; 58 characters returned..
  - Turn 20: `https://www.amazon.com/stores/ODDSOX/page/BC4CD0B0-0C28-4BA5-A26F-911A3512FBB9` -> success; Browsed https://www.amazon.com/stores/ODDSOX/page/BC4CD0B0-0C28-4BA5-A26F-911A3512FBB9; 5000 characters returned..
  - Turn 21: `https://www.oddsoxwholesale.com/account/register` -> success; Browsed https://www.oddsoxwholesale.com/account/register; 58 characters returned..
  - Turn 25: `https://www.oddsox.com/policies/terms-of-service` -> success; Browsed https://www.oddsox.com/policies/terms-of-service; 5000 characters returned..
  - Turn 26: `https://www.oddsoxwholesale.com/pages/support` -> success; Browsed https://www.oddsoxwholesale.com/pages/support; 58 characters returned..
  - Turn 27: `https://www.oddsox.com/pages/contact-us` -> success; Browsed https://www.oddsox.com/pages/contact-us; 3858 characters returned..

### MY CREATIVE CAMP (AI-85813)

- Session: `AI-85813`. Status: `active`. Turns: 16. Raw tool calls: 16.
- Final sqld verdict: `INCONCLUSIVE` / `LOW`. Queue write: present; synced at `2026-07-14 05:43:46`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `"MY CREATIVE CAMP" wholesale program` -> 10 results; generic/irrelevant per final verdict.
  - Turn 2: `"MY CREATIVE CAMP" Faire wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 3: `"MY CREATIVE CAMP" authorized distributor` -> 10 results; generic/irrelevant per final verdict.
  - Turn 4: `"My Creative Camp" brand craft` -> 10 results; generic/irrelevant per final verdict.
  - Turn 5: `B08QMM2MND My Creative Camp` -> 10 results; generic/irrelevant per final verdict.
  - Turn 6: `MY CREATIVE CAMP wholesale craft art supplies` -> 10 results; generic/irrelevant per final verdict.
  - Turn 7: `"My Creative Camp" product` -> 10 results; generic/irrelevant per final verdict.
  - Turn 8: `mycreativecamp.com` -> 10 results; generic/irrelevant per final verdict.
  - Turn 9: `B08QMM2MND Amazon` -> 10 results; generic/irrelevant per final verdict.
  - Turn 10: `"creative camp" brand wholesale craft` -> 10 results; generic/irrelevant per final verdict.
  - Turn 11: `"my creative camp" amazon` -> 10 results; generic/irrelevant per final verdict.
  - Turn 12: `"mycreativecamp"` -> 8 results; generic/irrelevant per final verdict.
  - Turn 13: `creativation "my creative camp"` -> 10 results; generic/irrelevant per final verdict.
  - Turn 14: `"creative camp" craft kit wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 15: `mycreativecamp` -> 10 results; generic/irrelevant per final verdict.
  - Turn 16: `"my creative camp" "creativity" "craft"` -> 10 results; generic/irrelevant per final verdict.
- Browse calls:
  - None recorded.

### Duck Brand (worker-duck-brand)

- Session: `duck_brand_research`. Status: `active`. Turns: 8. Raw tool calls: 8.
- Final sqld verdict: `INCONCLUSIVE` / `LOW`. Queue write: present; synced at `2026-07-14 05:43:45`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Duck Brand wholesale program` -> 10 results; generic/irrelevant per final verdict.
  - Turn 2: `"Duck Brand" duct tape wholesale program distributor` -> 10 results; generic/irrelevant per final verdict.
  - Turn 3: `Shurtape Duck Brand wholesale distributor` -> 10 results; generic/irrelevant per final verdict.
  - Turn 4: `duckbrand.com` -> 10 results; generic/irrelevant per final verdict.
  - Turn 5: `"Duck Brand" Faire wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 6: `"Duck Brand" authorized distributor` -> 10 results; generic/irrelevant per final verdict.
  - Turn 8: `ShurTech Brands LLC wholesale distributor program` -> 10 results; generic/irrelevant per final verdict.
- Browse calls:
  - Turn 7: `https://www.duckbrand.com` -> all CDP ports occupied; browse_page failed for https://www.duckbrand.com: All CDP ports are occupied; wait for a worker batch to finish.

### Vanicream (vanicream-worker)

- Session: `vanicream-research`. Status: `active`. Turns: 22. Raw tool calls: 22.
- Final sqld verdict: `CLOSED` / `HIGH`. Queue write: present; synced at `2026-07-14 05:43:53`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Vanicream wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `Vanicream Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `Vanicream authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 4: `Vanicream wholesale account reseller` -> 10 results; brand-matching candidate.
  - Turn 5: `Vanicream MAP policy Amazon reseller restrictions` -> 10 results; brand-matching candidate.
  - Turn 6: `Vanicream professional distributor dermatologist wholesale` -> 10 results; brand-matching candidate.
  - Turn 7: `site:vanicream.com wholesale dealer retailer` -> 0 results; no results.
  - Turn 8: `Pharmaceutical Specialties Inc Vanicream wholesale order` -> 10 results; not independently classified.
  - Turn 10: `"Vanicream" "wholesale" skincare brand` -> 10 results; brand-matching candidate.
  - Turn 13: `Vanicream Faire.com wholesale marketplace` -> 10 results; brand-matching candidate.
  - Turn 14: `"Vanicream" distributor account resell` -> 10 results; brand-matching candidate.
  - Turn 16: `"Pharmaceutical Specialties" Vanicream wholesale account reseller program` -> 10 results; not independently classified.
  - Turn 17: `"Vanicream" reseller program wholesale skincare` -> 10 results; brand-matching candidate.
  - Turn 18: `Vanicream Amazon brand registry reseller restrictions` -> 10 results; brand-matching candidate.
  - Turn 19: `faire.com Vanicream skincare wholesale` -> 10 results; not independently classified.
  - Turn 20: `"Vanicream" "wholesale" "distributor" pharmacy` -> 10 results; brand-matching candidate.
  - Turn 21: `"Vanicream" "authorized" "retailer" "Amazon" policy` -> 10 results; brand-matching candidate.
  - Turn 22: `"Vanicream" "professional" "order" "account" skincare wholesale` -> 10 results; brand-matching candidate.
- Browse calls:
  - Turn 9: `https://www.vanicream.com/` -> success; Browsed https://www.vanicream.com/; 4185 characters returned..
  - Turn 11: `https://www.vanicream.com/for-professionals` -> success; Browsed https://www.vanicream.com/for-professionals; 4564 characters returned..
  - Turn 12: `https://www.vanicream.com/where-to-buy` -> success; Browsed https://www.vanicream.com/where-to-buy; 3774 characters returned..
  - Turn 15: `https://www.vanicream.com/contact-us` -> success; Browsed https://www.vanicream.com/contact-us; 4034 characters returned..

### Vital Proteins (vital-proteins-01)

- Session: `vital-proteins-research`. Status: `active`. Turns: 13. Raw tool calls: 13.
- Final sqld verdict: `ACCESSIBLE` / `HIGH`. Queue write: present; synced at `2026-07-14 05:43:53`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Vital Proteins wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `"Vital Proteins" wholesale program distributor` -> 10 results; brand-matching candidate.
  - Turn 3: `Vital Proteins collagen wholesale` -> 10 results; brand-matching candidate.
  - Turn 4: `Vital Proteins Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 5: `vitalproteins.com wholesale retailer account` -> 10 results; brand-matching candidate.
  - Turn 6: `"Vital Proteins" authorized distributor reseller program` -> 10 results; brand-matching candidate.
  - Turn 7: `Vital Proteins become a retailer` -> 10 results; brand-matching candidate.
  - Turn 8: `Vital Proteins MAP policy Amazon reseller restrictions` -> 10 results; brand-matching candidate.
  - Turn 13: `Vital Proteins Nestl? MAP policy reseller agreement terms` -> 10 results; brand-matching candidate.
- Browse calls:
  - Turn 9: `https://www.vitalproteins.com/` -> success; Browsed https://www.vitalproteins.com/; 5000 characters returned..
  - Turn 10: `https://wholesale.vitalproteins.com/` -> success; Browsed https://wholesale.vitalproteins.com/; 1317 characters returned..
  - Turn 11: `https://amsb2b.nestle.com/NHSC-VP-NUUN` -> success; Browsed https://amsb2b.nestle.com/NHSC-VP-NUUN; 1574 characters returned..
  - Turn 12: `https://nestle-swbzl.formstack.com/forms/wholesale_account_inquiry` -> success; Browsed https://nestle-swbzl.formstack.com/forms/wholesale_account_inquiry; 1231 characters returned..

### Zotz (zotz-research-001)

- Session: `zotz-research-001`. Status: `active`. Turns: 18. Raw tool calls: 18.
- Final sqld verdict: `ACCESSIBLE` / `HIGH`. Queue write: present; synced at `2026-07-14 05:43:52`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Zotz wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `Zotz candy Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `Zotz candy authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 4: `Andre Prost Zotz wholesale account` -> 10 results; not independently classified.
  - Turn 5: `Zotz candy bulk wholesale purchase` -> 10 results; brand-matching candidate.
  - Turn 6: `Andre Prost Inc candy distributor wholesale` -> 10 results; not independently classified.
  - Turn 7: `Zotz candy Amazon reseller restrictions MAP policy` -> 10 results; brand-matching candidate.
  - Turn 8: `"Andre Prost" Zotz candy distributor wholesale account` -> 10 results; not independently classified.
  - Turn 9: `zotzpower.com wholesale` -> 10 results; not independently classified.
  - Turn 10: `andreprost.com Zotz` -> 10 results; not independently classified.
  - Turn 11: `site:zotzpower.com wholesale dealer` -> 0 results; no results.
  - Turn 12: `"Andre Prost" candy distributor` -> 10 results; not independently classified.
  - Turn 13: `Zotz candy wholesale supplier USA` -> 10 results; brand-matching candidate.
  - Turn 14: `Zotz candy site:faire.com` -> 0 results; no results.
  - Turn 15: `Zotz candy distributor Andre Prost Inc wholesale` -> 10 results; brand-matching candidate.
- Browse calls:
  - Turn 16: `https://zotzpower.com/` -> success; Browsed https://zotzpower.com/; 4999 characters returned..
  - Turn 17: `https://www.faire.com/direct/andrepostinc` -> success; Browsed https://www.faire.com/direct/andrepostinc; 4387 characters returned..
  - Turn 18: `https://zotzpower.com/#Contact` -> success; Browsed https://zotzpower.com/#Contact; 4999 characters returned..

### It's Sew Emma (itssewemma_researcher)

- Session: `itssewemma_researcher`. Status: `active`. Turns: 10. Raw tool calls: 10.
- Final sqld verdict: `INCONCLUSIVE` / `LOW`. Queue write: present; synced at `2026-07-14 05:43:51`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `"It's Sew Emma" wholesale program` -> 10 results; not independently classified.
  - Turn 2: `"It's Sew Emma" Faire wholesale` -> 10 results; not independently classified.
  - Turn 3: `"It's Sew Emma" authorized distributor` -> 10 results; not independently classified.
  - Turn 4: `"It's Sew Emma" quilting patterns wholesale` -> 10 results; not independently classified.
  - Turn 5: `"Its Sew Emma" sewing wholesale` -> 9 results; not independently classified.
  - Turn 6: `ItsSewEmma brand wholesale` -> 10 results; brand-matching candidate.
  - Turn 7: `ASIN 173493168X sewing pattern` -> 10 results; not independently classified.
  - Turn 8: `"Sew Emma" quilting wholesale` -> 10 results; not independently classified.
- Browse calls:
  - Turn 9: `https://www.itssewemma.com/` -> CDP browser-context protocol error on 9226; browse_page failed for https://www.itssewemma.com/: BrowserType.connect_over_cdp: Protocol error (Browser.setDownloadBehavior): Browser context management is not supported. Call log:   - <ws preparing> retrieving websocket url from http://localhost:9226   - <w.
  - Turn 10: `https://www.itssewemma.com/` -> CDP browser-context protocol error on 9226; browse_page failed for https://www.itssewemma.com/: BrowserType.connect_over_cdp: Protocol error (Browser.setDownloadBehavior): Browser context management is not supported. Call log:   - <ws preparing> retrieving websocket url from http://localhost:9226   - <w.

### Ivtivfu (ivtivfu-worker)

- Session: `ivtivfu-worker`. Status: `active`. Turns: 8. Raw tool calls: 8.
- Final sqld verdict: `INCONCLUSIVE` / `HIGH`. Queue write: present; synced at `2026-07-14 05:43:50`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Ivtivfu wholesale program` -> 10 results; generic/irrelevant per final verdict.
  - Turn 2: `Ivtivfu Faire wholesale` -> 9 results; generic/irrelevant per final verdict.
  - Turn 3: `Ivtivfu authorized distributor` -> 10 results; generic/irrelevant per final verdict.
  - Turn 4: `Ivtivfu brand` -> 10 results; generic/irrelevant per final verdict.
  - Turn 5: `Ivtivfu Amazon ASIN B0CWXMN6NX` -> 10 results; generic/irrelevant per final verdict.
  - Turn 6: `B0CWXMN6NX` -> 10 results; generic/irrelevant per final verdict.
  - Turn 7: `"Ivtivfu" product` -> 10 results; generic/irrelevant per final verdict.
- Browse calls:
  - Turn 8: `https://www.amazon.com/dp/B0CWXMN6NX` -> CDP browser-context protocol error on 9226; browse_page failed for https://www.amazon.com/dp/B0CWXMN6NX: BrowserType.connect_over_cdp: Protocol error (Browser.setDownloadBehavior): Browser context management is not supported. Call log:   - <ws preparing> retrieving websocket url from http://localhost:92.

### JT Eaton (jt-eaton-research)

- Session: `jt-eaton-research`. Status: `active`. Turns: 12. Raw tool calls: 12.
- Final sqld verdict: `INCONCLUSIVE` / `LOW`. Queue write: present; synced at `2026-07-14 05:43:51`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `JT Eaton wholesale program` -> 10 results; not independently classified.
  - Turn 2: `JT Eaton Faire wholesale` -> 10 results; not independently classified.
  - Turn 3: `JT Eaton authorized distributor` -> 10 results; not independently classified.
  - Turn 4: `"J.T. Eaton" pest control wholesale` -> 10 results; not independently classified.
  - Turn 5: `"J.T. Eaton" Faire` -> 10 results; not independently classified.
  - Turn 6: `"J.T. Eaton" authorized distributor pest control` -> 10 results; not independently classified.
  - Turn 7: `JT Eaton pest control products wholesale` -> 10 results; not independently classified.
  - Turn 8: `jteaton.com wholesale` -> 10 results; brand-matching candidate.
  - Turn 9: `"JT Eaton" pest control company` -> 10 results; not independently classified.
- Browse calls:
  - Turn 10: `https://www.jteaton.com/` -> CDP browser-context protocol error on 9226; browse_page failed for https://www.jteaton.com/: BrowserType.connect_over_cdp: Protocol error (Browser.setDownloadBehavior): Browser context management is not supported. Call log:   - <ws preparing> retrieving websocket url from http://localhost:9226   - <ws c.
  - Turn 11: `https://jteatonpmp.com/` -> CDP browser-context protocol error on 9226; browse_page failed for https://jteatonpmp.com/: BrowserType.connect_over_cdp: Protocol error (Browser.setDownloadBehavior): Browser context management is not supported. Call log:   - <ws preparing> retrieving websocket url from http://localhost:9226   - <ws co.
  - Turn 12: `https://www.jteaton.com/` -> CDP browser-context protocol error on 9226; browse_page failed for https://www.jteaton.com/: BrowserType.connect_over_cdp: Protocol error (Browser.setDownloadBehavior): Browser context management is not supported. Call log:   - <ws preparing> retrieving websocket url from http://localhost:9226   - <ws c.

### https://www.agmglobalvision.com/pages/dealer-locator-us (AI-85371)

- Session: `AI-85371`. Status: `active`. Turns: 17. Raw tool calls: 17.
- Final sqld verdict: `ACCESSIBLE` / `HIGH`. Queue write: present; synced at `2026-07-14 05:43:54`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `AGM Global Vision wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `AGM Global Vision Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `AGM Global Vision authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 4: `"AGM Global Vision" dealer program wholesale` -> 10 results; brand-matching candidate.
  - Turn 5: `"AGM Global Vision" dealer application reseller` -> 10 results; brand-matching candidate.
  - Turn 6: `"AGM Global Vision" dealer login partner` -> 10 results; brand-matching candidate.
  - Turn 7: `"AGM Global Vision" site:faire.com` -> 0 results; no results.
  - Turn 10: `"AGM Global Vision" Amazon reseller policy MAP` -> 10 results; brand-matching candidate.
  - Turn 11: `"AGM Global Vision" export policy reseller restrictions` -> 10 results; brand-matching candidate.
  - Turn 13: `"AGM Global Vision" Amazon` -> 10 results; brand-matching candidate.
  - Turn 14: `site:amazon.com "AGM Global Vision"` -> 0 results; no results.
  - Turn 15: `AGM Global Vision on Amazon` -> 10 results; brand-matching candidate.
  - Turn 16: `"AGM" thermal night vision dealer program wholesale authorized` -> 10 results; brand-matching candidate.
- Browse calls:
  - Turn 8: `https://www.agmglobalvision.com/` -> success; Browsed https://www.agmglobalvision.com/; 5000 characters returned..
  - Turn 9: `https://www.agmglobalvision.com/pages/dealer-sign-up` -> success; Browsed https://www.agmglobalvision.com/pages/dealer-sign-up; 4702 characters returned..
  - Turn 12: `https://www.agmglobalvision.com/pages/export-policy` -> success; Browsed https://www.agmglobalvision.com/pages/export-policy; 4460 characters returned..
  - Turn 17: `https://www.agmglobalvision.com/pages/dealer-locator-us` -> success; Browsed https://www.agmglobalvision.com/pages/dealer-locator-us; 3539 characters returned..

### Howard Leight (AI-85361)

- Session: `AI-85361`. Status: `active`. Turns: 25. Raw tool calls: 25.
- Final sqld verdict: `MAYBE` / `MEDIUM`. Queue write: present; synced at `2026-07-14 05:43:56`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Howard Leight wholesale program` -> 10 results; generic/irrelevant per final verdict.
  - Turn 2: `Howard Leight Faire wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 3: `Howard Leight authorized distributor` -> 10 results; generic/irrelevant per final verdict.
  - Turn 4: `"Howard Leight" hearing protection wholesale distributor` -> 10 results; generic/irrelevant per final verdict.
  - Turn 5: `"Howard Leight" Honeywell safety dealer account` -> 10 results; generic/irrelevant per final verdict.
  - Turn 6: `howardleight.com hearing safety` -> 10 results; generic/irrelevant per final verdict.
  - Turn 7: `"Howard Leight" earplugs wholesale Amazon reseller` -> 10 results; generic/irrelevant per final verdict.
  - Turn 8: `Honeywell hearing protection wholesale program reseller` -> 10 results; generic/irrelevant per final verdict.
  - Turn 9: `"Howard Leight" "distributor" safety supply` -> 10 results; generic/irrelevant per final verdict.
  - Turn 10: `"Howard Leight" earplugs Amazon Honeywell safety PPE` -> 10 results; generic/irrelevant per final verdict.
  - Turn 11: `site:howardleight.com` -> 0 results; no results.
  - Turn 12: `Howard Leight hearing protection B2B wholesale account` -> 10 results; generic/irrelevant per final verdict.
  - Turn 13: `Honeywell personal protective equipment wholesale dealer application` -> 10 results; generic/irrelevant per final verdict.
  - Turn 17: `Honeywell MAP policy Amazon reseller restrictions Howard Leight` -> 10 results; generic/irrelevant per final verdict.
  - Turn 18: `Honeywell distributor application small business reseller` -> 10 results; generic/irrelevant per final verdict.
  - Turn 21: `"Honeywell" "Howard Leight" authorized reseller program become distributor` -> 10 results; generic/irrelevant per final verdict.
  - Turn 24: `"Howard Leight" "wholesale" "safety" -university -Wikipedia` -> 10 results; generic/irrelevant per final verdict.
  - Turn 25: `"Howard Leight by Honeywell" safety` -> 10 results; generic/irrelevant per final verdict.
- Browse calls:
  - Turn 14: `https://safety.honeywell.com` -> site HTTP/2 error; browse_page failed for https://safety.honeywell.com: Page.goto: net::ERR_HTTP2_PROTOCOL_ERROR at https://safety.honeywell.com/ Call log:   - navigating to "https://safety.honeywell.com/", waiting until "domcontentloaded".
  - Turn 15: `https://www.honeywellsafety.com` -> success; Browsed https://www.honeywellsafety.com; 178 characters returned..
  - Turn 16: `https://www.honeywell.com/us/en/press/2020/07/honeywell-launches-new-online-portal-for-small-businesses` -> site HTTP/2 error; browse_page failed for https://www.honeywell.com/us/en/press/2020/07/honeywell-launches-new-online-portal-for-small-businesses: Page.goto: net::ERR_HTTP2_PROTOCOL_ERROR at https://www.honeywell.com/us/en/press/2020/07/honeywell-launches-new-online-portal-for-s.
  - Turn 19: `https://www.faire.com/search?q=howard+leight` -> success; Browsed https://www.faire.com/search?q=howard+leight; 3192 characters returned..
  - Turn 20: `https://www.faire.com/brand/b_wrskgvjfb6` -> success; Browsed https://www.faire.com/brand/b_wrskgvjfb6; 5000 characters returned..
  - Turn 22: `https://www.honeywell.com/us/en/become-a-distributor` -> site HTTP/2 error; browse_page failed for https://www.honeywell.com/us/en/become-a-distributor: Page.goto: net::ERR_HTTP2_PROTOCOL_ERROR at https://www.honeywell.com/us/en/become-a-distributor Call log:   - navigating to "https://www.honeywell.com/us/en/become-a-distributor", wa.
  - Turn 23: `https://www.honeywell.com/us/en/suppliers` -> site HTTP/2 error; browse_page failed for https://www.honeywell.com/us/en/suppliers: Page.goto: net::ERR_HTTP2_PROTOCOL_ERROR at https://www.honeywell.com/us/en/suppliers Call log:   - navigating to "https://www.honeywell.com/us/en/suppliers", waiting until "domcontentloaded".

### Nuun (AI-85363)

- Session: `AI-85363`. Status: `active`. Turns: 22. Raw tool calls: 22.
- Final sqld verdict: `MAYBE` / `MEDIUM`. Queue write: present; synced at `2026-07-14 05:43:55`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Nuun wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `Nuun Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `Nuun authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 4: `Nuun wholesale account retailer application` -> 10 results; brand-matching candidate.
  - Turn 5: `Nuun hydration wholesale dealer program` -> 10 results; brand-matching candidate.
  - Turn 6: `site:nuunlife.com wholesale` -> 0 results; no results.
  - Turn 7: `Nuun hydration "wholesale" "distributor"` -> 10 results; brand-matching candidate.
  - Turn 8: `Nuun Faire.com wholesale` -> 10 results; brand-matching candidate.
  - Turn 9: `"nuun" "wholesale" "retailer" "apply"` -> 10 results; brand-matching candidate.
  - Turn 10: `nuunlife.com wholesale dealer login` -> 10 results; not independently classified.
  - Turn 11: `faire.com direct checkout nuun` -> 10 results; not independently classified.
  - Turn 12: `"Nuun Hydration" wholesale distributor retailer account` -> 10 results; brand-matching candidate.
  - Turn 15: `Nuun Amazon MAP policy reseller restrictions` -> 10 results; brand-matching candidate.
  - Turn 16: `site:faire.com Nuun` -> 0 results; no results.
  - Turn 17: `"Become a Nuun Wholesaler" OR "Nuun wholesale program"` -> 10 results; not independently classified.
  - Turn 18: `Nuun hydration reseller policy terms conditions` -> 10 results; brand-matching candidate.
  - Turn 20: `site:nuunlife.com "terms" OR "conditions" OR "policy"` -> 0 results; no results.
  - Turn 22: `"Nuun" Amazon "authorized reseller" OR "unauthorized"` -> 10 results; brand-matching candidate.
- Browse calls:
  - Turn 13: `https://nuunlife.com/` -> success; Browsed https://nuunlife.com/; 5000 characters returned..
  - Turn 14: `https://nuunlife.com/pages/contact` -> success; Browsed https://nuunlife.com/pages/contact; 5000 characters returned..
  - Turn 19: `https://nuunlife.com/pages/faq` -> success; Browsed https://nuunlife.com/pages/faq; 5000 characters returned..
  - Turn 21: `https://nuunlife.com/policies/terms-of-service` -> success; Browsed https://nuunlife.com/policies/terms-of-service; 5000 characters returned..

### Ullman (AI-85370)

- Session: `AI-85370`. Status: `active`. Turns: 9. Raw tool calls: 9.
- Final sqld verdict: `ACCESSIBLE` / `HIGH`. Queue write: present; synced at `2026-07-14 05:43:54`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Ullman wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `Ullman Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `Ullman authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 8: `Ullman Devices MAP policy Amazon reseller` -> 10 results; brand-matching candidate.
- Browse calls:
  - Turn 4: `https://ullmandevices.com/` -> success; Browsed https://ullmandevices.com/; 3329 characters returned..
  - Turn 5: `https://ullmandevices.com/pages/become-a-distributor` -> success; Browsed https://ullmandevices.com/pages/become-a-distributor; 2466 characters returned..
  - Turn 6: `https://ullmandevices.com/pages/where-to-buy` -> success; Browsed https://ullmandevices.com/pages/where-to-buy; 3077 characters returned..
  - Turn 7: `https://ullmandevices.com/pages/contact-us` -> success; Browsed https://ullmandevices.com/pages/contact-us; 2507 characters returned..
  - Turn 9: `https://ullmandevices.com/pages/about` -> success; Browsed https://ullmandevices.com/pages/about; 3054 characters returned..

### SOLO (AI-85368)

- Session: `AI-85368`. Status: `active`. Turns: 20. Raw tool calls: 20.
- Final sqld verdict: `CLOSED` / `HIGH`. Queue write: present; synced at `2026-07-14 05:43:57`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `SOLO wholesale program` -> 7 results; not independently classified.
  - Turn 2: `SOLO Faire wholesale` -> 7 results; not independently classified.
  - Turn 3: `SOLO authorized distributor` -> 7 results; not independently classified.
  - Turn 4: `SOLO cups brand wholesale program distributor` -> 7 results; not independently classified.
  - Turn 5: `"SOLO" brand tableware wholesale Faire` -> 7 results; not independently classified.
  - Turn 6: `B00KY8R1AA product type` -> 10 results; not independently classified.
  - Turn 7: `solo cup company wholesale reseller program` -> 7 results; not independently classified.
  - Turn 9: `www.solocup.com wholesale` -> 10 results; not independently classified.
  - Turn 10: `"SOLO" "cake and pastry filling" brand wholesale` -> 7 results; not independently classified.
  - Turn 11: `SOLO baking filling wholesale Faire` -> 7 results; not independently classified.
  - Turn 13: `Solo brand pastry filling owned by company` -> 7 results; not independently classified.
- Browse calls:
  - Turn 8: `https://www.amazon.com/dp/B00KY8R1AA` -> success; Browsed https://www.amazon.com/dp/B00KY8R1AA; 5000 characters returned..
  - Turn 12: `https://www.solofoods.com` -> success; Browsed https://www.solofoods.com; 3986 characters returned..
  - Turn 14: `https://shopsolofoods.com` -> success; Browsed https://shopsolofoods.com; 2095 characters returned..
  - Turn 15: `https://www.solofoods.com/where-to-find` -> success; Browsed https://www.solofoods.com/where-to-find; 2344 characters returned..
  - Turn 16: `https://www.faire.com/search?q=solo%20foods` -> success; Browsed https://www.faire.com/search?q=solo%20foods; 2972 characters returned..
  - Turn 17: `https://www.solofoods.com/contact` -> success; Browsed https://www.solofoods.com/contact; 1820 characters returned..
  - Turn 18: `https://solofoods.com/faqs` -> success; Browsed https://solofoods.com/faqs; 2452 characters returned..
  - Turn 19: `https://www.sacofoods.com` -> success; Browsed https://www.sacofoods.com; 3182 characters returned..
  - Turn 20: `https://www.sacofoods.com/contact-us/` -> success; Browsed https://www.sacofoods.com/contact-us/; 4019 characters returned..

### Jack's Classic (JackClassic-001)

- Session: `JackClassic-001`. Status: `active`. Turns: 17. Raw tool calls: 17.
- Final sqld verdict: not present for this session/brand at report snapshot. No direct `record_verdict` tool result was logged.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Jack's Classic wholesale program` -> 10 results; not independently classified.
  - Turn 2: `Jack's Classic fertilizer wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `Jack's Classic Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 4: `JR Peters Jack's Classic plant fertilizer wholesale distributor` -> 10 results; not independently classified.
  - Turn 5: `"Jack's Classic" fertilizer authorized dealer` -> 10 results; brand-matching candidate.
  - Turn 6: `B001REA5NK Jack's Classic` -> 10 results; not independently classified.
  - Turn 7: `jrpeters.com Jack's Classic wholesale` -> 10 results; not independently classified.
  - Turn 10: `"Jack's Classic" fertilizer distributor dealer` -> 10 results; brand-matching candidate.
  - Turn 11: `"JR Peters" wholesale account dealer application` -> 10 results; not independently classified.
  - Turn 12: `jrpeters.com become a dealer retailer distributor` -> 10 results; not independently classified.
  - Turn 13: `jrpeters.com contact wholesale` -> 10 results; not independently classified.
  - Turn 14: `jrpeters.com contact page` -> 10 results; not independently classified.
  - Turn 15: `"Jack's Classic" Amazon MAP policy restriction` -> 10 results; brand-matching candidate.
  - Turn 16: `site:faire.com "JR Peters" OR "Jack's Classic"` -> 0 results; no results.
  - Turn 17: `"JR Peters" distributor network` -> 10 results; not independently classified.
- Browse calls:
  - Turn 8: `https://www.jrpeters.com/` -> CDP browser-context protocol error on 9226; browse_page failed for https://www.jrpeters.com/: BrowserType.connect_over_cdp: Protocol error (Browser.setDownloadBehavior): Browser context management is not supported. Call log:   - <ws preparing> retrieving websocket url from http://localhost:9226   - <ws .
  - Turn 9: `https://www.jrpeters.com/` -> all CDP ports occupied; browse_page failed for https://www.jrpeters.com/: All CDP ports are occupied; wait for a worker batch to finish.

### Weider (AI-85830)

- Session: `AI-85830`. Status: `active`. Turns: 24. Raw tool calls: 24.
- Final sqld verdict: `CLOSED` / `HIGH`. Queue write: present; synced at `2026-07-14 05:44:00`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Weider wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `Weider Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `Weider authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 4: `B0DK3Z6XL4 Weider` -> 10 results; not independently classified.
  - Turn 5: `Weider Amazon MAP policy reseller restrictions` -> 10 results; brand-matching candidate.
  - Turn 6: `Weider dealer wholesale account apply` -> 10 results; brand-matching candidate.
  - Turn 10: `Weider wholesale fitness equipment distributor` -> 10 results; brand-matching candidate.
  - Turn 13: `"Weider" "wholesale" "dealer" "apply" -amazon` -> 10 results; brand-matching candidate.
  - Turn 14: `"B0DK3Z6XL4" product` -> 10 results; not independently classified.
  - Turn 15: `Weider Global Nutrition wholesale bulk reseller program` -> 10 results; brand-matching candidate.
  - Turn 16: `site:faire.com Weider` -> 0 results; no results.
  - Turn 17: `Weider brand owned by parent company fitness equipment` -> 10 results; brand-matching candidate.
  - Turn 18: `Weider fitness equipment distributor wholesale account USA` -> 10 results; brand-matching candidate.
  - Turn 20: `"Weider" "authorized reseller" OR "wholesale application" OR "dealer portal"` -> 10 results; brand-matching candidate.
  - Turn 21: `"Weider Global Nutrition" wholesale reseller distributor program` -> 10 results; brand-matching candidate.
  - Turn 24: `weider.com wholesale account bulk order` -> 10 results; brand-matching candidate.
- Browse calls:
  - Turn 7: `https://www.weidersports.com/` -> success; Browsed https://www.weidersports.com/; 5000 characters returned..
  - Turn 8: `https://www.weider.com/` -> success; Browsed https://www.weider.com/; 3581 characters returned..
  - Turn 9: `https://theweiderhomegym.com/` -> success; Browsed https://theweiderhomegym.com/; 2766 characters returned..
  - Turn 11: `https://www.weider.com/pages/international-distributors` -> success; Browsed https://www.weider.com/pages/international-distributors; 2463 characters returned..
  - Turn 12: `https://www.weider.com/pages/our-partners` -> success; Browsed https://www.weider.com/pages/our-partners; 2502 characters returned..
  - Turn 19: `https://www.amazon.com/dp/B0DK3Z6XL4` -> success; Browsed https://www.amazon.com/dp/B0DK3Z6XL4; 5000 characters returned..
  - Turn 22: `https://www.amazon.com/stores/Weider/page/1A1B372C-0C9F-46B0-B42E-7B7F1EE9D6C7` -> success; Browsed https://www.amazon.com/stores/Weider/page/1A1B372C-0C9F-46B0-B42E-7B7F1EE9D6C7; 5000 characters returned..
  - Turn 23: `https://www.weider.com/pages/about-us` -> success; Browsed https://www.weider.com/pages/about-us; 4027 characters returned..

### Strymon (AI-85826)

- Session: `AI-85826`. Status: `active`. Turns: 17. Raw tool calls: 17.
- Final sqld verdict: `MAYBE` / `MEDIUM`. Queue write: present; synced at `2026-07-14 05:43:57`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Strymon wholesale program dealer application` -> 10 results; not independently classified.
  - Turn 2: `Strymon Faire wholesale` -> 10 results; not independently classified.
  - Turn 3: `Strymon authorized distributor dealer` -> 10 results; not independently classified.
  - Turn 4: `Strymon guitar pedals wholesale dealer program` -> 10 results; not independently classified.
  - Turn 5: `Strymon dealers retailers distributors` -> 10 results; not independently classified.
  - Turn 6: `"strymon" wholesale` -> 7 results; not independently classified.
  - Turn 11: `Strymon MAP policy Amazon reseller restrictions` -> 10 results; not independently classified.
  - Turn 13: `Strymon Faire wholesale marketplace` -> 10 results; not independently classified.
  - Turn 14: `Strymon authorized dealer requirements MAP policy` -> 10 results; not independently classified.
- Browse calls:
  - Turn 7: `https://www.strymon.net` -> success; Browsed https://www.strymon.net; 3349 characters returned..
  - Turn 8: `https://www.strymon.net/dealers/` -> success; Browsed https://www.strymon.net/dealers/; 2548 characters returned..
  - Turn 9: `https://www.strymon.net/contact/` -> success; Browsed https://www.strymon.net/contact/; 3127 characters returned..
  - Turn 10: `https://www.strymon.net/contact/dealers/` -> success; Browsed https://www.strymon.net/contact/dealers/; 2333 characters returned..
  - Turn 12: `https://www.strymon.net/terms-conditions/` -> success; Browsed https://www.strymon.net/terms-conditions/; 5000 characters returned..
  - Turn 15: `https://www.faire.com/search?q=strymon` -> success; Browsed https://www.faire.com/search?q=strymon; 2825 characters returned..
  - Turn 16: `https://www.amazon.com/s?k=Strymon` -> success; Browsed https://www.amazon.com/s?k=Strymon; 5000 characters returned..
  - Turn 17: `https://www.strymon.net/shop/` -> success; Browsed https://www.strymon.net/shop/; 5000 characters returned..

### Super (AI-85827)

- Session: `AI-85827`. Status: `active`. Turns: 20. Raw tool calls: 20.
- Final sqld verdict: `PRIVATE_LABEL` / `HIGH`. Queue write: present; synced at `2026-07-14 05:43:58`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `B00CMNIG68 Super ASIN product` -> 10 results; not independently classified.
  - Turn 2: `B00CMNIG68 ASIN product name Amazon` -> 10 results; not independently classified.
  - Turn 3: `"B00CMNIG68" Amazon` -> 10 results; not independently classified.
  - Turn 5: `"Super NutreMill" wholesale distributor` -> 10 results; brand-matching candidate.
  - Turn 6: `Super NutreMill 4in1 Cereal Brown Rice brand website` -> 10 results; brand-matching candidate.
  - Turn 7: `"Super NutreMill" Faire` -> 10 results; brand-matching candidate.
  - Turn 8: `"NutreMill" cereal brand` -> 10 results; not independently classified.
  - Turn 9: `"eSaving Shop" Amazon seller` -> 10 results; not independently classified.
  - Turn 10: `Super NutreMill manufacturer company` -> 10 results; brand-matching candidate.
  - Turn 12: `"Super" "NutreMill" "4in1 Cereal" manufacturer` -> 10 results; brand-matching candidate.
  - Turn 13: `NutreMill cereal halal brown rice` -> 10 results; not independently classified.
  - Turn 14: `Faire "NutreMill" OR "Super cereal" wholesale` -> 10 results; not independently classified.
  - Turn 16: `"eSaving Shop" Amazon brand NutreMill` -> 10 results; not independently classified.
  - Turn 17: `"SUPER" brand cereal NutreMill wholesale` -> 10 results; brand-matching candidate.
  - Turn 18: `amazon.com/shops/super brand store` -> 10 results; not independently classified.
  - Turn 19: `"eSaving Shop" company` -> 10 results; not independently classified.
  - Turn 20: `"super" "brown rice" cereal brand "4 in 1"` -> 10 results; brand-matching candidate.
- Browse calls:
  - Turn 4: `https://www.amazon.com/dp/B00CMNIG68` -> success; Browsed https://www.amazon.com/dp/B00CMNIG68; 5000 characters returned..
  - Turn 11: `https://www.amazon.com/stores/Super/page/B1C3AB7D-6D1C-4D39-9C07-1566340D2EC2` -> success; Browsed https://www.amazon.com/stores/Super/page/B1C3AB7D-6D1C-4D39-9C07-1566340D2EC2; 5000 characters returned..
  - Turn 15: `https://www.amazon.com/dp/B00CMNIG68#productFactsDesktopExpander` -> success; Browsed https://www.amazon.com/dp/B00CMNIG68#productFactsDesktopExpander; 5000 characters returned..

### The Beadsmith (AI-85829)

- Session: `AI-85829`. Status: `active`. Turns: 12. Raw tool calls: 12.
- Final sqld verdict: `BLOCKED_FOR_AMAZON` / `HIGH`. Queue write: present; synced at `2026-07-14 05:43:56`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `"The Beadsmith" wholesale program` -> 7 results; not independently classified.
  - Turn 2: `"The Beadsmith" Faire wholesale` -> 7 results; not independently classified.
  - Turn 3: `"The Beadsmith" authorized distributor` -> 7 results; not independently classified.
  - Turn 4: `Beadsmith wholesale program dealer` -> 10 results; brand-matching candidate.
  - Turn 5: `Beadsmith Faire wholesale jewelry supply` -> 10 results; brand-matching candidate.
  - Turn 6: `Beadsmith authorized distributor beading supplies` -> 10 results; brand-matching candidate.
  - Turn 7: `site:faire.com Beadsmith` -> 0 results; no results.
  - Turn 11: `"The Beadsmith" MAP policy` -> 7 results; not independently classified.
  - Turn 12: `beadsmith MAP policy reseller` -> 10 results; brand-matching candidate.
- Browse calls:
  - Turn 8: `https://www.beadsmith.com/` -> success; Browsed https://www.beadsmith.com/; 4753 characters returned..
  - Turn 9: `https://www.beadsmith.com/reseller-agreement` -> success; Browsed https://www.beadsmith.com/reseller-agreement; 5000 characters returned..
  - Turn 10: `https://www.beadsmith.com/apply` -> success; Browsed https://www.beadsmith.com/apply; 2521 characters returned..

### Tama (AI-85828)

- Session: `AI-85828`. Status: `active`. Turns: 23. Raw tool calls: 23.
- Final sqld verdict: `MAYBE` / `MEDIUM`. Queue write: present; synced at `2026-07-14 05:43:58`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Tama drums wholesale program dealer application` -> 10 results; brand-matching candidate.
  - Turn 2: `Tama Faire wholesale drums` -> 10 results; brand-matching candidate.
  - Turn 3: `Tama authorized distributor drums wholesale` -> 10 results; brand-matching candidate.
  - Turn 4: `"Tama" dealer login wholesale account drums` -> 10 results; brand-matching candidate.
  - Turn 5: `Tama drums MAP policy Amazon reseller restrictions` -> 10 results; brand-matching candidate.
  - Turn 6: `Hoshino USA Tama dealer application wholesale` -> 10 results; not independently classified.
  - Turn 7: `tama.com dealer locator become a dealer` -> 10 results; brand-matching candidate.
  - Turn 8: `Hoshino Gakki dealer network Tama drums wholesale account` -> 10 results; not independently classified.
  - Turn 9: `site:tama.com dealer wholesale` -> 0 results; no results.
  - Turn 10: `"become a dealer" Tama drums` -> 10 results; not independently classified.
  - Turn 11: `tama.com dealer login` -> 10 results; brand-matching candidate.
  - Turn 12: `Hoshino USA Inc Tama dealer wholesale B2B` -> 10 results; not independently classified.
  - Turn 13: `"Tama" "dealer" "application" drums wholesale` -> 10 results; brand-matching candidate.
  - Turn 14: `Hoshino USA dealer application musical instruments` -> 10 results; not independently classified.
  - Turn 15: `Tama drums wholesale distributor USA dealer program` -> 10 results; brand-matching candidate.
  - Turn 16: `hoshinohq.com OR hoshinousa.com dealer portal Tama` -> 10 results; not independently classified.
  - Turn 17: `"Tama drum" "dealer portal" OR "wholesale account" OR "B2B"` -> 10 results; brand-matching candidate.
  - Turn 21: `contact Tama drums wholesale become dealer Hoshino USA` -> 11 results; not independently classified.
  - Turn 22: `Tama drums Faire wholesale online marketplace` -> 10 results; brand-matching candidate.
  - Turn 23: `Tama Amazon drums reseller restrictions authorized` -> 10 results; brand-matching candidate.
- Browse calls:
  - Turn 18: `https://www.tama.com/usa/` -> success; Browsed https://www.tama.com/usa/; 4881 characters returned..
  - Turn 19: `https://www.tama.com/usa/dealers/` -> success; Browsed https://www.tama.com/usa/dealers/; 5000 characters returned..
  - Turn 20: `https://www.tama.com/usa/support/contact/` -> success; Browsed https://www.tama.com/usa/support/contact/; 5000 characters returned..

### 4into1 (4into1-worker)

- Session: `4into1-research`. Status: `active`. Turns: 18. Raw tool calls: 18.
- Final sqld verdict: `CLOSED` / `MEDIUM`. Queue write: present; synced at `2026-07-14 05:43:59`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `4into1 wholesale program` -> 10 results; generic/irrelevant per final verdict.
  - Turn 2: `4into1 Faire wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 3: `4into1 authorized distributor` -> 10 results; generic/irrelevant per final verdict.
  - Turn 4: `B09WX59SFM` -> 10 results; generic/irrelevant per final verdict.
  - Turn 5: `"4into1" brand motorcycle exhaust wholesale` -> 11 results; generic/irrelevant per final verdict.
  - Turn 6: `4into1 Amazon` -> 10 results; generic/irrelevant per final verdict.
  - Turn 7: `4into1 product` -> 10 results; generic/irrelevant per final verdict.
  - Turn 8: `Nike wholesale program` -> 10 results; generic/irrelevant per final verdict.
  - Turn 9: `"4into1" Amazon brand` -> 10 results; generic/irrelevant per final verdict.
  - Turn 10: `4into1.com` -> 10 results; generic/irrelevant per final verdict.
  - Turn 11: `B09WX59SFM 4into1 Amazon product` -> 10 results; generic/irrelevant per final verdict.
  - Turn 12: `4into1.com wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 13: `"4into1" motorcycle parts dealer application` -> 1 results; generic/irrelevant per final verdict.
  - Turn 14: `"4into1" website vintage Honda parts` -> 9 results; generic/irrelevant per final verdict.
  - Turn 15: `site:4into1.com wholesale dealer` -> 0 results; no results.
  - Turn 16: `"4into1" vintage motorcycle parts store` -> 10 results; generic/irrelevant per final verdict.
  - Turn 17: `4into1 wholesale account bulk` -> 11 results; generic/irrelevant per final verdict.
  - Turn 18: `"4into1" brand Amazon.com` -> 10 results; generic/irrelevant per final verdict.
- Browse calls:
  - None recorded.

### A.M. Leonard (am-leonard-research)

- Session: `am-leonard-research`. Status: `active`. Turns: 19. Raw tool calls: 19.
- Final sqld verdict: `MAYBE` / `MEDIUM`. Queue write: present; synced at `2026-07-14 05:44:01`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `"A.M. Leonard" wholesale program` -> 10 results; not independently classified.
  - Turn 2: `"A.M. Leonard" Faire wholesale` -> 10 results; not independently classified.
  - Turn 3: `"A.M. Leonard" authorized distributor` -> 10 results; not independently classified.
  - Turn 4: `"AM Leonard" wholesale` -> 9 results; not independently classified.
  - Turn 5: `AM Leonard gardening tools wholesale distributor` -> 9 results; not independently classified.
  - Turn 6: `A.M. Leonard Inc. gardening tools` -> 10 results; not independently classified.
  - Turn 7: `amleo.com wholesale` -> 10 results; brand-matching candidate.
  - Turn 11: `"A.M. Leonard" MAP policy Amazon reseller` -> 10 results; not independently classified.
  - Turn 14: `amleo.com reseller policy Amazon` -> 10 results; brand-matching candidate.
- Browse calls:
  - Turn 8: `https://www.amleo.com/` -> success; Browsed https://www.amleo.com/; 4513 characters returned..
  - Turn 9: `https://www.amleo.com/pro-plus` -> success; Browsed https://www.amleo.com/pro-plus; 5000 characters returned..
  - Turn 10: `https://www.amleo.com/distributormap` -> success; Browsed https://www.amleo.com/distributormap; 5000 characters returned..
  - Turn 12: `https://www.amleo.com/terms-conditions` -> success; Browsed https://www.amleo.com/terms-conditions; 4416 characters returned..
  - Turn 13: `https://www.amleo.com/privacy-policy` -> success; Browsed https://www.amleo.com/privacy-policy; 4406 characters returned..
  - Turn 15: `https://www.amleo.com/return-policy` -> success; Browsed https://www.amleo.com/return-policy; 4401 characters returned..
  - Turn 16: `https://www.amazon.com/dp/B015X6H3MS` -> success; Browsed https://www.amazon.com/dp/B015X6H3MS; 5000 characters returned..
  - Turn 17: `https://www.amleo.com/quotation/quote/` -> success; Browsed https://www.amleo.com/quotation/quote/; 3703 characters returned..
  - Turn 18: `https://www.amazon.com/stores/A.M.Leonard` -> success; Browsed https://www.amazon.com/stores/A.M.Leonard; 386 characters returned..
  - Turn 19: `https://www.amazon.com/stores/A.M.+Leonard/page/` -> success; Browsed https://www.amazon.com/stores/A.M.+Leonard/page/; 386 characters returned..

### aden + anais (aden-anais-research)

- Session: `aden-anais-research`. Status: `active`. Turns: 23. Raw tool calls: 23.
- Final sqld verdict: `MAYBE` / `MEDIUM`. Queue write: present; synced at `2026-07-14 05:44:01`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `aden + anais wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `aden and anais wholesale program distributor` -> 10 results; brand-matching candidate.
  - Turn 3: `"aden + anais" wholesale` -> 10 results; brand-matching candidate.
  - Turn 4: `adenanais wholesale baby swaddle` -> 10 results; not independently classified.
  - Turn 5: `"aden" "anais" wholesale retailer` -> 10 results; brand-matching candidate.
  - Turn 6: `aden and anais Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 7: `adenandanais.com wholesale` -> 13 results; not independently classified.
  - Turn 8: `"aden" "anais" muslin swaddle brand` -> 10 results; brand-matching candidate.
  - Turn 9: `"aden anais" baby muslin wholesale` -> 10 results; brand-matching candidate.
  - Turn 10: `"aden and anais" muslin swaddle blankets official website` -> 10 results; brand-matching candidate.
  - Turn 11: `"aden and anais" brand baby distributor` -> 10 results; brand-matching candidate.
  - Turn 12: `aden+anais Amazon brand store` -> 10 results; brand-matching candidate.
  - Turn 13: `aden+anais.com wholesale dealer` -> 10 results; brand-matching candidate.
  - Turn 16: `"aden and anais" Faire wholesale marketplace` -> 10 results; brand-matching candidate.
  - Turn 17: `"aden" "anais" "MAP policy" Amazon reseller restrictions` -> 10 results; brand-matching candidate.
  - Turn 18: `HALO sleep retailer program wholesale baby products` -> 10 results; not independently classified.
  - Turn 19: `halosleep.com wholesale retailer application distributor` -> 10 results; not independently classified.
- Browse calls:
  - Turn 14: `https://www.adenandanais.com` -> success; Browsed https://www.adenandanais.com; 5000 characters returned..
  - Turn 15: `https://www.halosleep.com/pages/become-a-halo-retailer-1` -> success; Browsed https://www.halosleep.com/pages/become-a-halo-retailer-1; 3420 characters returned..
  - Turn 20: `https://www.halosleep.com/pages/aden-and-anais` -> success; Browsed https://www.halosleep.com/pages/aden-and-anais; 5000 characters returned..
  - Turn 21: `https://www.faire.com/brand/b_aden-anais` -> success; Browsed https://www.faire.com/brand/b_aden-anais; 5000 characters returned..
  - Turn 22: `https://www.halosleep.com/pages/aden-anais-terms-conditions` -> success; Browsed https://www.halosleep.com/pages/aden-anais-terms-conditions; 3722 characters returned..
  - Turn 23: `https://www.halosleep.com/pages/terms-conditions` -> success; Browsed https://www.halosleep.com/pages/terms-conditions; 3700 characters returned..

### AeroPress (aeroPress_research)

- Session: `aeroPress_research`. Status: `active`. Turns: 24. Raw tool calls: 24.
- Final sqld verdict: `ACCESSIBLE` / `HIGH`. Queue write: present; synced at `2026-07-14 05:44:02`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `AeroPress wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `AeroPress Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `AeroPress authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 4: `AeroPress dealer application wholesale account` -> 10 results; brand-matching candidate.
  - Turn 5: `AeroPress Amazon MAP policy reseller restrictions` -> 10 results; brand-matching candidate.
  - Turn 6: `site:faire.com AeroPress` -> 0 results; no results.
  - Turn 7: `AeroPress wholesale page dealer portal` -> 10 results; brand-matching candidate.
  - Turn 8: `aeropress.com wholesale` -> 10 results; brand-matching candidate.
  - Turn 9: `"AeroPress" "wholesale" "dealer" "distributor"` -> 10 results; brand-matching candidate.
  - Turn 10: `"aeropress" "become a retailer" OR "wholesale application" OR "reseller"` -> 10 results; brand-matching candidate.
  - Turn 11: `aeropress.com/pages wholesale` -> 10 results; not independently classified.
  - Turn 12: `AeroPress wholesale distributor United States` -> 10 results; brand-matching candidate.
  - Turn 13: `"AeroPress" "wholesale pricing" OR "MAP policy" OR "minimum advertised price"` -> 10 results; brand-matching candidate.
  - Turn 20: `"AeroPress" "Amazon" "unauthorized" OR "not authorized" OR "policy" reseller` -> 10 results; brand-matching candidate.
  - Turn 21: `AeroPress MAP policy reseller agreement terms conditions` -> 10 results; brand-matching candidate.
- Browse calls:
  - Turn 14: `https://aeropress.com/` -> success; Browsed https://aeropress.com/; 5000 characters returned..
  - Turn 15: `https://wholesale.aeropress.com/` -> success; Browsed https://wholesale.aeropress.com/; 3135 characters returned..
  - Turn 16: `https://aeropress.faire.com/` -> success; Browsed https://aeropress.faire.com/; 4648 characters returned..
  - Turn 17: `https://wholesale.aeropress.com/pages/resources` -> success; Browsed https://wholesale.aeropress.com/pages/resources; 3373 characters returned..
  - Turn 18: `https://cdn.shopify.com/s/files/1/0614/6696/8270/files/2025_AeroPress_U.S._Price_List_-_July_V5.pdf?v=1751563828` -> unreadable page content; browse_page failed for https://cdn.shopify.com/s/files/1/0614/6696/8270/files/2025_AeroPress_U.S._Price_List_-_July_V5.pdf?v=1751563828: Page did not contain readable content.
  - Turn 19: `https://wholesale.aeropress.com/account/register` -> success; Browsed https://wholesale.aeropress.com/account/register; 5000 characters returned..
  - Turn 22: `https://www.aeropress.com/pages/privacy-policy` -> success; Browsed https://www.aeropress.com/pages/privacy-policy; 5000 characters returned..
  - Turn 23: `https://aeropress.com/policies/terms-of-service` -> success; Browsed https://aeropress.com/policies/terms-of-service; 5000 characters returned..
  - Turn 24: `https://www.faire.com/brand/b_6nn6knhkvw` -> success; Browsed https://www.faire.com/brand/b_6nn6knhkvw; 5000 characters returned..

### Aerosoft (aerosoft-research-001)

- Session: `aerosoft-research-001`. Status: `active`. Turns: 20. Raw tool calls: 20.
- Final sqld verdict: `MAYBE` / `MEDIUM`. Queue write: present; synced at `2026-07-14 05:44:00`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Aerosoft wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `Aerosoft Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `Aerosoft authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 4: `Aerosoft B2B wholesale reseller program` -> 10 results; brand-matching candidate.
  - Turn 5: `Aerosoft dealer apply reseller` -> 10 results; brand-matching candidate.
  - Turn 6: `Aerosoft Amazon B07XQBBLGM physical product` -> 10 results; brand-matching candidate.
  - Turn 7: `Aerosoft company about us publisher simulation games` -> 10 results; brand-matching candidate.
  - Turn 8: `"Aerosoft" wholesale physical products distribution` -> 10 results; brand-matching candidate.
  - Turn 9: `Aerosoft flight sim hardware wholesale distributor` -> 10 results; brand-matching candidate.
  - Turn 10: `"aerosoft.com" reseller become retailer` -> 10 results; brand-matching candidate.
  - Turn 11: `Aerosoft contact wholesale inquiry` -> 10 results; brand-matching candidate.
  - Turn 12: `site:aerosoft.com wholesale OR reseller OR dealer OR B2B OR partner` -> 0 results; no results.
  - Turn 18: `Aerosoft Amazon reseller restrictions MAP policy` -> 10 results; brand-matching candidate.
  - Turn 19: `B07XQBBLGM Aerosoft Amazon product` -> 7 results; not independently classified.
  - Turn 20: `Aerosoft B07XQBBLGM` -> 10 results; brand-matching candidate.
- Browse calls:
  - Turn 13: `https://www.aerosoft.com/us/` -> success; Browsed https://www.aerosoft.com/us/; 2609 characters returned..
  - Turn 14: `https://www.aerosoft.com/us/partners` -> success; Browsed https://www.aerosoft.com/us/partners; 4347 characters returned..
  - Turn 15: `https://www.aerosoft.com/us/company` -> success; Browsed https://www.aerosoft.com/us/company; 5000 characters returned..
  - Turn 16: `https://www.aerosoft.com/us/contact` -> success; Browsed https://www.aerosoft.com/us/contact; 4137 characters returned..
  - Turn 17: `https://www.aerosoft.com/us/terms-conditions` -> success; Browsed https://www.aerosoft.com/us/terms-conditions; 5000 characters returned..

### FloraCraft (AI-85380)

- Session: `AI-85380`. Status: `active`. Turns: 9. Raw tool calls: 9.
- Final sqld verdict: `ACCESSIBLE` / `HIGH`. Queue write: present; synced at `2026-07-14 05:44:03`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `FloraCraft wholesale program` -> 9 results; brand-matching candidate.
  - Turn 2: `FloraCraft Faire wholesale` -> 9 results; brand-matching candidate.
  - Turn 3: `FloraCraft authorized distributor` -> 9 results; brand-matching candidate.
  - Turn 6: `FloraCraft Amazon MAP policy reseller restrictions` -> 9 results; brand-matching candidate.
- Browse calls:
  - Turn 4: `https://www.floracraft.com/` -> success; Browsed https://www.floracraft.com/; 2787 characters returned..
  - Turn 5: `https://shop.floracraft.com/new-customer-application` -> success; Browsed https://shop.floracraft.com/new-customer-application; 4102 characters returned..
  - Turn 7: `https://shop.floracraft.com/terms-conditions` -> success; Browsed https://shop.floracraft.com/terms-conditions; 2762 characters returned..
  - Turn 8: `https://www.floracraft.com/terms-of-purchase/` -> success; Browsed https://www.floracraft.com/terms-of-purchase/; 2687 characters returned..
  - Turn 9: `https://shop.floracraft.com/brand-standard-policy` -> success; Browsed https://shop.floracraft.com/brand-standard-policy; 5000 characters returned..

### BabyGanics (AI-85373)

- Session: `AI-85373`. Status: `active`. Turns: 9. Raw tool calls: 9.
- Final sqld verdict: `BLOCKED_FOR_AMAZON` / `HIGH`. Queue write: present; synced at `2026-07-14 05:44:02`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `BabyGanics wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `BabyGanics Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `BabyGanics authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 4: `Babyganics wholesale account reseller program` -> 10 results; brand-matching candidate.
  - Turn 5: `"Babyganics" wholesale distributor B2B` -> 10 results; brand-matching candidate.
  - Turn 7: `Babyganics owned by parent company wholesale` -> 10 results; brand-matching candidate.
- Browse calls:
  - Turn 6: `https://babyganics.com/` -> success; Browsed https://babyganics.com/; 3929 characters returned..
  - Turn 8: `https://babyganics.com/reseller-guidelines/` -> success; Browsed https://babyganics.com/reseller-guidelines/; 5000 characters returned..
  - Turn 9: `https://babyganics.com/contact-us/` -> success; Browsed https://babyganics.com/contact-us/; 3411 characters returned..

### KLEAN-STRIP (AI-85388)

- Session: `AI-85388`. Status: `active`. Turns: 17. Raw tool calls: 17.
- Final sqld verdict: `CLOSED` / `HIGH`. Queue write: present; synced at `2026-07-14 05:44:04`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `KLEAN-STRIP wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `KLEAN-STRIP Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `KLEAN-STRIP authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 4: `KLEAN-STRIP paint stripper wholesale` -> 10 results; brand-matching candidate.
  - Turn 5: `KLEAN-STRIP W.M. Barr distributor` -> 10 results; brand-matching candidate.
  - Turn 6: `"Klean-Strip" dealer wholesale paint stripper` -> 10 results; not independently classified.
  - Turn 7: `W.M. Barr wholesale distributor program` -> 10 results; not independently classified.
  - Turn 8: `Klean Strip paint stripper wmbarr` -> 10 results; brand-matching candidate.
  - Turn 9: `site:kleanstrip.com wholesale` -> 0 results; no results.
  - Turn 10: `"KLEAN-STRIP" Walmart Home Depot supplier` -> 10 results; brand-matching candidate.
  - Turn 17: `"Klean Strip" "become a retailer" OR "wholesale" OR "distributor" OR "dealer"` -> 10 results; brand-matching candidate.
- Browse calls:
  - Turn 11: `https://www.wmbarr.com` -> success; Browsed https://www.wmbarr.com; 4614 characters returned..
  - Turn 12: `https://barrbrands.com/brands/` -> success; Browsed https://barrbrands.com/brands/; 4195 characters returned..
  - Turn 13: `https://kleanstrip.com/` -> success; Browsed https://kleanstrip.com/; 3300 characters returned..
  - Turn 14: `https://kleanstrip.com/contact-us/` -> success; Browsed https://kleanstrip.com/contact-us/; 3456 characters returned..
  - Turn 15: `https://kleanstrip.com/find-a-retailer/` -> success; Browsed https://kleanstrip.com/find-a-retailer/; 3104 characters returned..
  - Turn 16: `https://barrbrands.com/about/` -> success; Browsed https://barrbrands.com/about/; 4416 characters returned..

### Black Forest (AI-85374)

- Session: `AI-85374`. Status: `active`. Turns: 23. Raw tool calls: 23.
- Final sqld verdict: `CLOSED` / `HIGH`. Queue write: present; synced at `2026-07-14 05:44:06`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Black Forest wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `Black Forest Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `Black Forest authorized distributor` -> 10 results; not independently classified.
  - Turn 4: `"Black Forest" brand Amazon` -> 10 results; brand-matching candidate.
  - Turn 5: `Black Forest brand home decor` -> 10 results; brand-matching candidate.
  - Turn 6: `"Black Forest" brand products` -> 10 results; brand-matching candidate.
  - Turn 7: `B0CZPKBFB2 Black Forest` -> 14 results; brand-matching candidate.
  - Turn 8: `Black Forest candy` -> 10 results; brand-matching candidate.
  - Turn 9: `Black Forest gummy snacks` -> 10 results; brand-matching candidate.
  - Turn 10: `"blackforest" brand wholesale` -> 10 results; brand-matching candidate.
  - Turn 11: `amazon B0CZPKBFB2` -> 10 results; not independently classified.
  - Turn 14: `"black forest" supplements wholesale` -> 10 results; brand-matching candidate.
  - Turn 16: `"Black Forest" supplements Faire` -> 10 results; brand-matching candidate.
  - Turn 17: `"blackforestsupplements" wholesale` -> 10 results; not independently classified.
  - Turn 18: `blackforestsupplements.com wholesale` -> 10 results; not independently classified.
  - Turn 19: `"The Black Forest LLC" distributor` -> 7 results; not independently classified.
- Browse calls:
  - Turn 12: `https://www.amazon.com/dp/B0CZPKBFB2` -> success; Browsed https://www.amazon.com/dp/B0CZPKBFB2; 5000 characters returned..
  - Turn 13: `https://blackforestsupplements.com/` -> success; Browsed https://blackforestsupplements.com/; 5000 characters returned..
  - Turn 15: `https://blackforestsupplements.com/pages/wholesale` -> success; Browsed https://blackforestsupplements.com/pages/wholesale; 2485 characters returned..
  - Turn 20: `https://www.faire.com/search?q=black+forest` -> success; Browsed https://www.faire.com/search?q=black+forest; 2957 characters returned..
  - Turn 21: `https://blackforestsupplements.com/pages/faq` -> success; Browsed https://blackforestsupplements.com/pages/faq; 3509 characters returned..
  - Turn 22: `https://blackforestsupplements.com/pages/contact-us` -> success; Browsed https://blackforestsupplements.com/pages/contact-us; 3045 characters returned..
  - Turn 23: `https://blackforestsupplements.com/policies/terms-of-service` -> success; Browsed https://blackforestsupplements.com/policies/terms-of-service; 5000 characters returned..

### ENO (AI-85379)

- Session: `AI-85379`. Status: `active`. Turns: 20. Raw tool calls: 20.
- Final sqld verdict: `MAYBE` / `MEDIUM`. Queue write: present; synced at `2026-07-14 05:44:05`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `ENO hammock wholesale program` -> 10 results; not independently classified.
  - Turn 2: `ENO hammock Faire wholesale` -> 10 results; not independently classified.
  - Turn 3: `ENO hammock authorized distributor` -> 10 results; not independently classified.
  - Turn 4: `Eagles Nest Outfitters dealer application wholesale` -> 9 results; not independently classified.
  - Turn 5: `ENO hammock wholesale account retailer` -> 10 results; not independently classified.
  - Turn 6: `"eaglesnestoutfittersinc.com" wholesale` -> 10 results; not independently classified.
  - Turn 7: `ENO hammock MAP policy Amazon reseller` -> 10 results; not independently classified.
  - Turn 8: `site:faire.com ENO hammock` -> 0 results; no results.
  - Turn 9: `eaglesnestoutfittersinc.com wholesale dealer account` -> 10 results; not independently classified.
  - Turn 10: `"Eagles Nest Outfitters" wholesale program` -> 9 results; not independently classified.
  - Turn 13: `"Eagles Nest Outfitters" "become a dealer" OR "wholesale application" OR "reseller"` -> 9 results; not independently classified.
  - Turn 16: `ENO hammock wholesale distributor login apply` -> 10 results; not independently classified.
  - Turn 18: `"Eagles Nest Outfitters" "ENO" wholesale reseller program dealer` -> 9 results; not independently classified.
  - Turn 19: `"Eagles Nest Outfitters" Amazon seller policy` -> 9 results; not independently classified.
  - Turn 20: `"eaglesnestoutfittersinc.com" dealer wholesale distributor login` -> 10 results; not independently classified.
- Browse calls:
  - Turn 11: `https://eaglesnestoutfittersinc.com/` -> success; Browsed https://eaglesnestoutfittersinc.com/; 5000 characters returned..
  - Turn 12: `https://eaglesnestoutfittersinc.com/pages/distributor-access` -> success; Browsed https://eaglesnestoutfittersinc.com/pages/distributor-access; 3669 characters returned..
  - Turn 14: `https://eaglesnestoutfittersinc.com/pages/international-shipping` -> success; Browsed https://eaglesnestoutfittersinc.com/pages/international-shipping; 4288 characters returned..
  - Turn 15: `https://eaglesnestoutfittersinc.com/pages/contact-us` -> success; Browsed https://eaglesnestoutfittersinc.com/pages/contact-us; 4674 characters returned..
  - Turn 17: `https://eaglesnestoutfittersinc.com/policies/terms-of-service` -> success; Browsed https://eaglesnestoutfittersinc.com/policies/terms-of-service; 5000 characters returned..

### Afta (afta_research_01)

- Session: `afta_research_01`. Status: `active`. Turns: 27. Raw tool calls: 27.
- Final sqld verdict: `ACCESSIBLE` / `HIGH`. Queue write: present; synced at `2026-07-14 05:44:08`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Afta wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `Afta Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `Afta authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 4: `B010OSWZ6E Afta Amazon` -> 10 results; not independently classified.
  - Turn 5: `"Afta" brand skincare wholesale` -> 10 results; brand-matching candidate.
  - Turn 6: `"Afta" brand product` -> 10 results; brand-matching candidate.
  - Turn 7: `B010OSWZ6E product afta` -> 10 results; not independently classified.
  - Turn 8: `B010OSWZ6E aftas` -> 10 results; not independently classified.
  - Turn 9: `"Afta" "brand" wholesale beauty` -> 10 results; brand-matching candidate.
  - Turn 10: `"B010OSWZ6E" $17.99` -> 10 results; not independently classified.
  - Turn 11: `B010OSWZ6E afta aftershave` -> 10 results; not independently classified.
  - Turn 13: `Mennen Afta wholesale distributor` -> 10 results; not independently classified.
  - Turn 14: `Mennen aftershave wholesale program` -> 10 results; not independently classified.
  - Turn 16: `Colgate-Palmolive wholesale distributor program personal care` -> 7 results; not independently classified.
  - Turn 17: `Colgate Palmolive distributor application personal care wholesale` -> 7 results; not independently classified.
  - Turn 18: `"Afta" "Mennen" Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 19: `Colgate-Palmolive wholesale distributor USA personal care products` -> 7 results; not independently classified.
  - Turn 20: `Mennen aftershave buy wholesale bulk` -> 10 results; not independently classified.
  - Turn 21: `Colgate Palmolive become a distributor retailer` -> 10 results; not independently classified.
  - Turn 22: `"colgatepalmolive.com" wholesale distributor` -> 9 results; not independently classified.
  - Turn 24: `"Afta after shave" wholesale distributor supplier` -> 10 results; brand-matching candidate.
  - Turn 25: `Colgate Palmolive Amazon MAP policy reseller restrictions` -> 7 results; not independently classified.
  - Turn 26: `Colgate Palmolive authorized reseller Amazon policy` -> 7 results; not independently classified.
- Browse calls:
  - Turn 12: `https://www.amazon.com/dp/B010OSWZ6E` -> success; Browsed https://www.amazon.com/dp/B010OSWZ6E; 5000 characters returned..
  - Turn 15: `https://en.m.wikipedia.org/wiki/Mennen` -> success; Browsed https://en.m.wikipedia.org/wiki/Mennen; 5000 characters returned..
  - Turn 23: `https://www.colgatepalmolive.com/en-us/contact-us` -> success; Browsed https://www.colgatepalmolive.com/en-us/contact-us; 4664 characters returned..
  - Turn 27: `https://www.colgatepalmolive.com/en-us/suppliers` -> success; Browsed https://www.colgatepalmolive.com/en-us/suppliers; 3654 characters returned..

### Ajoura (ajoura-research)

- Session: `ajoura-research-session`. Status: `active`. Turns: 12. Raw tool calls: 12.
- Final sqld verdict: `CLOSED` / `HIGH`. Queue write: present; synced at `2026-07-14 05:44:07`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Ajoura wholesale program` -> 7 results; generic/irrelevant per final verdict.
  - Turn 2: `Ajoura Faire wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 3: `Ajoura authorized distributor` -> 10 results; generic/irrelevant per final verdict.
  - Turn 4: `B0D78HPDZD Ajoura` -> 10 results; generic/irrelevant per final verdict.
  - Turn 5: `Ajoura Amazon` -> 10 results; generic/irrelevant per final verdict.
  - Turn 6: `"Ajoura" brand` -> 10 results; generic/irrelevant per final verdict.
  - Turn 8: `ajoura beauty website` -> 11 results; generic/irrelevant per final verdict.
  - Turn 9: `ajourabeauty.com` -> 10 results; generic/irrelevant per final verdict.
  - Turn 10: `"Ajoura" wax beads` -> 10 results; generic/irrelevant per final verdict.
  - Turn 11: `site:faire.com Ajoura` -> 0 results; no results.
  - Turn 12: `Ajoura wholesale beauty supply` -> 10 results; generic/irrelevant per final verdict.
- Browse calls:
  - Turn 7: `https://www.amazon.com/dp/B0D78HPDZD` -> success; Browsed https://www.amazon.com/dp/B0D78HPDZD; 5000 characters returned..

### Amenazel (amenazel-research)

- Session: `amenazel-research`. Status: `active`. Turns: 12. Raw tool calls: 12.
- Final sqld verdict: `INCONCLUSIVE` / `HIGH`. Queue write: present; synced at `2026-07-14 05:44:04`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Amenazel wholesale program` -> 10 results; generic/irrelevant per final verdict.
  - Turn 2: `Amenazel Faire wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 3: `Amenazel authorized distributor` -> 10 results; generic/irrelevant per final verdict.
  - Turn 4: `Amenazel brand` -> 10 results; generic/irrelevant per final verdict.
  - Turn 5: `B0834NW3J7 Amenazel` -> 10 results; generic/irrelevant per final verdict.
  - Turn 6: `Amenazel` -> 10 results; generic/irrelevant per final verdict.
  - Turn 7: `B0834NW3J7 Amazon product` -> 10 results; generic/irrelevant per final verdict.
  - Turn 8: `"B0834NW3J7" Amazon` -> 10 results; generic/irrelevant per final verdict.
  - Turn 9: `"Amenazel" product` -> 10 results; generic/irrelevant per final verdict.
  - Turn 10: `camelcamelcamel B0834NW3J7` -> 10 results; generic/irrelevant per final verdict.
  - Turn 11: `site:amazon.com B0834NW3J7` -> 0 results; no results.
  - Turn 12: `Amenazel amazon` -> 10 results; generic/irrelevant per final verdict.
- Browse calls:
  - None recorded.

### ANFAR LONDON (anfar-london-research)

- Session: `anfar-london-research`. Status: `active`. Turns: 12. Raw tool calls: 12.
- Final sqld verdict: `INCONCLUSIVE` / `LOW`. Queue write: present; synced at `2026-07-14 05:44:05`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `ANFAR LONDON wholesale program` -> 10 results; generic/irrelevant per final verdict.
  - Turn 2: `ANFAR LONDON Faire wholesale` -> 7 results; generic/irrelevant per final verdict.
  - Turn 3: `ANFAR LONDON authorized distributor` -> 10 results; generic/irrelevant per final verdict.
  - Turn 4: `ANFAR LONDON brand` -> 10 results; generic/irrelevant per final verdict.
  - Turn 5: `B0DFQK4F7R` -> 10 results; generic/irrelevant per final verdict.
  - Turn 6: `"ANFAR LONDON" Amazon` -> 10 results; generic/irrelevant per final verdict.
  - Turn 7: `"ANFAR LONDON" jewelry fashion` -> 10 results; generic/irrelevant per final verdict.
  - Turn 8: `anfar brand` -> 7 results; generic/irrelevant per final verdict.
  - Turn 9: `"ANFAR" Amazon ASIN` -> 10 results; generic/irrelevant per final verdict.
  - Turn 10: `site:amazon.com "ANFAR LONDON"` -> 0 results; no results.
  - Turn 11: `B0DFQK4F7R "ANFAR" product` -> 10 results; generic/irrelevant per final verdict.
  - Turn 12: `amazon.com/dp/B0DFQK4F7R` -> 10 results; generic/irrelevant per final verdict.
- Browse calls:
  - None recorded.

### Annamaet (annamaet-worker)

- Session: `annamaet-research`. Status: `active`. Turns: 14. Raw tool calls: 14.
- Final sqld verdict: `MAYBE` / `MEDIUM`. Queue write: present; synced at `2026-07-14 05:44:07`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Annamaet wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `Annamaet Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `Annamaet authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 5: `Annamaet become a retailer dealer` -> 10 results; brand-matching candidate.
  - Turn 8: `Annamaet pet food wholesale distributor account` -> 10 results; brand-matching candidate.
  - Turn 10: `site:faire.com Annamaet` -> 0 results; no results.
  - Turn 11: `"Annamaet" "MAP policy" OR "minimum advertised price"` -> 10 results; brand-matching candidate.
  - Turn 13: `Annamaet pet food wholesale account application` -> 10 results; brand-matching candidate.
- Browse calls:
  - Turn 4: `https://annamaet.com/` -> success; Browsed https://annamaet.com/; 3854 characters returned..
  - Turn 6: `https://annamaet.com/retailer-resources/` -> success; Browsed https://annamaet.com/retailer-resources/; 2672 characters returned..
  - Turn 7: `https://annamaet.com/contact/` -> success; Browsed https://annamaet.com/contact/; 2805 characters returned..
  - Turn 9: `https://annamaet.com/buy-direct/` -> success; Browsed https://annamaet.com/buy-direct/; 4974 characters returned..
  - Turn 12: `https://annamaet.com/buyonline/` -> success; Browsed https://annamaet.com/buyonline/; 2853 characters returned..
  - Turn 14: `https://annamaet.com/find/` -> success; Browsed https://annamaet.com/find/; 3463 characters returned..

### Bernz-O-Matic (bernz-o-matic-worker)

- Session: `bernz-o-matic-research`. Status: `active`. Turns: 18. Raw tool calls: 18.
- Final sqld verdict: `MAYBE` / `MEDIUM`. Queue write: present; synced at `2026-07-14 05:44:12`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Bernz-O-Matic wholesale program` -> 10 results; not independently classified.
  - Turn 2: `Bernz-O-Matic Faire wholesale` -> 10 results; not independently classified.
  - Turn 3: `Bernz-O-Matic authorized distributor` -> 10 results; not independently classified.
  - Turn 4: `Bernzomatic wholesale` -> 7 results; brand-matching candidate.
  - Turn 5: `Bernzomatic dealer application wholesale account` -> 7 results; brand-matching candidate.
  - Turn 6: `Bernzomatic Faire` -> 7 results; brand-matching candidate.
  - Turn 7: `Bernzomatic distributor wholesale torch propane MAP policy` -> 7 results; brand-matching candidate.
  - Turn 10: `Bernzomatic distributor program Worthington Enterprises` -> 7 results; brand-matching candidate.
  - Turn 11: `Bernzomatic Amazon reseller restrictions MAP policy` -> 7 results; brand-matching candidate.
  - Turn 12: `Worthington Enterprises Bernzomatic wholesale distributor application` -> 10 results; not independently classified.
  - Turn 13: `site:faire.com Bernzomatic` -> 0 results; no results.
  - Turn 14: `"Bernzomatic" "distributor" "become" OR "wholesale"` -> 7 results; brand-matching candidate.
  - Turn 15: `Faire wholesale Bernzomatic torch` -> 10 results; not independently classified.
  - Turn 17: `Bernzomatic "become a distributor" Worthington Enterprises torches` -> 7 results; brand-matching candidate.
- Browse calls:
  - Turn 8: `https://www.bernzomatic.com/` -> success; Browsed https://www.bernzomatic.com/; 4999 characters returned..
  - Turn 9: `https://bernzomaticbrand.zendesk.com/hc/en-us/requests/new?ticket_form_id=34443882429979` -> success; Cloudflare challenge detected.
  - Turn 16: `https://www.bernzomatic.com/pages/contact-us` -> success; Browsed https://www.bernzomatic.com/pages/contact-us; 4885 characters returned..
  - Turn 18: `https://thebernzomatic.com/` -> success; Browsed https://thebernzomatic.com/; 2368 characters returned..

### BINBOK VR (worker-001)

- Session: `BINBOK-VR-001`. Status: `active`. Turns: 10. Raw tool calls: 10.
- Final sqld verdict: `INCONCLUSIVE` / `HIGH`. Queue write: present; synced at `2026-07-14 05:44:08`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `BINBOK VR wholesale program` -> 10 results; generic/irrelevant per final verdict.
  - Turn 2: `BINBOK VR Faire wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 3: `BINBOK VR authorized distributor` -> 10 results; generic/irrelevant per final verdict.
  - Turn 4: `BINBOK VR Amazon` -> 10 results; generic/irrelevant per final verdict.
  - Turn 5: `BINBOK VR website` -> 10 results; generic/irrelevant per final verdict.
  - Turn 6: `"BINBOK VR"` -> 10 results; generic/irrelevant per final verdict.
  - Turn 7: `B0FH7KDR4K Amazon` -> 10 results; generic/irrelevant per final verdict.
  - Turn 8: `BINBOK brand VR headset` -> 10 results; generic/irrelevant per final verdict.
  - Turn 9: `BINBOK brand` -> 10 results; generic/irrelevant per final verdict.
  - Turn 10: `binbok vr headset accessories` -> 10 results; generic/irrelevant per final verdict.
- Browse calls:
  - None recorded.

### Avlon (avlon_research)

- Session: `avlon_research`. Status: `active`. Turns: 20. Raw tool calls: 20.
- Final sqld verdict: `INCONCLUSIVE` / `LOW`. Queue write: present; synced at `2026-07-14 05:44:13`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Avlon wholesale program` -> 10 results; generic/irrelevant per final verdict.
  - Turn 2: `Avlon Faire wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 3: `Avlon authorized distributor` -> 10 results; generic/irrelevant per final verdict.
  - Turn 4: `Avlon hair care wholesale` -> 7 results; generic/irrelevant per final verdict.
  - Turn 5: `Avlon Industries wholesale distributor` -> 10 results; generic/irrelevant per final verdict.
  - Turn 6: `Avlon Industries hair products` -> 10 results; generic/irrelevant per final verdict.
  - Turn 7: `avlon.com` -> 10 results; generic/irrelevant per final verdict.
  - Turn 8: `Avlon Affirm hair care brand` -> 5 results; generic/irrelevant per final verdict.
  - Turn 10: `B007HNKIG4 Avlon hair product` -> 10 results; generic/irrelevant per final verdict.
  - Turn 12: `Avlon Industries KeraCare wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 13: `KeraCare wholesale program distributor` -> 10 results; generic/irrelevant per final verdict.
  - Turn 15: `Avlon Industries hair care official website` -> 10 results; generic/irrelevant per final verdict.
  - Turn 18: `"Avlon" "Avlon Industries" hair Chicago wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 19: `"Avlon Industries" wholesale salon` -> 10 results; generic/irrelevant per final verdict.
  - Turn 20: `Sally Beauty Avlon KeraCare distributor` -> 10 results; generic/irrelevant per final verdict.
- Browse calls:
  - Turn 9: `https://www.avlon.com` -> site DNS error; browse_page failed for https://www.avlon.com: Page.goto: net::ERR_NAME_NOT_RESOLVED at https://www.avlon.com/ Call log:   - navigating to "https://www.avlon.com/", waiting until "domcontentloaded".
  - Turn 11: `https://www.amazon.com/dp/B007HNKIG4` -> success; Browsed https://www.amazon.com/dp/B007HNKIG4; 5000 characters returned..
  - Turn 14: `https://keracare.com/` -> success; Browsed https://keracare.com/; 3108 characters returned..
  - Turn 16: `https://keracare.com/collections/professional` -> success; Browsed https://keracare.com/collections/professional; 4348 characters returned..
  - Turn 17: `https://keracare.com/pages/about` -> success; Browsed https://keracare.com/pages/about; 3079 characters returned..

### Boesklenn (boesklenn-research-001)

- Session: `boesklenn-research-001`. Status: `active`. Turns: 7. Raw tool calls: 7.
- Final sqld verdict: `INCONCLUSIVE` / `HIGH`. Queue write: present; synced at `2026-07-14 05:44:09`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Boesklenn wholesale program` -> 10 results; generic/irrelevant per final verdict.
  - Turn 2: `Boesklenn Faire wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 3: `Boesklenn authorized distributor` -> 10 results; generic/irrelevant per final verdict.
  - Turn 4: `B071DPPQM8 Boesklenn` -> 10 results; generic/irrelevant per final verdict.
  - Turn 5: `Boesklenn brand` -> 10 results; generic/irrelevant per final verdict.
  - Turn 7: `"Boesklenn"` -> 10 results; generic/irrelevant per final verdict.
- Browse calls:
  - Turn 6: `https://www.amazon.com/dp/B071DPPQM8` -> success; Browsed https://www.amazon.com/dp/B071DPPQM8; 5000 characters returned..

### BON AMI (bon-ami-research)

- Session: `bon-ami-research`. Status: `active`. Turns: 16. Raw tool calls: 16.
- Final sqld verdict: `BLOCKED_FOR_AMAZON` / `HIGH`. Queue write: present; synced at `2026-07-14 05:44:11`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `BON AMI wholesale program` -> 10 results; generic/irrelevant per final verdict.
  - Turn 2: `BON AMI Faire wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 3: `BON AMI authorized distributor` -> 10 results; generic/irrelevant per final verdict.
  - Turn 4: `"Bon Ami" cleaning product wholesale distributor` -> 10 results; generic/irrelevant per final verdict.
  - Turn 5: `"Bon Ami" Faire wholesale cleaning` -> 10 results; generic/irrelevant per final verdict.
  - Turn 6: `"Bon Ami" cleaner wholesale account retailer` -> 10 results; generic/irrelevant per final verdict.
  - Turn 7: `"Bon Ami" cleaning powder brand website` -> 10 results; generic/irrelevant per final verdict.
  - Turn 8: `"Bon Ami" cleanser company history` -> 10 results; generic/irrelevant per final verdict.
  - Turn 9: `bonami.com cleaning product wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 10: `"Bon Ami" site:faire.com` -> 0 results; no results.
  - Turn 12: `"Bon Ami" wholesale distributor account reseller` -> 10 results; generic/irrelevant per final verdict.
- Browse calls:
  - Turn 11: `https://www.bonami.com/` -> success; Browsed https://www.bonami.com/; 4460 characters returned..
  - Turn 13: `https://www.bonami.com/resale-policy/` -> success; Browsed https://www.bonami.com/resale-policy/; 5000 characters returned..
  - Turn 14: `https://faultlessbrands.com/` -> success; Browsed https://faultlessbrands.com/; 2910 characters returned..
  - Turn 15: `https://faultlessbrands.com/contact/` -> success; Browsed https://faultlessbrands.com/contact/; 2435 characters returned..
  - Turn 16: `https://faultlessbrands.com/commercial/` -> success; Browsed https://faultlessbrands.com/commercial/; 2215 characters returned..

### Pellon (AI-85392)

- Session: `AI-85392`. Status: `active`. Turns: 16. Raw tool calls: 16.
- Final sqld verdict: `CLOSED` / `MEDIUM`. Queue write: present; synced at `2026-07-14 05:44:09`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Pellon wholesale program` -> 11 results; brand-matching candidate.
  - Turn 2: `Pellon Faire wholesale` -> 11 results; brand-matching candidate.
  - Turn 3: `Pellon authorized distributor` -> 11 results; brand-matching candidate.
  - Turn 4: `Pellon interfacing wholesale distributor account` -> 11 results; brand-matching candidate.
  - Turn 5: `Pellon by Freudenberg wholesale` -> 11 results; brand-matching candidate.
  - Turn 8: `Freudenberg Pellon wholesale supplier` -> 7 results; not independently classified.
  - Turn 9: `Pellon nonwovens B2B wholesale where to buy` -> 11 results; brand-matching candidate.
  - Turn 10: `Pellon fabric interfacing bulk wholesale supplier` -> 11 results; brand-matching candidate.
  - Turn 11: `site:faire.com Pellon` -> 0 results; no results.
  - Turn 12: `Pellon brand Freudenberg corporate B2B` -> 11 results; brand-matching candidate.
  - Turn 13: `"Pellon" "distributor" OR "wholesale" OR "dealer" interfacing` -> 11 results; brand-matching candidate.
  - Turn 14: `"Pellon" "where to buy"` -> 11 results; brand-matching candidate.
  - Turn 15: `Freudenberg Nonwovens Pellon retailer wholesale account` -> 10 results; not independently classified.
  - Turn 16: `Pellon products buy wholesale direct` -> 11 results; brand-matching candidate.
- Browse calls:
  - Turn 6: `https://www.pellonprojects.com/` -> success; Browsed https://www.pellonprojects.com/; 2870 characters returned..
  - Turn 7: `https://www.pellonprojects.com/about/contact/` -> success; Browsed https://www.pellonprojects.com/about/contact/; 1588 characters returned..

### Rust-Oleum (AI-85393)

- Session: `AI-85393`. Status: `active`. Turns: 21. Raw tool calls: 21.
- Final sqld verdict: `MAYBE` / `MEDIUM`. Queue write: present; synced at `2026-07-14 05:44:12`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Rust-Oleum wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `Rust-Oleum Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `Rust-Oleum authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 4: `"Rust-Oleum" paint wholesale program distributor` -> 10 results; brand-matching candidate.
  - Turn 5: `"Rust-Oleum" Faire wholesale paint` -> 10 results; brand-matching candidate.
  - Turn 6: `"Rust-Oleum" authorized dealer reseller` -> 10 results; brand-matching candidate.
  - Turn 7: `Rustoleum wholesale spray paint distributor` -> 10 results; brand-matching candidate.
  - Turn 8: `Rust-Oleum dealer program wholesale account application` -> 10 results; brand-matching candidate.
  - Turn 12: `Rust-Oleum RPM wholesale distributor program become a dealer` -> 10 results; brand-matching candidate.
  - Turn 13: `Rust-Oleum Amazon reseller MAP policy restrictions` -> 10 results; brand-matching candidate.
  - Turn 15: `Rust-Oleum Faire.com wholesale paint coatings` -> 10 results; brand-matching candidate.
  - Turn 16: `Rustoleum rust-oleum dealer wholesale account become distributor` -> 10 results; brand-matching candidate.
  - Turn 17: `RPM Industrial Group Rust-Oleum wholesale distributor become reseller` -> 10 results; not independently classified.
- Browse calls:
  - Turn 9: `https://www.rustoleum.com/` -> success; Browsed https://www.rustoleum.com/; 5000 characters returned..
  - Turn 10: `https://www.rustoleum.com/Professionals` -> success; Browsed https://www.rustoleum.com/Professionals; 5000 characters returned..
  - Turn 11: `https://www.rustoleum.com/Recommended-Online-Retailers` -> success; Browsed https://www.rustoleum.com/Recommended-Online-Retailers; 3161 characters returned..
  - Turn 14: `https://www.rustoleum.com/Contact-Us` -> success; Browsed https://www.rustoleum.com/Contact-Us; 4192 characters returned..
  - Turn 18: `https://www.rpminc.com/` -> success; Browsed https://www.rpminc.com/; 5000 characters returned..
  - Turn 19: `https://www.zoro.com/rust-oleum/brand/00040817/` -> success; Browsed https://www.zoro.com/rust-oleum/brand/00040817/; 40 characters returned..
  - Turn 20: `https://www.grainger.com/category/rust-oleum/ecatalog/N-1z13dqv` -> success; Browsed https://www.grainger.com/category/rust-oleum/ecatalog/N-1z13dqv; 429 characters returned..
  - Turn 21: `https://www.amazon.com/stores/Rust-Oleum/page/D70F29D1-8B03-4F3F-9C90-83105D138856` -> success; Browsed https://www.amazon.com/stores/Rust-Oleum/page/D70F29D1-8B03-4F3F-9C90-83105D138856; 5000 characters returned..

### Muzzy (AI-85391)

- Session: `AI-85391`. Status: `active`. Turns: 13. Raw tool calls: 13.
- Final sqld verdict: `CLOSED` / `HIGH`. Queue write: present; synced at `2026-07-14 05:44:11`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Muzzy wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `Muzzy Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `Muzzy authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 4: `Muzzy BBC wholesale reseller program` -> 10 results; brand-matching candidate.
  - Turn 5: `Muzzy BBC bulk purchase distributor` -> 10 results; brand-matching candidate.
  - Turn 9: `Muzzy BBC Amazon reseller restrictions MAP policy` -> 10 results; brand-matching candidate.
  - Turn 10: `Growing Minds Media Muzzy wholesale distributor` -> 10 results; not independently classified.
- Browse calls:
  - Turn 6: `https://www.muzzybbc.com/` -> success; Browsed https://www.muzzybbc.com/; 2618 characters returned..
  - Turn 7: `https://www.muzzybbc.com/pages/muzzy-bbc-library` -> success; Browsed https://www.muzzybbc.com/pages/muzzy-bbc-library; 5000 characters returned..
  - Turn 8: `https://www.muzzybbc.com/pages/muzzy-bbc-classroom` -> success; Browsed https://www.muzzybbc.com/pages/muzzy-bbc-classroom; 5000 characters returned..
  - Turn 11: `https://www.muzzybbc.com/pages/about-us` -> success; Browsed https://www.muzzybbc.com/pages/about-us; 3492 characters returned..
  - Turn 12: `https://www.muzzybbc.com/pages/contact-us` -> success; Browsed https://www.muzzybbc.com/pages/contact-us; 2727 characters returned..
  - Turn 13: `https://www.muzzybbc.com/collections/all` -> success; Browsed https://www.muzzybbc.com/collections/all; 3990 characters returned..

### Bondhus (AI-85407)

- Session: `AI-85407`. Status: `active`. Turns: 9. Raw tool calls: 9.
- Final sqld verdict: `ACCESSIBLE` / `HIGH`. Queue write: present; synced at `2026-07-14 05:44:10`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Bondhus wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `Bondhus Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `Bondhus authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 4: `Bondhus dealer wholesale account` -> 10 results; brand-matching candidate.
  - Turn 8: `Bondhus MAP policy reseller restrictions` -> 10 results; brand-matching candidate.
- Browse calls:
  - Turn 5: `https://bondhus.com/` -> success; Browsed https://bondhus.com/; 5000 characters returned..
  - Turn 6: `https://bondhus.com/pages/USDistributor` -> success; Browsed https://bondhus.com/pages/USDistributor; 5000 characters returned..
  - Turn 7: `https://bondhus.com/pages/USAOnlineDistributors` -> success; Browsed https://bondhus.com/pages/USAOnlineDistributors; 5000 characters returned..
  - Turn 9: `https://bondhus.com/pages/us-distributors` -> success; Browsed https://bondhus.com/pages/us-distributors; 5000 characters returned..

### Wahl (AI-85400)

- Session: `AI-85400`. Status: `active`. Turns: 23. Raw tool calls: 23.
- Final sqld verdict: `CLOSED` / `HIGH`. Queue write: present; synced at `2026-07-14 05:44:14`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Wahl wholesale program` -> 10 results; not independently classified.
  - Turn 2: `Wahl Faire wholesale` -> 10 results; not independently classified.
  - Turn 3: `Wahl authorized distributor` -> 10 results; not independently classified.
  - Turn 4: `Wahl clipper wholesale dealer` -> 10 results; not independently classified.
  - Turn 5: `Wahl grooming products wholesale distributor` -> 10 results; not independently classified.
  - Turn 6: `wahl.com wholesale` -> 7 results; not independently classified.
  - Turn 7: `"Wahl" hair clippers brand` -> 10 results; not independently classified.
  - Turn 8: `wahl.com` -> 7 results; brand-matching candidate.
  - Turn 9: `Wahl wholesale dealer application` -> 9 results; not independently classified.
  - Turn 10: `Wahl professional dealer portal login` -> 7 results; not independently classified.
  - Turn 15: `Wahl MAP policy Amazon reseller restrictions` -> 10 results; brand-matching candidate.
  - Turn 18: `site:faire.com Wahl` -> 0 results; no results.
  - Turn 19: `Wahl B2B wholesale distributor USA` -> 10 results; brand-matching candidate.
  - Turn 21: `"Wahl" "MAP policy" reseller` -> 10 results; brand-matching candidate.
  - Turn 22: `Wahl wholesale distributor beauty supply online reseller` -> 10 results; brand-matching candidate.
- Browse calls:
  - Turn 11: `https://wahl.com` -> success; Browsed https://wahl.com; 4308 characters returned..
  - Turn 12: `https://wahlpro.com` -> success; Browsed https://wahlpro.com; 4999 characters returned..
  - Turn 13: `https://wahlusa.com` -> success; Browsed https://wahlusa.com; 5000 characters returned..
  - Turn 14: `https://www.wahlpro.com/sell-wahl-products` -> success; Browsed https://www.wahlpro.com/sell-wahl-products; 2941 characters returned..
  - Turn 16: `https://wahlusa.com/support` -> success; Browsed https://wahlusa.com/support; 2503 characters returned..
  - Turn 17: `https://wahlusa.com/support/retailers` -> success; Browsed https://wahlusa.com/support/retailers; 5000 characters returned..
  - Turn 20: `https://www.wahlpro.com/terms-of-purchase` -> success; Browsed https://www.wahlpro.com/terms-of-purchase; 4719 characters returned..
  - Turn 23: `https://www.wahlpro.com/barber-stylist` -> success; Browsed https://www.wahlpro.com/barber-stylist; 5000 characters returned..

### Brava (brava-research-001)

- Session: `brava-research-001`. Status: `active`. Turns: 15. Raw tool calls: 15.
- Final sqld verdict: `INCONCLUSIVE` / `LOW`. Queue write: present; synced at `2026-07-14 05:44:13`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Brava wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `Brava Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `Brava authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 4: `B01CUU3VKS Brava product` -> 10 results; not independently classified.
  - Turn 5: `Brava Home oven wholesale` -> 10 results; brand-matching candidate.
  - Turn 6: `Brava cooking system wholesale program` -> 10 results; brand-matching candidate.
  - Turn 7: `"B01CUU3VKS" Amazon` -> 10 results; not independently classified.
  - Turn 8: `"Brava" brand kitchen home` -> 10 results; brand-matching candidate.
  - Turn 9: `Brava products official website` -> 10 results; brand-matching candidate.
  - Turn 10: `Brava -Brave -browser oven cooktop` -> 10 results; brand-matching candidate.
  - Turn 11: `bravahome.com smart oven wholesale retailer` -> 10 results; not independently classified.
  - Turn 12: `"brava" "wholesale" "dealer" -Brave -browser` -> 10 results; brand-matching candidate.
  - Turn 13: `"Brava" home smart oven` -> 10 results; brand-matching candidate.
  - Turn 14: `Brava Home smart oven company wholesale retailers` -> 10 results; brand-matching candidate.
  - Turn 15: `"Brava Home" wholesale distributor` -> 10 results; brand-matching candidate.
- Browse calls:
  - None recorded.

### Cableguys (cableguys-research)

- Session: `cableguys-research`. Status: `active`. Turns: 31. Raw tool calls: 31.
- Final sqld verdict: `INCONCLUSIVE` / `LOW`. Queue write: present; synced at `2026-07-14 05:44:15`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Cableguys wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `Cableguys Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `Cableguys authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 4: `B0875394DP Cableguys` -> 10 results; not independently classified.
  - Turn 5: `Cable Guys gaming controller holder wholesale` -> 10 results; not independently classified.
  - Turn 6: `wecableguys.com wholesale` -> 10 results; not independently classified.
  - Turn 7: `"B0875394DP" Amazon product` -> 10 results; not independently classified.
  - Turn 8: `Cable Guys brand wholesale dealer program` -> 10 results; not independently classified.
  - Turn 11: `"Cable Guys" wholesale reseller program` -> 10 results; not independently classified.
  - Turn 12: `"Cable Guys" controller holder distributor` -> 10 results; not independently classified.
  - Turn 13: `"wecableguys" wholesale` -> 10 results; not independently classified.
  - Turn 14: `Faire "Cable Guys" controller` -> 10 results; not independently classified.
  - Turn 15: `site:faire.com "Cable Guys"` -> 0 results; no results.
  - Turn 16: `"Cable Guys" controller holder Amazon reseller restrictions MAP` -> 10 results; not independently classified.
  - Turn 17: `"Cable Guys" brand gaming controller holder wholesale account` -> 10 results; not independently classified.
  - Turn 18: `Cable Guys controller holder B2B bulk order` -> 10 results; not independently classified.
  - Turn 19: `"Cable Guys" "controller holder" wholesale -spectrum` -> 10 results; not independently classified.
  - Turn 22: `"Cable Guys" controller holder manufacturer company` -> 10 results; not independently classified.
  - Turn 23: `Amazon storefront 19339044011 Cable Guys brand` -> 10 results; not independently classified.
  - Turn 24: `"Cable Guys" gaming accessories brand owner company` -> 10 results; not independently classified.
  - Turn 25: `"Cable Guys" controller holder Faire wholesale -spectrum -tv -internet` -> 10 results; not independently classified.
  - Turn 26: `B0875394DP cable guy controller holder` -> 10 results; not independently classified.
  - Turn 27: `ShaperBox HalfTime Cableguys wholesale reseller` -> 10 results; brand-matching candidate.
  - Turn 29: `"Cable Guys" brand "officially licensed" Marvel controller holder wholesale` -> 10 results; not independently classified.
  - Turn 30: `"Cable Guys" controller holder trademark company` -> 10 results; not independently classified.
  - Turn 31: `Auth-Brand Cable Guys distributor` -> 10 results; not independently classified.
- Browse calls:
  - Turn 9: `https://www.cableguys.com/` -> success; Browsed https://www.cableguys.com/; 3172 characters returned..
  - Turn 10: `https://wecableguys.com/` -> success; Browsed https://wecableguys.com/; 5000 characters returned..
  - Turn 20: `https://wecableguys.com/contact/` -> success; Browsed https://wecableguys.com/contact/; 777 characters returned..
  - Turn 21: `https://wecableguys.com/#about` -> success; Browsed https://wecableguys.com/#about; 5000 characters returned..
  - Turn 28: `https://www.amazon.com/dp/B0875394DP` -> success; Browsed https://www.amazon.com/dp/B0875394DP; 5000 characters returned..

### Cameron's Coffee (camerons-coffee-research)

- Session: `camerons-coffee-research`. Status: `active`. Turns: 23. Raw tool calls: 23.
- Final sqld verdict: `MAYBE` / `MEDIUM`. Queue write: present; synced at `2026-07-14 05:44:15`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Cameron's Coffee wholesale program` -> 9 results; brand-matching candidate.
  - Turn 2: `Cameron's Coffee Faire wholesale` -> 9 results; brand-matching candidate.
  - Turn 3: `Cameron's Coffee authorized distributor` -> 9 results; brand-matching candidate.
  - Turn 4: `"Cameron's Coffee" wholesale coffee roaster` -> 9 results; brand-matching candidate.
  - Turn 5: `"Cameron's Coffee" wholesale program retailer` -> 9 results; brand-matching candidate.
  - Turn 6: `Camerons Coffee roaster wholesale account` -> 10 results; not independently classified.
  - Turn 7: `camerons coffee .com wholesale` -> 10 results; not independently classified.
  - Turn 8: `cameronscoffee.com` -> 10 results; brand-matching candidate.
  - Turn 11: `"Cameron's Coffee" wholesale distributor application` -> 9 results; brand-matching candidate.
  - Turn 13: `Camerons Coffee wholesale distributor reseller` -> 10 results; not independently classified.
  - Turn 15: `site:faire.com Camerons Coffee` -> 0 results; no results.
  - Turn 16: `Cameron's Coffee Amazon MAP policy reseller restrictions` -> 9 results; brand-matching candidate.
  - Turn 17: `"Cameron's Coffee" bulk wholesale coffee supplier` -> 9 results; brand-matching candidate.
  - Turn 18: `cameronscoffee.com wholesale become a retailer distributor` -> 10 results; not independently classified.
  - Turn 19: `"Cameron's" coffee Shakopee wholesale` -> 9 results; brand-matching candidate.
  - Turn 21: `Camerons Coffee parent company owner` -> 9 results; not independently classified.
  - Turn 23: `Grupo Nutresa Camerons Coffee wholesale distribution United States` -> 10 results; not independently classified.
- Browse calls:
  - Turn 9: `https://www.cameronscoffee.com/` -> success; Browsed https://www.cameronscoffee.com/; 4772 characters returned..
  - Turn 10: `https://www.cameronscoffee.com/pages/contact` -> success; Browsed https://www.cameronscoffee.com/pages/contact; 2922 characters returned..
  - Turn 12: `http://g2p1.trans411.com/gen2portal/login.jsp` -> success; Browsed http://g2p1.trans411.com/gen2portal/login.jsp; 167 characters returned..
  - Turn 14: `https://www.cameronscoffee.com/pages/faq` -> success; Browsed https://www.cameronscoffee.com/pages/faq; 5000 characters returned..
  - Turn 20: `https://www.cameronscoffee.com/pages/about-camerons` -> success; Browsed https://www.cameronscoffee.com/pages/about-camerons; 4998 characters returned..
  - Turn 22: `https://www.cameronscoffee.com/pages/wholesale` -> success; Browsed https://www.cameronscoffee.com/pages/wholesale; 2597 characters returned..

### Captain Rodney's (captain-rodneys-research)

- Session: `captain-rodneys-research`. Status: `active`. Turns: 23. Raw tool calls: 23.
- Final sqld verdict: `INCONCLUSIVE` / `LOW`. Queue write: present; synced at `2026-07-14 05:44:16`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Captain Rodney's wholesale program` -> 2 results; generic/irrelevant per final verdict.
  - Turn 2: `Captain Rodney's Faire wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 3: `Captain Rodney's authorized distributor` -> 10 results; generic/irrelevant per final verdict.
  - Turn 4: `"Captain Rodney's" bourbon glaze wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 5: `"Captain Rodney's" sauce wholesale distributor` -> 10 results; generic/irrelevant per final verdict.
  - Turn 6: `captainrodneys.com` -> 10 results; generic/irrelevant per final verdict.
  - Turn 7: `"Captain Rodney's" food sauce` -> 10 results; generic/irrelevant per final verdict.
  - Turn 8: `Rodney's bourbon glaze wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 9: `B06XJCWHGB Captain Rodney's` -> 10 results; generic/irrelevant per final verdict.
  - Turn 12: `captainrodneys` -> 10 results; generic/irrelevant per final verdict.
  - Turn 14: `"Captain Rodney's" "Boucan" wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 15: `"Sebago Distribution" "Captain Rodney"` -> 10 results; generic/irrelevant per final verdict.
  - Turn 16: `Captain Rodney Boucan glaze store` -> 10 results; generic/irrelevant per final verdict.
  - Turn 18: `"Captain Rodney" boucan pepper glaze Amazon store` -> 10 results; generic/irrelevant per final verdict.
  - Turn 21: `"Captain Rodney's" food gift wholesale` -> 10 results; generic/irrelevant per final verdict.
  - Turn 22: `"Sebago Distribution" wholesale food distributor` -> 10 results; generic/irrelevant per final verdict.
  - Turn 23: `captain rodneys boucan pepper glaze buy wholesale case` -> 10 results; generic/irrelevant per final verdict.
- Browse calls:
  - Turn 10: `https://captainrodneys.com` -> site certificate error; browse_page failed for https://captainrodneys.com: Page.goto: net::ERR_CERT_AUTHORITY_INVALID at https://captainrodneys.com/ Call log:   - navigating to "https://captainrodneys.com/", waiting until "domcontentloaded".
  - Turn 11: `https://www.captainrodneys.com` -> site certificate error; browse_page failed for https://www.captainrodneys.com: Page.goto: net::ERR_CERT_AUTHORITY_INVALID at https://www.captainrodneys.com/ Call log:   - navigating to "https://www.captainrodneys.com/", waiting until "domcontentloaded".
  - Turn 13: `https://www.amazon.com/dp/B06XJCWHGB` -> success; Browsed https://www.amazon.com/dp/B06XJCWHGB; 5000 characters returned..
  - Turn 17: `https://www.faire.com/search?q=captain+rodney` -> success; Browsed https://www.faire.com/search?q=captain+rodney; 3174 characters returned..
  - Turn 19: `https://www.faire.com/brand/search?q=captain+rodneys` -> success; Browsed https://www.faire.com/brand/search?q=captain+rodneys; 5000 characters returned..
  - Turn 20: `https://www.amazon.com/stores/page/2A1F5E0C-157A-45FF-8081-41C7486F4926` -> success; Browsed https://www.amazon.com/stores/page/2A1F5E0C-157A-45FF-8081-41C7486F4926; 386 characters returned..

### Carna4 (carna4-worker)

- Session: `carna4-001`. Status: `active`. Turns: 20. Raw tool calls: 20.
- Final sqld verdict: `ACCESSIBLE` / `MEDIUM`. Queue write: present; synced at `2026-07-14 05:44:16`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `CARNA 4 wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `CARNA 4 Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `CARNA 4 authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 4: `B011D61H6K CARNA 4` -> 1 results; not independently classified.
  - Turn 5: `"Carna4" dog food wholesale` -> 10 results; not independently classified.
  - Turn 6: `Carna4 dog food wholesale program` -> 10 results; not independently classified.
  - Turn 7: `Carna4 dog food dealer application retailer` -> 10 results; not independently classified.
  - Turn 8: `site:carna4.com wholesale retailer` -> 0 results; no results.
  - Turn 9: `Carna4 pet food Faire.com wholesale` -> 10 results; not independently classified.
  - Turn 13: `Carna4 Amazon MAP policy reseller restrictions` -> 9 results; not independently classified.
  - Turn 14: `Carna4 dog food Amazon restrictions authorized reseller` -> 10 results; not independently classified.
  - Turn 15: `"Carna4" Amazon dog food` -> 10 results; not independently classified.
  - Turn 17: `Carna4 pet food wholesale distributor Canada` -> 10 results; not independently classified.
- Browse calls:
  - Turn 10: `https://carna4.com` -> success; Browsed https://carna4.com; 4244 characters returned..
  - Turn 11: `https://carna4.com/buy-now/dealer-signup/` -> success; Browsed https://carna4.com/buy-now/dealer-signup/; 3092 characters returned..
  - Turn 12: `https://carna4.com/community/#retailerresources` -> success; Browsed https://carna4.com/community/#retailerresources; 5000 characters returned..
  - Turn 16: `https://carna4.com/buy-now/#buy-online` -> success; Browsed https://carna4.com/buy-now/#buy-online; 5000 characters returned..
  - Turn 18: `https://www.amazon.com/dp/B011D61H6K` -> success; Browsed https://www.amazon.com/dp/B011D61H6K; 5000 characters returned..
  - Turn 19: `https://carna4.com/community/carna4-dealer-resources/` -> success; Browsed https://carna4.com/community/carna4-dealer-resources/; 2474 characters returned..
  - Turn 20: `https://carna4.com/privacy-policy` -> success; Browsed https://carna4.com/privacy-policy; 5000 characters returned..

### Honees (AI-85429)

- Session: `AI-85429`. Status: `active`. Turns: 7. Raw tool calls: 7.
- Final sqld verdict: `ACCESSIBLE` / `HIGH`. Queue write: present; synced at `2026-07-14 05:44:17`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Honees wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `Honees Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `Honees authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 7: `Honees MAP policy Amazon reseller restrictions` -> 10 results; brand-matching candidate.
- Browse calls:
  - Turn 4: `https://honees.com/` -> success; Browsed https://honees.com/; 5000 characters returned..
  - Turn 5: `https://www.faire.com/direct/andrepostinc` -> success; Browsed https://www.faire.com/direct/andrepostinc; 4387 characters returned..
  - Turn 6: `https://honees.com/contact-us/` -> success; Browsed https://honees.com/contact-us/; 4999 characters returned..

### Calmoseptine (AI-85413)

- Session: `AI-85413`. Status: `active`. Turns: 8. Raw tool calls: 8.
- Final sqld verdict: `ACCESSIBLE` / `HIGH`. Queue write: present; synced at `2026-07-14 05:44:18`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Calmoseptine wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `Calmoseptine Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `Calmoseptine authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 8: `Calmoseptine MAP policy Amazon reseller restrictions` -> 10 results; brand-matching candidate.
- Browse calls:
  - Turn 4: `http://calmoseptineointment.com/` -> success; Browsed http://calmoseptineointment.com/; 2917 characters returned..
  - Turn 5: `https://calmoseptineointment.com/purchasing-wholesalers` -> success; Browsed https://calmoseptineointment.com/purchasing-wholesalers; 2756 characters returned..
  - Turn 6: `https://calmoseptineointment.com/purchasing-distributors` -> success; Browsed https://calmoseptineointment.com/purchasing-distributors; 2757 characters returned..
  - Turn 7: `https://calmoseptineointment.com/united-states-purchasing-and-pricing` -> success; Browsed https://calmoseptineointment.com/united-states-purchasing-and-pricing; 5000 characters returned..

### elleebana (AI-85420)

- Session: `AI-85420`. Status: `active`. Turns: 16. Raw tool calls: 16.
- Final sqld verdict: `MAYBE` / `MEDIUM`. Queue write: present; synced at `2026-07-14 05:44:19`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `elleebana wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `elleebana Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `elleebana authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 4: `elleebana become a distributor wholesale account` -> 10 results; brand-matching candidate.
  - Turn 5: `elleebana Faire` -> 10 results; brand-matching candidate.
  - Turn 14: `elleebana Amazon MAP policy reseller restrictions` -> 10 results; brand-matching candidate.
  - Turn 15: `elleebana on Amazon seller` -> 10 results; brand-matching candidate.
- Browse calls:
  - Turn 6: `https://elleebana.com/` -> success; Browsed https://elleebana.com/; 5000 characters returned..
  - Turn 7: `https://elleebana.com/where-to-buy/` -> success; Browsed https://elleebana.com/where-to-buy/; 3250 characters returned..
  - Turn 8: `https://elleebana-usa.com/` -> success; Browsed https://elleebana-usa.com/; 5000 characters returned..
  - Turn 9: `https://elleebana-usa.myshopify.com/` -> success; Browsed https://elleebana-usa.myshopify.com/; 2897 characters returned..
  - Turn 10: `https://elleebana-usa.com/who-we-are/` -> success; Browsed https://elleebana-usa.com/who-we-are/; 5000 characters returned..
  - Turn 11: `https://elleebana-usa.com/contact-us/` -> success; Browsed https://elleebana-usa.com/contact-us/; 2799 characters returned..
  - Turn 12: `https://elleebana-usa.com/sub-distributor-application/` -> success; Browsed https://elleebana-usa.com/sub-distributor-application/; 3570 characters returned..
  - Turn 13: `https://www.elleebana.com/contact-us/i-want-to-become-a-distributor/` -> success; Browsed https://www.elleebana.com/contact-us/i-want-to-become-a-distributor/; 5000 characters returned..
  - Turn 16: `https://www.amazon.com/dp/B07DL26FMY` -> success; Browsed https://www.amazon.com/dp/B07DL26FMY; 5000 characters returned..

### Coast Soap (AI-85414)

- Session: `AI-85414`. Status: `active`. Turns: 31. Raw tool calls: 31.
- Final sqld verdict: `CLOSED` / `HIGH`. Queue write: present; synced at `2026-07-14 05:44:19`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Coast wholesale program dealer application` -> 10 results; brand-matching candidate.
  - Turn 2: `Coast Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `Coast authorized distributor wholesale` -> 10 results; brand-matching candidate.
  - Turn 4: `B07B7FVFBX Coast Amazon` -> 10 results; not independently classified.
  - Turn 5: `Coast brand home fragrance candles wholesale` -> 10 results; brand-matching candidate.
  - Turn 6: `"Coast" brand flashlight wholesale distributor` -> 10 results; brand-matching candidate.
  - Turn 7: `Coast soap detergent brand wholesale` -> 10 results; brand-matching candidate.
  - Turn 8: `ASIN B07B7FVFBX product name` -> 10 results; not independently classified.
  - Turn 9: `"Coast" "brand" "B07B7FVFBX" Amazon product` -> 10 results; brand-matching candidate.
  - Turn 11: `"Coast" "deodorant soap" wholesale program distributor` -> 10 results; brand-matching candidate.
  - Turn 12: `Coast soap Faire wholesale marketplace` -> 10 results; brand-matching candidate.
  - Turn 13: `"Coast" bar soap brand manufacturer company` -> 10 results; brand-matching candidate.
  - Turn 14: `"Coast" "bar soap" website official` -> 10 results; brand-matching candidate.
  - Turn 16: `"Coast" soap brand "High Ridge" or "Dial" or brand owner` -> 10 results; brand-matching candidate.
  - Turn 17: `Coast soap website "coastsoap.com" OR "coastbarsoap"` -> 10 results; brand-matching candidate.
  - Turn 18: `"Coast" "deodorant soap" Wikipedia brand history` -> 10 results; brand-matching candidate.
  - Turn 19: `site:wikipedia.org "Coast" soap brand` -> 0 results; no results.
  - Turn 23: `Sodalis USA wholesale distributor Coast soap` -> 10 results; not independently classified.
  - Turn 26: `Sodalis USA wholesale account reseller application` -> 10 results; not independently classified.
  - Turn 27: `"High Ridge Brands" wholesale distributor application` -> 10 results; not independently classified.
  - Turn 28: `"Sodalis USA" wholesale become retailer` -> 10 results; not independently classified.
  - Turn 29: `"Sodalis USA" "Coast" "Zest" wholesale retailer account` -> 10 results; not independently classified.
- Browse calls:
  - Turn 10: `https://www.amazon.com/dp/B07B7FVFBX` -> success; Browsed https://www.amazon.com/dp/B07B7FVFBX; 5000 characters returned..
  - Turn 15: `https://www.amazon.com/stores/Coast/page/9C1BB276-91D5-4C33-947F-24A9C23379EA` -> success; Browsed https://www.amazon.com/stores/Coast/page/9C1BB276-91D5-4C33-947F-24A9C23379EA; 5000 characters returned..
  - Turn 20: `https://en.wikipedia.org/wiki/Coast_(soap)` -> success; Browsed https://en.wikipedia.org/wiki/Coast_(soap); 5000 characters returned..
  - Turn 21: `http://www.coastsoap.com/` -> success; Browsed http://www.coastsoap.com/; 1022 characters returned..
  - Turn 22: `https://www.coastsoap.com/faqs` -> success; Browsed https://www.coastsoap.com/faqs; 1046 characters returned..
  - Turn 24: `https://www.coastsoap.com/terms-of-service` -> success; Browsed https://www.coastsoap.com/terms-of-service; 1480 characters returned..
  - Turn 25: `https://sodalisgroup.com/en` -> success; Browsed https://sodalisgroup.com/en; 3964 characters returned..
  - Turn 30: `https://sodalisgroup.com/en/contacts` -> success; Browsed https://sodalisgroup.com/en/contacts; 3745 characters returned..
  - Turn 31: `https://sodalisgroup.com/en/about-us` -> success; Browsed https://sodalisgroup.com/en/about-us; 5000 characters returned..

### emuaid (AI-85421)

- Session: `AI-85421`. Status: `active`. Turns: 11. Raw tool calls: 11.
- Final sqld verdict: `ACCESSIBLE` / `MEDIUM`. Queue write: present; synced at `2026-07-14 05:44:18`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `emuaid wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `emuaid Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `emuaid authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 4: `emuaid wholesale` -> 10 results; brand-matching candidate.
  - Turn 5: `emuaid dealer reseller` -> 10 results; brand-matching candidate.
  - Turn 8: `emuaid Amazon MAP policy reseller restrictions` -> 10 results; brand-matching candidate.
- Browse calls:
  - Turn 6: `https://www.emuaid.com/` -> success; Browsed https://www.emuaid.com/; 4999 characters returned..
  - Turn 7: `https://www.emuaid.com/pages/wholesale-form` -> success; Browsed https://www.emuaid.com/pages/wholesale-form; 3873 characters returned..
  - Turn 9: `https://www.emuaid.com/pages/store-locator` -> success; Browsed https://www.emuaid.com/pages/store-locator; 3780 characters returned..
  - Turn 10: `https://www.emuaid.com/pages/contact-us` -> success; Browsed https://www.emuaid.com/pages/contact-us; 4344 characters returned..
  - Turn 11: `https://www.emuaid.com/pages/about` -> success; Browsed https://www.emuaid.com/pages/about; 5000 characters returned..

### Mr. Bar-B-Q (AI-85437)

- Session: `AI-85437`. Status: `active`. Turns: 16. Raw tool calls: 16.
- Final sqld verdict: `ACCESSIBLE` / `HIGH`. Queue write: present; synced at `2026-07-14 05:44:20`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Mr. Bar-B-Q wholesale program` -> 10 results; not independently classified.
  - Turn 2: `Mr. Bar-B-Q Faire wholesale` -> 10 results; not independently classified.
  - Turn 3: `Mr. Bar-B-Q authorized distributor` -> 10 results; not independently classified.
  - Turn 4: `"Mr Bar-B-Q" wholesale barbecue grilling accessories` -> 10 results; not independently classified.
  - Turn 5: `"Mr Bar-B-Q" company distributor` -> 10 results; not independently classified.
  - Turn 6: `"Mr BBQ" grill accessories wholesale` -> 10 results; not independently classified.
  - Turn 7: `B099FKMBVL brand manufacturer` -> 10 results; not independently classified.
  - Turn 8: `"Mr. Bar-B-Q" Amazon brand` -> 10 results; not independently classified.
  - Turn 9: `Mr Barbecue brand grilling tools` -> 10 results; not independently classified.
  - Turn 10: `"mrbarbq" OR "mister barbecue" wholesale` -> 10 results; not independently classified.
  - Turn 14: `"Mr. Bar-B-Q" MAP policy Amazon reseller restrictions` -> 10 results; not independently classified.
  - Turn 15: `"Mr. Bar-B-Q" Faire wholesale marketplace` -> 10 results; not independently classified.
- Browse calls:
  - Turn 11: `https://mrbarbq.com/` -> success; Browsed https://mrbarbq.com/; 4611 characters returned..
  - Turn 12: `https://mrbarbq.com/contact/` -> success; Browsed https://mrbarbq.com/contact/; 3223 characters returned..
  - Turn 13: `https://mrbarbqproducts.com/` -> success; Browsed https://mrbarbqproducts.com/; 3202 characters returned..
  - Turn 16: `https://mrbarbqproducts.com/contact-us/` -> success; Browsed https://mrbarbqproducts.com/contact-us/; 1429 characters returned..

### Mielle Organics (AI-85436)

- Session: `AI-85436`. Status: `active`. Turns: 20. Raw tool calls: 20.
- Final sqld verdict: `CLOSED` / `HIGH`. Queue write: present; synced at `2026-07-14 05:44:22`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Mielle Organics wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `Mielle Organics Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `Mielle Organics authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 4: `Mielle Organics wholesale account retailer sign up` -> 10 results; brand-matching candidate.
  - Turn 5: `"Mielle Organics" wholesale distributor login` -> 10 results; brand-matching candidate.
  - Turn 8: `Mielle Organics professional salon wholesale` -> 10 results; brand-matching candidate.
  - Turn 9: `Mielle Organics Amazon reseller policy` -> 10 results; brand-matching candidate.
  - Turn 11: `"Mielle" "wholesale" "distributor" -target -walmart` -> 10 results; brand-matching candidate.
  - Turn 13: `Mielle Organics B2B portal wholesale account` -> 10 results; brand-matching candidate.
  - Turn 14: `site:faire.com Mielle Organics` -> 0 results; no results.
  - Turn 15: `Mielle Organics P&G distribution wholesale` -> 10 results; brand-matching candidate.
  - Turn 16: `Mielle Organics Amazon seller central` -> 10 results; not independently classified.
  - Turn 17: `"Mielle Organics" "wholesale" "retailer" "apply"` -> 10 results; brand-matching candidate.
  - Turn 18: `buy Mielle Organics wholesale beauty supply distributor` -> 10 results; not independently classified.
  - Turn 19: `Mielle Organics MAP policy Amazon` -> 10 results; brand-matching candidate.
- Browse calls:
  - Turn 6: `https://mielleorganics.com/` -> success; Browsed https://mielleorganics.com/; 4998 characters returned..
  - Turn 7: `https://mielleorganics.com/pages/wholesale` -> success; Browsed https://mielleorganics.com/pages/wholesale; 3964 characters returned..
  - Turn 10: `https://mielleorganics.com/pages/mielle-and-pg-faqs` -> success; Browsed https://mielleorganics.com/pages/mielle-and-pg-faqs; 4033 characters returned..
  - Turn 12: `https://mielleorganics.com/pages/contact` -> success; Browsed https://mielleorganics.com/pages/contact; 3895 characters returned..
  - Turn 20: `https://www.amazon.com/dp/B0BXZ73HDG` -> success; Browsed https://www.amazon.com/dp/B0BXZ73HDG; 5000 characters returned..

### Jacobs (AI-85430)

- Session: `AI-85430`. Status: `active`. Turns: 26. Raw tool calls: 26.
- Final sqld verdict: `INCONCLUSIVE` / `MEDIUM`. Queue write: present; synced at `2026-07-14 05:44:21`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Jacobs wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `Jacobs Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `Jacobs authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 4: `B00IT6A4HG Jacobs Amazon` -> 10 results; not independently classified.
  - Turn 5: `B001GVIT6E Jacobs Amazon` -> 10 results; not independently classified.
  - Turn 6: `"Jacobs" brand Amazon product` -> 10 results; brand-matching candidate.
  - Turn 7: `Jacobs coffee wholesale` -> 10 results; brand-matching candidate.
  - Turn 8: `B00IT6A4HG product Amazon` -> 10 results; not independently classified.
  - Turn 9: `B001GVIT6E product Amazon` -> 10 results; not independently classified.
  - Turn 10: `"Jacobs" coffee brand Amazon wholesale reseller` -> 10 results; brand-matching candidate.
  - Turn 11: `"Jacobs" brand wholesale distributor coffee` -> 10 results; brand-matching candidate.
  - Turn 12: `B00IT6A4HG ASIN product name` -> 10 results; not independently classified.
  - Turn 13: `B001GVIT6E ASIN product name` -> 10 results; not independently classified.
  - Turn 14: `site:amazon.com "Jacobs" brand` -> 0 results; no results.
  - Turn 15: `Jacobs brand wholesale Amazon reseller program` -> 10 results; brand-matching candidate.
  - Turn 16: `B00IT6A4HG B001GVIT6E` -> 10 results; not independently classified.
  - Turn 19: `Jacobs Douwe Egberts wholesale program distributor` -> 10 results; brand-matching candidate.
  - Turn 20: `"Jacobs Kronung" wholesale distributor` -> 10 results; brand-matching candidate.
  - Turn 21: `"JDE" "Jacobs" wholesale coffee reseller` -> 10 results; not independently classified.
  - Turn 22: `"Jacobs Kr?nung" wholesale coffee USA import` -> 10 results; brand-matching candidate.
  - Turn 23: `Jacobs coffee Faire wholesale marketplace` -> 10 results; brand-matching candidate.
  - Turn 24: `"Jacobs" "coffee" authorized distributor USA` -> 10 results; brand-matching candidate.
  - Turn 25: `"Jacobs Kronung" coffee wholesale -"Jacobs Solutions" -engineering` -> 10 results; brand-matching candidate.
  - Turn 26: `"JDE" "Jacobs Douwe Egberts" wholesale coffee USA` -> 10 results; not independently classified.
- Browse calls:
  - Turn 17: `https://www.amazon.com/dp/B00IT6A4HG` -> success; Browsed https://www.amazon.com/dp/B00IT6A4HG; 5000 characters returned..
  - Turn 18: `https://www.amazon.com/dp/B001GVIT6E` -> success; Browsed https://www.amazon.com/dp/B001GVIT6E; 5000 characters returned..

### NKOK (AI-85440)

- Session: `AI-85440`. Status: `active`. Turns: 10. Raw tool calls: 10.
- Final sqld verdict: `MAYBE` / `MEDIUM`. Queue write: present; synced at `2026-07-14 05:44:20`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `NKOK wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `NKOK Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `NKOK authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 7: `NKOK wholesale dealer account application` -> 10 results; brand-matching candidate.
  - Turn 8: `NKOK toys wholesale distributor` -> 10 results; brand-matching candidate.
  - Turn 9: `NKOK MAP policy Amazon reseller restrictions` -> 10 results; brand-matching candidate.
  - Turn 10: `"NKOK" "wholesale" "reseller"` -> 10 results; brand-matching candidate.
- Browse calls:
  - Turn 4: `https://www.nkok.com/` -> success; Browsed https://www.nkok.com/; 1582 characters returned..
  - Turn 5: `https://www.nkok.com/contact-us` -> success; Browsed https://www.nkok.com/contact-us; 1703 characters returned..
  - Turn 6: `https://www.nkok.com/about-us` -> success; Browsed https://www.nkok.com/about-us; 4832 characters returned..

### MTM (AI-85438)

- Session: `AI-85438`. Status: `active`. Turns: 16. Raw tool calls: 16.
- Final sqld verdict: `ACCESSIBLE` / `HIGH`. Queue write: present; synced at `2026-07-14 05:44:21`.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `MTM wholesale program` -> 10 results; not independently classified.
  - Turn 2: `MTM Faire wholesale` -> 10 results; not independently classified.
  - Turn 3: `MTM authorized distributor` -> 10 results; not independently classified.
  - Turn 4: `B00I8NJM5K MTM` -> 10 results; not independently classified.
  - Turn 5: `MTM brand wholesale reseller` -> 10 results; not independently classified.
  - Turn 6: `"B00I8NJM5K" product` -> 10 results; not independently classified.
  - Turn 7: `"B08X5XV63Q" product` -> 10 results; not independently classified.
  - Turn 8: `MTM Case-Gard wholesale distributor` -> 10 results; not independently classified.
  - Turn 9: `"MTM" "ammo box" wholesale` -> 10 results; not independently classified.
  - Turn 10: `"MTM Products" wholesale dealer account` -> 10 results; not independently classified.
  - Turn 11: `mtmcasegard.com wholesale` -> 10 results; not independently classified.
  - Turn 14: `MTM Case-Gard MAP policy Amazon reseller restrictions` -> 10 results; not independently classified.
- Browse calls:
  - Turn 12: `https://mtmcase-gard.com/` -> success; Browsed https://mtmcase-gard.com/; 5000 characters returned..
  - Turn 13: `https://mtmcase-gard.com/pages/dealer-inquiry` -> success; Browsed https://mtmcase-gard.com/pages/dealer-inquiry; 4849 characters returned..
  - Turn 15: `https://mtmcase-gard.com/pages/contact-us` -> success; Browsed https://mtmcase-gard.com/pages/contact-us; 4310 characters returned..
  - Turn 16: `https://mtmcase-gard.com/policies/terms-of-service` -> success; Browsed https://mtmcase-gard.com/policies/terms-of-service; 5000 characters returned..

### Plink (AI-85442)

- Session: `AI-85442`. Status: `active`. Turns: 7. Raw tool calls: 7.
- Final sqld verdict: not present for this session/brand at report snapshot. No direct `record_verdict` tool result was logged.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `Plink wholesale program` -> 10 results; not independently classified.
  - Turn 2: `Plink Faire wholesale` -> 9 results; not independently classified.
  - Turn 3: `Plink authorized distributor` -> 10 results; not independently classified.
  - Turn 4: `Plink brand sound machine sleep` -> 10 results; not independently classified.
  - Turn 5: `Plink brand Amazon wholesale` -> 10 results; not independently classified.
  - Turn 6: `B07T9G3CGX Plink Amazon` -> 10 results; not independently classified.
  - Turn 7: `"Plink" brand sleep device website` -> 10 results; not independently classified.
- Browse calls:
  - None recorded.

### ZOUT (AI-85451)

- Session: `AI-85451`. Status: `active`. Turns: 7. Raw tool calls: 6.
- Final sqld verdict: not present for this session/brand at report snapshot. No direct `record_verdict` tool result was logged.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `ZOUT wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `ZOUT Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `ZOUT authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 4: `Summit Brands wholesale program reseller` -> 10 results; not independently classified.
  - Turn 5: `ZOUT laundry stain remover wholesale account` -> 10 results; brand-matching candidate.
  - Turn 7: `ZOUT site:faire.com` -> 0 results; no results.
- Browse calls:
  - None recorded.

### ALPHA LION (AI-85454)

- Session: `AI-85454`. Status: `active`. Turns: 6. Raw tool calls: 6.
- Final sqld verdict: not present for this session/brand at report snapshot. No direct `record_verdict` tool result was logged.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `ALPHA LION wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `ALPHA LION Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `ALPHA LION authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 4: `"ALPHA LION" supplements wholesale` -> 10 results; brand-matching candidate.
  - Turn 5: `"ALPHA LION" pre-workout wholesale distributor` -> 10 results; brand-matching candidate.
  - Turn 6: `alphalion.com wholesale` -> 10 results; brand-matching candidate.
- Browse calls:
  - None recorded.

### SureFire (AI-85447)

- Session: `AI-85447`. Status: `active`. Turns: 5. Raw tool calls: 5.
- Final sqld verdict: not present for this session/brand at report snapshot. No direct `record_verdict` tool result was logged.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `SureFire wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `SureFire Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `SureFire authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 4: `SureFire dealer application wholesale account` -> 10 results; brand-matching candidate.
  - Turn 5: `SureFire MAP policy Amazon reseller restrictions` -> 10 results; brand-matching candidate.
- Browse calls:
  - None recorded.

### Port Authority (85443)

- Session: `85443`. Status: `active`. Turns: 7. Raw tool calls: 7.
- Final sqld verdict: not present for this session/brand at report snapshot. No direct `record_verdict` tool result was logged.
- `acquire_cdp`: no direct call record in the Node context store.
- Search calls:
  - Turn 1: `"Port Authority" wholesale program` -> 10 results; brand-matching candidate.
  - Turn 2: `"Port Authority" Faire wholesale` -> 10 results; brand-matching candidate.
  - Turn 3: `"Port Authority" authorized distributor` -> 10 results; brand-matching candidate.
  - Turn 4: `"Port Authority" apparel wholesale` -> 10 results; brand-matching candidate.
  - Turn 5: `"Port Authority" clothing brand SanMar` -> 10 results; brand-matching candidate.
  - Turn 6: `"Port Authority" "SanMar" wholesale` -> 10 results; brand-matching candidate.
  - Turn 7: `"Port Authority" jackets wholesale distributor` -> 10 results; brand-matching candidate.
- Browse calls:
  - None recorded.

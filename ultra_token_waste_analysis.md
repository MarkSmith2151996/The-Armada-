# ULTRA Token Waste Analysis

Generated: 2026-06-28

## Summary

- Sampled 20 executed `brand-outreach-worker` instructions from the ULTRA range `AI-81928` through `AI-83226`.
- Tokenizer: `tiktoken` with `cl100k_base`.
- Pricing basis: DeepSeek docs list `deepseek-v4-flash` output tokens at `$0.28 / 1M` tokens: `https://api-docs.deepseek.com/quick_start/pricing`.
- Result: the stored `execution_notes` are already terse. I did not find the long, flowery memo-style outputs the task hypothesis expected.
- Average per-sample waste ratio (`execution_notes_tokens / lean_tokens`): `1.17x`.
- Aggregate token ratio (`641 / 562`): `1.14x`.
- Net extra tokens across the 20-sample set versus a compact structured rewrite: `79`.
- Extrapolated net extra tokens across `676` executed instructions: about `2,670` output tokens.
- Estimated waste cost at DeepSeek V4 Flash output pricing: about `$0.00075`.
- Conservative upper bound if I only count positive overage and ignore samples that were already as short as or shorter than the rewrite: about `3,143` tokens, or about `$0.00088`.

## Sampling Notes

- I started with the evenly spaced seed IDs from the task brief: `AI-81928, AI-81993, AI-82058, ... AI-83163`.
- Nine of those seed IDs were still `open`, not `executed`.
- To reach 20 executed samples, I replaced the open seeds with other executed IDs still inside the ULTRA range.
- Because the upper end of the range contains long open runs, several replacement samples came from the dense executed block around `AI-82923` through `AI-83019`.
- This is still representative of the stored `execution_notes`, but that clustering is worth noting.
- Important scope note: this report measures only the text stored in `get_agent_instruction(...).execution_notes`. If the real concern is verbose browser/research traces that were never written into `execution_notes`, this analysis will understate total worker verbosity.

## Per-Sample Table

| Instruction | Brand | Total Tokens | Lean Tokens | Ratio | Net Extra | Flag |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `AI-81928` | Good Smile Company | 45 | 41 | 1.10x | +4 | - |
| `AI-81993` | RADA | 32 | 34 | 0.94x | -2 | - |
| `AI-82058` | Kuat | 30 | 37 | 0.81x | -7 | - |
| `AI-82253` | Astragon | 31 | 27 | 1.15x | +4 | - |
| `AI-82318` | Miracle-Gro | 34 | 26 | 1.31x | +8 | Output references Dyson |
| `AI-82383` | Denso | 33 | 20 | 1.65x | +13 | Output references HyCraft |
| `AI-82578` | Suncloud | 44 | 35 | 1.26x | +9 | - |
| `AI-82643` | Nite Ize | 41 | 33 | 1.24x | +8 | - |
| `AI-82708` | Greenlee | 36 | 29 | 1.24x | +7 | - |
| `AI-82903` | Enforcer | 37 | 32 | 1.16x | +5 | - |
| `AI-82968` | Mister Landscaper | 30 | 31 | 0.97x | -1 | - |
| `AI-82923` | Gemini Sound | 23 | 21 | 1.10x | +2 | - |
| `AI-82934` | Hilton Herbs | 27 | 29 | 0.93x | -2 | - |
| `AI-82945` | Jim Dunlop | 31 | 33 | 0.94x | -2 | - |
| `AI-82956` | LO Ink Specialties | 26 | 16 | 1.63x | +10 | - |
| `AI-82969` | MOCINNA | 32 | 24 | 1.33x | +8 | - |
| `AI-82981` | Nicole Home Collection | 26 | 24 | 1.08x | +2 | - |
| `AI-82993` | PetSport | 28 | 22 | 1.27x | +6 | - |
| `AI-83006` | REGA | 26 | 19 | 1.37x | +7 | - |
| `AI-83019` | Shell Rotella | 29 | 29 | 1.00x | +0 | - |

## Worst Offenders

### 1. `AI-82383` / Denso

- Stored note: `Verdict: BRAND NOT FOUND. HyCraft - zero detectable public presence. No website, no Faire, no Amazon listings. Needs ASIN-level investigation.`
- Lean rewrite: `VERDICT=INCONCLUSIVE; RESTRICT=brand not found; NOTES=output references HyCraft`
- Tokens: `33 -> 20`
- Ratio: `1.65x`
- Main issue: repeated negative evidence fragments.
- Bigger issue than token waste: the note appears to describe `HyCraft`, not `Denso`.

### 2. `AI-82956` / LO Ink Specialties

- Stored note: `LO Ink Specialties - Verdict: Unlikely wholesale partner. Dead domain. Amazon-only seller. Commodity products. Completed.`
- Lean rewrite: `VERDICT=CLOSED; RESTRICT=dead domain; Amazon-only seller`
- Tokens: `26 -> 16`
- Ratio: `1.63x`
- Main issue: narrative phrasing and completion boilerplate can compress into one verdict plus one restriction line.

### 3. `AI-83006` / REGA

- Stored note: `REGA - Verdict: INACCESSIBLE. Controlled UK hi-fi brand. Exclusive dist. Requires B&M storefront. Completed.`
- Lean rewrite: `VERDICT=CLOSED; DIST=exclusive distribution; RESTRICT=requires B&M storefront`
- Tokens: `26 -> 19`
- Ratio: `1.37x`
- Main issue: descriptive context adds some color, but not much operational value beyond the distribution and storefront restrictions.

## Common Waste Patterns

- Repeating the brand name even though the instruction already carries it.
- Prefix and suffix boilerplate like `Verdict:` and `Completed.`.
- Small narrative fillers like `Best path`, `parent company`, `163yr old tool brand`, or `one of tightest distribution models`.
- Mixed freeform confidence labels like `MEDIUM`, `HARD`, and `Conditional` instead of a normalized field.
- Short prose phrases where a fielded value would be cleaner, such as `Amazon open resale`, `trade account required`, or `dead domain`.

## More Important Than Waste

- `AI-82318` is a `Miracle-Gro` instruction, but the stored note talks about `Dyson`.
- `AI-82383` is a `Denso` instruction, but the stored note talks about `HyCraft`.
- Those mismatches are a much more serious operational problem than the token overhead itself.

## Conclusion

- Based on the stored `execution_notes`, the measurable verbosity problem is small.
- The stored notes are not full creative research memos; they are already compressed summaries.
- A structured-output-only recorder would still improve consistency and downstream parsing.
- If the decision is purely about output-token cost on the persisted note field, the savings are effectively negligible: well under one cent for the entire 676-instruction ULTRA run.
- If the decision is about quality and machine-readability, structured output is still a good move, especially because it would make brand/output mismatches easier to detect automatically.

## Appendix: Compact Lean Rewrites

- `AI-81928`: `VERDICT=ACCESSIBLE_BUT_GATED; WHOLESALE=partner.goodsmile.info; DIST=Shumi Co/BLYN; RESTRICT=Amazon gated; NOTES=Faire path`
- `AI-81993`: `VERDICT=BLOCKED_FOR_AMAZON; WHOLESALE=reseller program; RESTRICT=blocking new Amazon 3P sellers; NOTES=$125 min`
- `AI-82058`: `VERDICT=MAYBE; WHOLESALE=kuat.com B2B; DIST=QBP; RESTRICT=must disclose online channels; D2C competes`
- `AI-82253`: `VERDICT=ACCESSIBLE; CONTACT=distribution@astragon.de; NOTES=email for wholesale catalog; RESTRICT=no Amazon restriction found`
- `AI-82318`: `VERDICT=BLOCKED; RESTRICT=no wholesale for new resellers; NOTES=output references Dyson, not Miracle-Gro`
- `AI-82383`: `VERDICT=INCONCLUSIVE; RESTRICT=brand not found; NOTES=output references HyCraft`
- `AI-82578`: `VERDICT=CONDITIONAL_ACCESS; WHOLESALE=b2b.smithoptics.com; DIST=Smith Optics; RESTRICT=MAP but no Amazon ban`
- `AI-82643`: `VERDICT=GATED; WHOLESALE=reseller/distributor apps; CONTACT=policyadmin@niteize.com; RESTRICT=ARP gate; strict MAP`
- `AI-82708`: `VERDICT=DISTRIBUTOR_ONLY; DIST=Zoro/Ohio Power Tool/Grainger; RESTRICT=direct POD needs full-line commitment`
- `AI-82903`: `VERDICT=WHOLESALE_LIKELY; WHOLESALE=Zep distributor program; DIST=Zep; RESTRICT=Amazon open`
- `AI-82968`: `VERDICT=ACCESSIBLE; WHOLESALE=Maxijet B2B pricing; DIST=Maxijet; RESTRICT=Amazon unrestricted`
- `AI-82923`: `VERDICT=BLOCKED; RESTRICT=ToS prohibits reseller orders; NOTES=no wholesale program`
- `AI-82934`: `VERDICT=ACCESSIBLE; WHOLESALE=Shopify wholesale portal; RESTRICT=trade account required; NOTES=Iowa fulfillment`
- `AI-82945`: `VERDICT=CONDITIONAL; WHOLESALE=B2B portal; CONTACT=customerservice@jimdunlop.com; RESTRICT=Amazon resale open`
- `AI-82956`: `VERDICT=CLOSED; RESTRICT=dead domain; Amazon-only seller`
- `AI-82969`: `VERDICT=CLOSED; DIST=Alibaba/generic; RESTRICT=dead domain; Amazon FBA label`
- `AI-82981`: `VERDICT=MAYBE; DIST=Mediaflix; CONTACT=Amazon seller messaging; RESTRICT=Amazon-native brand`
- `AI-82993`: `VERDICT=MAYBE; WHOLESALE=Faire; RESTRICT=written Amazon approval + MAP`
- `AI-83006`: `VERDICT=CLOSED; DIST=exclusive distribution; RESTRICT=requires B&M storefront`
- `AI-83019`: `VERDICT=CLOSED; WHOLESALE=DPQA network; DIST=DPQA; RESTRICT=Amazon gated + hazmat`

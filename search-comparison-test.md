# Google Search vs. SearXNG Disambiguation Test

Date: 2026-07-14

## Environment

- Chrome CDP listeners verified on `127.0.0.1:9222`, `9223`, `9224`, and `9225`.
- The dedicated node-MCP `google_search` tool could not be resolved or invoked from this session. A direct Chrome Google fallback was attempted for the first query and Google returned its unusual-traffic interstitial rather than search results.

## Query 1: Duck Brand duct tape wholesale

### google_search

Result count: 0

```json
[]
```

Top-result brand relevance: Not assessable. Google blocked the direct fallback before returning organic results.

### search_brand (SearXNG)

Result count: 10 returned by SearXNG; tool returned the top 3 below.

```json
[
  {
    "title": "DuckDuckGo - Protection. Privacy. Peace of mind.",
    "url": "https://duckduckgo.com/",
    "snippet": "The Internet privacy company that empowers you to seamlessly take control of your personal information online, without any tradeoffs."
  },
  {
    "title": "Duck - Wikipedia",
    "url": "https://en.wikipedia.org/wiki/Duck",
    "snippet": "Duck is the common name for numerous species of waterfowl in the family Anatidae. Ducks are generally smaller and shorter-necked than swans and geese, which are members of the same family. …"
  },
  {
    "title": "Duck | Definition, Types, & Facts | Britannica",
    "url": "https://www.britannica.com/animal/duck",
    "snippet": "duck, any of various species of relatively small, short-necked, large-billed waterfowl. In true ducks—i.e., those classified in the subfamily Anatinae in the waterfowl family Anatidae—the legs are placed …"
  }
]
```

Top-result brand relevance: No. All returned results concern the search engine or waterfowl, not Duck Brand duct tape.

## Query 2: Halo Headband wholesale program

### google_search

Result count: 0

```json
[]
```

Top-result brand relevance: Not assessable; the dedicated tool was unavailable, and the direct fallback was already Google rate-limited.

### search_brand (SearXNG)

Result count: 10 returned by SearXNG; tool returned the top 3 below.

```json
[
  {
    "title": "Halo - Official Site (en)",
    "url": "https://www.halowaypoint.com/",
    "snippet": "HaloWaypoint.com is the official site for the Halo universe, featuring the latest information about Halo games and media, news from 343 Industries and the home of the Halo community."
  },
  {
    "title": "Halo (franchise) - Wikipedia",
    "url": "https://en.wikipedia.org/wiki/Halo_(franchise)",
    "snippet": "Halo is a military science fiction video game series and media franchise, originally developed by Bungie and currently managed and developed by Halo Studios (previously 343 Industries), part of Microsoft …"
  },
  {
    "title": "Welcome to the Halo Universe: Halo Games & Updates | XBOX",
    "url": "https://www.xbox.com/en-US/games/halo?msockid=2b3049e28a5d68961fc15e748b6a69e0",
    "snippet": "From one of gaming's most iconic sagas, Halo is bigger than ever. Featuring an expansive open-world campaign and a dynamic free to play multiplayer experience. The Master Chief’s iconic journey …"
  }
]
```

Top-result brand relevance: No. All returned results concern the Halo video-game franchise, not Halo Headbands.

## Query 3: Captain Rodney's wholesale distributor

### google_search

Result count: 0

```json
[]
```

Top-result brand relevance: Not assessable; the dedicated tool was unavailable, and the direct fallback was Google rate-limited.

### search_brand (SearXNG)

Result count: 10 returned by SearXNG; tool returned the top 3 below.

```json
[
  {
    "title": "Captain - Wikipedia",
    "url": "https://en.wikipedia.org/wiki/Captain",
    "snippet": "Captain Captain of a ship during a U.S. Fish and Wildlife Service mission Captain is a title, an appellative for the commanding officer of a military unit; the commander or highest rank officer of a …"
  },
  {
    "title": "CAPTAIN Definition & Meaning - Merriam-Webster",
    "url": "https://www.merriam-webster.com/dictionary/captain",
    "snippet": "4 days ago · The meaning of CAPTAIN is a military leader : the commander of a unit or a body of troops. How to use captain in a sentence."
  },
  {
    "title": "CAPTAIN | English meaning - Cambridge Dictionary",
    "url": "https://dictionary.cambridge.org/dictionary/english/captain",
    "snippet": "CAPTAIN definition: 1. the leader of a sports team: 2. the person in charge of a ship or an aircraft: 3. an officer's…."
  }
]
```

Top-result brand relevance: No. All returned results concern the generic word "captain," not Captain Rodney's products or distributors.

## Verdict

Inconclusive: this run cannot establish that `google_search` is better at brand disambiguation because the tool was unavailable from the node/Custodian MCP surface, while the direct Google fallback was blocked before it produced organic results. SearXNG clearly failed all three disambiguation tests: none of its returned top-three results was about the intended brand. Re-run after restoring the dedicated `google_search` tool or a Google session that is not rate-limited.

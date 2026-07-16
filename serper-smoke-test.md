# Serper Search Smoke Test

Run date: 2026-07-14

## Environment

- `SERPER_API_KEY`: not set in the node MCP shell.
- `SEARCH_API_KEY`: not set in the node MCP shell.
- Serper comparison could not be executed without consuming or fabricating credentials. Set either key and rerun the three queries to complete the live quality validation.
- The implementation was syntax-checked, and `search_brand` was exercised with no API key. It logged the Serper failure and returned SearXNG results in the unchanged worker response shape (`title`, `url`, `snippet`).

## Comparison

### Duck Brand wholesale distributor

| SearXNG top 5 | Serper top 5 |
| --- | --- |
| Duck Brand Wholesale \| Palletfy - Authorized Duck Brand Distributer<br>https://www.palletfly.com/products/brand/Duck%20Brand | Not run: API key unavailable |
| Duck Wholesale \| Palletfy - Authorized Duck Distributer<br>https://www.palletfly.com/products/brand/Duck | Not run: API key unavailable |
| Duck Brand Wholesale Deals - Regal Distributor<br>https://regaldistributor.com/pages/duck-brand | Not run: API key unavailable |
| DuckDuckGo - Protection. Privacy. Peace of mind.<br>https://duckduckgo.com/ | Not run: API key unavailable |
| Duck Wholesale Deals - Regal Distributor<br>https://regaldistributor.com/pages/duck | Not run: API key unavailable |

- Actual brand website: not present in the SearXNG top 5.
- Wholesale/dealer/distributor page: present in the SearXNG top 5 (Palletfy and Regal Distributor).

### Halo Headband wholesale

| SearXNG top 5 | Serper top 5 |
| --- | --- |
| Halo Headband Wholesale - High Quality & Stylish Design \| DHgate<br>https://www.dhgate.com/wholesale/halo+headband.html | Not run: API key unavailable |
| Halo Headband Sports Headwear: Head Sweatbands for Athletes<br>https://haloheadband.com/ | Not run: API key unavailable |
| Wholesale Halo Headband Available in Various Styles - Alibaba.com<br>https://www.alibaba.com/showroom/halo-headband.html | Not run: API key unavailable |
| Halo - Official Site (en)<br>https://www.halowaypoint.com/ | Not run: API key unavailable |
| Halo Headbands - PA Sports & Leisure \| Wholesale<br>https://www.pasportsandleisure.com.au/halo-headbands | Not run: API key unavailable |

- Actual brand website: present in the SearXNG top 5 (`haloheadband.com`).
- Wholesale/dealer/distributor page: present in the SearXNG top 5 (DHgate, Alibaba, and PA Sports & Leisure).

### Captain Rodney's wholesale

| SearXNG top 5 | Serper top 5 |
| --- | --- |
| Captain - Wikipedia<br>https://en.wikipedia.org/wiki/Captain | Not run: API key unavailable |
| Admiral Rodney Officer's Release No. 1 Port Cask \| 2006<br>https://avantgardedrinks.com/admiral-rodney-rum-officers-release-1-port-70cl | Not run: API key unavailable |
| CAPTAIN Definition & Meaning - Merriam-Webster<br>https://www.merriam-webster.com/dictionary/captain | Not run: API key unavailable |
| Admiral Rodney Officer's Release No. 2 \| Irish Whiskey Cask<br>https://avantgardedrinks.com/admiral-rodney-rum-officers-release-2-irish-70cl | Not run: API key unavailable |
| CAPTAIN \| English meaning - Cambridge Dictionary<br>https://dictionary.cambridge.org/dictionary/english/captain | Not run: API key unavailable |

- Actual brand website: not present in the SearXNG top 5.
- Wholesale/dealer/distributor page: not present in the SearXNG top 5.

## Completed Verification

- `python -m py_compile server.py config.py tools/search_brand.py` passed.
- Missing-key behavior was validated: Serper raised a controlled configuration error, then `search_brand` logged the fallback and successfully returned SearXNG results.
- The fallback response summary was `SearXNG: 20 search results for Captain Rodney's wholesale; returned top 3.`

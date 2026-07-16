# SearXNG Fix Results

Run: 2026-07-14 06:44 UTC

## Configuration changes

- Confirmed the bundled configuration already defines Google, Brave, Bing, DuckDuckGo, Startpage, Qwant, and Mojeek.
- Enabled Qwant and Mojeek by removing their `disabled: true` flags.
- Set weights: Google 2, Brave 1.5, DuckDuckGo 1, Bing 1.
- Set Google `use_mobile_ui: false`.
- No `google web` engine was added because this SearXNG version has no `google_web` engine module; the existing Google engine is the supported web-search engine.
- Restarted the actual listener (`venv/bin/searxng-run`) and confirmed it is listening on `127.0.0.1:8888`.

## DuckDuckGo connectivity

- Direct `https://html.duckduckgo.com/html/?q=test`: URLError: <urlopen error timed out>.

## Engine checks

- **google**: 0 result(s); attribution: none
- **brave**: 0 result(s); attribution: none; failures: brave: Suspended: too many requests
- **bing**: 10 result(s); attribution: bing
- **duckduckgo**: 0 result(s); attribution: none; failures: duckduckgo: timeout
- **duckduckgo web**: 0 result(s); attribution: none; failures: duckduckgo web: timeout
- **startpage**: 0 result(s); attribution: none; failures: startpage: Suspended: CAPTCHA
- **qwant**: 0 result(s); attribution: none; failures: qwant: Suspended: access denied
- **mojeek**: 0 result(s); attribution: none

## Disambiguation tests

### Duck Brand duct tape wholesale

- Match: **NO**
- Engines: bing
- [bing] DuckDuckGo - Protection. Privacy. Peace of mind.
  https://duckduckgo.com/
- [bing] Duck - Wikipedia
  https://en.wikipedia.org/wiki/Duck
- [bing] Duck | Definition, Types, & Facts | Britannica
  https://www.britannica.com/animal/duck
- [bing] 41 Types of Ducks in North America (Complete ID Guide)
  https://avibirds.com/types-of-ducks/
- [bing] Duck.ai by DuckDuckGo. Private AI chat. Free.
  https://duck.ai/
- Unresponsive: brave: Suspended: too many requests; duckduckgo: Suspended: timeout; duckduckgo web: Suspended: timeout; mojeek: access denied; qwant: Suspended: access denied; startpage: Suspended: CAPTCHA

### Halo Headband wholesale program

- Match: **YES**
- Engines: bing
- [bing] Halo - Official Site (en)
  https://www.halowaypoint.com/
- [bing] Halo (franchise) - Wikipedia
  https://en.wikipedia.org/wiki/Halo_(franchise)
- [bing] Welcome to the Halo Universe: Halo Games & Updates | XBOX
  https://www.xbox.com/en-US/games/halo?msockid=133bdf39780e6a3d1896c8af79a96b9c
- [bing] Halo: Campaign Evolved Launches July 28, Pre-Orders Available Now
  https://news.xbox.com/en-us/2026/06/07/halo-campaign-evolved-launch-preorder-xbox-games-showcase-2026/
- [bing] The Latest Update On ‘Halo’ Season 3 After Its Netflix Arrival
  https://www.forbes.com/sites/paultassi/2025/10/06/the-latest-update-on-halo-season-3-after-its-netflix-arrival/
- Unresponsive: brave: Suspended: too many requests; duckduckgo: Suspended: timeout; duckduckgo web: Suspended: timeout; mojeek: Suspended: access denied; qwant: Suspended: access denied; startpage: Suspended: CAPTCHA

### Captain Rodney's wholesale distributor

- Match: **NO**
- Engines: bing
- [bing] Captain - Wikipedia
  https://en.wikipedia.org/wiki/Captain
- [bing] CAPTAIN Definition & Meaning - Merriam-Webster
  https://www.merriam-webster.com/dictionary/captain
- [bing] CAPTAIN | English meaning - Cambridge Dictionary
  https://dictionary.cambridge.org/dictionary/english/captain
- [bing] Wiz Khalifa - Captain [Official Video] - YouTube
  https://www.youtube.com/watch?v=aFFxT9zdT78
- [bing] CA Autism Professional Training and Information Network - CAPTAIN
  https://captain.ca.gov/
- Unresponsive: brave: Suspended: too many requests; duckduckgo: Suspended: timeout; duckduckgo web: Suspended: timeout; mojeek: Suspended: access denied; qwant: Suspended: access denied; startpage: Suspended: CAPTCHA

### Sound Town pro audio wholesale

- Match: **NO**
- Engines: bing
- [bing] Stream and listen to music online for free with SoundCloud
  https://m.soundcloud.com/
- [bing] 120,000+ Free Sound Effects for Download - Pixabay
  https://pixabay.com/sound-effects/
- [bing] SoundCloud — Register, sign-in or access our Homepage
  https://m.soundcloud.com/signin
- [bing] Sound Effects Soundboard - Categories - United States ...
  https://www.myinstants.com/en/categories/sound%20effects/us/
- [bing] Freesound
  https://freesound.org/
- Unresponsive: brave: Suspended: too many requests; duckduckgo: Suspended: timeout; duckduckgo web: Suspended: timeout; mojeek: Suspended: access denied; qwant: Suspended: access denied; startpage: Suspended: CAPTCHA

### Brava cookware wholesale

- Match: **YES**
- Engines: bing
- [bing] The browser that puts you first | Brave
  https://brave.com/
- [bing] Brave Browser Download | Brave
  https://dl.brave.com/
- [bing] Brava vs. Bravo: Give Your Compliments Correctly
  https://www.yourdictionary.com/articles/brava-bravo-compliments
- [bing] The Brava
  https://shop.brava.com/collections/brava-oven
- [bing] getbrava – Brava
  https://shop.brava.com/pages/getbrava/
- Unresponsive: brave: Suspended: too many requests; duckduckgo: Suspended: timeout; duckduckgo web: Suspended: timeout; mojeek: Suspended: access denied; qwant: Suspended: access denied; startpage: Suspended: CAPTCHA; wikidata: timeout

## Verdict

**FAIL: SearXNG is not yet usable for reliable brand research.**

- General queries returned results only from: bing.
- Google returned zero results without reporting an engine error.
- Brave is rate-limited, DuckDuckGo and DuckDuckGo Web time out, Startpage is CAPTCHA-blocked, and Qwant is access-denied.
- Enabling engines corrected the local configuration, but upstream access restrictions still prevent multi-engine search quality.

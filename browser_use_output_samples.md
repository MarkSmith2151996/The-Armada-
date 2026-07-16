# browser_use Output Samples

Generated: 2026-06-29

## Method

- Approach 1 failed: `query_build_sessions` did not surface raw ULTRA `brand-outreach-worker` sessions with `browser_use` tool parts, and the indexed OpenCode `part` table for 2026-06-27 through 2026-06-28 contained no `browser_use` tool rows.
- Fallback used the local `browser-use` venv at `/Users/tubslamanna/browser-use-service/venv/`.
- Captured the exact browser-use `state` action surface implemented in `browser_use/skill_cli/commands/browser.py`, which returns a single object shaped like `{"_raw_text": state_text}`.
- That `_raw_text` payload is built from:
  - a fixed three-line header: `viewport`, `page`, `scroll`
  - `state.dom_state.llm_representation()` from the browser-use DOM serializer
- Raw HTML size was measured from a direct HTTP GET of the same public URL.

## What browser_use actually returns

- The live browser-use state action is not a giant JSON accessibility tree.
- The worker-facing payload is a compact text snapshot wrapped in a single `_raw_text` field.
- Common structure markers in the returned text:
  - indexed interactive elements like `[178]<a />`
  - inline text content under those elements
  - `|scroll element|...` markers for scrollable containers
  - `|SHADOW(open)|...` markers for shadow DOM sections
  - `<!-- SVG content collapsed -->` placeholders instead of full SVG markup
  - `... (more content below viewport - scroll to reveal)` when the page extends below the current viewport

## Brand: Curveball
## URL: `https://curveball-leisure.com/customers/`
## Final URL: `https://curveball-leisure.com/customers/`
## Token count: `96.50`
## Raw HTML size: `95,586 bytes` -> Accessibility tree size: `386 bytes` (`247.63x` reduction)

Note: browser_use hit a Cloudflare verification interstitial instead of the wholesale page body.

### Full browser_use output:
```python
{"_raw_text": """
viewport: 1800x1169
page: 1800x1169
scroll: (0, 0)
[2]<img alt=Icon for curveball-leisure.com />
curveball-leisure.com
Performing security verification
This website uses a security service to protect against malicious bots. This page is displayed while the website verifies you are not a bot.
Ray ID:
a13237050b70104d
Performance and Security by
[58]<a />
	Cloudflare
[61]<a />
	Privacy
"""}
```

## Brand: Westclox
## URL: `https://westcloxsource.com/pages/wholesale`
## Final URL: `https://westcloxsource.com/pages/wholesale`
## Token count: `1230.50`
## Raw HTML size: `259,331 bytes` -> Accessibility tree size: `4,922 bytes` (`52.69x` reduction)

### Full browser_use output:
```python
{"_raw_text": """
viewport: 1800x1169
page: 1800x3021
scroll: (0, 0)
[178]<a />
	Skip to content
[180]<button name=previous aria-label=Previous announcement />
|scroll element|<div id=Slider-sections--20761490620631__announcement-bar /> (horizontal 100%)
	[6]<div id=Slide-sections--20761490620631__announcement-bar-2 role=group aria-label=2 of 3 />
	Sitewide Discounts Automatically Applied at Checkout
[183]<button name=next aria-label=Next announcement />
[1044]<details-modal />
	|SHADOW(open)|*[224]<details compound_components=(name=Toggle Disclosure,role=button),(name=Content Area,role=region) />
		[225]<summary aria-label=Search role=button expanded=false />
			[1048]<span />
				[1050]<span />
					[1051]<svg /> <!-- SVG content collapsed -->
		Search
[230]<a />
	[1114]<span />
		The Westclox Source
[231]<a id=HeaderMenu-home />
	Home
|SHADOW(open)|*[232]<details id=Details-HeaderMenu-2 compound_components=(name=Toggle Disclosure,role=button),(name=Content Area,role=region) />
	[233]<summary id=HeaderMenu-catalog role=button expanded=false />
		[1131]<span />
			Catalog
		[1133]<svg /> <!-- SVG content collapsed -->
|SHADOW(open)|*[243]<details id=Details-HeaderMenu-3 compound_components=(name=Toggle Disclosure,role=button),(name=Content Area,role=region) />
	[244]<summary id=HeaderMenu-shop-by-brand role=button expanded=false />
		[1163]<span />
			Shop by Brand
		[1165]<svg /> <!-- SVG content collapsed -->
[251]<a id=HeaderMenu-wholesale />
	Wholesale
[252]<a id=HeaderMenu-our-history />
	Our History
|SHADOW(open)|*[253]<details id=Details-HeaderMenu-6 compound_components=(name=Toggle Disclosure,role=button),(name=Content Area,role=region) />
	[254]<summary id=HeaderMenu-help-center role=button expanded=false />
		[1199]<span />
			Help Center
		[1201]<svg /> <!-- SVG content collapsed -->
[265]<a />
	[1296]<span />
		Log in
[266]<a id=cart-icon-bubble />
	Cart
[1358]<main id=MainContent role=main />
	General Wholesale
	General Wholesale - Let's Grow Together!
	Westclox has been the trusted name in reliable timepieces for hospitality, medical facilities, schools, offices, and countless other businesses for generations - and we'd love to become your partner too.
	We've made it easier than ever to work with us. Sign up directly through our
	[272]<a title=Wholesale Portal />
		Wholesale Portal
	and you'll instantly unlock:
	Premium wholesale discounts
	Personalized service & dedicated account support
	Opportunities to join our global manufacturer rep network and tap into new markets
	Access to closeout deals and our full 200+ product catalog
	Whether you're ready to place larger orders for better pricing, explore a partnership, or simply have a quick chat about how we can support your business, we're here for you.
	Call us anytime at
	410-358-0863
	- no form required. Our team is friendly, knowledgeable, and genuinely excited to help you succeed.
	Prefer to start online? Just fill out the form below and we'll get right back to you.
	We can't wait to hear from you and start building something great together!
	Contact form
	|SHADOW(open)|[25]<input autocomplete=name type=text id=ContactForm-name name=contact[Name] placeholder=Name />
	Name
	|SHADOW(open)|[26]<input autocomplete=email type=email id=ContactForm-email name=contact[email] placeholder=Email required=true />
	Email
	|SHADOW(open)|[27]<input type=tel id=ContactForm-phone autocomplete=tel name=contact[Phone number] pattern=[0-9\-]* placeholder=Phone number />
	Phone number
	|SHADOW(open)|[28]<textarea id=ContactForm-body name=contact[Comment] placeholder=Comment />
	Comment
	[273]<button type=submit />
		Send
	Need More Assistance?
	User Manuals
	Each clock comes with a printed guidebook which can also be found online. In case of loss or damage, ask
	[274]<a title=Contact />
		customer service team
	for help
	[275]<a />
		See Manuals
		[1516]<span />
			[1518]<svg /> <!-- SVG content collapsed -->
	Wholesale
	Order Westclox products directly through our wholesale  site. Register for an account to access wholesale pricing, place bulk orders anytime, and get fast, reliable shipping.
	[276]<a />
		Register for an Account
		[1536]<span />
			[1538]<svg /> <!-- SVG content collapsed -->
	FAQ
	Discover in-depth explanations and solutions on the Westclox FAQs page. Access valuable insights and expert advice for your inquiries.
	[277]<a />
		Read Our FAQ
		[1556]<span />
			[1558]<svg /> <!-- SVG content collapsed -->
	Top Sellers 2025
	Explore Westclox's most popular clocks of 2025, featuring bold LED alarm clocks, classic analog wall clocks, and timeless wind up designs. Each combines dependable performance with vintage inspired style, making them a perfect fit for your bedside, living space, or as a thoughtful gift.
[307]<div aria-label=Click to open Judge.me floating reviews tab role=button />
	Reviews
[397]<div title=Drag />
	<svg /> <!-- SVG content collapsed -->
"""}
```

## Brand: Alconox
## URL: `https://alconox.com/dealership-application/`
## Final URL: `https://alconox.com/dealership-application/`
## Token count: `830.75`
## Raw HTML size: `91,121 bytes` -> Accessibility tree size: `3,323 bytes` (`27.42x` reduction)

### Full browser_use output:
```python
{"_raw_text": """
viewport: 1800x1169
page: 1800x1912
scroll: (0, 0)
[19]<a />
	COAs
[265]<a />
	login
[268]<a />
	[28]<span />
[277]<div />
	[47]<div />
		[291]<a />
			English
[305]<a />
[324]<a />
	Products
[329]<a />
	Industries
[334]<a />
	Resources
[339]<a />
	Ask Alconox
[344]<a />
	Testing
[348]<a />
	Q&A
[353]<a />
	Locate Dealers
[358]<a />
	Contact Us
[362]<div />
	[363]<i />
<svg /> <!-- SVG content collapsed -->
Dealership Application
How to Become an Alconox, LLC Approved Dealer
Step 1
: To start the dealer registration process with open account status send the following documents to the email address
[600]<a />
	po@alconox.com
For USA dealers ONLY applying for open account include:
3 trade references with fax number and/or email to the contacts
A bank reference with fax number and/or email for the bank contacts
A letter on your letterhead authorizing your bank to release credit information with bank acct #, tax ID #, Year Established, date and a signature
A resale certificate
For all other dealers including dealers outside the USA, also include:
A statement that you wish to purchase for resale
A description of your company, your website, how long you have been in business, and the types of customers and markets you serve
How your company proposes to promote Alconox, LLC detergents
Names of other well-known brands or companies that you represent
Note: For U.S. dealers only interested in using credit cards, contact po@alconox.com
Step 2
: Upon receipt of the items above, Alconox, LLC will check references and review the application. If everything is satisfactory, we will send you the following documents that need to be filled out and returned to po@alconox.com. These allow you to become a dealer that is eligible for the discounts:
Alconox, LLC National Sales Policy signed and dated indicating what stocking and promoting you will do.
[681]<i />
Stay in the Loop
Get exclusive discounts, product updates, new technical resources, and cleaning tips delivered straight to your inbox.
[692]<a />
	Subscribe to Our Newsletter
Customer Services
[721]<a />
	About Us
[725]<a />
	Ask Alconox
[729]<a />
	Create an Account
[733]<a />
	Open Positions
[737]<a />
	Locate Dealers
Shop Alconox
[750]<a />
	Products
[754]<a />
	SDS Sheets/Technical Bulletins
[758]<a />
	Certificate of Analysis (COA)
[762]<a />
	Certificate of Conformance (COC)
Terms & Policies
[778]<a />
	Terms of Service
[782]<a />
	Privacy Policy
[786]<a />
	Sustainability Policy
[790]<a />
	Shipping and Return Policy
For Dealers
[803]<a />
	Dealer Policy
[807]<a />
	New Dealer Registration
30 Glenn St.
Suite #309
White Plains, NY 10603
[829]<a />
	(914) 948-4040
[837]<a />
	cleaning@alconox.com
[846]<a />
[850]<a />
[854]<a />
[858]<a />
[862]<a />
[876]<a />
	[877]<i />
	ISO 9001:2015 | ISO 13485:2016 | CERTIFIED
Alconox, LLC is part of TCP Analytical. TCP Analytical is dedicated to making research and production simpler, faster, and more reliable through a focused portfolio of chemical, research reagents, and labratory product companies in the USA & Canada. Learn more at
[896]<a />
	www.tcpanalytical.com
[899]<hr />
Copyright  2026 Alconox, LLC
[905]<span />
	site by
[908]<a />
[924]<button aria-label=Open chat />
	Chat with us
|scroll element|<iframe /> (scroll)
... (more content below viewport - scroll to reveal)
"""}
```

## Brand: Vollrath
## URL: `https://vollrathfoodservice.com/vfs-partners/for-dealers`
## Final URL: `https://www.vollrathfoodservice.com/vfs-partners/for-dealers`
## Token count: `831.50`
## Raw HTML size: `71,153 bytes` -> Accessibility tree size: `3,326 bytes` (`21.39x` reduction)

### Full browser_use output:
```python
{"_raw_text": """
viewport: 1800x1169
page: 1800x2601
scroll: (0, 0)
Skip to the main content
|scroll element|<div id=outer-container /> (horizontal 0%)
	[263]<span />
		Vollrath Companies
	[316]<a id=util-nav-phone />
		920.457.4851
	[322]<a id=util-nav-phone-toll-free />
		toll free: 800.624.2051
	[47]<button expanded=false />
		Ask A Question
	[22]<a />
		Resources
	[425]<a />
		Partners
	[463]<a />
		About Us
	[469]<a />
		Contact Us
	[475]<a />
		Send Us Feedback
	[486]<a />
		Login
	[494]<a />
		Wishlist
	[520]<a />
		[522]<svg /> <!-- SVG content collapsed -->
		[527]<span />
			The Vollrath Company, LLC
	[24]<a />
		Products
	[953]<a />
		Support
	[985]<a />
		Industries
	[1057]<a />
		Inspiration
	[26]<a />
		Where To Buy
	[1102]<li level=1 />
		[1104]<div />
			[60]<button />
				Search...
				search icon
	[1404]<a title=VFS Partners />
		VFS Partners
	For Dealers
	Dealer Resource Page
	Vollrath really is everywhere, thanks in large part to our network of authorized Vollrath dealers. Your knowledge of and passion for our products is what puts our best in kitchens, venues, and facilities all across the globe.
	Customer Self-Service
	Access your Vollrath ordering information 24 hours a day, 7 days a week. Search for specific orders and conveniently view tracking information for orders that have shipped from the Vollrath Sheboygan Distribution Center.
	[1448]<a />
		Get started
	Resource Library
	Explore our newly reorganized Resource Library, featuring all the tools and info your customers will need to get the most out of their Vollrath products.
	[1458]<a />
		View Resource Library
	Video Gallery
	Find, show, and share videos from our Video Gallery to help your customers better understand how our products look and work.
	[1468]<a />
		View Video Gallery
	Terms & Conditions of Sale
	Download and read our official Terms & Conditions of Sale Policy.
	[1478]<a />
		View Terms & Conditions of Sale
	Vollrath
	Inspiration
	[1505]<a />
		10 Reasons to Buy a Cayenne Heat Strip
	Fixed or remote controls allow installation flexibility for your operation - available with infinite or toggle switch.  Toggle controls come standard with boots for cool...
	[1509]<a />
		Read More >
	[1518]<a />
		How Vollrath Equipment helps Wooden City restaurants execute their vision
	Known for serving familiar foods with an elevated twist, Wooden City restaurants have been popular from the moment they opened. Their unique menu, sophisticated style and...
	[1522]<a />
		Read More >
	[1531]<a />
		Affordable Portable Features
	Our Affordable Portable serving lines are a great value in serving equipment.  Product Features   Optional UL listed incandescent/infrared lighting assembly showcases...
	[1535]<a />
		Read More >
	[65]<a />
		Back to Top
[34]<div id=onetrust-banner-sdk role=region aria-label=Cookie banner />
	By clicking "Accept All Cookies", you agree to the storing of cookies on your device to enhance site navigation, analyze site usage, and assist in our marketing efforts.
	[2238]<a aria-label=More information about your privacy, opens in a new tab />
		Cookie Policy
	[66]<button id=onetrust-accept-btn-handler />
		Accept All Cookies
	[67]<button id=onetrust-reject-all-handler />
		Reject All
	[68]<button id=onetrust-pc-btn-handler />
		Cookies Settings
	[32]<button aria-label=Close />
"""}
```

## Brand: Cressi
## URL: `https://cressiamerica.com/pages/become-a-cressi-america-authorized-dealer`
## Final URL: `https://cressiamerica.com/pages/become-a-cressi-america-authorized-dealer`
## Token count: `1067.75`
## Raw HTML size: `228,399 bytes` -> Accessibility tree size: `4,271 bytes` (`53.48x` reduction)

### Full browser_use output:
```python
{"_raw_text": """
viewport: 1800x1169
page: 1800x1451
scroll: (0, 0)
[173]<div id=bss-map-popup />
	[578]<span />
		[57]<img id=icon-map alt=Marker />
[613]<a />
	Skip to content
|scroll element|<div /> (horizontal 50%)
	Become a Cressi Dealer -
	[645]<a title=Become Dealer />
		Join our network today!
	Discover Cressi's New 2025 Products -
	[653]<a title=New Arrivals 2025 />
		Learn More
[657]<div />
[684]<a />
	Who we are
[688]<a />
	Our history
[692]<a />
	Cressi Blog
[696]<a />
	Cressi Ambassador
[700]<a />
	Dealer locator
[704]<a />
	Help Center
[718]<a />
[177]<div />
	Search
	[733]<search-form />
		|SHADOW(open)|[46]<input type=search id=header-search name=q placeholder=Search for colle role=combobox autocomplete=list aria-autocomplete=list expanded=false />
		[739]<button />
			Search
	[764]<span role=status />
[768]<a aria-label=Go HOME />
|SHADOW(open)|*[182]<details compound_components=(name=Toggle Disclosure,role=button),(name=Content Area,role=region) />
	[184]<ul />
		|SHADOW(open)|*[805]<details compound_components=(name=Toggle Disclosure,role=button),(name=Content Area,role=region) />
			[185]<summary expanded=false />
				[5]<a />
					Scuba Diving
		|SHADOW(open)|*[1277]<details compound_components=(name=Toggle Disclosure,role=button),(name=Content Area,role=region) />
			[206]<summary expanded=false />
				[16]<a />
					Freediving
		|SHADOW(open)|*[1365]<details compound_components=(name=Toggle Disclosure,role=button),(name=Content Area,role=region) />
			[209]<summary expanded=false />
				[18]<a />
					Spearfishing
		|SHADOW(open)|*[1525]<details compound_components=(name=Toggle Disclosure,role=button),(name=Content Area,role=region) />
			[216]<summary expanded=false />
				[22]<a />
					Snorkeling
		|SHADOW(open)|*[1658]<details compound_components=(name=Toggle Disclosure,role=button),(name=Content Area,role=region) />
			[221]<summary expanded=false />
				[25]<a />
					Swimming
	|SHADOW(open)|*[226]<details compound_components=(name=Toggle Disclosure,role=button),(name=Content Area,role=region) />
		[227]<summary expanded=false />
			[32]<a />
				Snorkeling Adults
	|SHADOW(open)|*[229]<details compound_components=(name=Toggle Disclosure,role=button),(name=Content Area,role=region) />
		[230]<summary expanded=false />
			[33]<a />
				Snorkeling Kids
CRESSI PARTNERS
Are you interested in collaborating with Cressi? Please fill out the form below. If we find it to be a good fit, we'll get in touch!
|scroll element[1917]<iframe id=frame_6HydltMJJA-ElRlVDKD_0g title=Become a Cressi Dealer /> (scroll)
Cressi-sub USA, Inc.
3 Rosol Lane, Saddle Brook
NJ 07663, USA
Copyright Cressi-sub USA, Inc.
All rights reserved
[2023]<a title=Cressi 1946  on Facebook />
	Facebook
[2032]<a title=Cressi 1946  on YouTube />
	YouTube
[2041]<a title=Cressi 1946  on Instagram />
	Instagram
[2052]<a title=Cressi 1946  on Twitter />
	Twitter
[2061]<a title=Cressi 1946  on LinkedIn />
	LinkedIn
|SHADOW(open)|*[234]<details compound_components=(name=Toggle Disclosure,role=button),(name=Content Area,role=region) />
	[40]<summary expanded=true />
		COMPANY INFO
	[2093]<a />
		Who We Are
	[2098]<a />
		Our History
	[2103]<a />
		California Proposition 65 Warning
|SHADOW(open)|*[235]<details compound_components=(name=Toggle Disclosure,role=button),(name=Content Area,role=region) />
	[41]<summary expanded=true />
		HELP CENTER
	[2133]<a />
		Contact Us
	[2138]<a />
		Product Registration
	[2142]<a />
		Download Area
	[2147]<a />
		Dealer Locator
|SHADOW(open)|*[236]<details compound_components=(name=Toggle Disclosure,role=button),(name=Content Area,role=region) />
	[42]<summary expanded=true />
		SUPPORT & DOWNLOAD
	[2177]<a />
		Product Support
	[2182]<a />
		Manuals & Software
	[2187]<a />
		Declarations of Conformity
	[2192]<a />
		Privacy Policy
	[2197]<a />
		Catalogs
|SHADOW(open)|*[237]<details compound_components=(name=Toggle Disclosure,role=button),(name=Content Area,role=region) />
	[43]<summary expanded=true />
		NEWSLETTER
	Sign up for exclusive offers, original stories, events and more.
	Email
	|SHADOW(open)|[48]<input type=email id=footer-signup name=contact[email] placeholder=Your email autocomplete=email required=true />
	[2237]<button />
		Subscribe
[2260]<hr />
 2026
[2268]<a />
	Cressi 1946
"""}
```

## Summary

### Averages

| Metric | All 5 Samples | Excluding Curveball Cloudflare page |
| --- | ---: | ---: |
| Avg token count | `811.40` | `990.12` |
| Avg compression ratio vs raw HTML | `80.52x` | `38.74x` |

### Assessment

- The actual browser-use state surface is compact compared with raw HTML. Real wholesale pages landed around `831` to `1231` tokens each, while the raw HTML was `21x` to `53x` larger.
- The output is not a raw DOM dump. It is a filtered, line-oriented page sketch with indexed interactives, visible text, shadow DOM markers, and clipped SVG content.
- This is probably compact enough to keep **single-page snapshots** in normal context without a special sandboxing layer.
- It is **not** free: if a worker bounces through many pages, `~1k tokens/page` still accumulates quickly across repeated turns.
- The Curveball sample also shows a non-obvious operational risk: browser-use may return a Cloudflare challenge page instead of the intended wholesale content, which is compact but unproductive.
- Combined with EE-436, the evidence points to this: browser-use page snapshots themselves are not the main cost problem. Repeated tool wrappers and accumulated history are still more likely to dominate ULTRA session spend.

### Bottom line

- For public wholesale pages, browser-use's native page-state output is **surprisingly compact**.
- I would not add a sandboxing layer just to shrink the page snapshot itself.
- I would still focus on reducing repeated turns, repeated tool envelopes, and stale-history rereads.

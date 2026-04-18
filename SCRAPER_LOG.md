# Scraper Debug Log

This document tracks every change made to the scraper, why it was made, and what the test result was.

---

## Background

**App:** Onbogo — Flask app that scrapes Publix weekly ads and sends BOGO/sale alerts.  
**Deployment:** Google Cloud e2-micro VM (1 GB RAM), Ubuntu 22.04, gunicorn + systemd.  
**Store:** Springs Plaza, store_id=2655116, store_num=472.

---

## Change 1 — Rebuilt scraper from requests/BS4 to Playwright

**Why:** Publix redesigned their website to a Vue.js SPA. The old scraper used BeautifulSoup on a static HTML response, which no longer contained product data.

**Approach:** Use Playwright headless Chromium to load the page, wait for Vue to render product cards, then query DOM.

**Selectors identified from DevTools:**
- Container: `li.p-grid-item`
- Title: `[data-qa-automation='prod-title']`
- Badge: `.p-savings-badge__text`
- Price: `.additional-info`
- Dates: `.valid-dates`

**Result:** ❌ Scraper found 0 items. Vue rendering never completed within timeout.

---

## Change 2 — Add `--no-sandbox`, `--disable-dev-shm-usage`, `--disable-gpu` flags

**Why:** Gunicorn WORKER TIMEOUT + SIGKILL suggested OOM. These flags reduce Chromium memory usage.

**Result:** ❌ Still timing out. Gunicorn worker still getting SIGKILL'd.

---

## Change 3 — Bot detection bypass

**Why:** Suspected Publix was blocking headless Chromium via `navigator.webdriver` detection.

**Changes:**
- Added `--disable-blink-features=AutomationControlled`
- Added `context.add_init_script` to mask `navigator.webdriver`, `navigator.plugins`, `navigator.languages`
- Updated User-Agent to Chrome 124
- Added `Accept-Language` / `Accept` headers

**Result:** ❌ Still timing out. Vue never renders products.

---

## Change 4 — Block third-party trackers with `page.route()`

**Why:** HTML snapshot showed Dynatrace, GTM, Optimizely, YouTube scripts loading and eating 1 GB RAM before Vue renders products.

**Domains blocked:** googletagmanager, dynatrace, optimizely, youtube, doubleclick, demdex, foresee, mapbox, pinterest, google-analytics, ruxitagent

**Result:** ❌ Dynatrace script is inline in the HTML — can't be blocked via `page.route()`. Vue still doesn't render.

---

## Change 5 — Log all JSON API responses to find the real data endpoint

**Why:** Switched strategy from scraping rendered HTML to intercepting the API calls the Vue app makes internally.

**Finding:** Three JSON responses captured:
- `https://metrix.publix.com/...` — Dynatrace analytics, useless
- `https://www.publix.com/navigationApi/secondaryNavigation` — nav links, no store data
- **`https://services.publix.com/search/api/search/storeproductssavings/`** — the weekly ad data endpoint ✅

**Result:** ✅ Found the API endpoint. Captured request headers:
```
publixstore: 472
x-pe: True
x-src: WEB_PROMOBANNER
content-type: application/json
```
Note: `publixstore: 472` is the **store number**, NOT the location ID (`2655116`) used in the URL.

---

## Change 6 — Use `page.expect_response()` to capture POST body and response

**Why:** `response.body()` inside an event callback throws `CancelledError` in Playwright sync API.

**Finding (POST body):**
```json
{
  "operationName": "GetStoreProductsSavingsSearchResultAsync",
  "variables": {
    "keyword": "90355",
    "source": "WEB_PROMOBANNER",
    "take": 1,
    ...
  },
  "query": "query GetStoreProductsSavingsSearchResultAsync(...) { ... }"
}
```
This is a **GraphQL API**. The promo banner request fetches 1 item by item code. The full weekly ad would need `keyword: ""` and larger `take`.

**Result:** ✅ Full GraphQL query captured. Confirmed it's a POST to a GraphQL endpoint.

---

## Change 7 — Replace Playwright entirely with `requests.post()`

**Why:** Playwright is too heavy for the 1 GB VM. The GraphQL API is callable directly.

**Approach:**
- Dropped Playwright entirely
- Called `services.publix.com/search/api/search/storeproductssavings/` directly via `requests`
- Tried sources: `WEB_WEEKLYAD`, `WEB_WEEKLYADVIEWALL`, `WEB_SAVINGS`
- Used `publixstore: {store_id}` (2655116) in header

**Result:** ❌ HTTP 500 — `"Value was either too large or too small for an Int16"`. The API field that receives `publixstore` is an Int16 (max 32,767). Location ID 2655116 overflows it. The API needs the short store number (472), not the location ID.

---

## Change 8 — Discover store number via HTML / navigation API

**Why:** Needed to map location ID 2655116 → store number 472 without hardcoding.

**Attempts:**
- GET weekly ad page HTML → searched for storeNumber/storeNbr patterns → ❌ Not in HTML (Vue SPA, no SSR)
- GET `navigationApi/secondaryNavigation` → only generic nav links, no store data → ❌

**Result:** ❌ Store number not discoverable from either source.

---

## Change 9 — Resolve store number via Publix store locator API *(pending test)*

**How found:** Searched the web. The Publix store locator API returns all stores with both identifiers per store:
- `weeklyAd.storeId` = 2655116 (the URL location ID)
- `storeNumber` = "472" (the Int16 value the GraphQL API needs)

**Endpoint:**
```
GET https://services.publix.com/storelocator/api/v1/stores/?count=3000&distance=5000&includeOpenAndCloseDates=true&isWebsite=true&latitude=27.0&longitude=-81.5
```

**Implementation:**
- `_resolve_store_num(store_id)` calls this API, iterates stores, matches on `weeklyAd.storeId == store_id_int`, returns `storeNumber`
- Result cached in module-level `_store_num_cache` dict to avoid repeated lookups

**Expected result:** Store num resolves to `472`, API call succeeds with HTTP 200, products returned.

**Actual result:** ✅ Store number resolved correctly — Springs Plaza → `storeNumber=1428` (not 472; that was a wrong assumption from Playwright context). Store locator API works perfectly.

---

## Change 10 — Find correct `source` value and fix TypeError

**Why:** Change 9 confirmed store number resolves to 1428. But all three guessed source values (`WEB_WEEKLYAD`, `WEB_WEEKLYADVIEWALL`, `WEB_SAVINGS`) returned `"Bad Request - Invalid Source"`. Added `WEB_PROMOBANNER` as fallback — it returned HTTP 200 with 100 products, totalCount=35372.

**Problem:** `WEB_PROMOBANNER` with empty keyword returns the entire product catalog (35,372 items), not just the weekly ad. Three items came back with `onSale: True` but `savingLine: None`, causing `TypeError: sequence item 2: expected str instance, NoneType found` in onbogo.py when building the notification message.

**Changes:**
- Added `filterQuery: "onSale:true"` to the GraphQL payload (should reduce result set)
- Added pagination (up to 500 items, 100 per page)
- Fixed None → `""` for all string fields in sale item builder
- Added filter: only include items where `savingLine` or `promoMsg` is non-null

**Expected result:** TypeError fixed. Need to check if filterQuery reduces the set and if weekly ad BOGO items appear.

**Actual result:** ❌ `filterQuery: "onSale:true"` broke all sources — returned HTTP 200 with 0 results everywhere (including previously-working `WEB_PROMOBANNER`). The Solr field syntax was wrong.

---

## Change 11 — Remove broken filterQuery, sort by savings, try more source values

**Why:** filterQuery=onSale:true returned 0 results for all sources. Need to find a source that returns only weekly-ad items, or sort `WEB_PROMOBANNER` results so deals appear first.

**Changes:**
- Removed `filterQuery` (back to `""`)
- Added `sortOrder: "promoTotalSavings desc"` — should surface highest-value deals first
- Added more source candidates: `WEB_WEEKLY_AD`, `WEEKLY_AD`, `WEB_WEEKLYADALL`

**Actual result:** ✅ Scraper working. New source candidates all returned "Bad Request - Invalid Source". `WEB_PROMOBANNER` ran, returned 500 items (out of totalCount=35,372) sorted by savings. After Python filter (`onSale=True` and `savingLine or promoMsg` non-null), real weekly ad BOGO deals surfaced — e.g. "Jinx Dog Food - Buy 1 Get 1 Free", "Pompeian Olive Oil - Buy 1 Get 1 Free", Coca-Cola multi-pack deals, all valid 4/16–4/22. Email send failed with UnicodeEncodeError (see Change 12).

---

## Change 12 — Fix UnicodeEncodeError in notify.py

**Why:** Product titles like "Café Bustelo" contain non-ASCII characters (é = U+00E9). `smtplib.sendmail()` called `.encode('ascii')` on the raw f-string email, causing `UnicodeEncodeError: 'ascii' codec can't encode character '\xe9'`.

**Changes:**
- Added `from email.mime.text import MIMEText` import
- Replaced raw `f"Subject:...\n{message}"` string with `MIMEText(message, 'plain', 'utf-8')` in both `send_email()` and `send_sms_via_email()`
- Pass `msg.as_string()` to `sendmail()` — MIMEText handles Content-Type and charset headers automatically

**Actual result:** ✅ Email sent successfully. No UnicodeEncodeError. "Notifications sent to jameswillish!" confirmed in logs. Note: API returns "CafÃ©" (mojibake) instead of "Café" — this is a data encoding issue in the Publix API response, not our code. The email still sends fine.

---

## Change 13 — Fix mojibake, remove verbose logging, rewrite store.py

**Why:** Three cleanup items after end-to-end success:
1. Product titles like "CafÃ©" (should be "Café") — the Publix API returns data with wrong Content-Type charset, causing `requests` to decode UTF-8 bytes as Latin-1.
2. Store locator was logging the full first-store JSON blob (verbose noise, no longer needed).
3. `store.py` still used Playwright + `accessibleweeklyad.publix.com` (unreachable site).

**Changes:**
- `sales.py`: Added `import json`; replaced all `resp.json()` calls with `json.loads(resp.content.decode('utf-8'))` to force UTF-8 regardless of Content-Type header; removed sample store key/data debug lines
- `store.py`: Rewrote entirely — no Playwright; geocodes zip → lat/lon via Nominatim (free, no key), then calls store locator API; returns `[{title, address, store_id}]` same shape as before
- `requirements.txt`: Removed `playwright`, `beautifulsoup4`, `bs4`, `soupsieve` (none used)
- `DEPLOY.md`: Removed Playwright system lib install steps and `playwright install chromium`

**Expected result:** No more mojibake in product titles. Store search by zip works. Faster deploys (no Playwright install).

**Actual result:** *(pending)*

---

## Key Facts

| Item | Value |
|---|---|
| Store | Springs Plaza |
| Location ID (URL) | 2655116 |
| Store Number (API header) | 1428 (not 472 — that was a wrong assumption) |
| GraphQL endpoint | `https://services.publix.com/search/api/search/storeproductssavings/` |
| Store locator endpoint | `https://services.publix.com/storelocator/api/v1/stores/` |
| Correct source value for weekly ad | Unknown — to be determined by test |
| API auth | None required (no tokens, just headers) |

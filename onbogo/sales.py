import logging
import time
import requests

_GRAPHQL_URL = "https://services.publix.com/search/api/search/storeproductssavings/"
_STORE_LOCATOR_URL = "https://services.publix.com/storelocator/api/v1/stores/"

_GRAPHQL_QUERY = (
    "query GetStoreProductsSavingsSearchResultAsync("
    "$keyword: String, $skip: Int!, $take: Int!, $facetOverrideStr: String, "
    "$facets: String, $sortOrder: String, $ispu: Boolean, $categoryID: String, "
    "$minMatch: Int!, $boostVarIndex: Int!, $wildcardSearch: Boolean!, "
    "$isPreviewSite: Boolean!, $segmentVarIndex: Int!, $getOrderHistory: Boolean!, "
    "$filterQuery: String, $reorderItemCodes: [Int!], $intents: [String!], "
    "$searchRetryIndex: Int!, $intentVarIndex: Int!, $boostBuryQuery: String, "
    "$source: String, $elevatedProducts: [KeyValuePairOfStringAndStringInput!], "
    "$couponId: String, $forceElevation: Boolean, "
    "$searchVariation: [KeyValuePairOfStringAndStringInput!], $userCoupon: String) {"
    "\n  storeProductsSavingsSearchResult(\n    keyword: $keyword\n    skip: $skip"
    "\n    take: $take\n    facetOverrideStr: $facetOverrideStr\n    facets: $facets"
    "\n    sortOrder: $sortOrder\n    ispu: $ispu\n    categoryID: $categoryID"
    "\n    minMatch: $minMatch\n    boostVarIndex: $boostVarIndex"
    "\n    wildcardSearch: $wildcardSearch\n    isPreviewSite: $isPreviewSite"
    "\n    segmentVarIndex: $segmentVarIndex\n    getOrderHistory: $getOrderHistory"
    "\n    filterQuery: $filterQuery\n    reorderItemCodes: $reorderItemCodes"
    "\n    intents: $intents\n    boostBuryQuery: $boostBuryQuery"
    "\n    searchRetryIndex: $searchRetryIndex\n    intentVarIndex: $intentVarIndex"
    "\n    source: $source\n    elevatedProducts: $elevatedProducts"
    "\n    couponId: $couponId\n    forceElevation: $forceElevation"
    "\n    searchVariation: $searchVariation\n    userCoupon: $userCoupon"
    "\n  ) {\n    storeProducts {\n      title\n      savingLine\n      onSale"
    "\n      priceLine\n      promoMsg\n      promoConditionsMsg\n      promoValidThruMsg"
    "\n      promoTotalSavings\n      storeNbr\n    }\n    totalCount\n    searchStoreNum"
    "\n  }\n}\n"
)

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

# In-memory cache so the store locator API is only called once per process lifetime
_store_num_cache = {}


def _resolve_store_num(store_id):
    """
    The weekly-ad URL uses a location ID (e.g. 2655116) but the GraphQL API
    header needs the short store number (e.g. 472, which fits in an Int16).
    Resolve via the Publix store locator API which returns both fields.
    """
    store_id_int = int(store_id)
    if store_id_int in _store_num_cache:
        return _store_num_cache[store_id_int]

    try:
        resp = requests.get(
            _STORE_LOCATOR_URL,
            params={
                "count": 3000,
                "distance": 5000,
                "includeOpenAndCloseDates": "true",
                "isWebsite": "true",
                "latitude": 27.0,   # central Florida — large radius covers all Publix states
                "longitude": -81.5,
            },
            headers={"user-agent": _UA, "accept": "application/json"},
            timeout=20,
        )
        if resp.ok:
            stores = resp.json().get("stores", [])
            logging.debug(f"Store locator returned {len(stores)} stores")
            # Log first store's full structure so we can verify field names
            if stores:
                logging.debug(f"Sample store keys: {list(stores[0].keys())}")
                logging.debug(f"Sample store data: {stores[0]}")
            for store in stores:
                wa = store.get("weeklyAd")
                if wa and int(wa.get("storeId", 0)) == store_id_int:
                    num = str(store["storeNumber"])
                    logging.debug(f"Matched store: storeNumber={num}, weeklyAd={wa}, name={store.get('name')}")
                    _store_num_cache[store_id_int] = num
                    return num
                # Also check top-level storeId fields
                for field in ("storeId", "locationId", "id"):
                    if str(store.get(field, "")) == str(store_id_int):
                        num = str(store["storeNumber"])
                        logging.debug(f"Matched via top-level field '{field}': storeNumber={num}")
                        _store_num_cache[store_id_int] = num
                        return num
        logging.warning(f"store_id {store_id} not found in store locator response")
    except Exception as e:
        logging.error(f"Store locator API failed: {e}")

    return str(store_id)


def _build_payload(source, skip=0):
    return {
        "operationName": "GetStoreProductsSavingsSearchResultAsync",
        "variables": {
            "keyword": "",
            "boostBuryQuery": "",
            "skip": skip,
            "source": source,
            "sortOrder": "promoTotalSavings desc",
            "take": 100,
            "minMatch": 0,
            "segmentVarIndex": 0,
            "filterQuery": "",
            "getOrderHistory": False,
            "intents": [],
            "isPreviewSite": False,
            "reorderItemCodes": None,
            "wildcardSearch": False,
            "elevatedProducts": [],
            "forceElevation": False,
            "boostVarIndex": 0,
            "searchRetryIndex": 0,
            "intentVarIndex": 1,
            "userCoupon": None,
            "searchVariation": [],
        },
        "query": _GRAPHQL_QUERY,
    }


def get_weekly_ad(store_id, user=None):
    start_time = time.time()
    store_num = _resolve_store_num(store_id)

    session = requests.Session()
    session.headers.update({
        "user-agent": _UA,
        "accept": "application/json",
        "accept-language": "en-US,en;q=0.9",
        "referer": "https://www.publix.com/",
        "x-pe": "True",
        "publixstore": store_num,
        "content-type": "application/json",
    })

    products = []
    for source in ("WEB_WEEKLYAD", "WEB_WEEKLYADVIEWALL", "WEB_SAVINGS",
                   "WEB_WEEKLY_AD", "WEEKLY_AD", "WEB_WEEKLYADALL",
                   "WEB_PROMOBANNER"):
        session.headers["x-src"] = source
        skip = 0
        page_products = []
        while True:
            try:
                resp = session.post(_GRAPHQL_URL, json=_build_payload(source, skip=skip), timeout=30)
                if not resp.ok:
                    logging.debug(f"source={source} skip={skip}: HTTP {resp.status_code} — {resp.text[:200]}")
                    break
                result = (resp.json().get("data") or {}).get("storeProductsSavingsSearchResult") or {}
                batch = result.get("storeProducts") or []
                total = result.get("totalCount", 0)
                logging.debug(f"source={source} skip={skip}: {len(batch)} products (totalCount={total})")
                if not batch:
                    break
                page_products.extend(batch)
                skip += len(batch)
                # Stop paginating after 500 items or when we have all results
                if skip >= total or skip >= 500:
                    break
            except Exception as e:
                logging.error(f"API call failed for source={source} skip={skip}: {e}")
                break
        if page_products:
            products = page_products
            break

    sale_items = [
        {
            "title": p.get("title") or "",
            "deal": p.get("savingLine") or p.get("promoMsg") or "",
            "price_info": p.get("priceLine") or "",
            "valid_dates": p.get("promoValidThruMsg") or "",
        }
        for p in products
        if p.get("onSale") and (p.get("savingLine") or p.get("promoMsg"))
    ]

    elapsed = time.time() - start_time
    logging.debug(f"Scraping done in {elapsed:.2f}s. Found {len(sale_items)} sale items.")
    return sale_items

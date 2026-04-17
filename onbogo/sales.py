import logging
import re
import time
import requests

_GRAPHQL_URL = "https://services.publix.com/search/api/search/storeproductssavings/"

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


def _resolve_store_num(store_id):
    """
    Publix URL uses a location ID (e.g. 2655116) but the API header needs
    the store number (e.g. 472). Extract it from the weekly ad page HTML.
    """
    try:
        resp = requests.get(
            f"https://www.publix.com/savings/weekly-ad/view-all?storeid={store_id}",
            headers={"user-agent": _UA, "accept-language": "en-US,en;q=0.9"},
            timeout=20,
        )
        for pat in [
            r'"storeNumber"\s*:\s*"?(\d+)"?',
            r'"storeNbr"\s*:\s*"?(\d+)"?',
            r'"storeNum"\s*:\s*"?(\d+)"?',
            r'publixstore["\s:]+(\d+)',
        ]:
            m = re.search(pat, resp.text, re.IGNORECASE)
            if m:
                logging.debug(f"Resolved store_id {store_id} → {m.group(1)}")
                return m.group(1)
    except Exception as e:
        logging.debug(f"Store num lookup failed: {e}")
    logging.warning(f"Could not resolve store num for {store_id}, using it directly")
    return str(store_id)


def _build_payload(source, take=200):
    return {
        "operationName": "GetStoreProductsSavingsSearchResultAsync",
        "variables": {
            "keyword": "",
            "boostBuryQuery": "",
            "skip": 0,
            "source": source,
            "sortOrder": "",
            "take": take,
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
    for source in ("WEB_WEEKLYAD", "WEB_WEEKLYADVIEWALL", "WEB_SAVINGS"):
        session.headers["x-src"] = source
        try:
            resp = session.post(_GRAPHQL_URL, json=_build_payload(source), timeout=30)
            data = resp.json()
            result = data.get("data", {}).get("storeProductsSavingsSearchResult", {})
            batch = result.get("storeProducts") or []
            total = result.get("totalCount", 0)
            logging.debug(f"source={source}: {len(batch)} products (totalCount={total})")
            if batch:
                products = batch
                break
        except Exception as e:
            logging.error(f"API call failed for source={source}: {e}")

    sale_items = []
    for p in products:
        if p.get("onSale"):
            sale_items.append({
                "title": p.get("title", ""),
                "deal": p.get("savingLine", ""),
                "price_info": p.get("priceLine", ""),
                "valid_dates": p.get("promoValidThruMsg", "") or "",
            })

    elapsed = time.time() - start_time
    logging.debug(f"Scraping done in {elapsed:.2f}s. Found {len(sale_items)} sale items.")
    return sale_items

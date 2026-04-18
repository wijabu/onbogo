#!/usr/bin/env python3

import json
import logging
import requests

_STORE_LOCATOR_URL = "https://services.publix.com/storelocator/api/v1/stores/"
_GEOCODE_URL = "https://nominatim.openstreetmap.org/search"
_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


def locate(zip_code):
    try:
        geo = requests.get(
            _GEOCODE_URL,
            params={"postalcode": zip_code, "country": "US", "format": "json", "limit": 1},
            headers={"user-agent": _UA},
            timeout=10,
        )
        results = geo.json()
        if not results:
            logging.warning(f"Could not geocode zip: {zip_code}")
            return []
        lat = float(results[0]["lat"])
        lon = float(results[0]["lon"])
    except Exception as e:
        logging.error(f"Geocoding failed for zip {zip_code}: {e}")
        return []

    try:
        resp = requests.get(
            _STORE_LOCATOR_URL,
            params={
                "count": 10,
                "distance": 25,
                "includeOpenAndCloseDates": "true",
                "isWebsite": "true",
                "latitude": lat,
                "longitude": lon,
            },
            headers={"user-agent": _UA, "accept": "application/json"},
            timeout=20,
        )
        if not resp.ok:
            logging.error(f"Store locator API returned {resp.status_code}")
            return []
        stores_data = json.loads(resp.content.decode('utf-8')).get("stores", [])
    except Exception as e:
        logging.error(f"Store locator API failed: {e}")
        return []

    stores = []
    for s in stores_data:
        wa = s.get("weeklyAd") or {}
        store_id = wa.get("storeId")
        if not store_id:
            continue
        addr = s.get("address") or {}
        address = f"{addr.get('streetAddress', '')}, {addr.get('city', '')}, {addr.get('state', '')} {addr.get('zip', '')}".strip(", ")
        stores.append({
            "title": s.get("name", ""),
            "address": address,
            "store_id": int(store_id),
        })
        logging.debug(f"Found store: {s.get('name')} (ID: {store_id})")

    if not stores:
        logging.warning(f"No stores found for zip: {zip_code}")

    return stores


if __name__ == "__main__":
    locate("32779")

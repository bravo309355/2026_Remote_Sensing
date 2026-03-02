import json
import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import requests
from dotenv import load_dotenv

from aqi_monitor import normalize_api_records

load_dotenv()


def mask_api_key_in_url(url):
    parts = urlsplit(url)
    query_pairs = parse_qsl(parts.query, keep_blank_values=True)
    masked_pairs = []
    for key, value in query_pairs:
        if key.lower() == "api_key":
            masked_pairs.append((key, "***REDACTED***"))
        else:
            masked_pairs.append((key, value))
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path, urlencode(masked_pairs), parts.fragment)
    )


def extract_records_and_type(payload):
    records, response_type = normalize_api_records(payload)
    return records, response_type


def debug_api_request(api_key=None, timeout=10):
    api_key = api_key or os.getenv("API_KEY_MOENV")
    if not api_key:
        print("Error: API_KEY_MOENV is not set")
        return False

    url = "https://data.moenv.gov.tw/api/v2/aqx_p_432"
    try:
        params = {"api_key": api_key, "format": "json"}
        response = requests.get(url, params=params, timeout=timeout)
        print(f"Status: {response.status_code}")
        print(f"URL: {mask_api_key_in_url(response.url)}")
        response.raise_for_status()

        payload = response.json()
        records, response_type = extract_records_and_type(payload)
        print(f"Response type: {response_type}")
        print(f"Record count: {len(records)}")
        if records:
            preview = json.dumps(records[0], indent=2, ensure_ascii=False)
            print(f"Sample record: {preview[:1000]}")
        else:
            print("No records found")
        return True
    except Exception as exc:
        print(f"Error: {exc}")
        return False


if __name__ == "__main__":
    raise SystemExit(0 if debug_api_request() else 1)

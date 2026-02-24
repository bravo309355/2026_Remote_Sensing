import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv('API_KEY_MOENV')
url = 'https://data.moenv.gov.tw/api/v2/aqx_p_432'

try:
    params = {'api_key': api_key, 'format': 'json'}
    response = requests.get(url, params=params, timeout=10)
    print(f'Status: {response.status_code}')
    print(f'URL: {response.url}')
    data = response.json()
    print(f'Keys: {list(data.keys())}')
    if 'records' in data:
        print(f'Records count: {len(data["records"])}')
        print(f'Sample record: {json.dumps(data["records"][0], indent=2, ensure_ascii=False)}')
    else:
        print('No records key found')
        print(f'Sample response: {json.dumps(data, indent=2, ensure_ascii=False)[:500]}...')
except Exception as e:
    print(f'Error: {e}')

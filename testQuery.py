import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8012"

def print_response(response):
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Number of flares found: {len(data['flares'])}")
        for flare in data['flares']:
            print(f"Flare ID: {flare.get('Flare_ID', 'N/A')}, "
                  f"Date: {flare.get('Date', 'N/A')}, "
                  f"Time: {flare.get('Time (UT)', 'N/A')}, "
                  f"Class: {flare.get('flare_class', 'N/A')}")
    else:
        print(f"Error: {response.text}")
    print("\n" + "="*50 + "\n")

queries = [
    {
        "name": "Query 1: B and C class flares in September 2021",
        "params": {
            "instr": "eovsa",
            "type": "flarelist",
            "t0": "2021-09-01T00:00:00",
            "t1": "2021-09-30T23:59:59",
            "flare_class": ["B", "C"]
        }
    },
    {
        "name": "Query 2: All flares in October 2021",
        "params": {
            "instr": "eovsa",
            "type": "flarelist",
            "t0": "2021-10-01T00:00:00",
            "t1": "2021-10-31T23:59:59"
        }
    },
    {
        "name": "Query 3: M and X class flares in 2022",
        "params": {
            "instr": "eovsa",
            "type": "flarelist",
            "t0": "2022-01-01T00:00:00",
            "t1": "2022-12-31T23:59:59",
            "flare_class": ["M", "X"]
        }
    },
    {
        "name": "Query 4: Invalid instrument (should return error)",
        "params": {
            "instr": "invalid",
            "type": "flarelist",
            "t0": "2021-09-01T00:00:00",
            "t1": "2021-09-30T23:59:59"
        }
    }
]

for query in queries:
    print(query["name"])
    response = requests.get(f"{BASE_URL}/query_flares", params=query["params"])
    print_response(response)
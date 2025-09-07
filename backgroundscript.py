import requests
import json
import re

def get_open_seats(crn: str):
    url = "https://cab.brown.edu/api/?page=fose&route=details"

    payload = {
        "key": f"crn:{crn}",
        "srcdb": "202510",  # Fall 2025
        "userWithRolesStr": "!!!!!!"
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Origin": "https://cab.brown.edu",
        "Referer": "https://cab.brown.edu/",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
        "X-Requested-With": "XMLHttpRequest"
    }


    resp = requests.post(url, data=json.dumps(payload), headers=headers)
    resp.raise_for_status()
    data = resp.json()

    # Seats field is HTML snippet
    seats_html = data.get("seats", "")
    match = re.search(r'class="seats_avail">(\d+)<', seats_html)
    return int(match.group(1)) if match else "Class does not have cap."
import requests

def lookup_pin(pin):
    url = f"https://api.postalpincode.in/pincode/{pin}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json"
    }

    try:
        print("Requesting:", url)  # DEBUG
        resp = requests.get(url, headers=headers, timeout=10)

        print("Status:", resp.status_code)  # DEBUG
        print("Raw response:", resp.text[:200], "...")  # DEBUG

        if resp.status_code != 200:
            return None

        data = resp.json()

        if isinstance(data, list) and len(data) > 0:
            if data[0]["Status"] == "Success":
                po_list = data[0]["PostOffice"]
                # Prefer the Block name as City
                block = po_list[0].get("Block", "")

                # If Block missing, fallback to Name
                if not block:
                    block = po_list[0].get("Name", "")

                return {
                    "tehsil": po_list[0]["Block"],      # ← Tehsil
                    "district": po_list[0]["District"],
                    "state": po_list[0]["State"]
                }

        return None

    except Exception as e:
        print("ERROR:", e)  # DEBUG
        return None

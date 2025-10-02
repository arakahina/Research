import requests
import json
import time

BASE_URL = "https://review.opendev.org"
PROJECT = "openstack/nova"
STATUS = "merged"
LIMIT = 50
OUTPUT_FILE = "gerrit_changes_comments.json"

def fetch_changes():
    all_changes = []
    start = 0
    while True:
        query = {
            "q": f"project:{PROJECT} status:{STATUS}",
            "o": [
                "DETAILED_LABELS",
                "ALL_REVISIONS",
                "ALL_COMMITS",
                "ALL_FILES",
                "MESSAGES"
            ],
            "n": LIMIT,
            "S": start
        }

        try:
            response = requests.get(f"{BASE_URL}/changes/", params=query, timeout=60)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            print(f"Request failed at start={start}: {e}")
            break

        text = response.text.lstrip(")]}'\n")
        changes = json.loads(text)

        if not changes:
            break

        # 追加: 各 change_id ごとに comments を取得
        for change in changes:
            change_id = change["id"]
            try:
                cmt_resp = requests.get(f"{BASE_URL}/changes/{change_id}/comments", timeout=60)
                cmt_resp.raise_for_status()
                cmt_text = cmt_resp.text.lstrip(")]}'\n")
                change["comments"] = json.loads(cmt_text)
                time.sleep(0.2)  # 負荷対策
            except requests.exceptions.RequestException as e:
                print(f"Failed to fetch comments for {change_id}: {e}")
                change["comments"] = {}

        all_changes.extend(changes)
        print(f"Fetched {len(changes)} changes (total {len(all_changes)})")

        if "_more_changes" not in changes[-1]:
            break

        start += LIMIT
        time.sleep(1)

    return all_changes

if __name__ == "__main__":
    changes = fetch_changes()
    print(f"Collected {len(changes)} changes in total")
    with open(OUTPUT_FILE, "w") as f:
        json.dump(changes, f, indent=2)
    print(f"Saved changes with comments to {OUTPUT_FILE}")

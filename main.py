import os
import json
import time
import requests

# ── Config ────────────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID   = os.environ["TELEGRAM_CHAT_ID"]
SEEN_FILE = "seen_ids.json"

GAMERPOWER_GAME = "https://www.gamerpower.com/api/giveaways?type=game"
GAMERPOWER_LOOT = "https://www.gamerpower.com/api/giveaways?type=loot"

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ── Seen IDs (deduplication — ذخیره توی repo) ────────────────────────────────
def load_seen() -> set:
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    return set()

def save_seen(seen: set):
    with open(SEEN_FILE, "w") as f:
        json.dump(sorted(list(seen)), f, indent=2)

# ── Get final URL (مثل n8n: اول ریدایرکت رو بگیر) ────────────────────────────
def get_claim_url(item: dict) -> str:
    # GamerPower توی API فیلد open_giveaway داره که لینک صفحه‌شونه
    # اون صفحه ریدایرکت میکنه به لینک اصلی — ما همون هدر location رو میخوایم
    url = item.get("open_giveaway", "")
    if not url:
        return ""
    try:
        r = requests.get(url, allow_redirects=False, timeout=10)
        location = r.headers.get("location", "")
        if location:
            return location
        # اگه ریدایرکت نبود، همون URL رو برگردون
        return url
    except Exception:
        return url

# ── Send photo to Telegram ────────────────────────────────────────────────────
def send_photo(item: dict, emoji: str = "🎮"):
    claim_url = get_claim_url(item)

    caption = (
        f"{emoji} {item.get('title', '')}\n\n"
        f"📝 {item.get('description', '')}\n\n"
        f"💻 Platform: {item.get('platforms', '')}\n"
        f"📂 Type: #{item.get('type', '')}\n"
        f"💸 Original Price: {item.get('worth', '')}\n"
        f"⏳ Offer Ends: {item.get('end_date', '')}\n\n"
        f"📌 How to Claim\n{item.get('instructions', '')}"
    )

    payload = {
        "chat_id": CHAT_ID,
        "photo": item.get("image", ""),
        "caption": caption,
        "reply_markup": json.dumps({
            "inline_keyboard": [[
                {"text": "✅ Claim Now", "url": claim_url}
            ]]
        })
    }

    resp = requests.post(f"{TELEGRAM_API}/sendPhoto", data=payload, timeout=15)
    if not resp.ok:
        print(f"  ⚠️  Telegram error: {resp.status_code} - {resp.text[:200]}")
        return False
    else:
        print(f"  ✅ Sent: {item.get('title', '')} → {claim_url}")
        return True

# ── Fetch & process one category ─────────────────────────────────────────────
def process(url: str, seen: set, emoji: str):
    try:
        r = requests.get(url, timeout=15)
        data = r.json()
    except Exception as e:
        print(f"  ❌ Fetch error: {e}")
        return

    if not isinstance(data, list):
        print(f"  ❌ Unexpected response: {str(data)[:100]}")
        return

    new_items = [i for i in data if str(i.get("id")) not in seen]
    print(f"  Found {len(data)} total | {len(new_items)} new | {len(data)-len(new_items)} already sent")

    for item in new_items:
        item_id = str(item.get("id", ""))
        ok = send_photo(item, emoji)
        if ok:
            seen.add(item_id)
        time.sleep(30)

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    seen = load_seen()
    print(f"📋 Loaded {len(seen)} seen IDs")

    print("🎮 Processing Games...")
    process(GAMERPOWER_GAME, seen, "🎮")

    print("✨ Processing Loot/DLC...")
    process(GAMERPOWER_LOOT, seen, "✨")

    save_seen(seen)
    print(f"💾 Saved {len(seen)} seen IDs")
    print("Done.")

if __name__ == "__main__":
    main()

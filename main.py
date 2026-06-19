import os
import json
import time
import requests

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID   = os.environ["TELEGRAM_CHAT_ID"]
SEEN_FILE = "seen_ids.json"

GAMERPOWER_GAME = "https://www.gamerpower.com/api/giveaways?type=game"
GAMERPOWER_LOOT = "https://www.gamerpower.com/api/giveaways?type=loot"
TELEGRAM_API    = f"https://api.telegram.org/bot{BOT_TOKEN}"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'en-US,en;q=0.9',
}

def load_seen() -> set:
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    return set()

def save_seen(seen: set):
    with open(SEEN_FILE, "w") as f:
        json.dump(sorted(list(seen)), f, indent=2)

def get_claim_url(item: dict) -> str:
    gp_url = item.get("open_giveaway", "").strip()
    if not gp_url:
        return ""
    try:
        r = requests.get(gp_url, headers=HEADERS, allow_redirects=False, timeout=10)
        location = r.headers.get("location", "").strip()
        if location:
            print(f"    🔗 {gp_url} → {location}")
            return location
        return gp_url
    except Exception as e:
        print(f"    ⚠️ {e}")
        return gp_url

def send_photo(item: dict, emoji: str = "🎮") -> bool:
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

    # دکمه با رنگ سبز (Bot API 9.4)
    inline_keyboard = {
        "inline_keyboard": [[
            {
                "text": "✅ Claim Now",
                "url": claim_url,
                "style": "success"   # سبز | "primary" = آبی | "danger" = قرمز
            }
        ]]
    }

    payload = {
        "chat_id": CHAT_ID,
        "photo": item.get("image", ""),
        "caption": caption,
        "reply_markup": json.dumps(inline_keyboard)
    }

    resp = requests.post(f"{TELEGRAM_API}/sendPhoto", data=payload, timeout=15)
    if not resp.ok:
        print(f"  ⚠️ Telegram error: {resp.status_code} - {resp.text[:300]}")
        return False
    print(f"  ✅ Sent: {item.get('title', '')}")
    return True

def process(url: str, seen: set, emoji: str):
    try:
        data = requests.get(url, timeout=15).json()
    except Exception as e:
        print(f"  ❌ Fetch error: {e}")
        return

    if not isinstance(data, list):
        print(f"  ❌ Unexpected: {str(data)[:200]}")
        return

    new_items = [i for i in data if str(i.get("id")) not in seen]
    print(f"  Total: {len(data)} | New: {len(new_items)} | Skipped: {len(data)-len(new_items)}")

    for item in new_items:
        ok = send_photo(item, emoji)
        if ok:
            seen.add(str(item.get("id", "")))
        time.sleep(30)

def main():
    seen = load_seen()
    print(f"📋 Loaded {len(seen)} seen IDs")

    print("\n🎮 Processing Games...")
    process(GAMERPOWER_GAME, seen, "🎮")

    print("\n✨ Processing Loot/DLC...")
    process(GAMERPOWER_LOOT, seen, "✨")

    save_seen(seen)
    print(f"\n💾 Saved {len(seen)} seen IDs — Done.")

if __name__ == "__main__":
    main()

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

# ── Seen IDs ──────────────────────────────────────────────────────────────────
def load_seen() -> set:
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    return set()

def save_seen(seen: set):
    with open(SEEN_FILE, "w") as f:
        json.dump(sorted(list(seen)), f, indent=2)

# ── Get final claim URL ───────────────────────────────────────────────────────
def get_claim_url(item: dict) -> str:
    """
    GamerPower API فیلدهای مختلف داره:
    - open_giveaway      : لینک صفحه GamerPower (JS redirect - کار نمیکنه)
    - open_giveaway_url  : لینک مستقیم به استیم/اپیک/GOG (همینو میخوایم!)
    """
    # اول open_giveaway_url رو امتحان کن (لینک مستقیم)
    direct = item.get("open_giveaway_url", "").strip()
    if direct:
        return direct
    
    # اگه نبود، از open_giveaway با HTTP redirect بگیر
    gp_url = item.get("open_giveaway", "").strip()
    if not gp_url:
        return ""
    
    try:
        r = requests.get(gp_url, allow_redirects=False, timeout=10)
        location = r.headers.get("location", "").strip()
        if location:
            return location
    except Exception as e:
        print(f"    ⚠️ redirect error: {e}")
    
    return gp_url

# ── Send photo to Telegram ────────────────────────────────────────────────────
def send_photo(item: dict, emoji: str = "🎮") -> bool:
    claim_url = get_claim_url(item)
    print(f"    🔗 Claim URL: {claim_url}")

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
        print(f"  ⚠️  Telegram error: {resp.status_code} - {resp.text[:300]}")
        return False
    print(f"  ✅ Sent: {item.get('title', '')}")
    return True

# ── Debug: print all URL fields of first item ─────────────────────────────────
def debug_item(item: dict):
    print("  🔍 URL fields in API response:")
    for k, v in item.items():
        if "url" in k.lower() or "link" in k.lower() or "giveaway" in k.lower():
            print(f"    {k}: {v}")

# ── Fetch & process one category ─────────────────────────────────────────────
def process(url: str, seen: set, emoji: str):
    try:
        r = requests.get(url, timeout=15)
        data = r.json()
    except Exception as e:
        print(f"  ❌ Fetch error: {e}")
        return

    if not isinstance(data, list):
        print(f"  ❌ Unexpected response: {str(data)[:200]}")
        return

    new_items = [i for i in data if str(i.get("id")) not in seen]
    print(f"  Total: {len(data)} | New: {len(new_items)} | Skipped: {len(data)-len(new_items)}")

    # اولین آیتم جدید رو debug کن
    if new_items:
        debug_item(new_items[0])

    for item in new_items:
        ok = send_photo(item, emoji)
        if ok:
            seen.add(str(item.get("id", "")))
        time.sleep(30)

# ── Main ──────────────────────────────────────────────────────────────────────
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

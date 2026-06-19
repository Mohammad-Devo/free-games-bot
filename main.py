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

# ── Seen IDs (deduplication) ──────────────────────────────────────────────────
def load_seen() -> set:
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    return set()

def save_seen(seen: set):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)

# ── Resolve redirect URL ──────────────────────────────────────────────────────
def resolve_redirect(url: str) -> str:
    try:
        r = requests.get(url, allow_redirects=True, timeout=10)
        return r.url
    except Exception:
        return url

# ── Send photo to Telegram ────────────────────────────────────────────────────
def send_photo(item: dict, emoji: str = "🎮"):
    final_url = resolve_redirect(item.get("open_giveaway", ""))

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
                {"text": "✅ Claim Now", "url": final_url}
            ]]
        })
    }

    resp = requests.post(f"{TELEGRAM_API}/sendPhoto", data=payload, timeout=15)
    if not resp.ok:
        print(f"  ⚠️  Telegram error: {resp.text}")
    else:
        print(f"  ✅ Sent: {item.get('title', '')}")

# ── Fetch & process one category ─────────────────────────────────────────────
def process(url: str, seen: set, emoji: str):
    try:
        data = requests.get(url, timeout=15).json()
    except Exception as e:
        print(f"  ❌ Fetch error: {e}")
        return

    new_items = [i for i in data if str(i.get("id")) not in seen]
    print(f"  {len(new_items)} new item(s) (skipped {len(data)-len(new_items)} duplicates)")

    for item in new_items:
        send_photo(item, emoji)
        seen.add(str(item["id"]))
        time.sleep(30)   # same 30-sec wait as n8n workflow

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    seen = load_seen()
    print(f"🎮 Processing Games...")
    process(GAMERPOWER_GAME, seen, "🎮")
    print(f"✨ Processing Loot/DLC...")
    process(GAMERPOWER_LOOT, seen, "✨")
    save_seen(seen)
    print("Done.")

if __name__ == "__main__":
    main()

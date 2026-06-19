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

# ── ایموجی پریوم ──────────────────────────────────────────────────────────────
# فرمت: <tg-emoji emoji-id="ID">FALLBACK</tg-emoji>
# اگه بات Premium نداشته باشه، همون fallback ایموجی معمولی نشون داده میشه
def pe(emoji_id: str, fallback: str) -> str:
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

# آیدی‌های ایموجی پریوم (میتونی عوض کنی)
EMOJI_GAME    = pe("5309984423003823061", "🎮")   # کنترلر بازی
EMOJI_DESC    = pe("5368324170671202286", "📝")   # یادداشت
EMOJI_PLATFORM= pe("5440539497383087970", "💻")   # لپتاپ
EMOJI_TYPE    = pe("5472164874456909070", "📂")   # پوشه
EMOJI_PRICE   = pe("5471952986970267163", "💸")   # پول
EMOJI_DATE    = pe("5445284980978621387", "⏳")   # ساعت شنی
EMOJI_HOW     = pe("5447644880824181073", "📌")   # پین
EMOJI_LOOT    = pe("5188450271998577553", "✨")   # ستاره

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

def send_photo(item: dict, is_loot: bool = False) -> bool:
    claim_url = get_claim_url(item)
    title_emoji = EMOJI_LOOT if is_loot else EMOJI_GAME

    # کپشن با HTML و ایموجی پریوم
    caption = (
        f"{title_emoji} <b>{item.get('title', '')}</b>\n\n"
        f"{EMOJI_DESC} {item.get('description', '')}\n\n"
        f"{EMOJI_PLATFORM} <b>Platform:</b> {item.get('platforms', '')}\n"
        f"{EMOJI_TYPE} <b>Type:</b> #{item.get('type', '')}\n"
        f"{EMOJI_PRICE} <b>Original Price:</b> {item.get('worth', '')}\n"
        f"{EMOJI_DATE} <b>Offer Ends:</b> {item.get('end_date', '')}\n\n"
        f"{EMOJI_HOW} <b>How to Claim</b>\n{item.get('instructions', '')}"
    )

    inline_keyboard = {
        "inline_keyboard": [[
            {
                "text": "✅ Claim Now",
                "url": claim_url,
                "style": "success"
            }
        ]]
    }

    payload = {
        "chat_id": CHAT_ID,
        "photo": item.get("image", ""),
        "caption": caption,
        "parse_mode": "HTML",
        "reply_markup": json.dumps(inline_keyboard)
    }

    resp = requests.post(f"{TELEGRAM_API}/sendPhoto", data=payload, timeout=15)
    if not resp.ok:
        print(f"  ⚠️ Telegram error: {resp.status_code} - {resp.text[:300]}")
        return False
    print(f"  ✅ Sent: {item.get('title', '')}")
    return True

def process(url: str, seen: set, is_loot: bool = False):
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
        ok = send_photo(item, is_loot=is_loot)
        if ok:
            seen.add(str(item.get("id", "")))
        time.sleep(30)

def main():
    seen = load_seen()
    print(f"📋 Loaded {len(seen)} seen IDs")

    print("\n🎮 Processing Games...")
    process(GAMERPOWER_GAME, seen, is_loot=False)

    print("\n✨ Processing Loot/DLC...")
    process(GAMERPOWER_LOOT, seen, is_loot=True)

    save_seen(seen)
    print(f"\n💾 Saved {len(seen)} seen IDs — Done.")

if __name__ == "__main__":
    main()

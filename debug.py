import requests, json

r = requests.get('https://www.gamerpower.com/api/giveaways?type=game', timeout=15)
items = r.json()
item = items[0]

print("=== ALL FIELDS OF FIRST ITEM ===")
for k, v in item.items():
    print(f"{k}: {v}")

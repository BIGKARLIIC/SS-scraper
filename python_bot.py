import requests
from bs4 import BeautifulSoup
import time
import schedule
from datetime import datetime

SEARCH_URL = "https://www.ss.com/lv/electronics/phones/mobile-phones/apple/"
MAX_PAGES = 30
MIN_PRICE = 0
MAX_PRICE = 1000
KEYWORDS = [
    "iphone 16", "iphone 16 pro", "iphone 17 pro max"
]

TELEGRAM_BOT_TOKEN = ""
TELEGRAM_CHAT_ID = ""

HEADERS = {"User-Agent": "Mozilla/5.0"}


def send_telegram_message(text):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML"
        }
        response = requests.post(url, data=payload)
        if response.status_code != 200:
            print(f"[!] Failed to send Telegram message: {response.text}")
    except Exception as e:
        print(f"[!] Telegram error: {e}")


def fetch_listings(max_pages=MAX_PAGES):
    filtered_listings = []

    for page in range(1, max_pages + 1):
        url = SEARCH_URL if page == 1 else f"{SEARCH_URL}page{page}.html"
        print(f"[{datetime.now()}] Checking page {page}: {url}")

        response = requests.get(url, headers=HEADERS)
        response.encoding = 'utf-8'

        if response.status_code != 200:
            print(f"Failed to load page {page}")
            break

        soup = BeautifulSoup(response.text, 'html.parser')
        rows = soup.find_all("tr", id=lambda x: x and x.startswith("tr_"))

        if not rows:
            print(f"No listings found on page {page}.")
            break

        for row in rows:
            try:
                title_link = row.find("a", class_="am")
                title = title_link.get_text(strip=True)
                href = title_link['href']
                link = "https://www.ss.com" + href

                price_td = row.find_all("td", class_="msga2-o pp6")[-1]
                price_text = price_td.get_text(strip=True).replace("€", "").replace(" ", "")
                price = int(price_text) if price_text.isdigit() else None

                if price is None or price < MIN_PRICE or price > MAX_PRICE:
                    continue

                title_lower = title.lower()
                if not any(keyword in title_lower for keyword in KEYWORDS):
                    continue

                filtered_listings.append({
                    "title": title,
                    "price": price,
                    "link": link
                })

            except Exception as e:
                print(f"[!] Error parsing a listing: {e}")

    return filtered_listings


def job():
    print(f"\n[{datetime.now()}] Checking filtered listings...")
    listings = fetch_listings()
    if listings:
        print(f"Found {len(listings)} matching listing(s):")
        for item in listings:
            print(f" - {item['title']} ({item['price']} EUR)\n   {item['link']}")
            message = (
                f"📱 <b>{item['title']}</b>\n"
                f"💰 <b>{item['price']} EUR</b>\n"
                f"🔗 <a href=\"{item['link']}\">View Listing</a>"
            )
            send_telegram_message(message)
    else:
        print("No matching listings found.")


job()

schedule.every(30).minutes.do(job)

print("\n--- Bot is now running. Press CTRL+C to stop. ---")
while True:
    schedule.run_pending()
    time.sleep(1)

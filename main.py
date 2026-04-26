import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os
import smtplib

import schedule
import time

# -------------------------------
# CONFIG
# -------------------------------
HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

PRODUCTS_FILE = "products.csv"
DATA_FILE = "prices.csv"

EMAIL_SENDER = "mishrayogesh9960@gmail.com"
EMAIL_PASSWORD = "Yogesh9960*"
EMAIL_RECEIVER = "sm9960320648@gmail.com"

# -------------------------------
# SCRAPER
# -------------------------------
def get_product_data(url, name):
    try:
        response = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(response.content, "html.parser")

        title = soup.find("h1")
        price = soup.find("p", class_="price_color")

        if not title or not price:
            raise ValueError("Selectors not working")

        price_value = float(price.text.strip().replace("£", ""))

        return {
            "Name": name,
            "Product": title.text.strip(),
            "Price": price_value,
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "URL": url
        }

    except Exception as e:
        print(f"Error scraping {name}:", e)
        return None

# -------------------------------
# GET LAST PRICE FOR PRODUCT
# -------------------------------
def get_last_price(product_name):
    if not os.path.isfile(DATA_FILE):
        return None

    try:
        df = pd.read_csv(DATA_FILE)

        if df.empty or "Price" not in df.columns:
            return None

        product_data = df[df["Name"] == product_name]

        if product_data.empty:
            return None

        return float(product_data.iloc[-1]["Price"])

    except Exception:
        return None

# -------------------------------
# SAVE DATA
# -------------------------------
def save_to_csv(data):
    df = pd.DataFrame([data])
    file_exists = os.path.isfile(DATA_FILE)

    df.to_csv(
        DATA_FILE,
        mode='a',
        header=not file_exists,
        index=False
    )

# -------------------------------
# EMAIL ALERT
# -------------------------------
def send_email(name, product, old_price, new_price, url):
    try:
        subject = f"🔥 Price Drop Alert for {name}"
        body = f"""
Product: {product}

Old Price: {old_price}
New Price: {new_price}

Link: {url}
"""

        message = f"Subject: {subject}\n\n{body}"

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, message)
        server.quit()

        print(f"📧 Email sent for {name}")

    except Exception as e:
        print("Email error:", e)

# -------------------------------
# MAIN
# -------------------------------
def main():
    print("🔍 Checking multiple products...")

    try:
        products = pd.read_csv(PRODUCTS_FILE)
    except Exception:
        print("❌ Error reading products.csv")
        return

    for _, row in products.iterrows():
        url = row["URL"]
        name = row["Name"]

        print(f"\n➡ Checking: {name}")

        data = get_product_data(url, name)

        if not data:
            continue

        last_price = get_last_price(name)

        print("Current Price:", data["Price"])

        if last_price is None:
            print("No previous data.")
        elif data["Price"] < last_price:
            print("🔥 PRICE DROPPED!")
            send_email(name, data["Product"], last_price, data["Price"], url)
        else:
            print("No price drop.")

        save_to_csv(data)

    print("\n✅ Done checking all products")
def job():
    print("Running scheduled task...")
    main()   # your existing function

if __name__ == "__main__":
    # main()
    schedule.every(1).minutes.do(job)   # change to .day.at("10:00")
    while True:
        schedule.run_pending()
        time.sleep(1)

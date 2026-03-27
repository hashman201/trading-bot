from fastapi import FastAPI
import requests
import pandas as pd

app = FastAPI()

# 🔑 ADD YOUR DETAILS
TOKEN = "8731437941:AAGc5Y0EE-dzqv2DKofxfisaJmyxrpeEdqU"
CHAT_ID = "8239286737"


# 📩 TELEGRAM ALERT
def send_alert(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


# 📊 SAFE DATA FETCH FROM COINGECKO
def get_data():
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"

    params = {
        "vs_currency": "usd",
        "days": "1"
    }

    headers = {
        "accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

    # Debug info
    print("Status:", response.status_code)
    print("Response:", response.text[:200])

    if response.status_code != 200:
        return {"error": f"API error: {response.status_code}", "data": response.text}

    try:
        data = response.json()
    except:
        return {"error": "Invalid JSON response", "raw": response.text[:200]}

    if "prices" not in data:
        return {"error": "Invalid data format", "data": data}

    prices = data["prices"]

    if not prices or len(prices) < 2:
        return {"error": "Not enough data from API"}

    df = pd.DataFrame(prices, columns=["time", "price"])

    if df.empty:
        return {"error": "Empty DataFrame"}

    df["close"] = df["price"]

    return df


# 🚀 MAIN BOT
@app.get("/run")
def run():
    result = get_data()

    if isinstance(result, dict):
        return result

    df = result

    last = df.iloc[-1]["close"]
    prev = df.iloc[-2]["close"]

    if last > prev:
        signal = "CALL 📈"
    else:
        signal = "PUT 📉"

    message = f"""
📊 LIVE SIGNAL

Asset: BTC
Signal: {signal}
Price: {last}
Timeframe: 5 min
"""

    send_alert(message)

    return {"signal": signal}


# 🏠 HOME CHECK
@app.get("/")
def home():
    return {"status": "Bot is running"}

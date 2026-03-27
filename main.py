from fastapi import FastAPI
import requests
import pandas as pd

app = FastAPI()

# 🔑 REPLACE THESE
TOKEN = "8731437941:AAGc5Y0EE-dzqv2DKofxfisaJmyxrpeEdqU"
CHAT_ID = "8239286737"


# 📩 TELEGRAM ALERT FUNCTION
def send_alert(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


# 📊 GET LIVE DATA FROM COINGECKO (WORKS IN INDIA)
def get_data():
    url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"

    params = {
        "vs_currency": "usd",
        "days": "1",
        "interval": "minute"
    }

    response = requests.get(url)

    try:
        data = response.json()
    except:
        return {"error": "Invalid JSON response"}

    if "prices" not in data:
        return {"error": "Invalid data format", "data": data}

    prices = data["prices"]

    df = pd.DataFrame(prices, columns=["time", "price"])

    if df.empty:
        return {"error": "Empty data"}

    # Use price as close
    df["close"] = df["price"]

    return df


# 🚀 MAIN BOT
@app.get("/run")
def run():
    result = get_data()

    if isinstance(result, dict):
        return result

    df = result

    if len(df) < 2:
        return {"error": "Not enough data"}

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


# 🏠 HOME ROUTE
@app.get("/")
def home():
    return {"status": "Bot is running"}

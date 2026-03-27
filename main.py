from fastapi import FastAPI
import requests
import pandas as pd
import ta

app = FastAPI()

TOKEN = "YOUR_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"


def send_alert(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


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

    response = requests.get(url, params=params, headers=headers)

    data = response.json()

    if "prices" not in data:
        return None

    df = pd.DataFrame(data["prices"], columns=["time", "price"])

    df["close"] = df["price"]

    return df


@app.get("/run")
def run():
    df = get_data()

    if df is None or len(df) < 20:
        return {"error": "Not enough data"}

    # 📊 INDICATORS
    df["ema20"] = ta.trend.EMAIndicator(df["close"], window=20).ema_indicator()
    df["rsi"] = ta.momentum.RSIIndicator(df["close"], window=14).rsi()

    latest = df.iloc[-1]

    signal = "NO TRADE"

    # 🧠 SMART LOGIC
    if latest["close"] > latest["ema20"] and latest["rsi"] < 40:
        signal = "CALL 📈"

    elif latest["close"] < latest["ema20"] and latest["rsi"] > 60:
        signal = "PUT 📉"

    # 🚫 Only send strong signals
    if signal != "NO TRADE":
        message = f"""
🚀 SMART SIGNAL

Asset: BTC
Signal: {signal}
Price: {latest['close']}
RSI: {round(latest['rsi'],2)}
Trend EMA20: {round(latest['ema20'],2)}
Timeframe: 5–15 min
"""

        send_alert(message)

    return {
        "signal": signal,
        "price": latest["close"],
        "rsi": latest["rsi"]
    }


@app.get("/")
def home():
    return {"status": "Smart bot running"}

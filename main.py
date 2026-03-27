from fastapi import FastAPI
import requests
import pandas as pd
import ta

app = FastAPI()

TOKEN = "8731437941:AAGc5Y0EE-dzqv2DKofxfisaJmyxrpeEdqU"
CHAT_ID = "8239286737"

# 🔍 ASSETS TO SCAN
CRYPTOS = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "binancecoin": "BNB",
    "solana": "SOL",
    "ripple": "XRP",
    "cardano": "ADA",
    "dogecoin": "DOGE"
}

# Commodities via Yahoo Finance
COMMODITIES = {
    "GC=F": "GOLD",
    "SI=F": "SILVER",
    "CL=F": "OIL"
}

# Forex proxies
FOREX = {
    "EURUSD=X": "EUR/USD",
    "GBPUSD=X": "GBP/USD"
}


def send_alert(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


# 🪙 CRYPTO DATA
def get_crypto(asset):
    url = f"https://api.coingecko.com/api/v3/coins/{asset}/market_chart"
    params = {"vs_currency": "usd", "days": "1"}

    response = requests.get(url, params=params)
    data = response.json()

    if "prices" not in data:
        return None

    df = pd.DataFrame(data["prices"], columns=["time", "price"])
    df["close"] = df["price"]

    return df


# 🛢️ YAHOO FINANCE DATA
def get_yahoo(symbol):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=5m&range=1d"

    response = requests.get(url)
    data = response.json()

    try:
        prices = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]
    except:
        return None

    df = pd.DataFrame(prices, columns=["close"])
    df.dropna(inplace=True)

    return df


# 🧠 ANALYSIS ENGINE
def analyze(df, name):
    if df is None or len(df) < 30:
        return None

    df["ema20"] = ta.trend.EMAIndicator(df["close"], window=20).ema_indicator()
    df["rsi"] = ta.momentum.RSIIndicator(df["close"], window=14).rsi()

    latest = df.iloc[-1]

    signal = None
    score = 0

    # Trend
    if latest["close"] > latest["ema20"]:
        score += 30
        trend = "UP"
    else:
        score += 30
        trend = "DOWN"

    # RSI
    if latest["rsi"] < 40:
        signal = "CALL 📈"
        score += 40
    elif latest["rsi"] > 60:
        signal = "PUT 📉"
        score += 40

    # Strength
    if abs(latest["close"] - latest["ema20"]) > 0:
        score += 30

    if signal is None:
        return None

    return {
        "asset": name,
        "signal": signal,
        "score": score,
        "price": latest["close"],
        "rsi": latest["rsi"]
    }


@app.get("/run")
def run():
    best_trade = None

    # 🔐 Scan cryptos
    for asset, symbol in CRYPTOS.items():
        df = get_crypto(asset)
        result = analyze(df, symbol)

        if result and (best_trade is None or result["score"] > best_trade["score"]):
            best_trade = result

    # 🛢️ Scan commodities
    for symbol, name in COMMODITIES.items():
        df = get_yahoo(symbol)
        result = analyze(df, name)

        if result and (best_trade is None or result["score"] > best_trade["score"]):
            best_trade = result

    # 💱 Scan forex proxies
    for symbol, name in FOREX.items():
        df = get_yahoo(symbol)
        result = analyze(df, name)

        if result and (best_trade is None or result["score"] > best_trade["score"]):
            best_trade = result

    if best_trade is None:
        return {"message": "No trades found"}

    if best_trade["score"] < 70:
        return {"message": "No high-quality trades"}

    message = f"""
🚀 BEST TRADE (A+)

Asset: {best_trade['asset']}
Signal: {best_trade['signal']}
Score: {best_trade['score']}/100
Price: {round(best_trade['price'],2)}
RSI: {round(best_trade['rsi'],2)}
"""

    send_alert(message)

    return best_trade


@app.get("/")
def home():
    return {"status": "Advanced scanner running"}

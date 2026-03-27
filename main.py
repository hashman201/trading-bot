from fastapi import FastAPI
import requests
import pandas as pd
import ta

app = FastAPI()

TOKEN = "8731437941:AAGc5Y0EE-dzqv2DKofxfisaJmyxrpeEdqU"
CHAT_ID = "8239286737"

# Assets (keep small for stability)
CRYPTOS = {
    "bitcoin": "BTC",
    "ethereum": "ETH"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}


# 📩 TELEGRAM
def send_alert(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=5)
    except Exception as e:
        print("Telegram error:", e)


# 🪙 CRYPTO DATA (FIXED)
def get_crypto(asset):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{asset}/market_chart"
        params = {"vs_currency": "usd", "days": "1"}

        res = requests.get(url, params=params, headers=HEADERS, timeout=10)

        print("Crypto status:", res.status_code)

        if res.status_code != 200:
            return None

        data = res.json()

        if "prices" not in data:
            return None

        df = pd.DataFrame(data["prices"], columns=["time", "price"])

        df["close"] = df["price"]

        return df

    except Exception as e:
        print("Crypto error:", e)
        return None


# 🧠 ANALYSIS
def analyze(df, name):
    try:
        if df is None or len(df) < 30:
            return None

        df["ema20"] = ta.trend.EMAIndicator(df["close"], window=20).ema_indicator()
        df["rsi"] = ta.momentum.RSIIndicator(df["close"], window=14).rsi()

        latest = df.iloc[-1]

        if pd.isna(latest["ema20"]) or pd.isna(latest["rsi"]):
            return None

        signal = None
        score = 0

        # Trend
        if latest["close"] > latest["ema20"]:
            score += 30
        else:
            score += 30

        # RSI logic
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
            "price": float(latest["close"]),
            "rsi": float(latest["rsi"])
        }

    except Exception as e:
        print("Analysis error:", e)
        return None


# 🚀 MAIN
@app.get("/run")
def run():
    debug = []
    best_trade = None

    for asset, symbol in CRYPTOS.items():
        df = get_crypto(asset)

        if df is None:
            debug.append(f"{symbol}: API failed")
            continue

        result = analyze(df, symbol)

        if result is None:
            debug.append(f"{symbol}: no signal")
            continue

        if best_trade is None or result["score"] > best_trade["score"]:
            best_trade = result

    if best_trade is None:
        return {
            "status": "no trade",
            "debug": debug
        }

    if best_trade["score"] < 70:
        return {
            "status": "low quality",
            "trade": best_trade,
            "debug": debug
        }

    message = f"""
🚀 BEST TRADE

Asset: {best_trade['asset']}
Signal: {best_trade['signal']}
Score: {best_trade['score']}
Price: {round(best_trade['price'],2)}
RSI: {round(best_trade['rsi'],2)}
"""

    send_alert(message)

    return {
        "status": "success",
        "trade": best_trade,
        "debug": debug
    }


@app.get("/")
def home():
    return {"status": "Stable crypto bot running"}

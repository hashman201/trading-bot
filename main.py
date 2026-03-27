from fastapi import FastAPI
import requests
import pandas as pd
import ta

app = FastAPI()

TOKEN = "YOUR_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

# Assets
CRYPTOS = {
    "bitcoin": "BTC",
    "ethereum": "ETH",
    "binancecoin": "BNB"
}

COMMODITIES = {
    "GC=F": "GOLD",
    "CL=F": "OIL"
}


# 📩 TELEGRAM
def send_alert(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=5)
    except Exception as e:
        print("Telegram error:", e)


# 🪙 CRYPTO DATA (SAFE)
def get_crypto(asset):
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{asset}/market_chart"
        params = {"vs_currency": "usd", "days": "1"}

        res = requests.get(url, params=params, timeout=10)

        if res.status_code != 200:
            print("Crypto API error:", res.status_code)
            return None

        data = res.json()

        if "prices" not in data:
            print("Crypto bad data:", data)
            return None

        df = pd.DataFrame(data["prices"], columns=["time", "price"])

        if df.empty:
            return None

        df["close"] = df["price"]

        return df

    except Exception as e:
        print("Crypto fetch error:", e)
        return None


# 🛢️ YAHOO DATA (SAFE)
def get_yahoo(symbol):
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=5m&range=1d"

        res = requests.get(url, timeout=10)

        if res.status_code != 200:
            print("Yahoo API error:", res.status_code)
            return None

        data = res.json()

        prices = data["chart"]["result"][0]["indicators"]["quote"][0]["close"]

        df = pd.DataFrame(prices, columns=["close"])
        df.dropna(inplace=True)

        if df.empty:
            return None

        return df

    except Exception as e:
        print("Yahoo fetch error:", e)
        return None


# 🧠 ANALYSIS (SAFE)
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
            "price": float(latest["close"]),
            "rsi": float(latest["rsi"])
        }

    except Exception as e:
        print("Analysis error:", e)
        return None


# 🚀 MAIN ROUTE (FULL DEBUG)
@app.get("/run")
def run():
    debug_log = []

    best_trade = None

    try:
        # 🔐 CRYPTO SCAN
        for asset, symbol in CRYPTOS.items():
            df = get_crypto(asset)

            if df is None:
                debug_log.append(f"{symbol}: data failed")
                continue

            result = analyze(df, symbol)

            if result is None:
                debug_log.append(f"{symbol}: no signal")
                continue

            if best_trade is None or result["score"] > best_trade["score"]:
                best_trade = result

        # 🛢️ COMMODITIES SCAN
        for symbol, name in COMMODITIES.items():
            df = get_yahoo(symbol)

            if df is None:
                debug_log.append(f"{name}: data failed")
                continue

            result = analyze(df, name)

            if result is None:
                debug_log.append(f"{name}: no signal")
                continue

            if best_trade is None or result["score"] > best_trade["score"]:
                best_trade = result

        # ❌ NO TRADE
        if best_trade is None:
            return {
                "status": "no trade",
                "debug": debug_log
            }

        # ❌ LOW QUALITY
        if best_trade["score"] < 70:
            return {
                "status": "low quality",
                "debug": debug_log,
                "best": best_trade
            }

        # ✅ SEND ALERT
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
            "debug": debug_log
        }

    except Exception as e:
        return {
            "error": str(e),
            "debug": debug_log
        }


@app.get("/")
def home():
    return {"status": "Stable bot running"}

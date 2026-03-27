from fastapi import FastAPI
import requests
import pandas as pd

app = FastAPI()

# 🔑 REPLACE THESE WITH YOUR VALUES
TOKEN = "8731437941:AAGc5Y0EE-dzqv2DKofxfisaJmyxrpeEdqU"
CHAT_ID = "8239286737"


# 📩 SEND TELEGRAM ALERT
def send_alert(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})


# 📊 FETCH MARKET DATA (SAFE VERSION)
def get_data():
    url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=5m&limit=50"
    
    response = requests.get(url)

    # Debug info (visible in Render logs)
    print("Status Code:", response.status_code)
    print("Raw Data:", response.text[:200])  # first 200 chars only

    try:
        data = response.json()
    except:
        return {"error": "Invalid JSON response"}

    # Check if correct format
    if not isinstance(data, list):
        return {"error": "API did not return list", "data": data}

    # Convert to DataFrame safely
    try:
        df = pd.DataFrame(data)
    except Exception as e:
        return {"error": f"DataFrame error: {str(e)}"}

    if df.empty:
        return {"error": "Empty DataFrame"}

    # Keep required columns
    df = df.iloc[:, :5]
    df.columns = ["time", "open", "high", "low", "close"]

    try:
        df["open"] = df["open"].astype(float)
        df["high"] = df["high"].astype(float)
        df["low"] = df["low"].astype(float)
        df["close"] = df["close"].astype(float)
    except Exception as e:
        return {"error": f"Conversion error: {str(e)}"}

    return df


# 🚀 MAIN BOT ROUTE
@app.get("/run")
def run():
    result = get_data()

    # If error returned, show it
    if isinstance(result, dict):
        return result

    df = result

    # Ensure enough data
    if len(df) < 2:
        return {"error": "Not enough data"}

    last = df.iloc[-1]
    prev = df.iloc[-2]

    # Simple signal logic
    if last['close'] > prev['close']:
        signal = "CALL 📈"
    else:
        signal = "PUT 📉"

    message = f"""
📊 LIVE SIGNAL

Asset: BTC/USDT
Signal: {signal}
Price: {last['close']}
Timeframe: 5 min
"""

    send_alert(message)

    return {"signal": signal}


# 🏠 HOME ROUTE (FOR TEST)
@app.get("/")
def home():
    return {"status": "Bot is running"}

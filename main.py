from fastapi import FastAPI
import requests
import pandas as pd

app = FastAPI()

TOKEN = "8731437941:AAGc5Y0EE-dzqv2DKofxfisaJmyxrpeEdqU"
CHAT_ID = "8239286737"

def send_alert(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

# Get last 50 candles (5 min each)
def get_data():
    url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=5m&limit=50"
    data = requests.get(url).json()

    df = pd.DataFrame(data)
    df = df.iloc[:, :5]
    df.columns = ["time","open","high","low","close"]
    df = df.astype(float)

    return df

@app.get("/run")
def run():
    try:
        df = get_data()

        last = df.iloc[-1]
        prev = df.iloc[-2]

        if last['close'] > prev['close']:
            signal = "CALL 📈"
        else:
            signal = "PUT 📉"

        message = f"""
📊 LIVE SIGNAL

Signal: {signal}
Price: {last['close']}
"""

        send_alert(message)

        return {"signal": signal}

    except Exception as e:
        return {"error": str(e)}
    df = get_data()

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

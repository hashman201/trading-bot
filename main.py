from fastapi import FastAPI
import requests

app = FastAPI()

TOKEN = "YOUR_TOKEN"
CHAT_ID = "YOUR_CHAT_ID"

def send_alert(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

@app.get("/")
def home():
    return {"status": "running"}

@app.get("/run")
def run():
    send_alert("Bot is working!")
    return {"status": "sent"}

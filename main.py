from fastapi import FastAPI
import requests

app = FastAPI()

TOKEN = "8731437941:AAGc5Y0EE-dzqv2DKofxfisaJmyxrpeEdqU"
CHAT_ID = "8239286737"

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

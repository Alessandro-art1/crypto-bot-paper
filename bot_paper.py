import ccxt
import pandas as pd
import ta
import time
from datetime import datetime
from flask import Flask
from threading import Thread

# ===== FLASK KEEP ALIVE =====
app = Flask(__name__)

@app.route("/")
def home():
    return "BOT AVVIATO (PAPER TRADING)"

def run():
    app.run(host="0.0.0.0", port=8080)

Thread(target=run).start()

# ===== CONFIG =====
CAPITALE_INIZIALE = 100.0
capitale = CAPITALE_INIZIALE
posizione = None
prezzo_ingresso = 0

exchange = ccxt.binance()

symbol = "BTC/USDT"
timeframe = "15m"

# ===== FUNZIONI =====
def get_data():
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=200)
    df = pd.DataFrame(ohlcv, columns=["time","open","high","low","close","volume"])
    df["rsi"] = ta.momentum.RSIIndicator(df["close"]).rsi()
    df["ema50"] = ta.trend.EMAIndicator(df["close"], 50).ema_indicator()
    df["ema200"] = ta.trend.EMAIndicator(df["close"], 200).ema_indicator()
    return df

# ===== LOOP =====
print("=== BOT AVVIATO (PAPER TRADING) ===")

while True:
    try:
        df = get_data()
        last = df.iloc[-1]
        prezzo = last["close"]

        if posizione is None:
            if last["rsi"] < 30 and last["ema50"] > last["ema200"]:
                posizione = "LONG"
                prezzo_ingresso = prezzo
                print(f"[BUY] {prezzo}")
        else:
            profitto = (prezzo - prezzo_ingresso) / prezzo_ingresso * 100

            if last["rsi"] > 70 or profitto >= 4 or profitto <= -2:
                capitale *= (1 + profitto / 100)
                print(f"[SELL] {prezzo} | Profitto: {profitto:.2f}% | Capitale: {capitale:.2f}€")
                posizione = None

        time.sleep(60)
        import csv
import os

LOG_FILE = "trades.csv"

def salva_trade(data, tipo, prezzo, capitale):
    file_esiste = os.path.isfile(LOG_FILE)
    with open(LOG_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_esiste:
            writer.writerow(["data", "tipo", "prezzo", "capitale"])
        writer.writerow([data, tipo, prezzo, round(capitale, 2)])


    except Exception as e:
        print("Errore:", e)
        time.sleep(60)

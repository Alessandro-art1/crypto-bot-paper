from flask import Flask
from threading import Thread
import ccxt
import pandas as pd
import ta
import time
from datetime import datetime

app = Flask('')

@app.route('/')
def home():
    return "BOT ATTIVO"

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()

CAPITALE_INIZIALE = 100.0
capitale = CAPITALE_INIZIALE
posizione = None
prezzo_ingresso = 0

exchange = ccxt.binance()
symbol = 'BTC/USDT'
timeframe = '15m'

def log(msg):
    print(msg)
    with open("log.txt", "a") as f:
        f.write(f"{datetime.now()} - {msg}\n")

log("=== BOT AVVIATO (PAPER TRADING) ===")

while True:
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=100)
        df = pd.DataFrame(ohlcv, columns=['t','o','h','l','c','v'])

        df['ema9'] = ta.trend.ema_indicator(df['c'], 9)
        df['ema21'] = ta.trend.ema_indicator(df['c'], 21)
        df['rsi'] = ta.momentum.rsi(df['c'], 14)

        last = df.iloc[-1]
        prezzo = last['c']

        if posizione is None:
            if last['ema9'] > last['ema21'] and last['rsi'] < 30:
                posizione = capitale / prezzo
                prezzo_ingresso = prezzo
                capitale = 0
                log(f"BUY a {prezzo:.2f}")

        else:
            profit = (prezzo - prezzo_ingresso) / prezzo_ingresso

            if profit >= 0.03 or profit <= -0.02 or last['rsi'] > 70:
                capitale = posizione * prezzo
                log(f"SELL a {prezzo:.2f} | Capitale: {capitale:.2f}€")
                posizione = None

        time.sleep(60)

    except Exception as e:
        log(f"ERRORE: {e}")
        time.sleep(60)

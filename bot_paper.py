from flask import Flask, jsonify, render_template_string
from datetime import datetime
import csv
import os
import random
import time
import threading
import requests

app = Flask(__name__)

# ===== CONFIG =====
CAPITALE_INIZIALE = 100.0
capitale = CAPITALE_INIZIALE
LOG_FILE = "trades.csv"

prezzi = []
posizione_aperta = False
prezzo_ingresso = 0.0
numero_trade = 0

# ===== TEMPLATE HTML =====
HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>BOT RSI (BTC)</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body{
            background: linear-gradient(135deg,#0f172a,#020617);
            font-family: Arial;
            color:white;
            display:flex;
            justify-content:center;
            align-items:center;
            height:100vh;
        }
        .card{
            background:#020617;
            padding:30px;
            border-radius:15px;
            width:350px;
            box-shadow:0 0 30px rgba(0,255,255,0.15);
        }
        h1{margin-bottom:20px;}
        .row{margin:8px 0;}
    </style>
</head>
<body>
    <div class="card">
        <h1>🤖 BOT RSI (BTC)</h1>
        <div class="row">Prezzo BTC: {{ prezzo }}</div>
        <div class="row">RSI: {{ rsi }}</div>
        <div class="row">Capitale: €{{ capitale }}</div>
        <div class="row">Trade: {{ trade }}</div>
        <div class="row">Profitto: {{ profitto }} €</div>
        <div class="row">Posizione: {{ posizione }}</div>
        <div class="row">Update: {{ update }}</div>
    </div>
</body>
</html>
"""

# ===== UTILS =====

def get_btc_price():
    try:
        url = "https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT"
        r = requests.get(url, timeout=5)
        data = r.json()
        return float(data["price"])
    except:
        return None

def calcola_rsi(prezzi, periodi=14):
    if len(prezzi) < periodi + 1:
        return 50

    guadagni = []
    perdite = []

    for i in range(-periodi, 0):
        delta = prezzi[i] - prezzi[i - 1]
        if delta >= 0:
            guadagni.append(delta)
        else:
            perdite.append(abs(delta))

    avg_gain = sum(guadagni) / periodi if guadagni else 0.0001
    avg_loss = sum(perdite) / periodi if perdite else 0.0001

    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)),2)

def salva_trade(tipo, prezzo):
    global capitale
    file_esiste = os.path.exists(LOG_FILE)
    with open(LOG_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_esiste:
            writer.writerow(["data", "tipo", "prezzo", "capitale"])
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            tipo,
            round(prezzo, 2),
            round(capitale, 2)
        ])

# ===== BOT =====

def trading_bot():
    global capitale, posizione_aperta, prezzo_ingresso, numero_trade

    while True:
        prezzo = get_btc_price()
        if prezzo:
            prezzi.append(prezzo)

            rsi = calcola_rsi(prezzi)

            if rsi < 30 and not posizione_aperta:
                posizione_aperta = True
                prezzo_ingresso = prezzo
                salva_trade("BUY", prezzo)

            elif rsi > 70 and posizione_aperta:
                profitto = (prezzo - prezzo_ingresso) / prezzo_ingresso
                capitale *= (1 + profitto)
                posizione_aperta = False
                numero_trade += 1
                salva_trade("SELL", prezzo)

        time.sleep(10)  # aggiornamento ogni 10 sec

# ===== ROUTE =====

@app.route("/")
def dashboard():
    prezzo = prezzi[-1] if prezzi else 0
    rsi = calcola_rsi(prezzi)
    profitto = round(capitale - CAPITALE_INIZIALE,2)
    posizione = "APERTO" if posizione_aperta else "CHIUSO"

    return render_template_string(
        HTML,
        prezzo=round(prezzo,2),
        rsi=rsi,
        capitale=round(capitale,2),
        trade=numero_trade,
        profitto=profitto,
        posizione=posizione,
        update=datetime.now().strftime("%H:%M:%S")
    )

# ===== START =====

if __name__ == "__main__":
    t = threading.Thread(target=trading_bot)
    t.daemon = True
    t.start()
    app.run(host="0.0.0.0", port=8080)

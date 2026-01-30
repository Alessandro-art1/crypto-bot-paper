from flask import Flask, jsonify, render_template_string
from datetime import datetime
import csv
import os
import random
import time
import threading

app = Flask(__name__)

CAPITALE_INIZIALE = 100.0
capitale = CAPITALE_INIZIALE
LOG_FILE = "trades.csv"

prezzi = [100.0]
posizione_aperta = False
prezzo_ingresso = 0.0
numero_trade = 0

# ---------- RSI ----------
def calcola_rsi(prezzi, periodi=14):
    if len(prezzi) < periodi + 1:
        return 50

    guadagni, perdite = [], []
    for i in range(-periodi, 0):
        delta = prezzi[i] - prezzi[i - 1]
        if delta >= 0:
            guadagni.append(delta)
        else:
            perdite.append(abs(delta))

    avg_gain = sum(guadagni) / periodi if guadagni else 0
    avg_loss = sum(perdite) / periodi if perdite else 1
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

# ---------- LOG ----------
def salva_trade(tipo, prezzo):
    global capitale, numero_trade
    numero_trade += 1

    file_esiste = os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_esiste:
            writer.writerow(["data", "tipo", "prezzo", "capitale"])
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            tipo,
            round(prezzo, 2),
            round(capitale, 2)
        ])

# ---------- BOT ----------
def trading_bot():
    global capitale, posizione_aperta, prezzo_ingresso

    while True:
        nuovo_prezzo = round(prezzi[-1] + random.uniform(-1.5, 1.5), 2)
        prezzi.append(nuovo_prezzo)

        rsi = calcola_rsi(prezzi)

        if rsi < 45 and not posizione_aperta:
            posizione_aperta = True
            prezzo_ingresso = nuovo_prezzo
            salva_trade("BUY", nuovo_prezzo)

        elif rsi > 55 and posizione_aperta:
            profitto = (nuovo_prezzo - prezzo_ingresso) / prezzo_ingresso
            capitale *= (1 + profitto)
            posizione_aperta = False
            salva_trade("SELL", nuovo_prezzo)

        time.sleep(5)

# ---------- UI ----------
HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Crypto Bot Paper</title>
    <meta http-equiv="refresh" content="5">
    <style>
        body { font-family: Arial; background:#0f172a; color:#e5e7eb; text-align:center }
        .box { background:#1e293b; padding:20px; margin:20px auto; width:320px; border-radius:12px }
        h1 { color:#38bdf8 }
        .green { color:#4ade80 }
        .red { color:#f87171 }
    </style>
</head>
<body>
    <h1>🤖 Crypto Bot (Paper Trading)</h1>

    <div class="box">
        <p>⏱ Aggiornamento: {{time}}</p>
        <p>💰 Capitale: <b>{{capitale}} €</b></p>
        <p>📊 Profitto: <b class="{{color}}">{{profitto}} € ({{profitto_pct}}%)</b></p>
        <p>🔄 Trade: {{trade}}</p>
        <p>📈 Prezzo: {{prezzo}}</p>
        <p>📉 RSI: {{rsi}}</p>
        <p>⚙ Stato: {{stato}}</p>
    </div>
</body>
</html>
"""

@app.route("/")
def dashboard():
    profitto = round(capitale - CAPITALE_INIZIALE, 2)
    profitto_pct = round((profitto / CAPITALE_INIZIALE) * 100, 2)
    color = "green" if profitto >= 0 else "red"

    return render_template_string(
        HTML,
        time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        capitale=round(capitale, 2),
        profitto=profitto,
        profitto_pct=profitto_pct,
        trade=numero_trade,
        prezzo=prezzi[-1],
        rsi=calcola_rsi(prezzi),
        stato="POSIZIONE APERTA" if posizione_aperta else "IN ATTESA",
        color=color
    )

# ---------- START ----------
threading.Thread(target=trading_bot, daemon=True).start()

if __name__ == "__main__":
    app.run()

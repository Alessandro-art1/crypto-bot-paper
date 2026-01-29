from flask import Flask, jsonify
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

# ---------- UTILS ----------

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

    avg_gain = sum(guadagni) / periodi if guadagni else 0
    avg_loss = sum(perdite) / periodi if perdite else 1

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


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

# ---------- BOT LOGIC ----------

def trading_bot():
    global capitale, posizione_aperta, prezzo_ingresso

    while True:
        # prezzo simulato
        nuovo_prezzo = prezzi[-1] + random.uniform(-1, 1)
        prezzi.append(round(nuovo_prezzo, 2))

        rsi = calcola_rsi(prezzi)

        if rsi < 30 and not posizione_aperta:
            posizione_aperta = True
            prezzo_ingresso = nuovo_prezzo
            salva_trade("BUY", nuovo_prezzo)

        elif rsi > 70 and posizione_aperta:
            profitto = (nuovo_prezzo - prezzo_ingresso) / prezzo_ingresso
            capitale *= (1 + profitto)
            posizione_aperta = False
            salva_trade("SELL", nuovo_prezzo)

        time.sleep(15)  # ogni 15 secondi (simula timeframe)

# ---------- DASHBOARD ----------

@app.route("/")
def dashboard():
    profitto = capitale - CAPITALE_INIZIALE
    profitto_pct = (profitto / CAPITALE_INIZIALE) * 100

    return jsonify({
        "stato": "BOT ATTIVO (RSI PA

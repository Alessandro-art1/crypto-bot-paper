from flask import Flask, jsonify
import requests
import time
import threading
from datetime import datetime

app = Flask(__name__)

# ===== CONFIG =====
CAPITALE_INIZIALE = 100.0
capitale = CAPITALE_INIZIALE
btc_qty = 0.0
prezzo_ingresso = 0.0
posizione_aperta = False
numero_trade = 0
prezzi = []

# ===== PREZZO BTC REALE =====
def get_btc_price():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": "bitcoin", "vs_currencies": "eur"}
    r = requests.get(url, params=params, timeout=10)
    return r.json()["bitcoin"]["eur"]

# ===== RSI =====
def calcola_rsi(data, periodi=14):
    if len(data) < periodi + 1:
        return 50

    guadagni = []
    perdite = []

    for i in range(-periodi, 0):
        delta = data[i] - data[i - 1]
        if delta >= 0:
            guadagni.append(delta)
        else:
            perdite.append(abs(delta))

    avg_gain = sum(guadagni) / periodi if guadagni else 0
    avg_loss = sum(perdite) / periodi if perdite else 1

    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

# ===== BOT =====
def trading_bot():
    global capitale, btc_qty, prezzo_ingresso, posizione_aperta, numero_trade

    while True:
        try:
            prezzo = get_btc_price()
            prezzi.append(prezzo)
            rsi = calcola_rsi(prezzi)

            # BUY
            if rsi < 45 and not posizione_aperta:
                btc_qty = capitale / prezzo
                capitale = 0
                prezzo_ingresso = prezzo
                posizione_aperta = True
                numero_trade += 1

            # SELL
            elif rsi > 55 and posizione_aperta:
                capitale = btc_qty * prezzo
                btc_qty = 0
                posizione_aperta = False
                numero_trade += 1

            time.sleep(15)

        except Exception as e:
            time.sleep(10)

# ===== DASHBOARD =====
@app.route("/")
def dashboard():
    prezzo = prezzi[-1] if prezzi else 0
    valore_totale = capitale + (btc_qty * prezzo)
    profitto = valore_totale - CAPITALE_INIZIALE
    profitto_pct = (profitto / CAPITALE_INIZIALE) * 100

    return jsonify({
        "stato": "IN POSIZIONE BTC" if posizione_aperta else "IN ATTESA",
        "prezzo_btc_eur": prezzo,
        "rsi": calcola_rsi(prezzi),
        "capitale_eur": round(capitale, 2),
        "btc_qty": round(btc_qty, 6),
        "valore_totale_eur": round(valore_totale, 2),
        "profitto_eur": round(profitto, 2),
        "profitto_percento": round(profitto_pct, 2),
        "numero_trade": numero_trade,
        "ultimo_aggiornamento": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

# ===== AVVIO =====
threading.Thread(target=trading_bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

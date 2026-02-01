from flask import Flask, jsonify, render_template_string
import requests
import time
import threading
from datetime import datetime, timedelta

app = Flask(__name__)

# ================= CONFIG =================
CAPITALE_TOTALE = 100.0
COOLDOWN_MINUTI = 15
STOP_LOSS = -0.03      # -3%
TAKE_PROFIT = 0.05    # +5%
UPDATE_SECONDS = 15

CRYPTOS = {
    "BTC": {"symbol": "bitcoin", "capitale": 34.0},
    "ETH": {"symbol": "ethereum", "capitale": 33.0},
    "SOL": {"symbol": "solana", "capitale": 33.0},
}

# ================= STATE =================
stato = {}

for c in CRYPTOS:
    stato[c] = {
        "capitale": CRYPTOS[c]["capitale"],
        "qty": 0.0,
        "prezzi": [],
        "prezzo_ingresso": 0.0,
        "ultimo_trade": None,
        "trade": 0,
        "rsi": None
    }

# ================= UTILS =================
def get_prezzi():
    ids = ",".join([CRYPTOS[c]["symbol"] for c in CRYPTOS])
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=eur"
    return requests.get(url, timeout=10).json()

def calcola_rsi(data, periodi=14):
    if len(data) < periodi + 1:
        return None

    gains, losses = 0, 0
    for i in range(-periodi, 0):
        delta = data[i] - data[i - 1]
        if delta >= 0:
            gains += delta
        else:
            losses += abs(delta)

    if losses == 0:
        return 100

    rs = (gains / periodi) / (losses / periodi)
    return round(100 - (100 / (1 + rs)), 2)

# ================= BOT =================
def bot_loop():
    while True:
        prezzi = get_prezzi()
        now = datetime.now()

        for c in CRYPTOS:
            price = prezzi[CRYPTOS[c]["symbol"]]["eur"]
            s = stato[c]
            s["prezzi"].append(price)
            s["rsi"] = calcola_rsi(s["prezzi"])

            # COOLDOWN
            if s["ultimo_trade"] and now - s["ultimo_trade"] < timedelta(minutes=COOLDOWN_MINUTI):
                continue

            # BUY
            if s["qty"] == 0 and s["rsi"] and s["rsi"] < 30:
                s["qty"] = s["capitale"] / price
                s["prezzo_ingresso"] = price
                s["capitale"] = 0
                s["ultimo_trade"] = now
                s["trade"] += 1

            # SELL
            if s["qty"] > 0:
                variazione = (price - s["prezzo_ingresso"]) / s["prezzo_ingresso"]

                if variazione <= STOP_LOSS or variazione >= TAKE_PROFIT or (s["rsi"] and s["rsi"] > 70):
                    s["capitale"] = s["qty"] * price
                    s["qty"] = 0
                    s["ultimo_trade"] = now
                    s["trade"] += 1

        time.sleep(UPDATE_SECONDS)

# ================= API =================
@app.route("/api")
def api():
    totale = 0
    dettagli = {}

    for c in stato:
        prezzo = stato[c]["prezzi"][-1] if stato[c]["prezzi"] else 0
        valore = stato[c]["capitale"] + stato[c]["qty"] * prezzo
        totale += valore

        dettagli[c] = {
            "prezzo": prezzo,
            "qty": round(stato[c]["qty"], 6),
            "rsi": stato[c]["rsi"],
            "valore": round(valore, 2),
            "trade": stato[c]["trade"]
        }

    return jsonify({
        "valore_totale": round(totale, 2),
        "profitto": round(totale - CAPITALE_TOTALE, 2),
        "ultimo_aggiornamento": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dettagli": dettagli
    })

# ================= DASHBOARD =================
@app.route("/")
def dashboard():
    return render_template_string("""
    <html>
    <head>
        <meta http-equiv="refresh" content="5">
        <style>
            body { background:#111; color:#0f0; font-family:Arial }
            .card { border:1px solid #0f0; padding:10px; margin:10px }
        </style>
    </head>
    <body>
        <h2>Crypto Bot – Paper Trading</h2>
        <div class="card">
            <p>Valore totale: {{data.valore_totale}} €</p>
            <p>Profitto: {{data.profitto}} €</p>
            <p>Aggiornato: {{data.ultimo_aggiornamento}}</p>
        </div>
        {% for c,v in data.dettagli.items() %}
        <div class="card">
            <h3>{{c}}</h3>
            <p>Prezzo: {{v.prezzo}} €</p>
            <p>RSI: {{v.rsi}}</p>
            <p>Qty: {{v.qty}}</p>
            <p>Valore: {{v.valore}} €</p>
            <p>Trade: {{v.trade}}</p>
        </div>
        {% endfor %}
    </body>
    </html>
    """, data=api().json)

# ================= START =================
threading.Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

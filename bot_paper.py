from flask import Flask, jsonify, index.html
import requests
import time
from datetime import datetime
import threading

app = Flask(__name__)

# ===== CONFIG =====
CAPITALE_INIZIALE = 100.0
RSI_BUY = 30
RSI_SELL = 70
UPDATE_SECONDS = 5

CRYPTO = {
    "BTC": {"symbol": "bitcoin", "budget": 34},
    "ETH": {"symbol": "ethereum", "budget": 33}
}

# ===== STATO =====
stato = {
    "capitale_eur": CAPITALE_INIZIALE,
    "profitto_eur": 0.0,
    "numero_trade": 0,
    "ultimo_aggiornamento": "",
    "portfolio": {}
}

for c in CRYPTO:
    stato["portfolio"][c] = {
        "qty": 0.0,
        "prezzo": 0.0,
        "rsi": None,
        "trade": 0,
        "investito": CRYPTO[c]["budget"]
    }

# ===== FUNZIONI =====
def get_price(coin):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=eur"
    return requests.get(url).json()[coin]["eur"]

def get_rsi(prices, period=14):
    if len(prices) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, period + 1):
        diff = prices[-i] - prices[-i - 1]
        if diff >= 0:
            gains.append(diff)
        else:
            losses.append(abs(diff))
    avg_gain = sum(gains) / period if gains else 0
    avg_loss = sum(losses) / period if losses else 1
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

price_history = {c: [] for c in CRYPTO}

def bot_loop():
    global stato
    while True:
        for c, cfg in CRYPTO.items():
            prezzo = get_price(cfg["symbol"])
            price_history[c].append(prezzo)
            if len(price_history[c]) > 100:
                price_history[c].pop(0)

            rsi = get_rsi(price_history[c])
            asset = stato["portfolio"][c]

            asset["prezzo"] = prezzo
            asset["rsi"] = rsi

            # BUY
            if rsi is not None and rsi <= RSI_BUY and asset["qty"] == 0:
                qty = asset["investito"] / prezzo
                asset["qty"] = qty
                asset["trade"] += 1
                stato["numero_trade"] += 1
                stato["capitale_eur"] -= asset["investito"]

            # SELL
            if rsi is not None and rsi >= RSI_SELL and asset["qty"] > 0:
                valore = asset["qty"] * prezzo
                profitto = valore - asset["investito"]
                stato["profitto_eur"] += round(profitto, 2)
                stato["capitale_eur"] += valore
                asset["qty"] = 0
                asset["trade"] += 1
                stato["numero_trade"] += 1

        stato["ultimo_aggiornamento"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time.sleep(UPDATE_SECONDS)

# ===== ROUTE =====
@app.route("/")
def home():
    return ("index.html")

@app.route("/api/status")
def status():
    valore_totale = stato["capitale_eur"]
    for a in stato["portfolio"].values():
        valore_totale += a["qty"] * a["prezzo"]

    return jsonify({
        "valore_totale_eur": round(valore_totale, 2),
        "profitto_eur": stato["profitto_eur"],
        "numero_trade": stato["numero_trade"],
        "ultimo_aggiornamento": stato["ultimo_aggiornamento"],
        "portfolio": stato["portfolio"]
    })

# ===== START =====
threading.Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, threaded=True)


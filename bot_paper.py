from flask import Flask, jsonify
import threading
import time
import requests
from datetime import datetime

app = Flask(__name__)

# ===== CONFIG =====
CAPITALE_INIZIALE = 100.0
REFRESH_SECONDS = 5
RSI_PERIOD = 14

CRYPTO = {
    "BTC": {"id": "bitcoin", "allocazione": 0.5},
    "ETH": {"id": "ethereum", "allocazione": 0.5},
}

# ===== STATO =====
stato = {
    "capitale_eur": CAPITALE_INIZIALE,
    "portfolio": {},
    "profitto_eur": 0.0,
    "numero_trade": 0,
    "ultimo_aggiornamento": None
}

prezzi = {k: [] for k in CRYPTO}


# ===== RSI =====
def calcola_rsi(prices, period=14):
    if len(prices) < period + 1:
        return None

    gains, losses = [], []
    for i in range(-period, 0):
        diff = prices[i] - prices[i - 1]
        if diff >= 0:
            gains.append(diff)
        else:
            losses.append(abs(diff))

    avg_gain = sum(gains) / period if gains else 0.0001
    avg_loss = sum(losses) / period if losses else 0.0001

    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)


# ===== PREZZI REALI =====
def fetch_prezzi():
    ids = ",".join(c["id"] for c in CRYPTO.values())
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=eur"

    try:
        r = requests.get(url, timeout=10)
        data = r.json()
        return {
            name: data[info["id"]]["eur"]
            for name, info in CRYPTO.items()
        }
    except Exception:
        return None


# ===== BOT =====
def trading_bot():
    while True:
        prezzi_reali = fetch_prezzi()
        if not prezzi_reali:
            time.sleep(REFRESH_SECONDS)
            continue

        for coin, prezzo in prezzi_reali.items():
            prezzi[coin].append(prezzo)
            rsi = calcola_rsi(prezzi[coin])

            if coin not in stato["portfolio"]:
                stato["portfolio"][coin] = {
                    "qty": 0.0,
                    "prezzo": prezzo,
                    "rsi": rsi,
                    "trade": 0
                }

            asset = stato["portfolio"][coin]
            asset["prezzo"] = prezzo
            asset["rsi"] = rsi

            # BUY
            if rsi and rsi < 30 and stato["capitale_eur"] > 1:
                investimento = stato["capitale_eur"] * CRYPTO[coin]["allocazione"]
                qty = investimento / prezzo
                asset["qty"] += qty
                stato["capitale_eur"] -= investimento
                asset["trade"] += 1
                stato["numero_trade"] += 1

            # SELL
            if rsi and rsi > 70 and asset["qty"] > 0:
                stato["capitale_eur"] += asset["qty"] * prezzo
                asset["qty"] = 0
                asset["trade"] += 1
                stato["numero_trade"] += 1

        valore_totale = stato["capitale_eur"]
        for asset in stato["portfolio"].values():
            valore_totale += asset["qty"] * asset["prezzo"]

        stato["profitto_eur"] = round(valore_totale - CAPITALE_INIZIALE, 2)
        stato["ultimo_aggiornamento"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        time.sleep(REFRESH_SECONDS)


# ===== API =====
@app.route("/")
def dashboard():
    valore_totale = stato["capitale_eur"]
    for asset in stato["portfolio"].values():
        valore_totale += asset["qty"] * asset["prezzo"]

    return jsonify({
        "valore_totale_eur": round(valore_totale, 2),
        "capitale_eur": round(stato["capitale_eur"], 2),
        "profitto_eur": stato["profitto_eur"],
        "numero_trade": stato["numero_trade"],
        "ultimo_aggiornamento": stato["ultimo_aggiornamento"],
        "portfolio": stato["portfolio"]
    })


# ===== START =====
if __name__ == "__main__":
    threading.Thread(target=trading_bot, daemon=True).start()
    app.run(host="0.0.0.0", port=8080)

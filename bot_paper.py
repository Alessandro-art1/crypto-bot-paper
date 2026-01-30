from flask import Flask, jsonify
import threading
import time
import requests
from datetime import datetime

app = Flask(__name__)

# ===== CONFIG =====
SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
INTERVALLO = 15
RSI_BUY = 45
RSI_SELL = 55
RSI_PERIOD = 14

# ===== STATO =====
stato = {
    "capitale_iniziale": 100.0,
    "capitale_attuale": 100.0,
    "profitto_euro": 0.0,
    "profitto_percento": 0.0,
    "numero_trade": 0,
    "symbol_attivo": None,
    "posizione_aperta": False,
    "prezzo_ingresso": 0.0,
    "ultimo_aggiornamento": ""
}

prezzi = {s: [] for s in SYMBOLS}

# ===== RSI =====
def calcola_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50
    gains, losses = [], []
    for i in range(-period, 0):
        delta = prices[i] - prices[i - 1]
        if delta >= 0:
            gains.append(delta)
        else:
            losses.append(abs(delta))
    avg_gain = sum(gains) / period if gains else 0.0001
    avg_loss = sum(losses) / period if losses else 0.0001
    rs = avg_gain / avg_loss
    return round(100 - (100 / (1 + rs)), 2)

# ===== PREZZI =====
def get_price(symbol):
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    return float(requests.get(url, timeout=5).json()["price"])

# ===== BOT =====
def bot_loop():
    while True:
        try:
            rsi_map = {}

            for s in SYMBOLS:
                p = get_price(s)
                prezzi[s].append(p)
                rsi_map[s] = calcola_rsi(prezzi[s])

            # BUY
            if not stato["posizione_aperta"]:
                migliore = min(rsi_map, key=rsi_map.get)
                if rsi_map[migliore] < RSI_BUY:
                    stato["posizione_aperta"] = True
                    stato["symbol_attivo"] = migliore
                    stato["prezzo_ingresso"] = prezzi[migliore][-1]
                    stato["numero_trade"] += 1

            # SELL
            else:
                s = stato["symbol_attivo"]
                rsi_attuale = calcola_rsi(prezzi[s])
                if rsi_attuale > RSI_SELL:
                    prezzo = prezzi[s][-1]
                    profitto = (prezzo - stato["prezzo_ingresso"]) / stato["prezzo_ingresso"]
                    stato["capitale_attuale"] *= (1 + profitto)
                    stato["posizione_aperta"] = False
                    stato["symbol_attivo"] = None

            stato["profitto_euro"] = round(
                stato["capitale_attuale"] - stato["capitale_iniziale"], 2
            )
            stato["profitto_percento"] = round(
                stato["profitto_euro"] / stato["capitale_iniziale"] * 100, 2
            )
            stato["ultimo_aggiornamento"] = datetime.now().strftime("%H:%M:%S")

        except Exception as e:
            print("Errore:", e)

        time.sleep(INTERVALLO)

threading.Thread(target=bot_loop, daemon=True).start()

# ===== API =====
@app.route("/api/status")
def api_status():
    return jsonify(stato)

# ===== DASHBOARD =====
@app.route("/")
def dashboard():
    return f"""
<!DOCTYPE html>
<html>
<head>
<title>Multi Crypto Bot</title>
<style>
body {{ background:#0f172a; color:#e5e7eb; font-family:Arial; }}
.box {{ background:#020617; padding:20px; width:420px; border-radius:10px; }}
</style>
</head>
<body>
<div class="box">
<h2>🤖 MULTI CRYPTO BOT</h2>
<p>Capitale: €{stato["capitale_attuale"]:.2f}</p>
<p>Profitto: €{stato["profitto_euro"]} ({stato["profitto_percento"]}%)</p>
<p>Trade: {stato["numero_trade"]}</p>
<p>Posizione: {"APERTO su " + stato["symbol_attivo"] if stato["posizione_aperta"] else "CHIUSO"}</p>
<p>Update: {stato["ultimo_aggiornamento"]}</p>
<p><i>RSI BUY &lt; {RSI_BUY} | RSI SELL &gt; {RSI_SELL}</i></p>
</div>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

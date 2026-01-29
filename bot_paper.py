from flask import Flask, jsonify
import threading
import time
import requests
from datetime import datetime

app = Flask(__name__)

# ===== CONFIG =====
SYMBOL = "BTCUSDT"
INTERVALLO = 15        # secondi
RSI_PERIOD = 14

# ===== STATO BOT =====
stato = {
    "capitale_iniziale": 100.0,
    "capitale_attuale": 100.0,
    "numero_trade": 0,
    "profitto_euro": 0.0,
    "profitto_percento": 0.0,
    "posizione_aperta": False,
    "prezzo_ingresso": 0.0,
    "prezzo_attuale": 0.0,
    "rsi": 50,
    "ultimo_aggiornamento": ""
}

prezzi = []

# ===== RSI =====
def calcola_rsi(prices, period=14):
    if len(prices) < period + 1:
        return 50

    gains = []
    losses = []

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

# ===== PREZZO BINANCE =====
def get_price():
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={SYMBOL}"
    return float(requests.get(url, timeout=5).json()["price"])

# ===== BOT LOOP =====
def bot_loop():
    while True:
        try:
            prezzo = get_price()
            prezzi.append(prezzo)
            stato["prezzo_attuale"] = prezzo
            stato["rsi"] = calcola_rsi(prezzi, RSI_PERIOD)

            # BUY
            if stato["rsi"] < 30 and not stato["posizione_aperta"]:
                stato["posizione_aperta"] = True
                stato["prezzo_ingresso"] = prezzo
                stato["numero_trade"] += 1

            # SELL
            elif stato["rsi"] > 70 and stato["posizione_aperta"]:
                profitto = (prezzo - stato["prezzo_ingresso"]) / stato["prezzo_ingresso"]
                stato["capitale_attuale"] *= (1 + profitto)
                stato["posizione_aperta"] = False

            stato["profitto_euro"] = round(
                stato["capitale_attuale"] - stato["capitale_iniziale"], 2
            )
            stato["profitto_percento"] = round(
                (stato["profitto_euro"] / stato["capitale_iniziale"]) * 100, 2
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
    return """
<!DOCTYPE html>
<html>
<head>
<title>Crypto Bot RSI</title>
<style>
body { background:#0f172a; color:#e5e7eb; font-family:Arial; }
.box { background:#020617; padding:20px; width:380px; border-radius:10px; }
.green { color:#22c55e; }
.red { color:#ef4444; }
</style>
</head>
<body>
<div class="box">
<h1>🤖 BOT RSI (BTC)</h1>
<p>Prezzo BTC: <b id="prezzo"></b></p>
<p>RSI: <b id="rsi"></b></p>
<p>Capitale: €<b id="capitale"></b></p>
<p>Trade: <b id="trade"></b></p>
<p>Profitto: <b id="profitto"></b> €</p>
<p>Posizione: <b id="posizione"></b></p>
<p>Update: <b id="update"></b></p>
</div>

<script>
async function aggiorna(){
    const r = await fetch('/api/status');
    const d = await r.json();
    document.getElementById('prezzo').innerText = d.prezzo_attuale;
    document.getElementById('rsi').innerText = d.rsi;
    document.getElementById('capitale').innerText = d.capitale_attuale.toFixed(2);
    document.getElementById('trade').innerText = d.numero_trade;
    document.getElementById('profitto').innerText = d.profitto_euro;
    document.getElementById('posizione').innerText = d.posizione_aperta ? "APERTO" : "CHIUSO";
    document.getElementById('update').innerText = d.ultimo_aggiornamento;
}
setInterval(aggiorna, 5000);
aggiorna();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

from flask import Flask, jsonify, render_template_string
import requests
import time
import threading
from datetime import datetime

app = Flask(__name__)

# ================= CONFIG =================
CAPITALE_INIZIALE = 100.0
UPDATE_SECONDS = 5
RSI_BUY = 30
RSI_SELL = 70

CRYPTOS = {
    "BTC": {"id": "bitcoin", "budget": 50},
    "ETH": {"id": "ethereum", "budget": 50}
}

# ================= STATO =================
stato = {
    "capitale_eur": CAPITALE_INIZIALE,
    "numero_trade": 0,
    "profitto_eur": 0.0,
    "ultimo_aggiornamento": "",
    "portfolio": {}
}

prezzi = {}

for c in CRYPTOS:
    stato["portfolio"][c] = {
        "qty": 0.0,
        "prezzo": 0.0,
        "rsi": None,
        "trade": 0,
        "investito": CRYPTOS[c]["budget"]
    }
    prezzi[c] = []

# ================= FUNZIONI =================
def fetch_prices():
    ids = ",".join(v["id"] for v in CRYPTOS.values())
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=eur"
    try:
        r = requests.get(url, timeout=10).json()
        return {k: r[v["id"]]["eur"] for k, v in CRYPTOS.items()}
    except:
        return None

def calcola_rsi(data, period=14):
    if len(data) < period + 1:
        return None
    gain = loss = 0
    for i in range(-period, 0):
        diff = data[i] - data[i - 1]
        if diff >= 0:
            gain += diff
        else:
            loss += abs(diff)
    if loss == 0:
        return 100
    rs = (gain / period) / (loss / period)
    return round(100 - (100 / (1 + rs)), 2)

# ================= BOT =================
def bot_loop():
    while True:
        prices = fetch_prices()
        if not prices:
            time.sleep(UPDATE_SECONDS)
            continue

        for c, price in prices.items():
            prezzi[c].append(price)
            if len(prezzi[c]) > 100:
                prezzi[c].pop(0)

            rsi = calcola_rsi(prezzi[c])
            asset = stato["portfolio"][c]
            asset["prezzo"] = price
            asset["rsi"] = rsi

            # BUY
            if rsi and rsi <= RSI_BUY and asset["qty"] == 0:
                qty = asset["investito"] / price
                asset["qty"] = qty
                stato["capitale_eur"] -= asset["investito"]
                asset["trade"] += 1
                stato["numero_trade"] += 1

            # SELL
            if rsi and rsi >= RSI_SELL and asset["qty"] > 0:
                valore = asset["qty"] * price
                profitto = valore - asset["investito"]
                stato["capitale_eur"] += valore
                stato["profitto_eur"] += round(profitto, 2)
                asset["qty"] = 0
                asset["trade"] += 1
                stato["numero_trade"] += 1

        stato["ultimo_aggiornamento"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time.sleep(UPDATE_SECONDS)

# ================= DASHBOARD =================
@app.route("/")
def dashboard():
    valore_totale = stato["capitale_eur"]
    for a in stato["portfolio"].values():
        valore_totale += a["qty"] * a["prezzo"]

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Crypto Bot</title>
<style>
body { background:#0b0f0c; color:#00ff66; font-family:Arial }
.card { border:1px solid #00ff66; padding:15px; margin:15px }
.grid { display:grid; grid-template-columns:1fr 1fr; gap:15px }
</style>
</head>
<body>

<h1>🤖 Crypto Bot – Paper Trading</h1>

<div class="card">
<p>Valore totale: {{valore}} €</p>
<p>Profitto: {{profitto}} €</p>
<p>Trade: {{trade}}</p>
<p>Aggiornato: {{time}}</p>
</div>

<div class="grid">
{% for c,a in portfolio.items() %}
<div class="card">
<h2>{{c}}</h2>
<p>Prezzo: {{a.prezzo}} €</p>
<p>RSI: {{a.rsi}}</p>
<p>Qty: {{ "%.6f"|format(a.qty) }}</p>
<p>Trade: {{a.trade}}</p>
</div>
{% endfor %}
</div>

<script>
setTimeout(() => location.reload(), 5000);
</script>

</body>
</html>
""",
    valore=round(valore_totale,2),
    profitto=round(stato["profitto_eur"],2),
    trade=stato["numero_trade"],
    time=stato["ultimo_aggiornamento"],
    portfolio=stato["portfolio"]
)

# ================= START =================
threading.Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000, threaded=True)

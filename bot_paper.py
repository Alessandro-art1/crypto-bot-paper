from flask import Flask, render_template_string
import requests, time, threading
from datetime import datetime

app = Flask(__name__)

# ========= CONFIG =========
CAPITALE_INIZIALE = 100.0
RSI_BUY = 30
RSI_SELL = 70
UPDATE_SEC = 5

CRYPTO = {
    "BTC": "bitcoin",
    "ETH": "ethereum"
}

# ========= STATO =========
capitale_eur = CAPITALE_INIZIALE
profitto_eur = 0.0
numero_trade = 0
ultimo_aggiornamento = ""

portfolio = {
    "BTC": {"qty": 0.0, "prezzo": 0.0, "rsi": None, "investito": 50},
    "ETH": {"qty": 0.0, "prezzo": 0.0, "rsi": None, "investito": 50}
}

prezzi = {c: [] for c in CRYPTO}

# ========= FUNZIONI =========
def rsi_calc(data, period=14):
    if len(data) < period + 1:
        return None
    gain = loss = 0
    for i in range(-period, 0):
        diff = data[i] - data[i-1]
        if diff > 0:
            gain += diff
        else:
            loss += abs(diff)
    if loss == 0:
        return 100
    rs = (gain / period) / (loss / period)
    return round(100 - (100 / (1 + rs)), 2)

def fetch_prices():
    ids = ",".join(CRYPTO.values())
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=eur"
    try:
        r = requests.get(url, timeout=10).json()
        return {k: r[v]["eur"] for k, v in CRYPTO.items()}
    except:
        return None

# ========= BOT =========
def bot():
    global capitale_eur, profitto_eur, numero_trade, ultimo_aggiornamento

    while True:
        prices = fetch_prices()
        if not prices:
            time.sleep(UPDATE_SEC)
            continue

        for c, price in prices.items():
            prezzi[c].append(price)
            if len(prezzi[c]) > 100:
                prezzi[c].pop(0)

            rsi = rsi_calc(prezzi[c])
            asset = portfolio[c]
            asset["prezzo"] = price
            asset["rsi"] = rsi

            # BUY
            if rsi and rsi <= RSI_BUY and asset["qty"] == 0:
                asset["qty"] = asset["investito"] / price
                capitale_eur -= asset["investito"]
                numero_trade += 1

            # SELL
            if rsi and rsi >= RSI_SELL and asset["qty"] > 0:
                valore = asset["qty"] * price
                profitto = valore - asset["investito"]
                capitale_eur += valore
                profitto_eur += profitto
                asset["qty"] = 0
                numero_trade += 1

        ultimo_aggiornamento = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time.sleep(UPDATE_SEC)

# ========= DASHBOARD =========
@app.route("/")
def dashboard():
    valore_tot = capitale_eur
    for a in portfolio.values():
        valore_tot += a["qty"] * a["prezzo"]

    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Crypto Bot</title>
<style>
body { background:#0b0f14; color:#e6f1ff; font-family:Arial }
h1 { color:#58a6ff }
.grid { display:grid; grid-template-columns:1fr 1fr; gap:20px }
.card { background:#161b22; padding:20px; border-radius:12px; box-shadow:0 0 10px #000 }
.value { font-size:22px; color:#3fb950 }
.small { color:#8b949e }
</style>
</head>
<body>

<h1>🤖 Crypto Bot – Paper Trading</h1>

<div class="card">
<div class="value">Valore totale: {{valore}} €</div>
<div>Profitto: {{profitto}} €</div>
<div>Trade totali: {{trade}}</div>
<div class="small">Aggiornato: {{time}}</div>
</div>

<br>

<div class="grid">
{% for c,a in portfolio.items() %}
<div class="card">
<h2>{{c}}</h2>
<p>Prezzo: {{a.prezzo}} €</p>
<p>RSI: {{a.rsi}}</p>
<p>Quantità: {{ "%.6f"|format(a.qty) }}</p>
</div>
{% endfor %}
</div>

<script>
setTimeout(() => location.reload(), 5000);
</script>

</body>
</html>
""",
        valore=round(valore_tot,2),
        profitto=round(profitto_eur,2),
        trade=numero_trade,
        time=ultimo_aggiornamento,
        portfolio=portfolio
    )

# ========= START =========
threading.Thread(target=bot, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

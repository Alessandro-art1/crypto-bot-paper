from flask import Flask, render_template_string
from datetime import datetime
import requests, time, threading, os

app = Flask(__name__)

CAPITALE_INIZIALE = 100.0
capitale = CAPITALE_INIZIALE
btc_qty = 0.0
posizione_aperta = False
numero_trade = 0

prezzi = []

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

# ---------- PREZZO BTC REALE ----------
def get_btc_price():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": "bitcoin", "vs_currencies": "eur"}
    r = requests.get(url, params=params, timeout=10)
    return r.json()["bitcoin"]["eur"]

# ---------- BOT ----------
def trading_bot():
    global capitale, btc_qty, posizione_aperta, numero_trade

    while True:
        prezzo = get_btc_price()
        prezzi.append(prezzo)

        rsi = calcola_rsi(prezzi)

        # BUY
        if rsi < 45 and not posizione_aperta:
            btc_qty = capitale / prezzo
            capitale = 0
            posizione_aperta = True
            numero_trade += 1

        # SELL
        elif rsi > 55 and posizione_aperta:
            capitale = btc_qty * prezzo
            btc_qty = 0
            posizione_aperta = False
            numero_trade += 1

        time.sleep(15)

# ---------- UI ----------
HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="10">
<title>Crypto Bot Reale</title>
<style>
body { background:#0f172a; color:#e5e7eb; font-family:Arial; text-align:center }
.box { background:#1e293b; padding:20px; margin:20px auto; width:360px; border-radius:12px }
.green { color:#4ade80 }
.red { color:#f87171 }
</style>
</head>
<body>
<h1>🤖 Crypto Bot – BTC Reale</h1>
<div class="box">
<p>⏱ {{time}}</p>
<p>💰 Capitale €: {{capitale}}</p>
<p>🪙 BTC qty: {{btc}}</p>
<p>📈 Prezzo BTC: {{prezzo}} €</p>
<p>📉 RSI: {{rsi}}</p>
<p>🔄 Trade: {{trade}}</p>
<p>⚙ Stato: {{stato}}</p>
</div>
</body>
</html>
"""

@app.route("/")
def dashboard():
    prezzo = prezzi[-1] if prezzi else 0
    rsi = calcola_rsi(prezzi)
    return render_template_string(
        HTML,
        time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        capitale=round(capitale, 2),
        btc=round(btc_qty, 6),
        prezzo=prezzo,
        rsi=rsi,
        trade=numero_trade,
        stato="IN POSIZIONE BTC" if posizione_aperta else "IN ATTESA"
    )

# ---------- START ----------
if __name__ == "__main__":
    threading.Thread(target=trading_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

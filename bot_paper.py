from flask import Flask, jsonify
from datetime import datetime
import csv
import os

app = Flask(__name__)

CAPITALE_INIZIALE = 100.0
LOG_FILE = "trades.csv"

def leggi_trades():
    if not os.path.exists(LOG_FILE):
        return []

    with open(LOG_FILE, newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)

@app.route("/")
def dashboard():
    trades = leggi_trades()

    capitale_attuale = CAPITALE_INIZIALE
    if trades:
        capitale_attuale = float(trades[-1]["capitale"])

    profitto = capitale_attuale - CAPITALE_INIZIALE
    profitto_pct = (profitto / CAPITALE_INIZIALE) * 100

    return jsonify({
        "stato": "BOT ATTIVO (PAPER TRADING)",
        "capitale_iniziale": CAPITALE_INIZIALE,
        "capitale_attuale": round(capitale_attuale, 2),
        "profitto_euro": round(profitto, 2),
        "profitto_percento": round(profitto_pct, 2),
        "numero_trade": len(trades),
        "ultimo_aggiornamento": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

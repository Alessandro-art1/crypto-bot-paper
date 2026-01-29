from flask import Flask, jsonify
from threading import Thread
from datetime import datetime
import time
import random
import os

app = Flask(__name__)

CAPITALE_INIZIALE = 100.0
capitale = CAPITALE_INIZIALE
numero_trade = 0
ultimo_update = None


def bot_loop():
    global capitale, numero_trade, ultimo_update

    while True:
        # simulazione profitto/perdita
        variazione = random.uniform(-0.5, 0.7)
        capitale += variazione
        capitale = round(capitale, 2)

        numero_trade += 1
        ultimo_update = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"TRADE {numero_trade} | capitale: {capitale}")
        time.sleep(20)  # ogni 20 secondi


@app.route("/")
def home():
    return "BOT ATTIVO (PAPER TRADING)"


@app.route("/status")
def status():
    profitto = round(capitale - CAPITALE_INIZIALE, 2)
    profitto_pct = round((profitto / CAPITALE_INIZIALE) * 100, 2)

    return jsonify({
        "stato": "BOT ATTIVO (PAPER TRADING)",
        "capitale_iniziale": CAPITALE_INIZIALE,
        "capitale_attuale": capitale,
        "numero_trade": numero_trade,
        "profitto_euro": profitto,
        "profitto_percento": profitto_pct,
        "ultimo_aggiornamento": ultimo_update
    })


if __name__ == "__main__":
    Thread(target=bot_loop, daemon=True).start()

    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

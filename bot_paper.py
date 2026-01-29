from flask import Flask, jsonify
import threading
import time
from datetime import datetime

app = Flask(__name__)

# Stato del bot (paper trading)
stato_bot = {
    "capitale_iniziale": 100.0,
    "capitale_attuale": 100.0,
    "numero_trade": 0,
    "profitto_euro": 0.0,
    "profitto_percento": 0.0,
    "stato": "BOT ATTIVO (PAPER TRADING)",
    "ultimo_aggiornamento": ""
}

def loop_bot():
    """Simulazione continua del bot"""
    while True:
        time.sleep(10)  # ogni 10 secondi

        # simulazione finta di un trade
        stato_bot["numero_trade"] += 1
        stato_bot["capitale_attuale"] += 0.5

        stato_bot["profitto_euro"] = round(
            stato_bot["capitale_attuale"] - stato_bot["capitale_iniziale"], 2
        )
        stato_bot["profitto_percento"] = round(
            (stato_bot["profitto_euro"] / stato_bot["capitale_iniziale"]) * 100, 2
        )
        stato_bot["ultimo_aggiornamento"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print("BOT ATTIVO | Stato aggiornato")

@app.route("/")
def home():
    return "🤖 BOT PAPER TRADING ATTIVO"

@app.route("/status")
def status():
    return jsonify(stato_bot)

if __name__ == "__main__":
    # Avvio thread del bot
    t = threading.Thread(target=loop_bot, daemon=True_

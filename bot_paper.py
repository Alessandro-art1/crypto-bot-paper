from flask import Flask, jsonify, Response
import time
import threading
from datetime import datetime

app = Flask(__name__)

# ===== STATO BOT =====
stato = {
    "capitale_iniziale": 100.0,
    "capitale_attuale": 100.0,
    "numero_trade": 0,
    "profitto_euro": 0.0,
    "profitto_percento": 0.0,
    "stato": "BOT ATTIVO (PAPER TRADING)",
    "ultimo_aggiornamento": ""
}

# ===== LOGICA BOT (SIMULATA) =====
def bot_loop():
    while True:
        time.sleep(10)

        stato["numero_trade"] += 1
        stato["capitale_attuale"] += 1.5
        stato["profitto_euro"] = stato["capitale_attuale"] - stato["capitale_iniziale"]
        stato["profitto_percento"] = round(
            (stato["profitto_euro"] / stato["capitale_iniziale"]) * 100, 2
        )
        stato["ultimo_aggiornamento"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# ===== AVVIO THREAD BOT =====
threading.Thread(target=bot_loop, daemon=True).start()

# ===== PAGINA STATUS AUTO-REFRESH =====
@app.route("/status")
def status_page():
    html = f"""
    <html>
    <head>
        <title>Crypto Bot – Status</title>
        <meta http-equiv="refresh" content="5">
        <style>
            body {{
                font-family: Arial;
                background: #0f172a;
                color: #e5e7eb;
                padding: 20px;
            }}
            .box {{
                background: #020617;
                padding: 20px;
                border-radius: 10px;
                width: 400px;
            }}
            h1 {{ color: #22c55e; }}
        </style>
    </head>
    <body>
        <div class="box">
            <h1>🤖 BOT PAPER TRADING</h1>
            <p><b>Capitale iniziale:</b> €{stato["capitale_iniziale"]}</p>
            <p><b>Capitale attuale:</b> €{stato["capitale_attuale"]}</p>
            <p><b>Numero trade:</b> {stato["numero_trade"]}</p>
            <p><b>Profitto €:</b> €{stato["profitto_euro"]}</p>
            <p><b>Profitto %:</b> {stato["profitto_percento"]}%</p>
            <p><b>Ultimo update:</b> {stato["ultimo_aggiornamento"]}</p>
            <p><i>Auto-refresh ogni 5 secondi</i></p>
        </div>
    </body>
    </html>
    """
    return Response(html, mimetype="text/html")

# ===== AVVIO SERVER =====
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

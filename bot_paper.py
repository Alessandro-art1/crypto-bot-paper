from flask import Flask
import datetime

app = Flask(__name__)

@app.route("/")
def home():
    return f"""
    <html>
    <head><title>BOT ONLINE</title></head>
    <body style="background:black;color:lime;font-family:Arial">
        <h1>✅ BOT ATTIVO</h1>
        <p>Ora server: {datetime.datetime.now()}</p>
        <p>Se vedi questa pagina, Render funziona.</p>
    </body>
    </html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

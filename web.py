from flask import Flask, request
import io
import sys
import os

from crescent_moon import *

app = Flask(__name__)


# -------------------------
# FORMULARIO PRINCIPAL
# -------------------------
@app.route("/")
def home():
    return """
    <html>
    <body style="font-family:Arial; background:#0b1a2a; color:#e0e6ed; padding:30px;">

    <h1 style="font-size:28px;">Crescent Moon Calculator</h1>

    <form action="/run" method="post" style="font-size:18px;">

        <label>Latitude:</label><br>
        <input type="text" name="lat" style="font-size:16px;"><br><br>

        <label>Longitude:</label><br>
        <input type="text" name="lon" style="font-size:16px;"><br><br>

        <label>Year:</label><br>
        <input type="text" name="year" style="font-size:16px;"><br><br>

        <input type="submit" value="Calculate" style="font-size:16px; padding:8px;">
    </form>

    </body>
    </html>
    """


# -------------------------
# EJECUCIÓN DEL PROGRAMA
# -------------------------
@app.route("/run", methods=["POST"])
def run():

    try:
        lat = float(request.form.get("lat"))
        lon = float(request.form.get("lon"))
        year = int(request.form.get("year"))
    except:
        return "<h2>Error en los datos introducidos</h2>"

    # -------------------------
    # CAPTURAR PRINTS DEL PROGRAMA
    # -------------------------
    buffer = io.StringIO()
    sys.stdout = buffer

    try:
        # Llama a tu programa (ajusta si tu función tiene otro nombre)
        main(lat, lon, year)
    except Exception as e:
        sys.stdout = sys.__stdout__
        return f"<h2>Error ejecutando el programa:</h2><pre>{e}</pre>"

    sys.stdout = sys.__stdout__
    result = buffer.getvalue()

    return f"""
    <html>
    <body style="background:#0b1a2a; color:#e0e6ed; font-family:monospace; padding:20px;">

    <h2>Resultados</h2>

    <pre style="
        font-size:16px;
        line-height:1.4;
        background:#111;
        padding:15px;
        border-radius:8px;
    ">
{result}
    </pre>

    <br>
    <a href="/" style="color:#6ec1ff;">← Nueva consulta</a>

    </body>
    </html>
    """


# -------------------------
# ARRANQUE PARA RENDER
# -------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


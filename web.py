from flask import Flask, request

from crescent_moon import *  # tu programa

app = Flask(__name__)


# -------------------------
# FORMULARIO PRINCIPAL
# -------------------------
@app.route("/")
def home():
    return """
    <h1 style="font-size:28px;">Crescent Moon Calculator</h1>

    <form action="/run" method="post" style="font-size:18px;">
        <label>Latitude:</label><br>
        <input type="text" name="lat"><br><br>

        <label>Longitude:</label><br>
        <input type="text" name="lon"><br><br>

        <label>Year:</label><br>
        <input type="text" name="year"><br><br>

        <input type="submit" value="Calculate">
    </form>
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
    # AQUÍ LLAMAS A TU PROGRAMA
    # -------------------------

    # Ejemplo: ajusta esta llamada a tu función real
    result = main(lat, lon, year)

    # Si tu programa devuelve texto → lo mostramos
    # Si imprime en consola → habría que capturarlo (te lo preparo si hace falta)

    return f"""
    <h2>Resultado</h2>

    <pre style="font-size:16px; line-height:1.4; background:#111; color:#0f0; padding:15px;">
{result}
    </pre>

    <br>
    <a href="/">Volver</a>
    """


# -------------------------
# ARRANQUE PARA RENDER
# -------------------------
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

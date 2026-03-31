from flask import Flask, request
import io
import sys
from crescent_moon import compute_visibility, PI

app = Flask(__name__)

# ---------------------------
# Página principal (formulario)
# ---------------------------
@app.route("/", methods=["GET"])
def home():
    return """
    <h1>Crescent Moon Visibility</h1>
    <form action="/run" method="post">
        Longitud (grados): <input name="lon" value="-5"><br><br>
        Latitud (grados): <input name="lat" value="36"><br><br>
        Año: <input name="year" value="2025"><br><br>
        Altura (km): <input name="height" value="0"><br><br>
        Humedad (%): <input name="humidity" value="50"><br><br>
        Probabilidad (%): <input name="prob" value="50"><br><br>
        Lunación (índice): <input name="lunation" value="0"><br><br>
        <input type="submit" value="Calcular">
    </form>
    """

# ---------------------------
# Ejecutar cálculo
# ---------------------------
@app.route("/run", methods=["POST"])
def run():
    try:
        lon = float(request.form["lon"])
        lat = float(request.form["lat"])
        year = int(request.form["year"])
        height = float(request.form["height"])
        humidity = float(request.form["humidity"])
        prob = float(request.form["prob"])
        lunation = int(request.form["lunation"])

        # Convertir a radianes
        long_rad = lon * PI / 180
        fi = lat * PI / 180

        # Capturar salida en texto
        buffer = io.StringIO()
        sys.stdout = buffer

        compute_visibility(long_rad, fi, year, height, humidity, prob, lunation)

        sys.stdout = sys.__stdout__
        output = buffer.getvalue()

        return f"<pre>{output}</pre><br><a href='/'>Volver</a>"

    except Exception as e:
        sys.stdout = sys.__stdout__
        return f"<h3>Error:</h3><pre>{str(e)}</pre><br><a href='/'>Volver</a>"

# ---------------------------
# ARRANQUE (IMPORTANTE)
# ---------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

from flask import Flask, request
import io
import sys
import os

from crescent_moon import compute_visibility, compute_new_moons, PI

app = Flask(__name__)

# ---------------------------
# Página principal
# ---------------------------
@app.route("/", methods=["GET"])
def home():
    year = 2025  # valor por defecto
    lunations = compute_new_moons(year)

    # Crear opciones del desplegable
    options = ""
    for i, nm in enumerate(lunations):
        _, y, m, d, h, mi, s, _ = nm
        options += f'<option value="{i}">{d}/{m}/{y} {h:02d}:{mi:02d}</option>'

    return f"""
    <h1>Crescent Moon Visibility</h1>

    <h3>Lunaciones disponibles ({year}):</h3>
    <select name="lunation" form="form1">
        {options}
    </select>

    <form id="form1" action="/run" method="post">
        <br><br>

        Año: <input name="year" value="{year}"><br><br>
        Longitud (grados): <input name="lon" value="-5"><br><br>
        Latitud (grados): <input name="lat" value="36"><br><br>
        Altura (km): <input name="height" value="0"><br><br>
        Humedad (%): <input name="humidity" value="50"><br><br>
        Probabilidad (%): <input name="prob" value="50"><br><br>

        <br>
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

        # Conversión a radianes
        long_rad = lon * PI / 180
        fi = lat * PI / 180

        # Capturar salida
        buffer = io.StringIO()
        sys.stdout = buffer

        compute_visibility(long_rad, fi, year, height, humidity, prob, lunation)

        sys.stdout = sys.__stdout__
        output = buffer.getvalue()

        return f"""
        <h2>Resultado</h2>
        <pre>{output}</pre>
        <br>
        <a href="/">← Volver</a>
        """

    except Exception as e:
        sys.stdout = sys.__stdout__
        return f"""
        <h3>Error:</h3>
        <pre>{str(e)}</pre>
        <br>
        <a href="/">← Volver</a>
        """

# ---------------------------
# Arranque (local + Render)
# ---------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

from flask import Flask, request
import math
import io
import sys

from crescent_moon import compute_visibility, compute_new_moons

app = Flask(__name__)

def deg_to_rad(deg):
    return deg * math.pi / 180.0

# ------------------------
# HOME (MEJORADO)
# ------------------------
@app.route("/")
def home():
    return """
    <html>
    <head>
    <style>
        body {
            font-family: Arial;
            background:#0b1a2a;
            color:#e0e6ed;
            padding:30px;
        }

        h2 {
            color:#6ec1ff;
            font-size:28px;
        }

        label {
            font-size:16px;
        }

        input {
            width: 220px;
            padding: 8px;
            margin: 5px 0 15px 0;
            font-size:16px;
            border-radius:5px;
            border:none;
        }

        input[type=submit] {
            width:240px;
            background:#2ea44f;
            color:white;
            font-size:16px;
            font-weight:bold;
            cursor:pointer;
        }

        input[type=submit]:hover {
            background:#279644;
        }
    </style>
    </head>

    <body>
    <h2>Crescent Moon Visibility</h2>

    <form action="/lunations">

      <label>Latitude:</label><br>
      <input name="lat" value="36.5"><br>

      <label>Longitude:</label><br>
      <input name="lon" value="-6.3"><br>

      <label>Year:</label><br>
      <input name="year" value="2025"><br>

      <label>Height (km):</label><br>
      <input name="height" value="0"><br>

      <label>Humidity (%):</label><br>
      <input name="humidity" value="50"><br>

      <label>Probability (%):</label><br>
      <input name="prob" value="50"><br>

      <input type="submit" value="Show lunations">

    </form>
    </body>
    </html>
    """

# ------------------------
# LUNATIONS
# ------------------------
@app.route("/lunations")
def lunations():
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    year = int(request.args.get("year"))
    height = request.args.get("height")
    humidity = request.args.get("humidity")
    prob = request.args.get("prob")

    nm_list = compute_new_moons(year)

    html = """
    <html>
    <body style="background:#0b1a2a; color:#e0e6ed; font-family:Arial; padding:30px;">
    <h3>Select lunation</h3>
    <form action='/run'>
    """

    for name, value in [("lat", lat), ("lon", lon), ("year", year),
                        ("height", height), ("humidity", humidity), ("prob", prob)]:
        html += f"<input type='hidden' name='{name}' value='{value}'>"

    html += "<select name='lunation' style='font-size:16px; padding:6px;'>"

    for (jd_nm, y, mo, da, ho, mi, se, idx) in nm_list:
        label = f"{idx} → {y}/{mo}/{da} {ho}:{mi}:{se}"
        html += f"<option value='{idx}'>{label}</option>"

    html += "</select><br><br>"
    html += "<input type='submit' value='Calculate visibility' style='font-size:16px; padding:8px;'>"
    html += "</form></body></html>"

    return html

# ------------------------
# RESULTADOS (MEJOR VISUALIZACIÓN)
# ------------------------
@app.route("/run")
def run():
    lat = float(request.args.get("lat"))
    lon = float(request.args.get("lon"))
    year = int(request.args.get("year"))
    height = float(request.args.get("height"))
    humidity = float(request.args.get("humidity"))
    prob = float(request.args.get("prob"))
    lunation = int(request.args.get("lunation"))

    old_stdout = sys.stdout
    buffer = io.StringIO()
    sys.stdout = buffer

    compute_visibility(
        long_rad=deg_to_rad(lon),
        fi=deg_to_rad(lat),
        yea_input=year,
        he=height,
        hu=humidity,
        prob=prob,
        lunation_index=lunation
    )

    sys.stdout = old_stdout
    result = buffer.getvalue()

    return f"""
    <html>
    <body style="background:#0b1a2a; color:#e0e6ed; font-family:monospace; padding:20px;">
    <h2>Results</h2>

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
    <a href="/" style="color:#6ec1ff;">← New calculation</a>
    </body>
    </html>
    """

# ------------------------
# START
# ------------------------
if __name__ == "__main__":
    app.run(debug=True)
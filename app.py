import streamlit as st
import io
import sys
import pandas as pd
import re
import numpy as np

from crescent_moon import compute_visibility, compute_new_moons, PI

st.set_page_config(page_title="Crescent Moon", layout="wide")
st.title("🌙 Crescent Moon Visibility Calculator")

# -------------------------
# INPUTS
# -------------------------
st.subheader("Input parameters")

col1, col2, col3 = st.columns(3)

with col1:
    year = st.number_input("Year", value=2025, step=1)

with col2:
    lat = st.number_input("Latitude (degrees)", value=36.0)

with col3:
    lon = st.number_input("Longitude (degrees)", value=-5.0)

col4, col5, col6 = st.columns(3)

with col4:
    height = st.number_input("Height (km)", value=0.0)

with col5:
    humidity = st.number_input("Humidity (%)", value=50.0)

with col6:
    prob = st.number_input("Visibility probability (%)", value=50.0)

# -------------------------
# LUNATIONS
# -------------------------
lunations = compute_new_moons(year)

options = []
for i, nm in enumerate(lunations):
    _, y, m, d, h, mi, s, _ = nm
    options.append(f"{i} → {d:02d}/{m:02d}/{y}")

selected = st.selectbox("Select lunation", options)
lunation_index = int(selected.split("→")[0].strip())

# -------------------------
# PARSER
# -------------------------
def extract_table(output):
    lines = output.split("\n")
    data = []
    current_date = None

    for line in lines:
        if "Date (prime meridian)" in line:
            match = re.search(r"(\d+/\d+/\d+)", line)
            if match:
                current_date = match.group(1)

        if re.match(r"\s*\d+\.\d+", line):
            parts = re.split(r"\s{2,}", line.strip())

            if len(parts) >= 6:
                row = {
                    "Date": current_date,
                    "Sun_dep": float(parts[0]),
                    "Vis_coef": float(parts[1]),
                }
                data.append(row)

    if not data:
        return None

    return pd.DataFrame(data)

# -------------------------
# RUN
# -------------------------
if st.button("🚀 Calculate"):

    long_rad = lon * PI / 180
    fi = lat * PI / 180

    buffer = io.StringIO()
    sys.stdout = buffer

    compute_visibility(long_rad, fi, int(year), height, humidity, prob, lunation_index)

    sys.stdout = sys.__stdout__
    output = buffer.getvalue()

    df = extract_table(output)

    st.success("Calculation completed")

    # -------------------------
    # 📈 GRÁFICO
    # -------------------------
    st.subheader("📈 Visibility curve")

    if df is not None:
        st.line_chart(df, x="Sun_dep", y="Vis_coef")

    # -------------------------
    # 🟢 PRIMER DÍA VISIBLE
    # -------------------------
    st.subheader("🟢 First visibility")

    if df is not None:
        visible = df[df["Vis_coef"] < 0]

        if not visible.empty:
            first_day = visible.iloc[0]
            st.success(f"First visible at Sun depression = {first_day['Sun_dep']}")
        else:
            st.warning("No visibility detected")

    # -------------------------
    # 🌍 MAPA GLOBAL (simple)
    # -------------------------
    st.subheader("🌍 Global visibility map (approximate)")

    lats = np.linspace(-60, 60, 20)
    lons = np.linspace(-180, 180, 40)

    map_data = []

    for la in lats:
        for lo in lons:

            try:
                buffer = io.StringIO()
                sys.stdout = buffer

                compute_visibility(lo * PI/180, la * PI/180, int(year), height, humidity, prob, lunation_index)

                sys.stdout = sys.__stdout__
                out = buffer.getvalue()

                val = -1 if "Very likely" in out else 1

                map_data.append([la, lo, val])

            except:
                pass

    map_df = pd.DataFrame(map_data, columns=["lat", "lon", "visibility"])

    st.map(map_df)

    # -------------------------
    # RAW OUTPUT
    # -------------------------
    with st.expander("Full output"):
        st.code(output)

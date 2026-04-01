import streamlit as st
import io
import sys
import pandas as pd
import re
import matplotlib.pyplot as plt

from crescent_moon import compute_visibility, compute_new_moons, PI

st.set_page_config(page_title="Crescent Moon", layout="wide")
st.title("🌙 Crescent Moon Visibility Calculator")

# -------------------------
# INPUTS
# -------------------------
col1, col2, col3 = st.columns(3)

with col1:
    year = st.number_input("Year", value=2025)

with col2:
    lat = st.number_input("Latitude", value=36.0)

with col3:
    lon = st.number_input("Longitude", value=-5.0)

col4, col5, col6 = st.columns(3)

with col4:
    height = st.number_input("Height", value=0.0)

with col5:
    humidity = st.number_input("Humidity", value=50.0)

with col6:
    prob = st.number_input("Probability", value=50.0)

# -------------------------
# LUNATIONS
# -------------------------
lunations = compute_new_moons(year)

options = [
    f"{i} → {nm[3]:02d}/{nm[2]:02d}/{nm[1]}"
    for i, nm in enumerate(lunations)
]

selected = st.selectbox("Lunation", options)
lunation_index = int(selected.split("→")[0])

# -------------------------
# PARSER COMPLETO
# -------------------------
def extract_table(output):

    lines = output.split("\n")
    data = []
    current_date = None

    for line in lines:

        # detectar fecha
        if "Date (prime meridian)" in line:
            match = re.search(r"(\d+/\d+/\d+)", line)
            if match:
                current_date = match.group(1)

        # detectar filas
        if re.match(r"\s*\d+\.\d+", line):
            parts = re.split(r"\s{2,}", line.strip())

            if len(parts) >= 6:
                row = {
                    "Date": current_date,
                    "Sun_dep": float(parts[0]),
                    "Vis_coef": float(parts[1]),
                    "Altitude": parts[2],
                    "Time_UT": parts[3],
                    "Date_PM": parts[4],
                    "Az_diff": parts[5],
                }

                if len(parts) > 6:
                    row["Time_local"] = parts[6]
                if len(parts) > 7:
                    row["Date_local"] = parts[7]
                if len(parts) > 8:
                    row["Age_h"] = parts[8]

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

    st.success("Calculation completed")

    # -------------------------
    # TABLA COMPLETA
    # -------------------------
    df = extract_table(output)

    st.subheader("📊 Full Table")

    if df is not None:
        st.dataframe(df, use_container_width=True)

    # -------------------------
    # GRÁFICA POR DÍAS
    # -------------------------
    st.subheader("📈 Visibility curves by day")

    if df is not None:

        fig, ax = plt.subplots()

        for date in df["Date"].unique():
            subset = df[df["Date"] == date]
            ax.plot(subset["Sun_dep"], subset["Vis_coef"], label=date)

        ax.set_xlabel("Sun depression (deg)")
        ax.set_ylabel("Visibility coefficient")
        ax.legend()

        st.pyplot(fig)

    # -------------------------
    # PRIMER DÍA VISIBLE
    # -------------------------
    st.subheader("🟢 First visibility")

    if df is not None:
        first = df[df["Vis_coef"] < 0]

        if not first.empty:
            st.success(f"First visibility on {first.iloc[0]['Date']}")
        else:
            st.warning("No visibility detected")

    # -------------------------
    # MAPA (CONTROLADO)
    # -------------------------
    st.subheader("🌍 Global map (quick view)")

    if st.checkbox("Generate map (slow)"):
        import numpy as np

        points = []

        for la in np.linspace(-50, 50, 10):
            for lo in np.linspace(-180, 180, 20):

                try:
                    buffer = io.StringIO()
                    sys.stdout = buffer

                    compute_visibility(lo * PI/180, la * PI/180, int(year), height, humidity, prob, lunation_index)

                    sys.stdout = sys.__stdout__
                    out = buffer.getvalue()

                    val = 1 if "Very likely" in out else 0

                    points.append([la, lo, val])

                except:
                    pass

        map_df = pd.DataFrame(points, columns=["lat", "lon", "vis"])

        st.map(map_df)

    # -------------------------
    # OUTPUT COMPLETO
    # -------------------------
    with st.expander("Raw output"):
        st.code(output)

import streamlit as st
import io
import sys
import pandas as pd
import re

from crescent_moon import compute_visibility, compute_new_moons, PI

# -------------------------
# CONFIG
# -------------------------
st.set_page_config(page_title="Crescent Moon", layout="wide")
st.title("🌙 Crescent Moon Visibility Calculator")

# -------------------------
# INPUTS
# -------------------------
col1, col2, col3 = st.columns(3)

year = col1.number_input("Year", value=2025)
lat = col2.number_input("Latitude", value=36.0)
lon = col3.number_input("Longitude", value=-5.0)

height = st.number_input("Height (km)", value=0.0)
humidity = st.number_input("Humidity (%)", value=50.0)
prob = st.number_input("Visibility probability (%)", value=50.0)

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
# PARSER ROBUSTO
# -------------------------
def extract_table(output):

    lines = output.split("\n")
    data = []
    current_date = None

    for line in lines:

        # Detectar fecha
        if "Date (prime meridian)" in line:
            match = re.search(r"(\d+/\d+/\d+)", line)
            if match:
                current_date = match.group(1)

        # Detectar filas de datos
        if re.match(r"\s*\d+\.\d+", line):
            parts = re.split(r"\s{2,}", line.strip())

            if len(parts) >= 6:
                data.append({
                    "Date": current_date,
                    "Sun_dep": pd.to_numeric(parts[0], errors="coerce"),
                    "Vis_coef": pd.to_numeric(parts[1], errors="coerce"),
                    "Altitude": parts[2],
                    "Time_UT": parts[3],
                    "Date_PM": parts[4],
                    "Az_diff": parts[5],
                })

    if not data:
        return None

    df = pd.DataFrame(data)

    # limpieza para evitar errores
    df = df.dropna(subset=["Date", "Sun_dep", "Vis_coef"])

    return df

# -------------------------
# RUN
# -------------------------
if st.button("🚀 Calculate"):

    long_rad = lon * PI / 180
    fi = lat * PI / 180

    buffer = io.StringIO()
    sys.stdout = buffer

    try:
        compute_visibility(long_rad, fi, int(year), height, humidity, prob, lunation_index)
        sys.stdout = sys.__stdout__
        output = buffer.getvalue()

        st.success("Calculation completed")

        # -------------------------
        # TABLA
        # -------------------------
        df = extract_table(output)

        st.subheader("📊 Full Table")

        if df is not None:
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No data extracted")

        # -------------------------
        # GRÁFICAS POR DÍA
        # -------------------------
        st.subheader("📈 Visibility curves by day")

        if df is not None:
            for date in df["Date"].unique():
                st.write(f"Day: {date}")
                subset = df[df["Date"] == date]

                if not subset.empty:
                    st.line_chart(subset, x="Sun_dep", y="Vis_coef")

        # -------------------------
        # PRIMER DÍA VISIBLE
        # -------------------------
        st.subheader("🟢 First visibility")

        if df is not None:
            visible = df[df["Vis_coef"] < 0]

            if not visible.empty:
                st.success(f"First visibility on {visible.iloc[0]['Date']}")
            else:
                st.warning("No visibility detected")

        # -------------------------
        # MAPA (OPCIONAL)
        # -------------------------
        st.subheader("🌍 Global map (quick view)")

        if st.checkbox("Generate map (slow)"):

            import numpy as np

            points = []

            for la in np.linspace(-50, 50, 6):
                for lo in np.linspace(-180, 180, 12):

                    try:
                        buffer = io.StringIO()
                        sys.stdout = buffer

                        compute_visibility(
                            lo * PI/180,
                            la * PI/180,
                            int(year),
                            height,
                            humidity,
                            prob,
                            lunation_index
                        )

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
        with st.expander("📄 Raw output"):
            st.code(output)

    except Exception as e:
        sys.stdout = sys.__stdout__
        st.error(f"Error: {e}")

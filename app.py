import streamlit as st
import io
import sys
import pandas as pd
import re
import matplotlib.pyplot as plt

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
# PARSER ROBUSTO
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
                    "Sun_dep": pd.to_numeric(parts[0], errors="coerce"),
                    "Vis_coef": pd.to_numeric(parts[1], errors="coerce"),
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

    df = pd.DataFrame(data)

    # limpieza crítica (evita crashes)
    df = df.dropna(subset=["Date", "Sun_dep", "Vis_coef"])

    return df

# -------------------------
# RUN
# -------------------------
if st.button("🚀 Calculate"):

    long_rad = lon * PI / 180
    fi = lat * PI / 180

    try:
        buffer = io.StringIO()
        sys.stdout = buffer

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
        # GRÁFICA POR DÍA
        # -------------------------
        st.subheader("📈 Visibility curves by day")

        if df is not None:

            fig, ax = plt.subplots()

            for date in df["Date"].dropna().unique():
                subset = df[df["Date"] == date].dropna()

                if not subset.empty:
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
            visible = df[df["Vis_coef"] < 0]

            if not visible.empty:
                st.success(f"First visibility on {visible.iloc[0]['Date']}")
            else:
                st.warning("No visibility detected")

        # -------------------------
        # MAPA CONTROLADO
        # -------------------------
        st.subheader("🌍 Global map (optional)")

        if st.checkbox("Generate map (slow)"):

            import numpy as np

            points = []

            for la in np.linspace(-50, 50, 8):
                for lo in np.linspace(-180, 180, 16):

                    try:
                        buffer = io.StringIO()
                        sys.stdout = buffer

                        compute_visibility(lo * PI/180, la * PI/180, int(year),
                                           height, humidity, prob, lunation_index)

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

    except Exception as e:
        sys.stdout = sys.__stdout__
        st.error(f"Critical error: {e}")

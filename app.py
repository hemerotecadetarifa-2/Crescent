import streamlit as st
import io
import sys
import pandas as pd
import re

from crescent_moon import compute_visibility, compute_new_moons, PI

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
# SELECTOR SIMPLE (SIN CÁLCULO PESADO)
# -------------------------
lunation_index = st.number_input("Lunation index (0–12)", value=0, step=1)

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
                data.append({
                    "Date": current_date,
                    "Sun_dep": pd.to_numeric(parts[0], errors="coerce"),
                    "Vis_coef": pd.to_numeric(parts[1], errors="coerce"),
                })

    if not data:
        return None

    df = pd.DataFrame(data)
    df = df.dropna()

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
        compute_visibility(long_rad, fi, int(year), height, humidity, prob, int(lunation_index))
        sys.stdout = sys.__stdout__
        output = buffer.getvalue()

        st.success("Calculation completed")

        df = extract_table(output)

        if df is not None:

            st.subheader("📊 Table")
            st.dataframe(df)

            st.subheader("📈 Graph by day")

            for date in df["Date"].unique():
                st.write(f"Day: {date}")
                subset = df[df["Date"] == date]
                st.line_chart(subset, x="Sun_dep", y="Vis_coef")

            st.subheader("🟢 First visibility")

            vis = df[df["Vis_coef"] < 0]

            if not vis.empty:
                st.success(f"First visibility on {vis.iloc[0]['Date']}")
            else:
                st.warning("No visibility")

        with st.expander("Raw output"):
            st.code(output)

    except Exception as e:
        sys.stdout = sys.__stdout__
        st.error(f"Error: {e}")

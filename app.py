import streamlit as st
import io
import sys

from crescent_moon import compute_visibility, compute_new_moons, PI

# -------------------------
# CONFIG
# -------------------------
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
st.subheader("Available lunations")

lunations = compute_new_moons(year)

options = []
for i, nm in enumerate(lunations):
    _, y, m, d, h, mi, s, _ = nm
    label = f"{i} → {d:02d}/{m:02d}/{y} {h:02d}:{mi:02d}"
    options.append(label)

selected = st.selectbox("Select lunation", options)
lunation_index = int(selected.split("→")[0].strip())

# -------------------------
# RUN BUTTON
# -------------------------
st.divider()

if st.button("🚀 Calculate"):

    long_rad = lon * PI / 180
    fi = lat * PI / 180

    with st.spinner("Computing astronomical visibility..."):

        buffer = io.StringIO()
        sys.stdout = buffer

        try:
            compute_visibility(long_rad, fi, int(year), height, humidity, prob, lunation_index)
            sys.stdout = sys.__stdout__
            output = buffer.getvalue()

            # -------------------------
            # 🔍 EXTRAER INFO CLAVE
            # -------------------------
            visibility_text = "Unknown"

            if "Very likely" in output:
                visibility_text = "🟢 Very likely visible"
            elif "Likely" in output:
                visibility_text = "🟡 Likely visible"
            elif "Difficult" in output:
                visibility_text = "🟠 Difficult"
            elif "Very difficult" in output:
                visibility_text = "🔴 Very difficult"

            # -------------------------
            # 📊 RESUMEN VISUAL
            # -------------------------
            st.success("Calculation completed")

            st.subheader("🌟 Visibility Summary")

            colA, colB = st.columns(2)

            with colA:
                st.metric("Visibility", visibility_text)

            with colB:
                st.metric("Year", year)

            # -------------------------
            # 📜 RESULTADO COMPLETO
            # -------------------------
            st.subheader("📄 Full Calculation Output")

            st.code(output, language="text")

        except Exception as e:
            sys.stdout = sys.__stdout__
            st.error(f"Error: {e}")

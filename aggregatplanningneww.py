import streamlit as st
import pandas as pd
import plotly.express as px
from engine import AggregateEngine

st.set_page_config(layout="wide", page_title="Master Aggregate Planning")

# Sidebar Input
with st.sidebar:
    st.title("Input Parameters")
    d_input = st.text_input("Demand (6 periods)", "1000, 1200, 1100, 1300, 1000, 900")
    w0 = st.number_input("Initial Workforce", 10)
    c_reg = st.number_input("Regular Cost", 10)
    c_inv = st.number_input("Inventory Cost", 2)
    # ... tambahkan parameter lainnya sesuai kebutuhan

demand = [int(x) for x in d_input.split(",")]
engine = AggregateEngine({'w0': w0, 'worker_cap': 100, 'ot_max': 200, 'i0': 50})

# Eksekusi Strategi
strategies = ["Chase", "Level", "Mixed"]
results = {s: engine.run_strategy(demand, s) for s in strategies}

# KPI Dashboard
st.subheader("📊 Executive Summary KPI")
cols = st.columns(3)
for i, s in enumerate(strategies):
    total_cost = (results[s]['Production'] * c_reg).sum()
    cols[i].metric(f"{s} Total Cost", f"Rp {total_cost:,.0f}")

# Visualisasi perbandingan
st.subheader("📈 Perbandingan Total Cost")
df_comp = pd.DataFrame({s: (results[s]['Production'] * c_reg).sum() for s in strategies}, index=["Cost"]).T
st.bar_chart(df_comp)

# Detail Tabel
st.subheader("📝 Detail Rencana Produksi")
selected_strat = st.selectbox("Pilih Strategi untuk Analisis Detail", strategies)
st.dataframe(results[selected_strat], use_container_width=True)

# Recommendation
st.divider()
st.subheader("🏆 Recommendation Section")
best_strat = min({s: (results[s]['Production'] * c_reg).sum() for s in strategies}, key=lambda k: strategies)
st.success(f"Berdasarkan efisiensi biaya, strategi terbaik saat ini adalah: **{best_strat}**")
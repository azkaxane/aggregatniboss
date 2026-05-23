import streamlit as st
import pandas as pd
from engine import AggregateEngine

st.set_page_config(layout="wide", page_title="Aggregate Planning Dashboard")

st.title("🏭 Aggregate Production Planning Dashboard")

# Input Parameter
with st.sidebar:
    st.header("Input Parameters")
    d_input = st.text_input("Demand (6 periods)", "1000, 1200, 1100, 1300, 1000, 900")
    w0 = st.number_input("Initial Workforce", value=10)
    c_reg = st.number_input("Regular Cost per Unit", value=10)
    
# Inisialisasi Engine
demand = [int(x) for x in d_input.split(",")]
engine = AggregateEngine({'w0': w0, 'worker_cap': 100, 'ot_max': 200, 'i0': 50})

# Eksekusi Strategi
strategies = ["Chase", "Level", "Mixed"]
results = {s: engine.run_strategy(demand, s) for s in strategies}

# Tampilan KPI
st.subheader("📊 Executive Summary")
cols = st.columns(3)
for i, s in enumerate(strategies):
    total_cost = (results[s]['Production'] * c_reg).sum()
    cols[i].metric(f"{s} Total Cost", f"Rp {total_cost:,.0f}")

# Detail Tabel
st.subheader("📝 Detail Rencana Produksi")
selected_strat = st.selectbox("Pilih Strategi untuk Analisis", strategies)
st.dataframe(results[selected_strat], use_container_width=True)

# Rekomendasi
st.divider()
st.subheader("🏆 Recommendation")
costs = {s: (results[s]['Production'] * c_reg).sum() for s in strategies}
best_strat = min(costs, key=costs.get)
st.success(f"Strategi terbaik berdasarkan biaya terendah adalah: **{best_strat}**")
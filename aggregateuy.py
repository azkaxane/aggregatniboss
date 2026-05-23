import streamlit as st
import pandas as pd
import plotly.express as px
from engine import AggregateEngine

st.set_page_config(layout="wide", page_title="Master Aggregate Planning")

# --- 1. INPUT SECTION ---
with st.sidebar:
    st.header("1. Input Parameters")
    d_input = st.text_input("Demand (6 periods)", "1000, 1200, 1100, 1300, 1000, 900")
    w0 = st.number_input("Initial Workforce", 10)
    worker_cap = st.number_input("Cap per Worker", 100)
    labor_cost = st.number_input("Labor Cost", 1000)
    inventory_cost = st.number_input("Holding Cost", 50)
    # Tambahkan input lainnya (ot_max, sub_cost, dll) di sini

params = {'w0': w0, 'worker_cap': worker_cap, 'labor_cost': labor_cost, 
          'inventory_cost': inventory_cost, 'i0': 50, 'rm_i0': 100, 
          'mat_req': 1, 'ot_max': 200, 'incoming_rm': [1000]*6}

engine = AggregateEngine(params)
demand = [int(x) for x in d_input.split(",")]

# --- 2. KPI & OUTPUT ---
strategies = ["Chase", "Level", "Mixed"]
results = {s: engine.run_strategy(demand, s) for s in strategies}

st.title("🏭 Strategic Aggregate Planning Dashboard")
tab1, tab2, tab3, tab4 = st.tabs(["Dashboard", "Detailed Tables", "Comparison", "Recommendation"])

with tab1:
    col1, col2, col3 = st.columns(3)
    # Tampilkan metric KPI di sini
    st.plotly_chart(px.line(results['Chase'], x="Period", y=["Demand", "Production"], title="Demand vs Production"))

with tab2:
    strat = st.selectbox("Select Strategy", strategies)
    st.dataframe(results[strat])

with tab4:
    st.subheader("🏆 Recommendation Engine")
    best = min(strategies, key=lambda s: results[s]['Total_Cost'].sum())
    st.success(f"Strategi terbaik adalah **{best}** dengan total biaya terendah.")
    st.write("Analisis: Strategi ini mengoptimalkan utilisasi kapasitas dan menekan biaya simpan.")
import streamlit as st
import pandas as pd
import plotly.express as px
from lp_model import *

st.set_page_config(page_title="Sistem Optimasi Produksi", layout="wide")

st.title("🏭 Dashboard Perencanaan Agregat Produksi")

# Sidebar
with st.sidebar.expander("💰 Parameter Biaya"):
    c_reg = st.number_input("Biaya Reguler", value=10.0)
    c_hire = st.number_input("Biaya Rekrutmen", value=50.0)
    c_fire = st.number_input("Biaya PHK", value=100.0)
    c_inv = st.number_input("Biaya Simpan", value=2.0)
    c_short = st.number_input("Biaya Penalti", value=30.0)

# Input Demand
col1, col2, col3 = st.columns(3)
d_opt = col1.text_input("Optimis", "1500, 1600, 1700, 1800, 1900, 2000")
d_nor = col2.text_input("Normal", "1000, 1050, 1100, 1150, 1200, 1250")
d_pes = col3.text_input("Pesimis", "800, 800, 750, 750, 700, 700")

if st.button("🚀 Jalankan Optimasi"):
    # Penyiapan Data
    scenarios = [DemandScenario("Optimis", [float(x) for x in d_opt.split(",")], 0.2),
                 DemandScenario("Normal", [float(x) for x in d_nor.split(",")], 0.6),
                 DemandScenario("Pesimis", [float(x) for x in d_pes.split(",")], 0.2)]
    
    cost = CostParams(c_reg, 15.0, 5.0, 20.0, c_hire, c_fire, c_inv, c_short)
    cap = CapacityParams(100.0, 2000.0, 1.0)
    init = InitialConditions(100.0, 500.0, 10.0)
    
    df_plan, df_cost = solve_all_scenarios(scenarios, cost, cap, init, None, "mixed")
    
    # KPI Cards
    st.subheader("📊 KPI Utama")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Biaya Ekspektasi", f"Rp {df_cost['Expected Cost'].sum():,.2f}")
    c2.metric("Total Produksi", f"{df_plan['Production'].sum():,.0f} unit")
    c3.metric("Rata-rata Pekerja", f"{df_plan['Workers'].mean():.1f} orang")
    
    # Visualisasi
    st.plotly_chart(px.line(df_plan[df_plan["Scenario"]=="Normal"], x="Period", y=["Production", "Demand"], title="Optimasi Produksi Normal"))
    st.dataframe(df_plan)
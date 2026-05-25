import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# ==============================================================================
# 1. KONFIGURASI HALAMAN & STYLE (SIDEBAR PUTIH, HEADER MAROON)
# ==============================================================================
st.set_page_config(
    page_title="Interactive Aggregate Planning Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Mengubah background sidebar menjadi putih */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
    }
    
    /* Mengatur warna teks di sidebar agar kontras */
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label {
        color: #333333 !important;
    }

    /* Mengubah kepala tabel (Table Header) menjadi Merah Maroon */
    thead tr th {
        background-color: #800000 !important;
        color: white !important;
    }

    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    
    .kpi-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 5px solid #007bff;
        margin-bottom: 15px;
        color: #111111;
    }
    .kpi-title { font-size: 14px; color: #495057; font-weight: bold; text-transform: uppercase; }
    .kpi-value { font-size: 24px; color: #000000; font-weight: bold; margin-top: 5px; }
    
    .recommendation-box {
        background-color: #e3f2fd;
        border-radius: 8px;
        padding: 25px;
        border-left: 6px solid #0d47a1;
        margin-top: 20px;
        color: #111111;
    }
    .recommendation-box h4 { color: #0d47a1; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.title("📊 Sistem Pendukung Keputusan: Perencanaan Agregat Interaktif")
st.markdown("Aplikasi analisis strategi produksi dengan pendekatan *Robust Planning*.")
st.markdown("---")

# ==============================================================================
# 2. SIDEBAR - INPUT PARAMETER
# ==============================================================================
st.sidebar.header("🛠️ Parameter Operasional")
num_periods = 12

# Input Demand
st.sidebar.subheader("Permintaan (Demand)")
default_demand = [1200, 1300, 1500, 1700, 1800, 1600, 1400, 1300, 1100, 1400, 1600, 1900]
demand_df = st.sidebar.data_editor(
    pd.DataFrame({"Periode": [f"Bulan {i+1}" for i in range(num_periods)], "Demand": default_demand}),
    hide_index=True
)
base_demand = demand_df["Demand"].tolist()

# Kapasitas
st.sidebar.subheader("Kapasitas & Tenaga Kerja")
init_workforce = st.sidebar.number_input("Tenaga Kerja Awal", value=20)
worker_cap = st.sidebar.number_input("Kapasitas per Pekerja/Bulan", value=70)
init_inv = st.sidebar.number_input("Inventori Awal", value=200)
safety_stock = st.sidebar.number_input("Safety Stock", value=100)

# Batasan Subkontrak & Overtime
max_ot_cap = st.sidebar.number_input("Batas Maks Overtime", value=300)
min_sub_cap = st.sidebar.number_input("Batas Min Subcontracting", value=50)
max_sub_cap = st.sidebar.number_input("Batas Maks Subcontracting", value=500)

# Struktur Biaya
st.sidebar.header("💰 Struktur Biaya (IDR)")
c_material = st.sidebar.number_input("Biaya Bahan Baku/Unit", value=150000)
c_regular = st.sidebar.number_input("Biaya Reguler/Unit", value=50000)
c_overtime = st.sidebar.number_input("Biaya Overtime/Unit", value=75000)
c_subcontract = st.sidebar.number_input("Biaya Subcontract/Unit", value=90000)
c_inventory = st.sidebar.number_input("Biaya Simpan/Unit", value=10000)
c_stockout = st.sidebar.number_input("Biaya Stockout/Unit", value=15000)
c_hiring = st.sidebar.number_input("Biaya Hiring/Pekerja", value=2000000)
c_firing = st.sidebar.number_input("Biaya Firing/Pekerja", value=3500000)

# Skenario
st.sidebar.header("🎲 Probabilitas Skenario")
p_normal = st.sidebar.slider("Normal", 0.0, 1.0, 0.6)
p_optimistic = st.sidebar.slider("Optimis (+25%)", 0.0, 1.0 - p_normal, 0.2)
p_pessimistic = round(1.0 - p_normal - p_optimistic, 2)
st.sidebar.text(f"Pesimis (-25%): {p_pessimistic}")

selected_scenario = st.selectbox("Pilih Skenario Tampilan:", ["Normal", "Optimis", "Pesimis"])

# ==============================================================================
# 3. LOGIKA PERHITUNGAN
# ==============================================================================
def calculate_aggregate_planning(strategy, demand_list):
    inv_prev = init_inv
    wf_prev = init_workforce
    records = []
    
    if strategy == "Level":
        total_net_demand = sum([d + safety_stock for d in demand_list])
        avg_prod = total_net_demand / num_periods
        constant_wf = int(np.ceil(avg_prod / worker_cap))
    else:
        constant_wf = init_workforce

    for t in range(num_periods):
        d_t = demand_list[t]
        net_demand = d_t + safety_stock
        
        # Workforce logic
        if strategy == "Chase":
            wf_current = int(np.ceil(net_demand / worker_cap))
            hiring = max(0, wf_current - wf_prev)
            firing = max(0, wf_prev - wf_current)
        elif strategy == "Level":
            wf_current = constant_wf
            hiring = max(0, wf_current - wf_prev) if t == 0 else 0
            firing = max(0, wf_prev - wf_current) if t == 0 else 0
        else: # Mixed
            wf_current = init_workforce
            hiring = firing = 0
            
        rt_prod = wf_current * worker_cap
        
        # Deficit & Subcontracting logic
        deficit = max(0, net_demand - rt_prod - inv_prev)
        ot_prod = sub_prod = 0
        
        if strategy == "Mixed" and deficit > 0:
            ot_prod = min(max_ot_cap, deficit)
            deficit -= ot_prod
            if deficit > 0:
                sub_prod = min(max_sub_cap, max(min_sub_cap, deficit))
                deficit = max(0, deficit - sub_prod)

        # Inventory balance
        total_supply = inv_prev + rt_prod + ot_prod + sub_prod
        balance = total_supply - net_demand
        inv_end = max(0, balance)
        stockout = abs(min(0, balance))
        
        # Costs
        cost_mat = (rt_prod + ot_prod) * c_material
        cost_rep = rt_prod * c_regular
        cost_ot = ot_prod * c_overtime
        cost_sub = sub_prod * c_subcontract
        cost_hold = inv_end * c_inventory
        cost_short = stockout * c_stockout
        cost_hire = hiring * c_hiring
        cost_fire = firing * c_firing
        
        total_cost = (cost_mat + cost_rep + cost_ot + cost_sub + 
                      cost_hold + cost_short + cost_hire + cost_fire)

        records.append({
            "Periode": f"Bulan {t+1}", "Demand": d_t, "Workforce": wf_current,
            "RT Production": rt_prod, "OT Production": ot_prod, "Subcontracting": sub_prod,
            "Inventory": inv_end, "Stockout": stockout, "Material Cost": cost_mat,
            "Production Cost": cost_rep, "Inventory Holding Cost": cost_hold,
            "Overtime Cost": cost_ot, "Subcontract Cost": cost_sub, 
            "Shortage Cost": cost_short, "Total Cost": total_cost
        })
        inv_prev = inv_end
        wf_prev = wf_current
        
    return pd.DataFrame(records)

# Data Generation
demand_scenarios = {
    "Normal": base_demand,
    "Optimis": [int(d * 1.25) for d in base_demand],
    "Pesimis": [int(d * 0.75) for d in base_demand]
}

results = {s: {sc: calculate_aggregate_planning(s, d) 
           for sc, d in demand_scenarios.items()} 
           for s in ["Chase", "Level", "Mixed"]}

# ==============================================================================
# 4. TAMPILAN DASHBOARD
# ==============================================================================
tab1, tab2 = st.tabs(["📈 Ringkasan Eksekutif", "🔍 Detail Operasional"])

with tab1:
    st.subheader(f"KPI Skenario: {selected_scenario}")
    cols = st.columns(3)
    
    for i, strat in enumerate(["Chase", "Level", "Mixed"]):
        df_act = results[strat][selected_scenario]
        total_c = df_act["Total Cost"].sum()
        
        # Expected cost calculation
        exp_c = (results[strat]["Normal"]["Total Cost"].sum() * p_normal +
                 results[strat]["Optimis"]["Total Cost"].sum() * p_optimistic +
                 results[strat]["Pesimis"]["Total Cost"].sum() * p_pessimistic)
        
        with cols[i]:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Strategi {strat}</div>
                <div class="kpi-value">IDR {total_c:,.0f}</div>
                <small>Expected Cost: IDR {exp_c:,.0f}</small>
            </div>
            """, unsafe_allow_html=True)

with tab2:
    sel_strat = st.radio("Pilih Strategi:", ["Chase", "Level", "Mixed"], horizontal=True)
    df_disp = results[sel_strat][selected_scenario]
    
    st.subheader("Tabel Master Perencanaan")
    st.dataframe(df_disp.style.format(precision=0), use_container_width=True)
    
    # Grafik Biaya (Perbaikan Error Stacked)
    st.subheader("Dinamika Komponen Biaya")
    fig_cb = px.bar(df_disp, x="Periode", 
                    y=["Material Cost", "Production Cost", "Inventory Holding Cost", 
                       "Overtime Cost", "Subcontract Cost", "Shortage Cost"],
                    title="Komposisi Biaya per Bulan",
                    barmode='stack')
    st.plotly_chart(fig_cb, use_container_width=True)
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# ==============================================================================
# 1. KONFIGURASI HALAMAN & STYLE DASHBOARD (MAROON & WHITE - NO DARK ELEMENTS)
# ==============================================================================
st.set_page_config(
    page_title="Interactive Aggregate Planning Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk tampilan Putih Bersih, Teks Hitam, dan Tabel Gradasi Maroon
st.markdown("""
<style>
    /* Latar belakang aplikasi menjadi putih murni */
    .stApp {
        background-color: #ffffff !important;
    }

    /* Memaksa semua teks di aplikasi menjadi hitam (Judul, Label, Isi) */
    h1, h2, h3, h4, p, span, label, li, .stMarkdown, .stSelectbox label {
        color: #000000 !important;
    }

    /* Sidebar Putih dengan border halus */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 2px solid #f0eded;
    }
    
    /* Judul di sidebar dengan warna Maroon */
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #800000 !important;
    }

    /* --- STYLING TABEL: Menghapus unsur hitam/gelap secara total --- */
    /* Header Tabel: Gradasi Maroon */
    thead tr th {
        background: linear-gradient(90deg, #800000 0%, #a52a2a 100%) !important;
        color: #ffffff !important;
        text-align: center !important;
        font-weight: bold !important;
        border: 1px solid #ffffff !important;
    }
    
    /* Body Tabel: Memaksa semua sel menjadi Putih (Menghapus baris hitam) */
    tbody tr td {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #f0f0f0 !important;
    }
    
    /* Baris selang-seling (Zebra) warna Merah Maroon sangat muda agar selaras */
    tbody tr:nth-child(even) {
        background-color: #fff8f8 !important;
    }
    
    /* Menghilangkan bayangan hitam pada dataframe */
    [data-testid="stTable"] {
        background-color: #ffffff !important;
    }

    /* KPI Card: Putih dengan bayangan halus dan border Maroon */
    .kpi-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border-top: 6px solid #800000;
        margin-bottom: 15px;
        text-align: center;
        color: #000000;
    }
    .kpi-title { font-size: 14px; color: #800000; font-weight: bold; text-transform: uppercase; }
    .kpi-value { font-size: 26px; color: #000000; font-weight: bold; margin-top: 5px; }
    .kpi-card small { color: #333333 !important; font-weight: 500; }
    
    /* Kotak Rekomendasi: Background Merah Maroon sangat muda, teks Hitam */
    .recommendation-box {
        background-color: #fff9f9;
        border-radius: 12px;
        padding: 25px;
        border: 1px solid #ffebeb;
        border-left: 10px solid #800000;
        margin-top: 20px;
        color: #000000 !important;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
    .recommendation-box h4 { color: #800000 !important; font-weight: bold; margin-bottom: 15px; }
    .recommendation-box li, .recommendation-box p { color: #000000 !important; }

    /* Memastikan widget input tidak gelap */
    .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #cccccc !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 Sistem Pendukung Keputusan: Perencanaan Agregat Interaktif (12 Periode)")
st.markdown("<p style='font-size: 1.1em; font-weight: 500;'>Aplikasi analisis strategi produksi komprehensif dengan pendekatan <i>Robust Planning</i> berbasis skenario.</p>", unsafe_allow_html=True)
st.markdown("---")

# ==============================================================================
# 2. SIDEBAR - INPUT PARAMETER OPERASIONAL & BIAYA
# ==============================================================================
st.sidebar.header("🛠️ Parameter Operasional")
num_periods = 12

# Input Demand Base via UI Dataframe
st.sidebar.subheader("Permintaan (Demand) per Periode")
default_demand = [1200, 1300, 1500, 1700, 1800, 1600, 1400, 1300, 1100, 1400, 1600, 1900]
demand_df = st.sidebar.data_editor(
    pd.DataFrame({"Periode": [f"Bulan {i+1}" for i in range(num_periods)], "Demand": default_demand}),
    hide_index=True
)
base_demand = demand_df["Demand"].tolist()

# Kapasitas & Tenaga Kerja
st.sidebar.subheader("Kapasitas & Tenaga Kerja")
init_workforce = st.sidebar.number_input("Tenaga Kerja Awal (Pekerja)", value=20, min_value=0)
worker_cap = st.sidebar.number_input("Kapasitas per Tenaga Kerja (Unit/Bulan)", value=70, min_value=1)
init_inv = st.sidebar.number_input("Inventori Awal (Unit)", value=200, min_value=0)
safety_stock = st.sidebar.number_input("Safety Stock (Unit)", value=100, min_value=0)

# Batasan Kapasitas Tambahan
max_ot_cap = st.sidebar.number_input("Batas Maksimum Overtime (Unit/Bulan)", value=300, min_value=0)
min_sub_cap = st.sidebar.number_input("Batas Minimum Subcontracting (Unit/Bulan)", value=50, min_value=0)
max_sub_cap = st.sidebar.number_input("Batas Maksimum Subcontracting (Unit/Bulan)", value=500, min_value=0)

if min_sub_cap > max_sub_cap:
    st.sidebar.error("⚠️ Batas minimum subkontrak tidak boleh lebih besar dari batas maksimum!")

# Struktur Biaya
st.sidebar.header("💰 Struktur Biaya (IDR / Unit / Pekerja)")
c_material = st.sidebar.number_input("Biaya Bahan Baku / Material Cost (/Unit)", value=150000, step=5000, min_value=0)
c_regular = st.sidebar.number_input("Biaya Produksi Reguler (/Unit)", value=50000, step=1000, min_value=0)
c_overtime = st.sidebar.number_input("Biaya Overtime (/Unit)", value=75000, step=1000, min_value=0)
c_subcontract = st.sidebar.number_input("Biaya Subcontracting (/Unit)", value=90000, step=1000, min_value=0)
c_inventory = st.sidebar.number_input("Biaya Simpan / Inventory (/Unit/Bulan)", value=10000, step=500, min_value=0)
c_stockout = st.sidebar.number_input("Biaya Stockout / Shortage (/Unit/Bulan)", value=15000, step=500, min_value=0)
c_hiring = st.sidebar.number_input("Biaya Rekrutmen / Hiring (/Pekerja)", value=2000000, step=50000, min_value=0)
c_firing = st.sidebar.number_input("Biaya PHK / Firing (/Pekerja)", value=3500000, step=50000, min_value=0)

# Skenario Ketidakpastian (Robust Planning)
st.sidebar.header("🎲 Skenario Ketidakpastian")
p_normal = st.sidebar.slider("Probabilitas Normal", 0.0, 1.0, 0.6, step=0.05)
p_optimistic = st.sidebar.slider("Probabilitas Optimis (Demand +25%)", 0.0, 1.0 - p_normal, 0.2, step=0.05)
p_pessimistic = round(1.0 - p_normal - p_optimistic, 2)
st.sidebar.text(f"Probabilitas Pesimis (Demand -25%): {p_pessimistic}")

if not np.isclose(p_normal + p_optimistic + p_pessimistic, 1.0):
    st.sidebar.error("⚠️ Total probabilitas skenario harus sama dengan 1.0")

# Pilih Skenario Aktif untuk Tampilan Detail Utama
selected_scenario = st.selectbox("Pilih Skenario Tampilan Utama Dashboard:", ["Normal", "Optimis", "Pesimis"])

# ==============================================================================
# 3. LOGIKA MESIN PERHITUNGAN STRATEGI AGREGAT
# ==============================================================================
def calculate_aggregate_planning(strategy, demand_list):
    inv_prev = init_inv
    wf_prev = init_workforce
    
    records = []
    
    if strategy == "Level":
        total_net_demand = sum([d + safety_stock for d in demand_list])
        avg_production_needed = total_net_demand / num_periods
        constant_wf = int(np.ceil(avg_production_needed / worker_cap))
    else:
        constant_wf = init_workforce

    for t in range(num_periods):
        d_t = demand_list[t]
        net_demand = d_t + safety_stock
        
        # 1. Workforce & Regular Time Production Planning Based on Strategy
        if strategy == "Chase":
            wf_needed = int(np.ceil(net_demand / worker_cap))
            hiring = max(0, wf_needed - wf_prev)
            firing = max(0, wf_prev - wf_needed)
            wf_current = wf_needed
            rt_prod = wf_current * worker_cap
        elif strategy == "Level":
            wf_current = constant_wf
            hiring = max(0, wf_current - wf_prev) if t == 0 else 0
            firing = max(0, wf_prev - wf_current) if t == 0 else 0
            rt_prod = wf_current * worker_cap
        elif strategy == "Mixed":
            wf_current = init_workforce
            hiring = 0
            firing = 0
            rt_prod = wf_current * worker_cap

        # 2. Perhitungan Overtime & Subcontracting
        deficit = max(0, net_demand - rt_prod - inv_prev)
        
        ot_prod = 0
        sub_prod = 0
        
        if strategy == "Mixed" and deficit > 0:
            ot_prod = min(max_ot_cap, deficit)
            deficit -= ot_prod
            
            if deficit > 0:
                sub_needed = max(min_sub_cap, deficit)
                sub_prod = min(max_sub_cap, sub_needed)
                deficit = max(0, deficit - sub_prod)
                
        elif strategy in ["Chase", "Level"] and deficit > 0:
            pass

        # 3. Logika Inventori & Stockout Balance Sheet
        total_supply = inv_prev + rt_prod + ot_prod + sub_prod
        balance = total_supply - net_demand
        
        if balance >= 0:
            inv_end = balance
            stockout = 0
        else:
            inv_end = 0
            stockout = abs(balance)
            
        # 4. Kalkulasi Struktur Biaya Detail per Periode
        cost_mat = (rt_prod + ot_prod) * c_material 
        cost_rep = rt_prod * c_regular
        cost_labor = wf_current * 3000000
        cost_hire = hiring * c_hiring
        cost_fire = firing * c_firing
        cost_hold = inv_end * c_inventory
        cost_ot = ot_prod * c_overtime
        cost_sub = sub_prod * c_subcontract
        cost_short = stockout * c_stockout
        total_cost = cost_mat + cost_rep + cost_hire + cost_fire + cost_hold + cost_ot + cost_sub + cost_short

        records.append({
            "Periode": f"Bulan {t+1}",
            "Demand": d_t,
            "Net Demand": net_demand,
            "Workforce": wf_current,
            "Hiring": hiring,
            "Firing": firing,
            "RT Production": rt_prod,
            "OT Production": ot_prod,
            "Subcontracting": sub_prod,
            "Inventory": inv_end,
            "Stockout": stockout,
            "Total Supply": total_supply,
            "Material Cost": cost_mat,
            "Production Cost": cost_rep,
            "Labor Cost": cost_labor,
            "Hiring Cost": cost_hire,
            "Firing Cost": cost_fire,
            "Inventory Holding Cost": cost_hold,
            "Overtime Cost": cost_ot,
            "Subcontract Cost": cost_sub,
            "Shortage Cost": cost_short,
            "Total Cost": total_cost
        })
        
        inv_prev = inv_end
        wf_prev = wf_current
        
    return pd.DataFrame(records)

# Penyesuaian Multiplier Skenario Demand Uncertainty
demand_scenarios = {
    "Normal": base_demand,
    "Optimis": [int(d * 1.25) for d in base_demand],
    "Pesimis": [int(d * 0.75) for d in base_demand]
}

# Generate Data untuk Seluruh Kombinasi Strategi & Skenario
results = {}
for strat in ["Chase", "Level", "Mixed"]:
    results[strat] = {}
    for scen, d_list in demand_scenarios.items():
        results[strat][scen] = calculate_aggregate_planning(strat, d_list)

# ==============================================================================
# 4. EVALUASI METRIK KPI UTAMA
# ==============================================================================
summary_metrics = []
for strat in ["Chase", "Level", "Mixed"]:
    c_norm = results[strat]["Normal"]["Total Cost"].sum()
    c_opt = results[strat]["Optimis"]["Total Cost"].sum()
    c_pess = results[strat]["Pesimis"]["Total Cost"].sum()
    
    expected_cost = (c_norm * p_normal) + (c_opt * p_optimistic) + (c_pess * p_pessimistic)
    
    df_active = results[strat][selected_scenario]
    total_demand = df_active["Demand"].sum()
    total_shortage = df_active["Stockout"].sum()
    
    service_level = max(0.0, ((total_demand - total_shortage) / total_demand) * 100)
    
    actual_production = df_active["RT Production"].sum() + df_active["OT Production"].sum()
    max_capacity = (df_active["Workforce"] * worker_cap).sum() + (max_ot_cap * num_periods)
    capacity_util = (actual_production / max_capacity) * 100 if max_capacity > 0 else 0
    
    summary_metrics.append({
        "Strategi": strat,
        "Total Cost (Active)": df_active["Total Cost"].sum(),
        "Expected Cost": expected_cost,
        "Service Level": service_level,
        "Capacity Utilization": capacity_util
    })

summary_df = pd.DataFrame(summary_metrics)

# ==============================================================================
# 5. LAYOUT UTAMA: TABS INTERAKTIF
# ==============================================================================
tab1, tab2, tab3 = st.tabs([
    "📈 Ringkasan Eksekutif & Rekomendasi", 
    "🔍 Detail Analisis Operasional", 
    "🎲 Analisis Risiko Skenario"
])

# ------------------------------------------------------------------------------
# TAB 1: EXECUTIVE SUMMARY
# ------------------------------------------------------------------------------
with tab1:
    st.subheader(f"Key Performance Indicator (KPI) - Skenario: {selected_scenario}")
    
    cols = st.columns(3)
    for idx, row in summary_df.iterrows():
        with cols[idx]:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Strategi {row['Strategi']}</div>
                <div class="kpi-value">IDR {row['Total Cost (Active)']:,.0f}</div>
                <small>Expected Cost: IDR {row['Expected Cost']:,.0f}</small><br>
                <small>Service Level: {row['Service Level']:.2f}%</small>
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        fig_cost = px.bar(summary_df, x="Strategi", y="Total Cost (Active)", 
                          title=f"Total Biaya Operasional ({selected_scenario})",
                          color_discrete_sequence=['#800000'], text_auto=',.0f')
        fig_cost.update_layout(plot_bgcolor='rgba(0,0,0,0)', font=dict(color="black"))
        st.plotly_chart(fig_cost, use_container_width=True)
    with c2:
        st.markdown(f"""
        <div class="recommendation-box">
            <h4>🎯 Rekomendasi Strategi</h4>
            <p>Berdasarkan analisis performa lintas skenario, strategi <b>{summary_df.loc[summary_df['Expected Cost'].idxmin()]['Strategi']}</b> 
            menunjukkan tingkat ketangguhan biaya (Expected Cost) yang paling optimal.</p>
        </div>
        """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# TAB 2: DETAILED OPERATIONAL
# ------------------------------------------------------------------------------
with tab2:
    selected_strategy = st.radio("Pilih Strategi:", ["Chase", "Level", "Mixed"], horizontal=True)
    df_selected = results[selected_strategy][selected_scenario]
    
    st.subheader(f"📋 Tabel Master: {selected_strategy} ({selected_scenario})")
    # Menggunakan Styler untuk memastikan baris tabel selaras (tanpa baris gelap)
    st.dataframe(df_selected[["Periode", "Demand", "RT Production", "OT Production", "Subcontracting", "Inventory", "Stockout", "Total Cost"]].style.format(precision=0), use_container_width=True)
    
    st.markdown("### 📊 Visualisasi Performa Berkala")
    v1, v2 = st.columns(2)
    with v1:
        fig_dp = go.Figure()
        fig_dp.add_trace(go.Scatter(x=df_selected["Periode"], y=df_selected["Demand"], name="Demand", line=dict(color='#800000', dash='dash')))
        fig_dp.add_trace(go.Bar(x=df_selected["Periode"], y=df_selected["RT Production"]+df_selected["OT Production"]+df_selected["Subcontracting"], name="Total Produksi", marker_color='#a52a2a'))
        fig_dp.update_layout(title="Demand vs Realisasi Pasokan", barmode='group', plot_bgcolor='white', font=dict(color="black"))
        st.plotly_chart(fig_dp, use_container_width=True)
    with v2:
        # Perbaikan TypeError: Menghapus stacked=True dan menggunakan barmode layout
        fig_cb = px.bar(df_selected, x="Periode", y=["Material Cost", "Production Cost", "Inventory Holding Cost", "Overtime Cost", "Subcontract Cost", "Shortage Cost"],
                        title="Dinamika Komponen Biaya", color_discrete_sequence=px.colors.sequential.Reds_r)
        fig_cb.update_layout(barmode='stack', plot_bgcolor='white', font=dict(color="black"))
        st.plotly_chart(fig_cb, use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 3: ROBUST ANALYSIS
# ------------------------------------------------------------------------------
with tab3:
    st.subheader("🎲 Matriks Robust Planning")
    robust_records = []
    for strat in ["Chase", "Level", "Mixed"]:
        c_norm = results[strat]["Normal"]["Total Cost"].sum()
        c_opt = results[strat]["Optimis"]["Total Cost"].sum()
        c_pess = results[strat]["Pesimis"]["Total Cost"].sum()
        exp_c = (c_norm * p_normal) + (c_opt * p_optimistic) + (c_pess * p_pessimistic)
        robust_records.append({"Strategi": strat, "Pesimis (IDR)": c_pess, "Normal (IDR)": c_norm, "Optimis (IDR)": c_opt, "Expected (IDR)": exp_c})
        
    robust_df = pd.DataFrame(robust_records)
    st.dataframe(robust_df.style.format(precision=0), use_container_width=True)
    
    fig_robust = go.Figure()
    colors_robust = ['#800000', '#a52a2a', '#660000']
    for idx, strat in enumerate(["Chase", "Level", "Mixed"]):
        row = robust_df[robust_df["Strategi"] == strat].iloc[0]
        fig_robust.add_trace(go.Scatter(x=["Pesimis", "Normal", "Optimis"], y=[row["Pesimis (IDR)"], row["Normal (IDR)"], row["Optimis (IDR)"]],
                                        mode='lines+markers', name=strat, line=dict(color=colors_robust[idx])))
    fig_robust.update_layout(title="Sensitivitas Biaya Lintas Skenario", plot_bgcolor='white', font=dict(color="black"))
    st.plotly_chart(fig_robust, use_container_width=True)
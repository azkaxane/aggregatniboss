import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# ==============================================================================
# 1. KONFIGURASI HALAMAN & STYLE DASHBOARD (WARNA TEKS DIUBAH KE HITAM)
# ==============================================================================
st.set_page_config(
    page_title="Interactive Aggregate Planning Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk memastikan seluruh teks di dalam card dan rekomendasi berwarna hitam
st.markdown("""
<style>
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .kpi-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 5px solid #007bff;
        margin-bottom: 15px;
        color: #111111; /* Memaksa warna teks utama menjadi hitam */
    }
    .kpi-title { font-size: 14px; color: #495057; font-weight: bold; text-transform: uppercase; }
    .kpi-value { font-size: 24px; color: #000000; font-weight: bold; margin-top: 5px; }
    .kpi-card small { color: #212529; font-weight: 500; } /* Teks kecil KPI menjadi hitam */
    
    .recommendation-box {
        background-color: #e3f2fd;
        border-radius: 8px;
        padding: 25px;
        border-left: 6px solid #0d47a1;
        margin-top: 20px;
        color: #111111; /* Memaksa seluruh teks rekomendasi menjadi hitam */
    }
    .recommendation-box h4 { color: #0d47a1; font-weight: bold; }
    .recommendation-box li { color: #111111; }
    .recommendation-box p { color: #111111; }
</style>
""", unsafe_allow_html=True)

st.title("📊 Sistem Pendukung Keputusan: Perencanaan Agregat Interaktif (12 Periode)")
st.markdown("Aplikasi analisis strategi produksi komprehensif dengan pendekatan *Robust Planning* berbasis skenario.")
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

        # 2. Perhitungan Overtime & Subcontracting dengan Kebijakan Minimum
        deficit = max(0, net_demand - rt_prod - inv_prev)
        
        ot_prod = 0
        sub_prod = 0
        
        if strategy == "Mixed" and deficit > 0:
            ot_prod = min(max_ot_cap, deficit)
            deficit -= ot_prod
            
            if deficit > 0:
                # Alokasi subkontrak harus memenuhi ambang batas minimum produksi yang ditentukan
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
# 4. EVALUASI METRIK KPI UTAMA VIA EXPECTED VALUE
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
    wf_util = (df_active["RT Production"].sum() / (df_active["Workforce"] * worker_cap).sum()) * 100
    
    summary_metrics.append({
        "Strategi": strat,
        "Total Cost (Active)": df_active["Total Cost"].sum(),
        "Expected Cost": expected_cost,
        "Total Inventory": df_active["Inventory"].sum(),
        "Total Stockout": df_active["Stockout"].sum(),
        "Total Overtime": df_active["OT Production"].sum(),
        "Total Subcontracting": df_active["Subcontracting"].sum(),
        "Service Level": service_level,
        "Workforce Utilization": wf_util,
        "Capacity Utilization": capacity_util
    })

summary_df = pd.DataFrame(summary_metrics)

# ==============================================================================
# 5. LAYOUT UTAMA: TABS INTERAKTIF
# ==============================================================================
tab1, tab2, tab3 = st.tabs([
    "📈 Ringkasan Eksekutif & Rekomendasi", 
    "🔍 Detail Analisis Operasional per Strategi", 
    "🎲 Analisis Risiko Skenario (Robust Planning)"
])

# ------------------------------------------------------------------------------
# TAB 1: EXECUTIVE SUMMARY & STRATEGIC RECOMMENDATION
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
                <small>Service Level: {row['Service Level']:.2f}%</small><br>
                <small>Cap. Util: {row['Capacity Utilization']:.1f}%</small>
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown("---")
    
    c1, c2 = st.columns(2)
    with c1:
        fig_cost = px.bar(summary_df, x="Strategi", y="Total Cost (Active)", 
                          title=f"Perbandingan Total Biaya Operasional Horison 12 Bulan ({selected_scenario})",
                          color="Strategi", text_auto=',.0f')
        st.plotly_chart(fig_cost, use_container_width=True)
    with c2:
        fig_sl = px.bar(summary_df, x="Strategi", y="Service Level", 
                        title="Tingkat Layanan Pemenuhan Permintaan (Service Level %)",
                        color="Strategi", text_auto='.2f', range_y=[0, 105])
        st.plotly_chart(fig_sl, use_container_width=True)

    st.markdown("### 🤖 Rekomendasi Strategi Optimal")
    best_cost_strat = summary_df.loc[summary_df["Expected Cost"].idxmin()]["Strategi"]
    best_sl_strat = summary_df.loc[summary_df["Service Level"].idxmax()]["Strategi"]
    best_util_strat = summary_df.loc[summary_df["Capacity Utilization"].idxmax()]["Strategi"]
    
    st.markdown(f"""
    <div class="recommendation-box">
        <h4>🎯 Keputusan Strategis Berdasarkan Aturan Optimasi Terpadu:</h4>
        <ul>
            <li><b>Efisiensi Biaya Terbaik (Robust):</b> Strategi <b>{best_cost_strat}</b> memberikan nilai ekonomis paling tangguh (Expected Cost terendah lintas skenario).</li>
            <li><b>Keterandalan Layanan (Service Level):</b> Strategi <b>{best_sl_strat}</b> paling optimal meminimalisir risiko stockout di pasar.</li>
            <li><b>Efisiensi Fasilitas (Utilisasi Kapasitas):</b> Strategi <b>{best_util_strat}</b> mencatatkan penggunaan infrastruktur produksi paling produktif.</li>
        </ul>
        <p><b>Rekomendasi Final:</b> Disarankan menggunakan pendekatan <b>{best_cost_strat} Strategy</b> untuk mengamankan struktur finansial perusahaan dari fluktuasi ketidakpastian pasar jangka panjang.</p>
    </div>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# TAB 2: DETAILED STRATEGY DEEP-DIVE
# ------------------------------------------------------------------------------
with tab2:
    selected_strategy = st.radio("Pilih Strategi untuk Analisis Mendalam:", ["Chase", "Level", "Mixed"], horizontal=True)
    df_selected = results[selected_strategy][selected_scenario]
    
    st.subheader(f"📋 Master Table Aggregate Production Planning: {selected_strategy} ({selected_scenario})")
    master_display = df_selected[["Periode", "Demand", "Net Demand", "RT Production", "OT Production", "Subcontracting", "Total Supply", "Inventory", "Stockout"]]
    st.dataframe(master_display.style.format(precision=0), use_container_width=True)
    
    if selected_strategy == "Chase":
        st.subheader("👨‍🏭 Workforce & Capacity Adjustment Sheet (Chase Focus)")
        st.dataframe(df_selected[["Periode", "Workforce", "Hiring", "Firing", "RT Production"]].style.format(precision=0), use_container_width=True)
        
    elif selected_strategy == "Level":
        st.subheader("📦 Inventory Buffer & Capacity Efficiency Sheet (Level Focus)")
        df_level_spec = df_selected[["Periode", "Inventory", "Stockout", "RT Production"]].copy()
        df_level_spec["Capacity Efficiency (%)"] = (df_level_spec["RT Production"] / (df_selected["Workforce"] * worker_cap)) * 100
        st.dataframe(df_level_spec.style.format(precision=1), use_container_width=True)
        
    elif selected_strategy == "Mixed":
        st.subheader("🔄 Sourcing Optimization & Make-or-Buy Analysis (Mixed Focus)")
        mob_df = df_selected[["Periode", "RT Production", "OT Production", "Subcontracting"]].copy()
        # Mencegah pembagian dengan nol jika tidak ada aktivitas produksi sama sekali
        total_p = mob_df["RT Production"] + mob_df["OT Production"] + mob_df["Subcontracting"]
        mob_df["Internal Content (%)"] = np.where(total_p > 0, ((mob_df["RT Production"] + mob_df["OT Production"]) / total_p) * 100, 0)
        st.dataframe(mob_df.style.format(precision=1), use_container_width=True)
        
        st.subheader("🪵 Raw Material Requirements Planning (BOM Explode Proxy)")
        raw_mat_df = pd.DataFrame({
            "Periode": df_selected["Periode"],
            "Incoming Material (Unit)": (df_selected["RT Production"] + df_selected["OT Production"]) * 1.05,
            "Usage Material (Unit)": (df_selected["RT Production"] + df_selected["OT Production"]),
            "Ending Inventory Material": np.maximum(0, 100 + ((df_selected["RT Production"] + df_selected["OT Production"]) * 0.05)),
            "Material Shortage": 0
        })
        st.dataframe(raw_mat_df.style.format(precision=0), use_container_width=True)

    st.subheader("💸 Analisis Finansial & Struktur Biaya Berjalan")
    cost_cols = ["Periode", "Material Cost", "Production Cost", "Labor Cost", "Hiring Cost", "Firing Cost", "Inventory Holding Cost", "Overtime Cost", "Subcontract Cost", "Shortage Cost", "Total Cost"]
    st.dataframe(df_selected[cost_cols].style.format(precision=0), use_container_width=True)
    
    st.markdown("### 📊 Visualisasi Performa Berkala (12 Periode)")
    v1, v2 = st.columns(2)
    with v1:
        fig_dp = go.Figure()
        fig_dp.add_trace(go.Scatter(x=df_selected["Periode"], y=df_selected["Demand"], name="Demand Real", line=dict(color='red', width=2, dash='dash')))
        fig_dp.add_trace(go.Bar(x=df_selected["Periode"], y=df_selected["RT Production"] + df_selected["OT Production"] + df_selected["Subcontracting"], name="Total Produksi", marker_color='royalblue'))
        fig_dp.update_layout(title="Perbandingan Tren Permintaan vs Realisasi Pasokan (12 Bulan)", barmode='group')
        st.plotly_chart(fig_dp, use_container_width=True)
    with v2:
        fig_cb = px.bar(df_selected, x="Periode", y=["Material Cost", "Production Cost", "Inventory Holding Cost", "Overtime Cost", "Subcontract Cost", "Shortage Cost"],
                        title="Dinamika Komponen Biaya per Periode")
        st.plotly_chart(fig_cb, use_container_width=True)

    v3, v4 = st.columns(2)
    with v3:
        fig_inv = px.line(df_selected, x="Periode", y="Inventory", title="Fluktuasi Tingkat Inventori Akhir", markers=True, line_shape="linear")
        st.plotly_chart(fig_inv, use_container_width=True)
    with v4:
        fig_os = go.Figure()
        fig_os.add_trace(go.Bar(x=df_selected["Periode"], y=df_selected["OT Production"], name="Overtime Vol", marker_color='orange'))
        fig_os.add_trace(go.Bar(x=df_selected["Periode"], y=df_selected["Subcontracting"], name="Subcontract Vol", marker_color='purple'))
        fig_os.update_layout(title="Alokasi Kapasitas Tambahan: Lembur vs Pihak Ketiga", barmode='stack')
        st.plotly_chart(fig_os, use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 3: ROBUST SCENARIO & RISK ANALYSIS
# ------------------------------------------------------------------------------
with tab3:
    st.subheader("🎲 Matriks Analisis Risiko & Robust Planning")
    st.markdown("Tabel di bawah menyajikan komparasi performa finansial di seluruh spektrum kemungkinan permintaan untuk menguji ketangguhan model.")
    
    robust_records = []
    for strat in ["Chase", "Level", "Mixed"]:
        c_norm = results[strat]["Normal"]["Total Cost"].sum()
        c_opt = results[strat]["Optimis"]["Total Cost"].sum()
        c_pess = results[strat]["Pesimis"]["Total Cost"].sum()
        exp_c = (c_norm * p_normal) + (c_opt * p_optimistic) + (c_pess * p_pessimistic)
        
        robust_records.append({
            "Strategi": strat,
            "Skenario Pesimis (Cost)": c_pess,
            "Skenario Normal (Cost)": c_norm,
            "Skenario Optimis (Cost)": c_opt,
            "Expected Robust Cost": exp_c
        })
        
    robust_df = pd.DataFrame(robust_records)
    st.dataframe(robust_df.style.format({
        "Skenario Pesimis (Cost)": "IDR {:,.0f}",
        "Skenario Normal (Cost)": "IDR {:,.0f}",
        "Skenario Optimis (Cost)": "IDR {:,.0f}",
        "Expected Robust Cost": "IDR {:,.0f}"
    }), use_container_width=True)
    
    fig_robust = go.Figure()
    for strat in ["Chase", "Level", "Mixed"]:
        row = robust_df[robust_df["Strategi"] == strat].iloc[0]
        fig_robust.add_trace(go.Scatter(
            x=["Pesimis", "Normal", "Optimis"], 
            y=[row["Skenario Pesimis (Cost)"], row["Skenario Normal (Cost)"], row["Skenario Optimis (Cost)"]],
            mode='lines+markers', name=f"Profil Risiko {strat}"
        ))
    fig_robust.update_layout(title="Analisis Sensitivitas Struktur Biaya Lintas Skenario Permintaan", yaxis_title="Total Biaya (IDR)")
    st.plotly_chart(fig_robust, use_container_width=True)
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from scipy.stats import weibull_min, kstest
from scipy.special import gamma
from scipy.integrate import cumulative_trapezoid
import io
import base64
import requests

# ==============================================================================
# 1. PAGE CONFIGURATION & PREMIUM MINIMALIST DESIGN STYLE
# ==============================================================================
st.set_page_config(
    page_title="Interactive Sustainable PM Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS: Professional Academic Theme + FIXED SOLID STICKY TABS
st.markdown("""
<style>
    :root {
        color-scheme: light !important;
        --st-background: #ffffff !important;
        --st-color: #0f172a !important;
    }
    
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .main {
        background-color: #ffffff !important;
        color: #0f172a !important;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    [data-testid="stSidebar"] { background-color: #f8fafc !important; border-right: 1px solid #e2e8f0 !important; }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label { color: #0f172a !important; font-weight: 600 !important; }

    /* Clean Dataframes */
    div[data-testid="stDataFrame"], div[data-testid="stDataEditor"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 6px !important;
    }

    /* KPI Component Cards */
    .kpi-card {
        background-color: #ffffff !important;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
        position: relative;
        overflow: hidden;
    }
    .kpi-card.blue::before { content: ""; position: absolute; top: 0; left: 0; bottom: 0; width: 4px; background: #2563eb; }
    .kpi-card.green::before { content: ""; position: absolute; top: 0; left: 0; bottom: 0; width: 4px; background: #10b981; }
    .kpi-card.orange::before { content: ""; position: absolute; top: 0; left: 0; bottom: 0; width: 4px; background: #f59e0b; }
    
    .kpi-title { font-size: 12px; color: #64748b !important; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
    .kpi-value { font-size: 22px; color: #0f172a !important; font-weight: 700; margin-top: 4px; }
    .kpi-card small { color: #475569 !important; font-weight: 500; }
    
    /* Academic Recommendation Box */
    .recommendation-box {
        background-color: #f8fafc !important;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 20px;
        position: relative;
    }
    .recommendation-box::before { content: ""; position: absolute; top: 0; left: 0; bottom: 0; width: 4px; background: #10b981; }
    
    /* Upload Guide Panel */
    .upload-box {
        background-color: #f8fafc !important;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 20px;
        position: relative;
        margin-bottom: 20px;
    }
    .upload-box::before { content: ""; position: absolute; top: 0; left: 0; bottom: 0; width: 4px; background: #2563eb; }
    .table-template { width: 100%; border-collapse: collapse; margin: 10px 0; background-color: #ffffff; }
    .table-template th { background-color: #f1f5f9; color: #0f172a; padding: 6px 12px; border: 1px solid #cbd5e1; font-size: 13px; text-align: left; }
    .table-template td { padding: 6px 12px; border: 1px solid #cbd5e1; color: #475569; font-size: 13px; font-family: monospace; }

    /* STICKY TABS */
    div[data-testid="stTabs"] [data-baseweb="tab-list"] { 
        gap: 4px; border-bottom: 2px solid #e2e8f0 !important;
        position: -webkit-sticky !important; position: sticky !important;
        top: 2.85rem !important; background-color: #ffffff !important;
        z-index: 99999 !important; padding-top: 12px !important; padding-bottom: 12px !important;
    }
    .stTabs [data-baseweb="tab"] { color: #64748b !important; font-weight: 500; }
    .stTabs [aria-selected="true"] { color: #2563eb !important; border-bottom: 2px solid #2563eb !important; font-weight: 600 !important; }

    /* Author Profiles */
    .author-profile-container { border-left: 3px solid #2563eb; padding-left: 12px; margin: 10px 0; }
    .author-profile-name { font-size: 14px; color: #0f172a !important; font-weight: 600; letter-spacing: 0.3px; line-height: 1.4; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# LOGO & HEADLINE STRUCTURE 
# ==============================================================================
# Anda dapat mengganti URL ini dengan URL Google Drive Anda sendiri yang bersifat Public
logo_gunadarma_url = "https://upload.wikimedia.org/wikipedia/commons/4/4f/Logo_Universitas_Gunadarma.png"
logo_elite_url = "https://cdn-icons-png.flaticon.com/512/1903/1903155.png" # Dummy Elite/Lab Logo

st.markdown(f"""
<div style="display: flex; align-items: center; flex-wrap: wrap; gap: 20px; margin-top: -45px; margin-bottom: 10px; width: 100%;">
    <div style="display: flex; gap: 12px; flex-shrink: 0; align-items: center;">
        <img src="{logo_gunadarma_url}" style="height: 65px; width: auto; object-fit: contain;">
        <img src="{logo_elite_url}" style="height: 55px; width: auto; object-fit: contain; border-radius: 50%;">
    </div>
    <div style="flex: 1; min-width: 320px;">
        <h1 style="margin: 0; padding: 0; font-size: 26px; font-weight: 700; color: #0f172a; line-height: 1.2;">
            Decision Support System: Sustainable Preventive Maintenance
        </h1>
        <p style="margin: 4px 0 0 0; color: #475569; font-size: 14px; line-height: 1.4;">
            Weibull Distribution Reliability Analysis & Eco-Cost Optimization Dashboard
        </p>
    </div>
</div>
<hr>
""", unsafe_allow_html=True)

# ==============================================================================
# DATA STATE MANAGEMENT & EXCEL TEMPLATE INTEGRATION
# ==============================================================================
default_tbf = [450, 520, 610, 480, 750, 590, 680, 540, 490, 810, 600, 720, 550, 670, 710]

if "base_tbf" not in st.session_state:
    st.session_state.base_tbf = default_tbf.copy()

st.markdown("""
<div class="upload-box">
    <h4 style="margin-top:0;">Integrasi Data Historis (Format Excel)</h4>
    <p style="margin-bottom:8px;">Unggah data <b>Time Between Failures (TBF)</b> mesin Anda. Pastikan file memiliki kolom dengan nama header yang tepat sesuai contoh tabel di bawah ini:</p>
    <table class="table-template">
        <tr><th>ID Mesin</th><th>TBF (Jam)</th><th>Status Observasi</th></tr>
        <tr><td>M-01</td><td>450</td><td>Failed</td></tr>
        <tr><td>M-02</td><td>520</td><td>Failed</td></tr>
    </table>
</div>
""", unsafe_allow_html=True)

# Generate Template File
template_df = pd.DataFrame({
    "ID Mesin": [f"M-{i+1:02d}" for i in range(len(default_tbf))],
    "TBF (Jam)": default_tbf,
    "Status Observasi": ["Failed"] * len(default_tbf)
})
template_io = io.BytesIO()
with pd.ExcelWriter(template_io, engine='openpyxl') as writer:
    template_df.to_excel(writer, index=False, sheet_name='TBF_Data')
template_io.seek(0)

col_dl, col_up = st.columns([1, 2])
with col_dl:
    st.write("") 
    st.download_button(
        label="📥 Download Template Excel",
        data=template_io,
        file_name="Template_Data_TBF.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

with col_up:
    uploaded_file = st.file_uploader("Upload Excel File TBF Anda:", type=["xlsx", "xls"], label_visibility="collapsed")

if uploaded_file is not None:
    try:
        excel_data = pd.read_excel(uploaded_file)
        if "TBF (Jam)" in excel_data.columns:
            st.session_state.base_tbf = pd.to_numeric(excel_data["TBF (Jam)"], errors='coerce').dropna().tolist()
            st.success("✅ Data historis TBF berhasil dimuat dan disinkronisasi ke dalam model!")
        else:
            st.error("❌ Kolom 'TBF (Jam)' tidak ditemukan. Pastikan header sesuai template.")
    except Exception as e:
        st.error(f"Gagal membaca file: {str(e)}")

st.markdown("---")

# ==============================================================================
# SIDEBAR - PARAMETERS
# ==============================================================================
st.sidebar.header("⚙️ Data TBF (Jam)")
tbf_editor_df = pd.DataFrame({"TBF (Jam)": st.session_state.base_tbf})
master_editor_df = st.sidebar.data_editor(tbf_editor_df, hide_index=True, use_container_width=True)
data_TBF = master_editor_df["TBF (Jam)"].values

st.sidebar.header("💰 Parameter Biaya Konvensional")
cp = st.sidebar.number_input("Biaya PM Rutin (Cp) [Rp]", value=500000, step=50000)
cf = st.sidebar.number_input("Biaya Breakdown (Cf) [Rp]", value=3500000, step=100000)
mttr = st.sidebar.number_input("Mean Time To Repair (MTTR) [Jam]", value=12.0, step=1.0)

st.sidebar.header("🌱 Parameter Ekologi (Emisi & Limbah)")
cp_eco = st.sidebar.number_input("Penalti Ekologi PM [Rp]", value=100000, step=10000, help="Biaya limbah suku cadang")
cf_eco = st.sidebar.number_input("Penalti Ekologi Breakdown [Rp]", value=1500000, step=50000, help="Lonjakan emisi energi saat breakdown")
w_bobot = st.sidebar.slider("Bobot Sustainability (w)", 0.0, 1.0, 0.5, step=0.1)

st.sidebar.header("🎯 Analisis Keandalan")
target_rel = st.sidebar.slider("Target Reliabilitas Min (%)", 50, 99, 80, step=1) / 100.0

# ==============================================================================
# CORE PROCESSING MATHEMATICAL ALGORITHM ENGINE (MLE & COST)
# ==============================================================================
# 1. Estimasi Parameter Weibull (MLE)
beta_est, loc_est, eta_est = weibull_min.fit(data_TBF, floc=0)

# 2. Uji Goodness-of-Fit (Kolmogorov-Smirnov)
D_stat, p_value = kstest(data_TBF, 'weibull_min', args=(beta_est, loc_est, eta_est))
is_weibull = p_value > 0.05

# 3. Hitung MTBF & Availability
mtbf = eta_est * gamma(1 + 1/beta_est)
availability = mtbf / (mtbf + mttr)

# 4. Distribusi Keandalan & Waktu
T_arr = np.linspace(1, max(data_TBF)*2, 1000)
R_arr = np.exp(- (T_arr / eta_est)**beta_est)
f_arr = (beta_est / eta_est) * (T_arr / eta_est)**(beta_est - 1) * np.exp(-(T_arr / eta_est)**beta_est)
h_arr = (beta_est / eta_est) * (T_arr / eta_est)**(beta_est - 1)

# Expected Time Calculation: integral dari R(t) dt
ET_arr = cumulative_trapezoid(R_arr, T_arr, initial=0)
# Hindari pembagian dengan nol
ET_arr[ET_arr == 0] = 1e-10 

# Menentukan T_target dari Reliability Slider
idx_target = np.abs(R_arr - target_rel).argmin()
T_target = T_arr[idx_target]

# 5. Model Biaya
Total_Cp_sust = cp + (cp_eco * w_bobot)
Total_Cf_sust = cf + (cf_eco * w_bobot)

# Kalkulasi ekspektasi biaya per satuan waktu C(T)
C_conv = (cp * R_arr + cf * (1 - R_arr)) / ET_arr
C_sust = (Total_Cp_sust * R_arr + Total_Cf_sust * (1 - R_arr)) / ET_arr

# Cari Optimal T*
idx_opt_conv = np.argmin(C_conv)
T_opt_conv = T_arr[idx_opt_conv]
Min_C_conv = C_conv[idx_opt_conv]

idx_opt_sust = np.argmin(C_sust)
T_opt_sust = T_arr[idx_opt_sust]
Min_C_sust = C_sust[idx_opt_sust]

# Final Rekomendasi Interval
Final_T_Rec = min(T_opt_sust, T_target)
Final_R_Rec = np.exp(- (Final_T_Rec / eta_est)**beta_est)

# Visual Theme Helper
def apply_forced_light_theme(fig, is_cost_chart=False):
    fig.update_layout(
        template="plotly_white", paper_bgcolor='#ffffff', plot_bgcolor='#f8fafc',  
        font=dict(color="#0f172a", size=12), title_font=dict(color="#0f172a", size=15),
        xaxis=dict(gridcolor="#e2e8f0", linecolor="#cbd5e1"),
        yaxis=dict(gridcolor="#e2e8f0", linecolor="#cbd5e1"),
        legend=dict(bordercolor="#e2e8f0", borderwidth=1, bgcolor="rgba(255,255,255,0.9)")
    )
    if is_cost_chart:
        fig.update_layout(yaxis=dict(tickprefix="Rp "))
    return fig

# ==============================================================================
# DASHBOARD INTERFACE LAYOUT
# ==============================================================================
tab1, tab2, tab3 = st.tabs([
    "🔍 Modul 1: Analisis Reliabilitas & MLE", 
    "📈 Modul 2: Optimasi Penjadwalan Berkelanjutan", 
    "📝 Ringkasan Eksekutif & Rekomendasi Sistem"
])

# ------------------------------------------------------------------------------
# TAB 1
# ------------------------------------------------------------------------------
with tab1:
    st.subheader("1. Estimasi Parameter Weibull (MLE) & Karakteristik Dasar")
    
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(f'<div class="kpi-card blue"><div class="kpi-title">Shape Parameter (β)</div><div class="kpi-value">{beta_est:.4f}</div></div>', unsafe_allow_html=True)
    with k2:
        st.markdown(f'<div class="kpi-card blue"><div class="kpi-title">Scale Parameter (η)</div><div class="kpi-value">{eta_est:.1f} Jam</div></div>', unsafe_allow_html=True)
    with k3:
        st.markdown(f'<div class="kpi-card orange"><div class="kpi-title">Mean Time Between Failures</div><div class="kpi-value">{mtbf:.1f} Jam</div></div>', unsafe_allow_html=True)
    with k4:
        st.markdown(f'<div class="kpi-card green"><div class="kpi-title">Availability Sistem</div><div class="kpi-value">{availability*100:.2f}%</div></div>', unsafe_allow_html=True)

    # Interpretasi Hasil beta
    interpretasi = ""
    if beta_est > 1:
        interpretasi = f"Nilai **$\\beta = {beta_est:.2f} > 1$** menunjukkan pola **wear-out (keausan)**. Hazard rate akan meningkat seiring waktu operasi. Preventive maintenance terjadwal efektif untuk mencegah kegagalan. Studi kasus pada industri manufaktur elektronik menunjukkan pola *wear-out* dengan $\\beta > 1$ sebagai rujukan hasil serupa."
    elif abs(beta_est - 1) < 0.1:
        interpretasi = f"Nilai **$\\beta \\approx 1$** menunjukkan **random failure**. Hazard rate konstan."
    else:
        interpretasi = f"Nilai **$\\beta = {beta_est:.2f} < 1$** menunjukkan fenomena **infant mortality**."

    st.info(f"💡 **Diagnostik Pola Kegagalan:**\n\n{interpretasi}")

    st.markdown("---")
    st.subheader("2. Kurva Reliabilitas Operasional $R(t)$ dan Hazard Rate $h(t)$")
    
    c1, c2 = st.columns(2)
    with c1:
        fig_rel = go.Figure()
        fig_rel.add_trace(go.Scatter(x=T_arr, y=R_arr, mode='lines', name='Reliability R(t)', line=dict(color='#2563eb', width=3)))
        fig_rel.add_vline(x=T_target, line_dash="dash", line_color="#ef4444", annotation_text=f"Batas Target {target_rel*100}%")
        fig_rel.update_layout(title="Distribusi Probabilitas Keandalan Sistem", xaxis_title="Waktu Operasi (Jam)", yaxis_title="Probabilitas Reliabilitas")
        st.plotly_chart(apply_forced_light_theme(fig_rel), use_container_width=True)
        
    with c2:
        fig_haz = go.Figure()
        fig_haz.add_trace(go.Scatter(x=T_arr, y=h_arr, mode='lines', name='Hazard h(t)', line=dict(color='#f59e0b', width=3)))
        fig_haz.update_layout(title="Profil Laju Kegagalan (Hazard Rate)", xaxis_title="Waktu Operasi (Jam)", yaxis_title="Laju Hazard h(t)")
        st.plotly_chart(apply_forced_light_theme(fig_haz), use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 2
# ------------------------------------------------------------------------------
with tab2:
    st.subheader("3. Model Optimalisasi *Age-Replacement Policy*")
    st.markdown("Analisis komparatif antara metode konvensional (fokus finansial) dengan metode berkelanjutan (*Sustainable*) yang mengikutsertakan parameter dampak ekologis.")
    
    k5, k6 = st.columns(2)
    with k5:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Interval PM Optimal (Konvensional)</div><div class="kpi-value">T* = {T_opt_conv:.0f} Jam</div><small>Ekspektasi Biaya/Jam: Rp {Min_C_conv:,.0f}</small></div>', unsafe_allow_html=True)
    with k6:
        st.markdown(f'<div class="kpi-card green"><div class="kpi-title">Interval PM Optimal (Sustainable)</div><div class="kpi-value">T* (Sust) = {T_opt_sust:.0f} Jam</div><small>Biaya + Ekologi/Jam: Rp {Min_C_sust:,.0f} | (Bobot w={w_bobot})</small></div>', unsafe_allow_html=True)

    fig_cost = go.Figure()
    fig_cost.add_trace(go.Scatter(x=T_arr, y=C_conv, mode='lines', name='Model Konvensional C(T)', line=dict(color='#64748b', width=2, dash='dash')))
    fig_cost.add_trace(go.Scatter(x=T_arr, y=C_sust, mode='lines', name='Model Sustainable C_total(T)', line=dict(color='#10b981', width=3)))
    
    fig_cost.add_trace(go.Scatter(x=[T_opt_conv], y=[Min_C_conv], mode='markers+text', name='Optimal Konvensional', marker=dict(color='gray', size=10), text=[f"Rp {Min_C_conv:,.0f}"], textposition="bottom center"))
    fig_cost.add_trace(go.Scatter(x=[T_opt_sust], y=[Min_C_sust], mode='markers+text', name='Optimal Sustainable', marker=dict(color='green', size=12), text=[f"Rp {Min_C_sust:,.0f}"], textposition="top center"))
    
    # Batasi view range agar y-axis tidak terlalu terdistorsi saat nilai kecil di awal
    min_cost = min(Min_C_conv, Min_C_sust)
    fig_cost.update_layout(title="Lanskap Fungsi Minimalisasi Biaya Ekspektasi Per Satuan Waktu", xaxis_title="Interval Eksekusi PM, T (Jam)", yaxis_title="Ekspektasi Total Biaya (Rp/Jam)", yaxis_range=[min_cost*0.8, min_cost*4])
    st.plotly_chart(apply_forced_light_theme(fig_cost, is_cost_chart=True), use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 3
# ------------------------------------------------------------------------------
with tab3:
    st.markdown(f"""
    <div class="recommendation-box">
        <h4>Kebijakan Final Preventive Maintenance Berkelanjutan:</h4>
        <p>Berdasarkan rumusan matematis dan batasan operasional (Safety Constraint Target Reliabilitas = <b>{target_rel*100}%</b>):</p>
        <ul style="font-size: 16px;">
            <li>Jadwal Tindakan Eksekusi PM yang Disarankan: <b>{Final_T_Rec:.0f} Jam Operasi</b></li>
            <li>Estimasi Kondisi Keandalan (Reliability) Mesin saat PM dilakukan: <b>{Final_R_Rec*100:.1f}%</b></li>
            <li>Expected Cycle Length: <b>{ET_arr[np.abs(T_arr - Final_T_Rec).argmin()]:.1f} Jam</b></li>
        </ul>
        <p><i>*Sistem mengambil nilai optimal T* Sustainable. Jika T* melewati batasan Target Reliabilitas, sistem secara otomatis akan menggunakan batas aman target reliabilitas.</i></p>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("Matriks Profil Biaya Ekspektasi per Siklus Operasional")
    
    def kalkulasi_profil_siklus(T_val):
        R_val = np.exp(- (T_val / eta_est)**beta_est)
        Exp_Break = 1 - R_val
        Finansial_Cost = (cp * R_val) + (cf * Exp_Break)
        Emisi_Cost = (cp_eco * R_val) + (cf_eco * Exp_Break)
        return Finansial_Cost, Emisi_Cost

    fin_conv, em_conv = kalkulasi_profil_siklus(T_opt_conv)
    fin_sust, em_sust = kalkulasi_profil_siklus(Final_T_Rec)

    df_compare = pd.DataFrame({
        "Skenario": ["Konvensional (T* Conv)", "Sustainable (T* Sust/Target)", "Konvensional (T* Conv)", "Sustainable (T* Sust/Target)"],
        "Kategori Alokasi": ["Biaya Operasional", "Biaya Operasional", "Estimasi Jejak Ekologi/Emisi", "Estimasi Jejak Ekologi/Emisi"],
        "Ekspektasi Nilai (Rp)": [fin_conv, fin_sust, em_conv, em_sust]
    })

    fig_bar = px.bar(df_compare, x="Skenario", y="Ekspektasi Nilai (Rp)", color="Kategori Alokasi", 
                     title="Pemetaan Ekspektasi Finansial vs Beban Emisi/Ekologi dalam 1 Siklus Evaluasi",
                     color_discrete_sequence=["#2563eb", "#ef4444"], barmode="group")
    st.plotly_chart(apply_forced_light_theme(fig_bar, is_cost_chart=True), use_container_width=True)

    # --------------------------------------------------------------------------
    # AUTHORS PROFILE SECTION
    # --------------------------------------------------------------------------
    st.markdown("""
    <div class="author-profile-container" style="margin-top: 40px;">
        <div class="author-profile-name">Analytical Framework & Modeling Credit</div>
        <small style="color: #64748b; font-size: 13px;">
            Engineered for Conference Paper on Sustainable Engineering.<br>
            <strong>Universitas Gunadarma</strong> | <strong>Laboratorium Elite</strong><br>
            This DSS uses Maximum Likelihood Estimation (MLE) and numerical integration methodologies to optimize sustainable PM scheduling.
        </small>
    </div>
    """, unsafe_allow_html=True)
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from scipy.stats import weibull_min, kstest
from scipy.special import gamma
import io

# ==============================================================================
# 1. PAGE CONFIGURATION & PREMIUM MINIMALIST DESIGN STYLE
# ==============================================================================
st.set_page_config(
    page_title="Reliability & Sustainable PM Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    [data-testid="stSidebar"] {
        background-color: #f8fafc !important;
        border-right: 1px solid #e2e8f0 !important;
    }
    [data-testid="stSidebar"] .stMarkdown, [data-testid="stSidebar"] label, [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2 {
        color: #0f172a !important;
        font-weight: 600 !important;
    }
    div[data-testid="stDataFrame"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 6px !important;
    }
    /* KPI Cards */
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
    
    .kpi-title { font-size: 13px; color: #64748b !important; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
    .kpi-value { font-size: 24px; color: #0f172a !important; font-weight: 700; margin-top: 4px; }
    
    /* Academic Recommendation Box */
    .recommendation-box {
        background-color: #f8fafc !important;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 20px;
        position: relative;
    }
    .recommendation-box::before { content: ""; position: absolute; top: 0; left: 0; bottom: 0; width: 4px; background: #10b981; }
    .recommendation-box h4 { color: #0f172a !important; font-weight: 700; margin-top: 0; }
    
    /* Sticky Tabs */
    div[data-testid="stTabs"] [data-baseweb="tab-list"] { 
        gap: 4px; 
        border-bottom: 2px solid #e2e8f0 !important;
        position: -webkit-sticky !important;
        position: sticky !important;
        top: 2.85rem !important; 
        background-color: #ffffff !important;
        z-index: 99999 !important;
        padding-top: 12px !important;
        padding-bottom: 12px !important;
    }
    .stTabs [data-baseweb="tab"] { color: #64748b !important; font-weight: 500; }
    .stTabs [aria-selected="true"] { color: #2563eb !important; border-bottom: 2px solid #2563eb !important; font-weight: 600 !important; }
</style>
""", unsafe_allow_html=True)

# Helper: Apply Plotly Theme
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
# 2. HEADER
# ==============================================================================
st.markdown("<style>div[data-testid='stVerticalBlock'] > div:first-child {margin-top: -30px;}</style>", unsafe_allow_html=True)
st.title("⚙️ Dashboard Analisis Reliabilitas & Sustainable PM")
st.markdown("""
Sistem Pendukung Keputusan Berbasis Distribusi Weibull untuk optimasi penjadwalan *Preventive Maintenance* (PM) konvensional dan *sustainable* pada industri manufaktur.
""")
st.markdown("---")

# ==============================================================================
# 3. SIDEBAR - INPUT PARAMETER & INTERACTIVE CONTROLS
# ==============================================================================
st.sidebar.header("📁 1. Input Data Historis TBF")
data_source = st.sidebar.radio("Sumber Data:", ["Gunakan Data Simulasi", "Upload CSV File"])

if data_source == "Gunakan Data Simulasi":
    st.sidebar.markdown("*Parameter Sintetis Weibull:*")
    sim_beta = st.sidebar.slider("Shape Parameter (True β)", 0.5, 5.0, 2.8, step=0.1)
    sim_eta = st.sidebar.slider("Scale Parameter (True η)", 100, 2000, 600, step=50)
    n_samples = st.sidebar.number_input("Jumlah Sampel Historis", min_value=20, value=100)
    np.random.seed(42)
    # Generate random Weibull data
    data_TBF = weibull_min.rvs(c=sim_beta, scale=sim_eta, size=n_samples)
else:
    uploaded_file = st.sidebar.file_uploader("Upload CSV (Kolom TBF_Jam)", type=["csv"])
    if uploaded_file:
        df_upload = pd.read_csv(uploaded_file)
        data_TBF = df_upload.iloc[:, 0].values
    else:
        st.sidebar.warning("Silakan upload file. Menggunakan data default sementara.")
        data_TBF = weibull_min.rvs(c=2.5, scale=500, size=50)

st.sidebar.header("💰 2. Parameter Biaya & Operasional")
cp = st.sidebar.number_input("Biaya PM Rutin (Cp) [Rp]", value=500000, step=50000)
cf = st.sidebar.number_input("Biaya Breakdown (Cf) [Rp]", value=3500000, step=100000)
mttr = st.sidebar.number_input("Mean Time To Repair (MTTR) [Jam]", value=12.0, step=1.0)

st.sidebar.header("🌱 3. Parameter Sustainability (Emisi/Energi)")
cp_eco = st.sidebar.number_input("Eco-Penalty PM (Limbah/Parts) [Rp]", value=100000, step=10000)
cf_eco = st.sidebar.number_input("Eco-Penalty Breakdown (Emisi) [Rp]", value=1500000, step=50000)
w = st.sidebar.slider("Bobot Sustainability (w)", 0.0, 1.0, 0.5, step=0.1, help="0 = Hanya fokus finansial, 1 = Maksimal pertimbangan emisi")

st.sidebar.header("🎯 4. Target Reliabilitas & Constraint")
target_rel = st.sidebar.slider("Target Reliabilitas Minimum (%)", 50, 99, 80, step=1) / 100.0

# ==============================================================================
# 4. CORE PROCESSING MATHEMATICAL ALGORITHM ENGINE (MLE & COST OPTIMIZATION)
# ==============================================================================
# 1. Estimasi Parameter (MLE)
beta_est, loc_est, eta_est = weibull_min.fit(data_TBF, floc=0)

# 2. Uji Goodness-of-Fit (Kolmogorov-Smirnov)
D_stat, p_value = kstest(data_TBF, 'weibull_min', args=(beta_est, loc_est, eta_est))
is_weibull = p_value > 0.05

# 3. Hitung MTBF & Availability
mtbf = eta_est * gamma(1 + 1/beta_est)
availability = mtbf / (mtbf + mttr)

# 4. Optimasi Cost Berbasis Grid Search
# Membangun array waktu T untuk evaluasi fungsi dan visualisasi
T_arr = np.linspace(1, max(data_TBF)*1.5, 500)
dT = T_arr[1] - T_arr[0]

# Fungsi Reliabilitas R(t), PDF f(t), Hazard h(t)
R_arr = np.exp(- (T_arr / eta_est)**beta_est)
f_arr = (beta_est / eta_est) * (T_arr / eta_est)**(beta_est - 1) * np.exp(-(T_arr / eta_est)**beta_est)
h_arr = (beta_est / eta_est) * (T_arr / eta_est)**(beta_est - 1)

# Mencari waktu dimana Reliabilitas mencapai batas target (T_target)
idx_target = np.abs(R_arr - target_rel).argmin()
T_target = T_arr[idx_target]

# Denominator (Ekspektasi waktu dalam 1 siklus) menggunakan pendekatan integral numerik (Cumulative Sum)
# E[T] = integral R(t) dt
ET_arr = np.cumsum(R_arr) * dT

# 5. Hitung Biaya Konvensional C(T)
C_conv = (cp * R_arr + cf * (1 - R_arr)) / ET_arr
idx_opt_conv = np.argmin(C_conv)
T_opt_conv = T_arr[idx_opt_conv]
Min_C_conv = C_conv[idx_opt_conv]

# 6. Hitung Biaya Sustainable C_total(T)
Total_Cp = cp + (cp_eco * w)
Total_Cf = cf + (cf_eco * w)
C_sust = (Total_Cp * R_arr + Total_Cf * (1 - R_arr)) / ET_arr
idx_opt_sust = np.argmin(C_sust)
T_opt_sust = T_arr[idx_opt_sust]
Min_C_sust = C_sust[idx_opt_sust]

# Aturan Bisnis: T optimal yang disarankan tidak boleh melebihi Target Reliabilitas Operasional
Final_T_Rec = min(T_opt_sust, T_target)
Final_R_Rec = np.exp(- (Final_T_Rec / eta_est)**beta_est)

# ==============================================================================
# 5. DASHBOARD INTERFACE LAYOUT
# ==============================================================================
tab1, tab2, tab3 = st.tabs([
    "📊 Analisis TBF & Model Reliabilitas (MLE)", 
    "📈 Optimasi Interval PM (Konvensional vs Sustainable)", 
    "📝 Ringkasan Eksekutif & Rekomendasi"
])

# ------------------------------------------------------------------------------
# TAB 1: Analisis Historis & Model Reliabilitas
# ------------------------------------------------------------------------------
with tab1:
    st.subheader("1. Estimasi Parameter Weibull (MLE) & Goodness-of-Fit")
    
    col_k1, col_k2, col_k3, col_k4 = st.columns(4)
    with col_k1:
        st.markdown(f'<div class="kpi-card blue"><div class="kpi-title">Shape Parameter (β)</div><div class="kpi-value">{beta_est:.4f}</div></div>', unsafe_allow_html=True)
    with col_k2:
        st.markdown(f'<div class="kpi-card blue"><div class="kpi-title">Scale Parameter (η)</div><div class="kpi-value">{eta_est:.1f} Jam</div></div>', unsafe_allow_html=True)
    with col_k3:
        st.markdown(f'<div class="kpi-card orange"><div class="kpi-title">MTBF</div><div class="kpi-value">{mtbf:.1f} Jam</div></div>', unsafe_allow_html=True)
    with col_k4:
        st.markdown(f'<div class="kpi-card green"><div class="kpi-title">Availability Sistem</div><div class="kpi-value">{availability*100:.2f}%</div></div>', unsafe_allow_html=True)

    # Interpretasi Hasil beta
    interpretasi = ""
    if beta_est > 1:
        interpretasi = f"Nilai **$\\beta = {beta_est:.2f} > 1$** menunjukkan pola **wear-out (keausan)**. Hazard rate akan meningkat seiring waktu operasi. Pemeliharaan terjadwal sangat efektif untuk mencegah kegagalan sistem. Studi kasus nyata pada sistem manufaktur elektronik menunjukkan pola *wear-out* dengan $\\beta > 1$ sebagai *benchmark* historis (sumber rujukan: Number AnalyticsUpnyk)."
    elif abs(beta_est - 1) < 0.1:
        interpretasi = f"Nilai **$\\beta \\approx 1$** menunjukkan kegagalan **acak (random failure)**. Hazard rate konstan."
    else:
        interpretasi = f"Nilai **$\\beta = {beta_est:.2f} < 1$** menunjukkan fenomena **infant mortality**. Kerusakan lebih sering terjadi di awal masa operasi."

    st.info(f"💡 **Interpretasi Pola Kegagalan:**\n\n{interpretasi}")

    # Uji Goodness-of-Fit
    gof_color = "green" if is_weibull else "red"
    gof_status = "DITERIMA" if is_weibull else "DITOLAK"
    st.markdown(f"""
    **Hasil Uji Goodness-of-Fit (Kolmogorov-Smirnov):** 
    P-Value = **{p_value:.4f}** $\\rightarrow$ Distribusi Weibull <strong style="color:{gof_color}">{gof_status}</strong> (Tingkat signifikansi 0.05).
    """)

    st.markdown("---")
    st.subheader("2. Visualisasi Kurva Probabilitas & Reliabilitas")
    
    c1, c2 = st.columns(2)
    with c1:
        fig_rel = go.Figure()
        fig_rel.add_trace(go.Scatter(x=T_arr, y=R_arr, mode='lines', name='Reliability R(t)', line=dict(color='#2563eb', width=3)))
        fig_rel.add_vline(x=T_target, line_dash="dash", line_color="#ef4444", annotation_text=f"Target {target_rel*100}%")
        fig_rel.update_layout(title="Fungsi Reliabilitas $R(t) = e^{-(t/\\eta)^\\beta}$", xaxis_title="Waktu Operasi (Jam)", yaxis_title="Probabilitas Reliabilitas")
        st.plotly_chart(apply_forced_light_theme(fig_rel), use_container_width=True)
        
    with c2:
        fig_haz = go.Figure()
        fig_haz.add_trace(go.Scatter(x=T_arr, y=h_arr, mode='lines', name='Hazard h(t)', line=dict(color='#f59e0b', width=3)))
        fig_haz.update_layout(title="Fungsi Laju Kegagalan / Hazard Rate $h(t)$", xaxis_title="Waktu Operasi (Jam)", yaxis_title="Hazard Rate h(t)")
        st.plotly_chart(apply_forced_light_theme(fig_haz), use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 2: Optimasi Biaya Maintenance Konvensional vs Sustainable
# ------------------------------------------------------------------------------
with tab2:
    st.subheader("3. Pemodelan Age-Replacement Policy & Minimalisasi Biaya")
    st.markdown("""
    Model age-replacement meminimalkan biaya ekspektasi per satuan waktu $C(T)$. Dalam skenario **Sustainable**, 
    $C(T)$ memperhitungkan *penalty cost* ekologis akibat pemborosan komponen (limbah PM) dan lonjakan emisi saat *sudden breakdown*.
    """)
    
    c3, c4 = st.columns(2)
    with c3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Interval PM Optimal (Konvensional)</div><div class="kpi-value">{T_opt_conv:.0f} Jam</div><small>Biaya/Jam: Rp {Min_C_conv:,.0f}</small></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="kpi-card green"><div class="kpi-title">Interval PM Optimal (Sustainable)</div><div class="kpi-value">{T_opt_sust:.0f} Jam</div><small>Biaya (termasuk emisi)/Jam: Rp {Min_C_sust:,.0f} | Bobot w={w}</small></div>', unsafe_allow_html=True)

    fig_cost = go.Figure()
    fig_cost.add_trace(go.Scatter(x=T_arr, y=C_conv, mode='lines', name='C(t) Konvensional', line=dict(color='#64748b', width=2, dash='dot')))
    fig_cost.add_trace(go.Scatter(x=T_arr, y=C_sust, mode='lines', name='C(t) Sustainable', line=dict(color='#10b981', width=3)))
    
    # Mark optimal points
    fig_cost.add_trace(go.Scatter(x=[T_opt_conv], y=[Min_C_conv], mode='markers', name='T* Konvensional', marker=dict(color='gray', size=10)))
    fig_cost.add_trace(go.Scatter(x=[T_opt_sust], y=[Min_C_sust], mode='markers', name='T* Sustainable', marker=dict(color='green', size=10)))
    
    fig_cost.update_layout(title="Perbandingan Evaluasi Biaya Ekspektasi per Satuan Waktu: $C(T)$", xaxis_title="Interval Waktu PM, T (Jam)", yaxis_title="Cost per Unit Time (Rp/Jam)")
    st.plotly_chart(apply_forced_light_theme(fig_cost, is_cost_chart=True), use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 3: Ringkasan Eksekutif
# ------------------------------------------------------------------------------
with tab3:
    st.subheader("4. Rekomendasi Interval Tindakan Berkelanjutan")
    
    st.markdown(f"""
    <div class="recommendation-box">
        <h4>Skenario Keputusan Final:</h4>
        <p>
            Berdasarkan target reliabilitas minimum sebesar <b>{target_rel*100}%</b> (dicapai pada {T_target:.0f} jam) 
            dan optimasi biaya berwawasan lingkungan (Sustainable Model), sistem merekomendasikan:
        </p>
        <ul style="font-size: 16px;">
            <li>Waktu eksekusi Preventive Maintenance dilakukan setiap: <b>{Final_T_Rec:.0f} Jam Operasi</b></li>
            <li>Estimasi keandalan (Reliability) mesin pada saat jadwal PM: <b>{Final_R_Rec*100:.1f}%</b></li>
        </ul>
        <p><i>*Catatan: Interval ini dipilih karena sistem secara otomatis membatasi jadwal agar tidak melewati batas Target Reliabilitas yang ditetapkan manajemen (Safety Constraint).</i></p>
    </div>
    <br>
    """, unsafe_allow_html=True)
    
    st.subheader("5. Matriks Perbandingan Efisiensi & Emisi (Per Siklus Operasi)")
    
    # Menghitung estimasi emisi per siklus T berdasarkan interval pilihan
    def hitung_estimasi_siklus(T_val):
        R_val = np.exp(- (T_val / eta_est)**beta_est)
        # Expected Breakdown probability dalam siklus T adalah 1 - R_val
        Exp_Breakdown = 1 - R_val
        # Komponen murni biaya lingkungan per siklus ekspektasi
        Emisi_Cost = (cp_eco * R_val) + (cf_eco * Exp_Breakdown)
        Finansial_Cost = (cp * R_val) + (cf * Exp_Breakdown)
        return Finansial_Cost, Emisi_Cost

    fin_conv, em_conv = hitung_estimasi_siklus(T_opt_conv)
    fin_sust, em_sust = hitung_estimasi_siklus(Final_T_Rec)

    df_compare = pd.DataFrame({
        "Skenario": ["Konvensional", "Sustainable", "Konvensional", "Sustainable"],
        "Kategori": ["Biaya Operasional Dasar", "Biaya Operasional Dasar", "Estimasi Penalti Ekologis/Emisi", "Estimasi Penalti Ekologis/Emisi"],
        "Nilai Ekspektasi (Rp)": [fin_conv, fin_sust, em_conv, em_sust]
    })

    fig_bar = px.bar(df_compare, x="Skenario", y="Nilai Ekspektasi (Rp)", color="Kategori", 
                     title="Perbandingan Ekspektasi Finansial vs Beban Ekologis per Siklus",
                     color_discrete_sequence=["#3b82f6", "#ef4444"])
    
    st.plotly_chart(apply_forced_light_theme(fig_bar, is_cost_chart=True), use_container_width=True)
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from scipy.stats import weibull_min, kstest
from scipy.special import gamma
from scipy.integrate import cumulative_trapezoid
import io
import datetime

# ==============================================================================
# 1. PAGE CONFIGURATION & THEME
# ==============================================================================
st.set_page_config(
    page_title="Dashboard Preventive Maintenance",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS terbatas HANYA untuk komponen spesifik agar tidak merusak UI Sidebar
st.markdown("""
<style>
    /* Styling khusus untuk Kartu Metrik/KPI */
    .metric-card {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        border: 1px solid #e2e8f0;
        position: relative;
        overflow: hidden;
        margin-bottom: 15px;
    }
    .metric-card.blue { border-left: 5px solid #2563eb; }
    .metric-card.green { border-left: 5px solid #10b981; }
    .metric-card.orange { border-left: 5px solid #f59e0b; }
    .metric-card.red { border-left: 5px solid #ef4444; }
    
    .metric-title { font-size: 13px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
    .metric-value { font-size: 24px; color: #0f172a; font-weight: 700; margin-top: 5px; }
    .metric-desc { font-size: 12px; color: #475569; margin-top: 5px; font-weight: 500; }
    
    /* Styling Info Box */
    .info-box {
        background-color: #f8fafc;
        border-left: 4px solid #3b82f6;
        padding: 15px 20px;
        border-radius: 4px;
        margin-bottom: 20px;
    }
    
    .recommendation-box {
        background-color: #ecfdf5;
        border: 1px solid #a7f3d0;
        border-radius: 8px;
        padding: 25px;
        margin-top: 20px;
        margin-bottom: 20px;
    }
    
    /* Styling Tabel Template */
    .template-table { width: 100%; border-collapse: collapse; margin-top: 10px; background-color: white; }
    .template-table th { background-color: #f1f5f9; padding: 8px; border: 1px solid #cbd5e1; font-size: 14px; text-align: left; }
    .template-table td { padding: 8px; border: 1px solid #cbd5e1; font-size: 14px; color: #333; }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. HEADER & IDENTITAS
# ==============================================================================
# Menggunakan URL Wikipedia yang lebih stabil, ditambah penanganan error gambar
logo_gunadarma = "https://upload.wikimedia.org/wikipedia/id/thumb/4/4f/Logo_Universitas_Gunadarma.png/250px-Logo_Universitas_Gunadarma.png"
logo_lab = "https://cdn-icons-png.flaticon.com/512/1903/1903155.png"

st.markdown(f"""
<div style="display: flex; align-items: center; gap: 20px; margin-bottom: 20px;">
    <div style="display: flex; gap: 10px; align-items: center;">
        <img src="{logo_gunadarma}" onerror="this.style.display='none'" style="height: 60px; width: auto; object-fit: contain;" alt="Logo Gunadarma">
        <img src="{logo_lab}" onerror="this.style.display='none'" style="height: 50px; width: auto; object-fit: contain; border-radius: 50%;" alt="Logo Lab">
    </div>
    <div>
        <h1 style="margin: 0; font-size: 28px; color: #1e293b;">Sistem Keputusan Perawatan Mesin (Sustainable PM)</h1>
        <p style="margin: 5px 0 0 0; color: #64748b; font-size: 15px;">
            Optimasi Jadwal Perawatan Mesin Berbasis Keandalan dan Efisiensi Biaya + Ekologi
        </p>
    </div>
</div>
<hr style="margin-top: 0; margin-bottom: 30px;">
""", unsafe_allow_html=True)

# ==============================================================================
# 3. MANAJEMEN DATA & UPLOAD EXCEL
# ==============================================================================
# Default Data (Histori Waktu Antar Kerusakan / Time Between Failures)
default_tbf = [450, 520, 610, 480, 750, 590, 680, 540, 490, 810, 600, 720, 550, 670, 710]

if "data_tbf" not in st.session_state:
    st.session_state.data_tbf = default_tbf.copy()

with st.expander("📂 PANDUAN & IMPORT DATA HISTORI KERUSAKAN (EXCEL)", expanded=False):
    st.markdown("""
    <div class="info-box">
        <h4 style="margin-top:0;">Cara Menggunakan Fitur Upload:</h4>
        <p>Unggah data histori waktu hidup mesin Anda (jarak waktu dari mesin menyala hingga terjadi kerusakan). File Excel Anda harus memiliki kolom dengan nama <b>TBF (Jam)</b> seperti contoh berikut:</p>
        <table class="template-table">
            <tr><th>Kode Mesin</th><th>TBF (Jam)</th><th>Keterangan</th></tr>
            <tr><td>M-001</td><td>450</td><td>Mesin Berhenti Beroperasi (Breakdown)</td></tr>
            <tr><td>M-002</td><td>520</td><td>Mesin Berhenti Beroperasi (Breakdown)</td></tr>
        </table>
    </div>
    """, unsafe_allow_html=True)
    
    # Generate Template Excel to Download
    template_df = pd.DataFrame({
        "Kode Mesin": [f"M-{i+1:03d}" for i in range(len(default_tbf))],
        "TBF (Jam)": default_tbf,
        "Keterangan": ["Breakdown"] * len(default_tbf)
    })
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        template_df.to_excel(writer, index=False, sheet_name='Data Kerusakan')
    
    col_dl, col_up = st.columns([1, 2])
    with col_dl:
        st.download_button(
            label="📥 Download Template Excel",
            data=buffer.getvalue(),
            file_name="Template_Data_Kerusakan.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    
    with col_up:
        uploaded_file = st.file_uploader("Unggah File Excel Anda di sini:", type=["xlsx", "xls"], label_visibility="collapsed")
        
    if uploaded_file:
        try:
            df_upload = pd.read_excel(uploaded_file)
            if "TBF (Jam)" in df_upload.columns:
                cleaned_data = pd.to_numeric(df_upload["TBF (Jam)"], errors='coerce').dropna().tolist()
                if len(cleaned_data) < 3:
                    st.error("❌ Data terlalu sedikit. Minimal diperlukan 3 baris data kerusakan untuk analisis yang akurat.")
                else:
                    st.session_state.data_tbf = cleaned_data
                    st.success(f"✅ Berhasil memuat {len(cleaned_data)} data kerusakan mesin!")
            else:
                st.error("❌ Gagal membaca: Pastikan file Excel Anda memiliki kolom bernama persis 'TBF (Jam)'.")
        except Exception as e:
            st.error(f"❌ Terjadi kesalahan sistem saat membaca file: {e}")

# ==============================================================================
# 4. SIDEBAR - PANEL PENGATURAN & PARAMETER
# ==============================================================================
st.sidebar.title("🎛️ Panel Parameter")

st.sidebar.markdown("---")
st.sidebar.subheader("1. Data Waktu Kerusakan (Jam)")
st.sidebar.caption("Anda dapat mengedit nilai data secara manual di bawah ini:")
df_editor = pd.DataFrame({"Waktu Operasi (Jam)": st.session_state.data_tbf})
edited_df = st.sidebar.data_editor(df_editor, hide_index=True, use_container_width=True, num_rows="dynamic")
# Pastikan tidak ada data negatif atau nol
raw_data = edited_df["Waktu Operasi (Jam)"].values
valid_data_tbf = [val for val in raw_data if val > 0]

st.sidebar.markdown("---")
st.sidebar.subheader("2. Biaya Perawatan & Perbaikan")
biaya_pm = st.sidebar.number_input("Biaya Perawatan Rutin (PM) [Rp]", value=500000, step=50000, 
                                   help="Biaya yang dikeluarkan saat melakukan pengecekan rutin sebelum mesin rusak.")
biaya_breakdown = st.sidebar.number_input("Biaya Turun Mesin (Breakdown) [Rp]", value=3500000, step=100000, 
                                          help="Total kerugian (sparepart mahal, produksi terhenti) saat mesin tiba-tiba rusak.")
waktu_perbaikan = st.sidebar.number_input("Rata-rata Waktu Perbaikan (Jam)", value=12.0, step=1.0)

st.sidebar.markdown("---")
st.sidebar.subheader("3. Dampak Ekologis (Sustainability)")
st.sidebar.caption("Estimasi denda/kerugian lingkungan akibat penggantian oli, limbah, atau emisi terbuang.")
eco_pm = st.sidebar.number_input("Biaya Emisi/Limbah Perawatan [Rp]", value=100000, step=10000)
eco_breakdown = st.sidebar.number_input("Biaya Emisi/Limbah Breakdown [Rp]", value=1500000, step=50000)

bobot_sustainability = st.sidebar.slider(
    "Prioritas Kepedulian Lingkungan (%)", 
    min_value=0, max_value=100, value=50, step=10,
    help="0% = Hanya fokus hemat uang. 100% = Sangat peduli dampak lingkungan."
) / 100.0

st.sidebar.markdown("---")
st.sidebar.subheader("4. Standar Keamanan")
target_keandalan = st.sidebar.slider(
    "Batas Aman Keandalan Mesin (%)", 
    min_value=50, max_value=99, value=80, step=1,
    help="Mesin tidak boleh beroperasi jika probabilitas keberhasilannya turun di bawah persentase ini."
) / 100.0

# ==============================================================================
# 5. LOGIKA BISNIS & KALKULASI ALGORITMA
# ==============================================================================
# Keamanan sistem jika data kosong
if len(valid_data_tbf) < 3:
    st.error("Data Waktu Operasi terlalu sedikit atau tidak valid. Harap masukkan angka positif pada sidebar.")
    st.stop()

# 5.1 Ekstraksi Pola Data (Kalkulasi Distribusi Kinerja Mesin)
pola_kerusakan, _, faktor_umur = weibull_min.fit(valid_data_tbf, floc=0)

# 5.2 Rata-rata Umur Mesin (MTBF)
mtbf = faktor_umur * gamma(1 + 1/pola_kerusakan)
ketersediaan_mesin = mtbf / (mtbf + waktu_perbaikan)

# 5.3 Proyeksi Keandalan & Waktu 
# Membuat rentang waktu simulasi dari 1 jam hingga 2.5 kali umur maksimum data
waktu_simulasi = np.linspace(1, max(valid_data_tbf) * 2.5, 1000)

# Probabilitas mesin masih bertahan hidup (Reliability)
peluang_bertahan = np.exp(- (waktu_simulasi / faktor_umur)**pola_kerusakan)

# Potensi mesin akan rusak di waktu tertentu (Hazard / Laju Kerusakan)
laju_potensi_rusak = (pola_kerusakan / faktor_umur) * (waktu_simulasi / faktor_umur)**(pola_kerusakan - 1)

# Ekspektasi panjang siklus mesin (Area di bawah kurva probabilitas)
ekspektasi_umur_siklus = cumulative_trapezoid(peluang_bertahan, waktu_simulasi, initial=0)
ekspektasi_umur_siklus[ekspektasi_umur_siklus == 0] = 1e-10 # Mencegah error pembagian nol

# Titik Waktu Batas Aman dari Slider Standar Keamanan
indeks_batas_aman = np.abs(peluang_bertahan - target_keandalan).argmin()
waktu_batas_aman = waktu_simulasi[indeks_batas_aman]

# 5.4 Algoritma Optimasi Biaya per Jam Operasi
# Menghitung Total Beban Biaya (Uang Tunai + Valuasi Dampak Lingkungan)
beban_pm_total = biaya_pm + (eco_pm * bobot_sustainability)
beban_breakdown_total = biaya_breakdown + (eco_breakdown * bobot_sustainability)

# Fungsi Ekspektasi Biaya Konvensional (Hanya Uang)
# Rumus: (Biaya PM * Peluang Bertahan + Biaya Rusak * Peluang Rusak) / Ekspektasi Panjang Umur
biaya_jam_konvensional = (biaya_pm * peluang_bertahan + biaya_breakdown * (1 - peluang_bertahan)) / ekspektasi_umur_siklus

# Fungsi Ekspektasi Biaya Sustainable (Uang + Lingkungan)
biaya_jam_sustainable = (beban_pm_total * peluang_bertahan + beban_breakdown_total * (1 - peluang_bertahan)) / ekspektasi_umur_siklus

# Mencari Titik Paling Murah / Efisien
idx_opt_konv = np.argmin(biaya_jam_konvensional)
jadwal_opt_konv = waktu_simulasi[idx_opt_konv]
harga_opt_konv = biaya_jam_konvensional[idx_opt_konv]

idx_opt_sust = np.argmin(biaya_jam_sustainable)
jadwal_opt_sust = waktu_simulasi[idx_opt_sust]
harga_opt_sust = biaya_jam_sustainable[idx_opt_sust]

# Aturan Keputusan Final: Ambil yang sustainable, tapi JANGAN melewati batas aman perusahaan
jadwal_rekomendasi_final = min(jadwal_opt_sust, waktu_batas_aman)
peluang_keandalan_final = np.exp(- (jadwal_rekomendasi_final / faktor_umur)**pola_kerusakan)

# ==============================================================================
# 6. PENYUSUNAN TAMPILAN DASHBOARD
# ==============================================================================
tab_profiling, tab_analisis, tab_optimasi, tab_laporan = st.tabs([
    "📊 Profiling Data Mesin", 
    "🔍 Diagnostik Kesehatan Mesin", 
    "📈 Simulasi Jadwal Optimal", 
    "📑 Rekomendasi Eksekutif"
])

# ------------------------------------------------------------------------------
# TAB 1: PROFILING DATA (EXPLORATORY DATA ANALYSIS)
# ------------------------------------------------------------------------------
with tab_profiling:
    st.subheader("Ringkasan Historis Kinerja Mesin")
    st.markdown("Visualisasi ini membantu Anda melihat sebaran waktu operasional mesin sebelum mengalami kerusakan pada masa lalu.")
    
    col_hist, col_box = st.columns(2)
    
    with col_hist:
        fig_hist = px.histogram(
            valid_data_tbf, nbins=10, 
            title="Distribusi Waktu Terjadinya Kerusakan",
            labels={'value': 'Waktu Operasi Hingga Rusak (Jam)'},
            color_discrete_sequence=['#3b82f6']
        )
        fig_hist.update_layout(showlegend=False, xaxis_title="Waktu Operasi (Jam)", yaxis_title="Jumlah Kejadian (Frekuensi)")
        st.plotly_chart(fig_hist, use_container_width=True)
        
    with col_box:
        fig_box = px.box(
            valid_data_tbf, 
            title="Penyebaran Data & Deteksi Anomali",
            labels={'value': 'Waktu Operasi (Jam)'},
            color_discrete_sequence=['#10b981']
        )
        fig_box.update_layout(xaxis_title="Penyebaran Historis", yaxis_title="Waktu Operasi (Jam)")
        st.plotly_chart(fig_box, use_container_width=True)
        
    st.markdown("""
    **Insight Singkat:**
    *   **Histogram:** Menunjukkan durasi mana yang paling sering menjadi titik kerusakan mesin Anda.
    *   **Boxplot:** Membantu mendeteksi apakah ada mesin yang rusak sangat cepat atau bertahan sangat lama (titik anomali/outlier).
    """)

# ------------------------------------------------------------------------------
# TAB 2: DIAGNOSTIK KESEHATAN MESIN (Weibull Analysis)
# ------------------------------------------------------------------------------
with tab_analisis:
    st.subheader("Karakteristik Ketahanan Mesin Saat Ini")
    
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="metric-card blue"><div class="metric-title">Tingkat / Pola Keausan</div><div class="metric-value">{pola_kerusakan:.2f}</div><div class="metric-desc">Indikator tren kerusakan mesin</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="metric-card blue"><div class="metric-title">Skala Faktor Umur</div><div class="metric-value">{faktor_umur:.0f} Jam</div><div class="metric-desc">Titik ukur rentang hidup</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="metric-card orange"><div class="metric-title">Rata-rata Waktu Hidup (MTBF)</div><div class="metric-value">{mtbf:.0f} Jam</div><div class="metric-desc">Sebelum mesin mati total</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="metric-card green"><div class="metric-title">Ketersediaan Sistem (Uptime)</div><div class="metric-value">{ketersediaan_mesin*100:.1f}%</div><div class="metric-desc">Persentase mesin siap pakai</div></div>', unsafe_allow_html=True)

    # Logika Penerjemahan Pola Keausan ke Bahasa Bisnis
    st.markdown("### Kesimpulan Diagnosis Mesin:")
    if pola_kerusakan > 1.1:
        pesan_diagnosis = f"Mesin Anda saat ini memiliki skor keausan **{pola_kerusakan:.2f} (Lebih dari 1)**. Ini berarti **mesin mengalami proses penuaan dan keausan**. Semakin lama mesin menyala, semakin besar peluangnya untuk tiba-tiba rusak. **Perawatan terjadwal (Preventive Maintenance) sangat direkomendasikan** untuk mencegah berhentinya produksi."
        warna_alert = "info"
    elif 0.9 <= pola_kerusakan <= 1.1:
        pesan_diagnosis = f"Mesin Anda saat ini memiliki skor keausan **{pola_kerusakan:.2f} (Mendekati 1)**. Ini berarti **kerusakan bersifat acak (Random Failure)**. Komponen bisa rusak kapan saja tanpa tanda-tanda penuaan fisik. Fokuslah pada penyediaan stok cadangan komponen (sparepart)."
        warna_alert = "warning"
    else:
        pesan_diagnosis = f"Mesin Anda saat ini memiliki skor keausan **{pola_kerusakan:.2f} (Kurang dari 1)**. Ini berarti ada fenomena **kegagalan dini (Infant Mortality)**. Kerusakan sering terjadi di awal saat mesin baru dinyalakan atau selesai diperbaiki (mungkin akibat kualitas teknisi, salah pasang, atau komponen cacat pabrik)."
        warna_alert = "error"

    if warna_alert == "info":
        st.info(pesan_diagnosis)
    elif warna_alert == "warning":
        st.warning(pesan_diagnosis)
    else:
        st.error(pesan_diagnosis)

    st.markdown("---")
    st.markdown("### Grafik Penurunan Kesehatan Mesin Seiring Waktu")
    
    c_kiri, c_kanan = st.columns(2)
    with c_kiri:
        fig_reliabilitas = go.Figure()
        fig_reliabilitas.add_trace(go.Scatter(x=waktu_simulasi, y=peluang_bertahan, mode='lines', name='Peluang Mesin Sehat', line=dict(color='#2563eb', width=3)))
        fig_reliabilitas.add_vline(x=waktu_batas_aman, line_dash="dash", line_color="#ef4444", annotation_text=f"Batas Minimum ({target_keandalan*100}%)", annotation_position="bottom right")
        fig_reliabilitas.update_layout(
            title="Kurva Peluang Mesin Tidak Rusak", 
            xaxis_title="Lama Waktu Mesin Menyala (Jam)", 
            yaxis_title="Persentase Peluang Mesin Sehat (%)",
            yaxis=dict(tickformat=".0%")
        )
        st.plotly_chart(fig_reliabilitas, use_container_width=True)
        
    with c_kanan:
        fig_hazard = go.Figure()
        fig_hazard.add_trace(go.Scatter(x=waktu_simulasi, y=laju_potensi_rusak, mode='lines', name='Potensi Rusak', line=dict(color='#f59e0b', width=3)))
        fig_hazard.update_layout(
            title="Grafik Lonjakan Potensi Kerusakan", 
            xaxis_title="Lama Waktu Mesin Menyala (Jam)", 
            yaxis_title="Tingkat Risiko Tiba-tiba Mati"
        )
        st.plotly_chart(fig_hazard, use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 3: SIMULASI JADWAL OPTIMAL (BIAYA & LINGKUNGAN)
# ------------------------------------------------------------------------------
with tab_optimasi:
    st.subheader("Pencarian Jadwal Perawatan Paling Murah & Ramah Lingkungan")
    st.markdown("Grafik ini menunjukkan perbandingan kerugian finansial jika Anda menggunakan metode konvensional (mengabaikan lingkungan) vs metode *Sustainable*.")
    
    v1, v2 = st.columns(2)
    with v1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Jadwal Target Tradisional (Hanya Finansial)</div><div class="metric-value">Lakukan Servis Tiap {jadwal_opt_konv:.0f} Jam</div><div class="metric-desc">Total Kerugian Operasional: Rp {harga_opt_konv:,.0f} per Jam</div></div>', unsafe_allow_html=True)
    with v2:
        st.markdown(f'<div class="metric-card green"><div class="metric-title">Jadwal Target Sustainable (Finansial + Ekologis)</div><div class="metric-value">Lakukan Servis Tiap {jadwal_opt_sust:.0f} Jam</div><div class="metric-desc">Total Kerugian Termasuk Valuasi Lingkungan: Rp {harga_opt_sust:,.0f} per Jam</div></div>', unsafe_allow_html=True)

    fig_biaya = go.Figure()
    fig_biaya.add_trace(go.Scatter(x=waktu_simulasi, y=biaya_jam_konvensional, mode='lines', name='Kurva Biaya Konvensional', line=dict(color='#94a3b8', width=2, dash='dot')))
    fig_biaya.add_trace(go.Scatter(x=waktu_simulasi, y=biaya_jam_sustainable, mode='lines', name='Kurva Beban Total (Sustainable)', line=dict(color='#10b981', width=3)))
    
    # Menandai titik terendah (Paling optimal/murah)
    fig_biaya.add_trace(go.Scatter(x=[jadwal_opt_konv], y=[harga_opt_konv], mode='markers+text', name='Titik Termurah Tradisional', marker=dict(color='#64748b', size=10), text=["Rp "+f"{harga_opt_konv:,.0f}"], textposition="bottom center"))
    fig_biaya.add_trace(go.Scatter(x=[jadwal_opt_sust], y=[harga_opt_sust], mode='markers+text', name='Titik Paling Ideal Sustainable', marker=dict(color='#059669', size=12), text=["Rp "+f"{harga_opt_sust:,.0f}"], textposition="top center"))
    
    # Membatasi tampilan sumbu Y agar tidak terdistorsi di awal waktu (saat grafik biayanya tak terhingga)
    batas_bawah = min(harga_opt_konv, harga_opt_sust) * 0.8
    batas_atas = min(harga_opt_konv, harga_opt_sust) * 3
    
    fig_biaya.update_layout(
        title="Simulasi Tekanan Biaya Operasional Berdasarkan Kapan Anda Memilih Servis", 
        xaxis_title="Jadwal Keputusan Melakukan Perawatan Mesin (Jam)", 
        yaxis_title="Tingkat Kerugian Finansial per Jam (Rp)",
        yaxis_range=[batas_bawah, batas_atas],
        yaxis=dict(tickprefix="Rp ")
    )
    st.plotly_chart(fig_biaya, use_container_width=True)

# ------------------------------------------------------------------------------
# TAB 4: LAPORAN & REKOMENDASI EKSEKUTIF
# ------------------------------------------------------------------------------
with tab_laporan:
    st.markdown(f"""
    <div class="recommendation-box">
        <h3 style="margin-top:0; color:#065f46;">Keputusan Strategis Perawatan Mesin Final</h3>
        <p style="font-size: 16px; color: #047857;">Sistem telah mempertimbangkan optimalisasi biaya, dampak lingkungan, serta tidak melanggar standar keselamatan perusahaan Anda ({target_keandalan*100}% peluang sehat).</p>
        
        <div style="background-color: white; padding: 15px; border-radius: 5px; border-left: 5px solid #10b981; margin: 15px 0;">
            <p style="margin:0; font-size: 14px; color: #64748b;">Rekomendasi Waktu Hentikan Mesin untuk Servis:</p>
            <h2 style="margin:5px 0; color: #0f172a;">Setiap {jadwal_rekomendasi_final:.0f} Jam Operasi</h2>
        </div>
        
        <ul style="font-size: 15px; color: #374151; line-height: 1.6;">
            <li>Pada titik waktu ini, mesin Anda diprediksi memiliki kondisi keandalan sebesar <b>{peluang_keandalan_final*100:.1f}%</b>.</li>
            <li>Jika Anda menunda lebih dari <b>{jadwal_rekomendasi_final:.0f} Jam</b>, maka potensi mesin mati mendadak akan sangat merugikan pabrik Anda secara finansial dan lingkungan.</li>
            <li>Rata-rata panjang siklus produksi aman Anda sebelum perbaikan adalah <b>{ekspektasi_umur_siklus[np.abs(waktu_simulasi - jadwal_rekomendasi_final).argmin()]:.1f} Jam</b> per periode.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("Rincian Alokasi Dana per Siklus (Estimasi)")
    
    # Fungsi sederhana untuk membedah beban biaya pada satu titik keputusan
    def hitung_breakdown_biaya(waktu_keputusan):
        prob_sehat = np.exp(- (waktu_keputusan / faktor_umur)**pola_kerusakan)
        prob_rusak_tiba_tiba = 1 - prob_sehat
        uang_tunai = (biaya_pm * prob_sehat) + (biaya_breakdown * prob_rusak_tiba_tiba)
        beban_lingkungan = (eco_pm * prob_sehat) + (eco_breakdown * prob_rusak_tiba_tiba)
        return uang_tunai, beban_lingkungan

    # Bandingkan jika kita pakai cara lama vs cara baru yang direkomendasikan sistem
    uang_lama, ling_lama = hitung_breakdown_biaya(jadwal_opt_konv)
    uang_baru, ling_baru = hitung_breakdown_biaya(jadwal_rekomendasi_final)

    df_komparasi = pd.DataFrame({
        "Strategi Perusahaan": ["Strategi Lama", "Strategi Baru (Sistem)", "Strategi Lama", "Strategi Baru (Sistem)"],
        "Jenis Pengeluaran": ["Uang Keluar Operasional", "Uang Keluar Operasional", "Taksiran Denda Emisi/Limbah", "Taksiran Denda Emisi/Limbah"],
        "Nominal (Rp)": [uang_lama, uang_baru, ling_lama, ling_baru]
    })

    fig_bar = px.bar(
        df_komparasi, x="Strategi Perusahaan", y="Nominal (Rp)", color="Jenis Pengeluaran", 
        title="Perbandingan Proporsi Kerugian dalam 1 Siklus Operasional",
        color_discrete_sequence=["#3b82f6", "#ef4444"], barmode="group",
        text_auto=".2s"
    )
    fig_bar.update_traces(textposition='outside')
    st.plotly_chart(fig_bar, use_container_width=True)

    # --------------------------------------------------------------------------
    # FITUR EXPORT LAPORAN
    # --------------------------------------------------------------------------
    st.markdown("---")
    st.subheader("Cetak Laporan Hasil Analisis")
    
    laporan_teks = f"""LAPORAN SISTEM KEPUTUSAN SUSTAINABLE PREVENTIVE MAINTENANCE
Tanggal Dibuat: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

1. PROFIL DATA MESIN
- Jumlah Data Kerusakan: {len(valid_data_tbf)} histori
- Rata-rata Umur Mesin (MTBF): {mtbf:.1f} Jam

2. DIAGNOSTIK
- Nilai Pola Kerusakan: {pola_kerusakan:.2f}
- Status: {'Keausan Normal, Perlu PM Rutin' if pola_kerusakan > 1.1 else 'Kerusakan Acak' if pola_kerusakan >= 0.9 else 'Kerusakan Dini, Periksa Perakitan'}

3. REKOMENDASI FINAL MANAJEMEN
- Lakukan penghentian produksi untuk Maintenance setiap: {jadwal_rekomendasi_final:.0f} JAM OPERASI.
- Tingkat keselamatan mesin pada jadwal tersebut: {peluang_keandalan_final*100:.1f} %

-- Analisis Selesai --
"""
    
    st.download_button(
        label="📄 Unduh Ringkasan Laporan (.txt)",
        data=laporan_teks,
        file_name=f"Laporan_Maintenance_{datetime.datetime.now().strftime('%Y%m%d')}.txt",
        mime="text/plain",
        use_container_width=True
    )

    st.caption("Aplikasi ini menggunakan algoritma optimasi umur penggantian terencana (Age-Replacement Strategy) yang mengintegrasikan valuasi kerugian lingkungan.")
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Kalkulator Aktuaria Asuransi Pendidikan",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FUNGSI BASELINE MORTALITAS (Orang Tua / Payor) ---
# Menggunakan model Gompertz-Makeham sederhana untuk menghitung peluang bertahan hidup orang tua
def hitung_mortalitas_orang_tua(usia_maks=100, a=0.0005, b=0.0001, c=1.10):
    usia = np.arange(0, usia_maks + 1)
    qx = a + b * (c ** usia)
    qx = np.clip(qx, 0, 1)
    px = 1 - qx
    
    lx = [100000]
    for i in range(len(px) - 1):
        lx.append(lx[-1] * px[i])
        
    df = pd.DataFrame({
        "Usia (x)": usia,
        "qx": qx,
        "px": px,
        "lx": lx
    })
    return df

# Memuat data mortalitas dasar
df_mortalitas = hitung_mortalitas_orang_tua()

# --- SIDEBAR NAVIGASI & ASUMSI GLOBAL ---
st.sidebar.image("https://img.icons8.com/external-flatart-icons-flat-flatarticons/128/external-education-online-learning-flatart-icons-flat-flatarticons.png", width=80)
st.sidebar.title("Asuransi Pendidikan")
st.sidebar.markdown("*Sistem Aktuaria Dwiguna (Endowment)*")

menu = st.sidebar.radio(
    "Pilih Fitur:",
    [
        "🏠 Panduan & Konsep",
        "🧮 Kalkulator Premi Anak & Orang Tua",
        "📅 Simulasi Pencairan Tahapan",
        "🛡️ Proyeksi Cadangan Dana"
    ]
)

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Asumsi Keuangan")
suku_bunga = st.sidebar.slider("Suku Bunga Tahunan Acuan (i)", 1.0, 10.0, 6.0, 0.5) / 100
v = 1 / (1 + suku_bunga) # Faktor diskonto

# =====================================================================
# FITUR 1: PANDUAN & KONSEP
# =====================================================================
if menu == "🏠 Panduan & Konsep":
    st.title("🎓 Portal Aktuaria: Asuransi Pendidikan Dwiguna")
    st.write("""
    Selamat datang di aplikasi simulasi aktuaria khusus **Asuransi Pendidikan**. 
    Produk ini dirancang menggunakan basis **Asuransi Jiwa Dwiguna (Endowment)**, yang menggabungkan unsur perlindungan jiwa dan tabungan terencana.
    """)
    
    st.markdown("### 🔍 Bagaimana Cara Kerjanya?")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info("""
        **1. Manfaat Tahapan Pendidikan (Pasti Cair)**
        Dana akan dicairkan secara bertahap kepada anak saat mereka mencapai usia sekolah tertentu:
        *   **Masuk SD** (Usia 6 Tahun)
        *   **Masuk SMP** (Usia 12 Tahun)
        *   **Masuk SMA** (Usia 15 Tahun)
        *   **Masuk Kuliah** (Usia 18 Tahun)
        """)
    with col2:
        st.success("""
        **2. Manfaat Proteksi Jiwa (Payor Benefit)**
        Jika Orang Tua (tertanggung utama) meninggal dunia dalam masa pembayaran premi:
        *   Kewajiban membayar premi tahunan langsung **dihentikan (Bebas Premi)**.
        *   Dana tahapan sekolah anak di masa depan **tetap dijamin cair** sesuai jadwal.
        """)

    st.markdown("### 🧮 Formula Matematika Aktuaria Utama")
    st.write("Aplikasi ini menghitung nilai sekarang dari seluruh pengeluaran manfaat di masa depan menggunakan rumus:")
    st.latex(r"NSP = \sum_{t=1}^{n} v^t \cdot {}_t p_x \cdot q_{x+t-1} \cdot UP + \sum_{k \in \text{Tahun Tahapan}} v^k \cdot {}_k p_x \cdot \text{Dana Tahapan}_k")
    st.caption("Keterangan: $NSP$ = Net Single Premium, $v$ = Faktor diskonto suku bunga, ${}_t p_x$ = Peluang orang tua tetap hidup hingga tahun ke-$t$.")


# =====================================================================
# FITUR 2: KALKULATOR PREMI ANAK & ORANG TUA
# =====================================================================
elif menu == "🧮 Kalkulator Premi Anak & Orang Tua":
    st.title("🧮 Kalkulator Premi Bersih Asuransi Pendidikan")
    st.write("Hitung kontribusi premi tahunan yang adil berdasarkan usia orang tua dan usia anak saat ini.")
    
    col_in1, col_in2 = st.columns(2)
    with col_in1:
        usia_orang_tua = st.number_input("Usia Orang Tua / Pembayar Premi (Tahun)", min_value=20, max_value=55, value=30)
        usia_anak = st.number_input("Usia Anak Saat Ini (Tahun)", min_value=0, max_value=5, value=1)
    with col_in2:
        target_dana_kuliah = st.number_input("Target Total Dana Pendidikan Kuliah (Rp)", min_value=25_000_000, value=150_000_000, step=10_000_000)
    
    # Skema Pembagian Porsi Dana Tahapan (Total 100% dari Target Dana)
    # SD (10%), SMP (15%), SMA (25%), Kuliah (50%)
    tahapan_sd = target_dana_kuliah * 0.10
    tahapan_smp = target_dana_kuliah * 0.15
    tahapan_sma = target_dana_kuliah * 0.25
    tahapan_kuliah = target_dana_kuliah * 0.50
    
    # Menghitung Jangka Waktu sampai Anak Lulus Kuliah (Asumsi Kuliah selesai di usia 22 tahun)
    tenor = 22 - usia_anak
    
    # PERHITUNGAN AKTUARIA:
    # 1. Menghitung Present Value (PV) dari Manfaat Pendidikan (Tahapan)
    pv_manfaat = 0
    tpx = 1.0
    
    for t in range(1, tenor + 1):
        usia_anak_t = usia_anak + t
        usia_ot_t = usia_orang_tua + t - 1
        
        # Cari peluang meninggal orang tua pada tahun berjalan untuk santunan jiwa
        qx_ot = df_mortalitas.loc[usia_ot_t, "qx"]
        
        # Payout Benefit Tahapan di usia tertentu anak
        benefit_cair = 0
        if usia_anak_t == 6:
            benefit_cair = tahapan_sd
        elif usia_anak_t == 12:
            benefit_cair = tahapan_smp
        elif usia_anak_t == 15:
            benefit_cair = tahapan_sma
        elif usia_anak_t == 18:
            benefit_cair = tahapan_kuliah
            
        # Akumulasikan PV Manfaat (Bunga + Peluang Hidup Orang Tua)
        pv_manfaat += (v ** t) * tpx * (benefit_cair + (qx_ot * target_dana_kuliah * 0.2)) # Ditambah asumsi santunan duka 20% jika meninggal
        
        # Update peluang bertahan hidup orang tua (tpx)
        px_ot = df_mortalitas.loc[usia_ot_t, "px"]
        tpx *= px_ot
        
    # 2. Menghitung Anuitas Hidup Orang Tua untuk mencicil Premi Tahunan (ä_x:n)
    anuitas_pembayaran = 0
    tpx = 1.0
    for t in range(tenor): # Pembayaran di awal tahun selama masa tenor
        usia_ot_t = usia_orang_tua + t
        anuitas_pembayaran += (v ** t) * tpx
        px_ot = df_mortalitas.loc[usia_ot_t, "px"]
        tpx *= px_ot
        
    premi_tahunan = pv_manfaat / anuitas_pembayaran if anuitas_pembayaran > 0 else 0
    
    # Menampilkan Hasil Perhitungan
    st.subheader("📋 Hasil Perhitungan Nilai Premi")
    
    res1, res2 = st.columns(2)
    with res1:
        st.metric(
            label="Masa Pembayaran & Proteksi", 
            value=f"{tenor} Tahun",
            help="Hingga anak selesai menempuh pendidikan tinggi (Asumsi usia 22 tahun)"
        )
        st.info(f"Suku bunga acuan yang digunakan: **{suku_bunga*100:.1f}% per tahun**.")
        
    with res2:
        st.subheader("💡 Premi Bersih Tahunan")
        st.subheader(f"Rp {premi_tahunan:,.2f} / Tahun")
        st.write(f"Atau setara dengan sekitar **Rp {premi_tahunan/12:,.2f} / Bulan**")

    # Ringkasan Tahapan Dana
    st.markdown("### 📌 Detail Alokasi Dana Tahapan Pendidikan Yang Diterima:")
    r_sd, r_smp, r_sma, r_kul = st.columns(4)
    r_sd.metric("SD (Usia 6)", f"Rp {tahapan_sd:,.0f}")
    r_smp.metric("SMP (Usia 12)", f"Rp {tahapan_smp:,.0f}")
    r_sma.metric("SMA (Usia 15)", f"Rp {tahapan_sma:,.0f}")
    r_kul.metric("Kuliah (Usia 18)", f"Rp {tahapan_kuliah:,.0f}")


# =====================================================================
# FITUR 3: SIMULASI PENCAIRAN TAHAPAN
# =====================================================================
elif menu == "📅 Simulasi Pencairan Tahapan":
    st.title("📅 Kalender & Timeline Pencairan Dana Pendidikan")
    st.write("Lihat proyeksi tepat kapan dana asuransi pendidikan anak akan dicairkan berdasarkan tahun kalender.")
    
    col_c1, col_c2 = st.columns(2)
    with col_c1:
        usia_anak_sekarang = st.slider("Usia Anak Saat Ini", 0, 5, 1)
    with col_c2:
        dana_target = st.number_input("Target Total Dana (Rp)", value=100_000_000, step=10_000_000)
        
    tahun_sekarang = 2026 # Basis tahun berjalan saat ini
    
    jadwal_pencairan = []
    for t in range(1, 23 - usia_anak_sekarang):
        usia_anak_t = usia_anak_sekarang + t
        tahun_pencairan = tahun_sekarang + t
        
        porsi = 0
        jenjang = "-"
        if usia_anak_t == 6:
            porsi = 0.10 * dana_target
            jenjang = "Masuk Sekolah Dasar (SD)"
        elif usia_anak_t == 12:
            porsi = 0.15 * dana_target
            jenjang = "Masuk SMP"
        elif usia_anak_t == 15:
            porsi = 0.25 * dana_target
            jenjang = "Masuk SMA"
        elif usia_anak_t == 18:
            porsi = 0.50 * dana_target
            jenjang = "Masuk Universitas (Kuliah)"
            
        if porsi > 0:
            jadwal_pencairan.append({
                "Tahun": tahun_pencairan,
                "Usia Anak": f"{usia_anak_t} Tahun",
                "Keterangan / Jenjang": jenjang,
                "Dana Dicairkan": porsi
            })
            
    df_jadwal = pd.DataFrame(jadwal_pencairan)
    
    if not df_jadwal.empty:
        st.write("### Jadwal Rencana Pencairan Dana Anda:")
        st.dataframe(df_jadwal.style.format({"Dana Dicairkan": "Rp {:,.2f}"}), use_container_width=True)
        
        # Membuat visualisasi bar chart pencairan dana
        fig_bar = px.bar(
            df_jadwal,
            x="Tahun",
            y="Dana Dicairkan",
            text="Dana Dicairkan",
            title="Grafik Rencana Pencairan Dana Berdasarkan Tahun",
            color_discrete_sequence=["#FF9900"]
        )
        fig_bar.update_traces(texttemplate='Rp %{y:,.0f}', textposition='outside')
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.warning("Usia anak Anda sudah melampaui masa awal tahapan masuk sekolah dasar.")


# =====================================================================
# FITUR 4: PROYEKSI CADANGAN DANA
# =====================================================================
elif menu == "🛡️ Proyeksi Cadangan Dana":
    st.title("🛡️ Proyeksi Dana Cadangan Perusahaan (Reserves)")
    st.write("Menganalisis akumulasi dana cadangan dari sisi perusahaan asuransi untuk menjamin pembayaran dana tahapan di masa depan.")
    
    u_anak = st.slider("Pilih Usia Anak saat Mulai Polis", 0, 5, 2)
    u_ot = st.slider("Pilih Usia Orang Tua saat Mulai Polis", 25, 50, 35)
    total_up = st.number_input("Nominal Target Dana Pendidikan (Rp)", value=120_000_000, step=10_000_000)
    
    tenor_total = 22 - u_anak
    tahun_berjalan = list(range(tenor_total + 1))
    
    # Model simulasi cadangan prospektif untuk produk Dwiguna (Endowment)
    # Cadangan akan naik perlahan, lalu turun secara berkala setiap kali ada dana tahapan yang dicairkan kepada nasabah.
    cadangan = []
    saldo_cadangan = 0
    premi_masuk_estimasi = total_up * 0.04 # Perkiraan premi tahunan masuk
    
    for t in tahun_berjalan:
        usia_anak_t = u_anak + t
        
        # Premi masuk di awal tahun (asumsi terkumpul terus dengan bunga)
        if t < tenor_total:
            saldo_cadangan = (saldo_cadangan + premi_masuk_estimasi) * (1 + suku_bunga)
        else:
            saldo_cadangan = saldo_cadangan * (1 + suku_bunga)
            
        # Pengurangan saldo karena adanya pencairan dana tahapan (Klaim)
        pembayaran_tahapan = 0
        if usia_anak_t == 6:
            pembayaran_tahapan = total_up * 0.10
        elif usia_anak_t == 12:
            pembayaran_tahapan = total_up * 0.15
        elif usia_anak_t == 15:
            pembayaran_tahapan = total_up * 0.25
        elif usia_anak_t == 18:
            pembayaran_tahapan = total_up * 0.50
            
        saldo_cadangan = max(0, saldo_cadangan - pembayaran_tahapan)
        cadangan.append(saldo_cadangan)
        
    df_cadangan = pd.DataFrame({
        "Tahun Ke-": tahun_berjalan,
        "Usia Anak": [u_anak + t for t in tahun_berjalan],
        "Proyeksi Dana Cadangan (Rp)": cadangan
    })
    
    col_g1, col_g2 = st.columns([1, 2])
    with col_g1:
        st.write("##### Tabel Nilai Cadangan")
        st.dataframe(df_cadangan.style.format({"Proyeksi Dana Cadangan (Rp)": "Rp {:,.2f}"}), use_container_width=True)
    with col_g2:
        st.write("##### Pola Cadangan Prospektif")
        fig_line = px.area(
            df_cadangan,
            x="Tahun Ke-",
            y="Proyeksi Dana Cadangan (Rp)",
            title="Tren Akumulasi Cadangan (Menurun Saat Terjadi Pencairan)",
            color_discrete_sequence=["#2E8B57"]
        )
        st.plotly_chart(fig_line, use_container_width=True)
        
        # PERBAIKAN DI BARIS INI
        st.caption("Perhatikan grafik: Cadangan akan terkumpul lalu turun drastis (anjlok) setiap kali anak memasuki usia SD (6), SMP (12), SMA (15), dan Kuliah (18) karena perusahaan membayarkan kewajiban dana pendidikannya.")
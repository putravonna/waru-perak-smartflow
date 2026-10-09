import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date, time
from pathlib import Path

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / 'smartflow.db'

st.set_page_config(page_title='Waru–Perak SmartFlow', page_icon='🚦', layout='wide')

# Prototype login for local demonstration only; change before any real deployment.
DEMO_USER = 'operator'
DEMO_PASSWORD = 'smartflow123'


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS traffic (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            waktu TEXT NOT NULL, lokasi TEXT NOT NULL, arah TEXT NOT NULL,
            volume INTEGER NOT NULL, kecepatan REAL NOT NULL, kepadatan TEXT NOT NULL,
            catatan TEXT DEFAULT ''
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS incidents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            waktu TEXT NOT NULL, lokasi TEXT NOT NULL, jenis TEXT NOT NULL,
            tingkat TEXT NOT NULL, status TEXT NOT NULL, deskripsi TEXT DEFAULT ''
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS gates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            waktu TEXT NOT NULL, gerbang TEXT NOT NULL, arah TEXT NOT NULL,
            antrean INTEGER NOT NULL, status TEXT NOT NULL, catatan TEXT DEFAULT ''
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tanggal TEXT NOT NULL, petugas TEXT NOT NULL, lokasi TEXT NOT NULL,
            tugas TEXT NOT NULL, status TEXT NOT NULL, catatan TEXT DEFAULT ''
        )''')
        conn.execute('''CREATE TABLE IF NOT EXISTS activity (
            id INTEGER PRIMARY KEY AUTOINCREMENT, waktu TEXT NOT NULL,
            pengguna TEXT NOT NULL, aktivitas TEXT NOT NULL
        )''')


def log_activity(action):
    with get_conn() as conn:
        conn.execute('INSERT INTO activity(waktu,pengguna,aktivitas) VALUES(?,?,?)',
                     (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), DEMO_USER, action))


def read_table(table):
    with get_conn() as conn:
        return pd.read_sql_query(f'SELECT * FROM {table} ORDER BY id DESC', conn)


init_db()

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title('🚦 Waru–Perak SmartFlow')
    st.subheader('Sistem pemantauan lalu lintas dan insiden — prototipe lokal')
    st.write('Masuk untuk membuka dashboard pemantauan koridor Waru–Perak.')
    with st.form('login_form'):
        username = st.text_input('Nama pengguna', value='operator')
        password = st.text_input('Kata sandi', type='password')
        submit = st.form_submit_button('Login', use_container_width=True)
    if submit:
        if username == DEMO_USER and password == DEMO_PASSWORD:
            st.session_state.logged_in = True
            st.session_state.username = username
            st.rerun()
        else:
            st.error('Nama pengguna atau kata sandi salah.')
    st.info('Akun demo: pengguna **operator** · kata sandi **smartflow123**')
    st.caption('Catatan: login ini untuk demonstrasi lokal, bukan keamanan produksi. Data disimpan di file smartflow.db dalam folder aplikasi.')
    st.stop()

with st.sidebar:
    st.title('🚦 SmartFlow')
    st.caption('Waru–Perak')
    page = st.radio('Menu', ['Dashboard', 'Data Lalu Lintas', 'Manajemen Insiden', 'Gerbang Tol', 'Tugas Petugas', 'Rekomendasi', 'Log Aktivitas', 'Ekspor Data', 'Panduan'])
    st.divider()
    st.write(f'Masuk sebagai: **{st.session_state.get("username", DEMO_USER)}**')
    if st.button('Keluar', use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

st.title('Waru–Perak SmartFlow')
st.caption('Prototipe pemantauan lalu lintas, insiden, gerbang tol, dan tugas petugas.')

if page == 'Dashboard':
    traffic = read_table('traffic')
    incidents = read_table('incidents')
    gates = read_table('gates')
    tasks = read_table('tasks')
    c1, c2, c3, c4 = st.columns(4)
    c1.metric('Catatan lalu lintas', len(traffic))
    c2.metric('Insiden tercatat', len(incidents))
    c3.metric('Catatan gerbang tol', len(gates))
    c4.metric('Tugas petugas', len(tasks))
    st.subheader('Ringkasan terbaru')
    left, right = st.columns(2)
    with left:
        st.markdown('**Data lalu lintas terbaru**')
        st.dataframe(traffic.head(8), use_container_width=True, hide_index=True)
    with right:
        st.markdown('**Insiden terbaru**')
        st.dataframe(incidents.head(8), use_container_width=True, hide_index=True)
    st.warning('Dashboard menggunakan data yang dimasukkan pengguna. Belum terhubung otomatis ke CCTV, sensor, atau sistem resmi operator jalan tol.')

elif page == 'Data Lalu Lintas':
    st.subheader('Input pemantauan lalu lintas')
    with st.form('traffic_form', clear_on_submit=True):
        a, b = st.columns(2)
        with a:
            waktu = st.text_input('Waktu pengamatan', value=datetime.now().strftime('%Y-%m-%d %H:%M'))
            lokasi = st.selectbox('Lokasi', ['Waru', 'Sidoarjo', 'Porong', 'Perak', 'Lokasi lain'])
            arah = st.selectbox('Arah perjalanan', ['Waru → Perak', 'Perak → Waru', 'Arah lain'])
        with b:
            volume = st.number_input('Volume kendaraan (kendaraan/jam)', min_value=0, step=1)
            kecepatan = st.number_input('Kecepatan rata-rata (km/jam)', min_value=0.0, max_value=200.0, value=40.0, step=1.0)
            kepadatan = st.selectbox('Kondisi lalu lintas', ['Lancar', 'Ramai lancar', 'Padat', 'Macet'])
        catatan = st.text_area('Catatan tambahan')
        save = st.form_submit_button('Simpan data', use_container_width=True)
    if save:
        with get_conn() as conn:
            conn.execute('INSERT INTO traffic(waktu,lokasi,arah,volume,kecepatan,kepadatan,catatan) VALUES(?,?,?,?,?,?,?)',
                         (waktu, lokasi, arah, int(volume), float(kecepatan), kepadatan, catatan))
        log_activity(f'Menambahkan data lalu lintas di {lokasi}')
        st.success('Data lalu lintas berhasil disimpan.')
    df = read_table('traffic')
    st.subheader('Riwayat data')
    st.dataframe(df, use_container_width=True, hide_index=True)
    if not df.empty:
        st.download_button('Unduh CSV data lalu lintas', df.to_csv(index=False).encode('utf-8-sig'), 'data_lalu_lintas.csv', 'text/csv')

elif page == 'Manajemen Insiden':
    st.subheader('Pencatatan insiden')
    with st.form('incident_form', clear_on_submit=True):
        a, b = st.columns(2)
        with a:
            waktu = st.text_input('Waktu kejadian', value=datetime.now().strftime('%Y-%m-%d %H:%M'))
            lokasi = st.text_input('Lokasi kejadian', placeholder='Contoh: akses Waru arah Perak')
            jenis = st.selectbox('Jenis insiden', ['Kecelakaan', 'Kendaraan mogok', 'Gangguan jalan', 'Antrean panjang', 'Lainnya'])
        with b:
            tingkat = st.selectbox('Tingkat dampak', ['Rendah', 'Sedang', 'Tinggi', 'Darurat'])
            status = st.selectbox('Status penanganan', ['Baru', 'Ditangani', 'Selesai'])
        deskripsi = st.text_area('Deskripsi / tindakan yang diperlukan')
        save = st.form_submit_button('Simpan insiden', use_container_width=True)
    if save:
        if not lokasi.strip():
            st.error('Isi lokasi kejadian terlebih dahulu.')
        else:
            with get_conn() as conn:
                conn.execute('INSERT INTO incidents(waktu,lokasi,jenis,tingkat,status,deskripsi) VALUES(?,?,?,?,?,?)',
                             (waktu, lokasi, jenis, tingkat, status, deskripsi))
            log_activity(f'Mencatat insiden {jenis} di {lokasi}')
            st.success('Insiden berhasil disimpan.')
    st.dataframe(read_table('incidents'), use_container_width=True, hide_index=True)

elif page == 'Gerbang Tol':
    st.subheader('Pemantauan antrean gerbang tol')
    with st.form('gate_form', clear_on_submit=True):
        a, b = st.columns(2)
        with a:
            waktu = st.text_input('Waktu pengamatan', value=datetime.now().strftime('%Y-%m-%d %H:%M'))
            gerbang = st.text_input('Nama gerbang / akses', placeholder='Contoh: Gerbang Tol Waru')
            arah = st.selectbox('Arah', ['Masuk', 'Keluar', 'Keduanya'])
        with b:
            antrean = st.number_input('Perkiraan panjang antrean (kendaraan)', min_value=0, step=1)
            status = st.selectbox('Kondisi gerbang', ['Normal', 'Padat', 'Gangguan', 'Ditutup sementara'])
        catatan = st.text_area('Catatan')
        save = st.form_submit_button('Simpan pemantauan', use_container_width=True)
    if save:
        if not gerbang.strip():
            st.error('Masukkan nama gerbang atau akses.')
        else:
            with get_conn() as conn:
                conn.execute('INSERT INTO gates(waktu,gerbang,arah,antrean,status,catatan) VALUES(?,?,?,?,?,?)',
                             (waktu, gerbang, arah, int(antrean), status, catatan))
            log_activity(f'Menambahkan pemantauan gerbang {gerbang}')
            st.success('Data gerbang tol berhasil disimpan.')
    st.dataframe(read_table('gates'), use_container_width=True, hide_index=True)

elif page == 'Tugas Petugas':
    st.subheader('Penugasan petugas lapangan')
    with st.form('task_form', clear_on_submit=True):
        tanggal = st.date_input('Tanggal tugas', value=date.today()).isoformat()
        petugas = st.text_input('Nama petugas')
        lokasi = st.text_input('Lokasi tugas')
        tugas = st.selectbox('Jenis tugas', ['Pemantauan arus', 'Pemeriksaan insiden', 'Pemantauan gerbang', 'Pengaturan lalu lintas', 'Pelaporan kondisi jalan', 'Lainnya'])
        status = st.selectbox('Status tugas', ['Belum dimulai', 'Berlangsung', 'Selesai'])
        catatan = st.text_area('Catatan tugas')
        save = st.form_submit_button('Simpan tugas', use_container_width=True)
    if save:
        if not petugas.strip() or not lokasi.strip():
            st.error('Nama petugas dan lokasi wajib diisi.')
        else:
            with get_conn() as conn:
                conn.execute('INSERT INTO tasks(tanggal,petugas,lokasi,tugas,status,catatan) VALUES(?,?,?,?,?,?)',
                             (tanggal, petugas, lokasi, tugas, status, catatan))
            log_activity(f'Membuat tugas untuk {petugas} di {lokasi}')
            st.success('Tugas berhasil disimpan.')
    st.dataframe(read_table('tasks'), use_container_width=True, hide_index=True)

elif page == 'Rekomendasi':
    st.subheader('Rekomendasi operasional sederhana')
    traffic = read_table('traffic')
    incidents = read_table('incidents')
    gates = read_table('gates')
    if traffic.empty and incidents.empty and gates.empty:
        st.info('Tambahkan data lalu lintas, insiden, atau gerbang tol terlebih dahulu agar rekomendasi dapat ditampilkan.')
    else:
        recommendations = []
        if not traffic.empty:
            for _, r in traffic.head(100).iterrows():
                if r['kepadatan'] == 'Macet': recommendations.append(f"Prioritaskan pemeriksaan arus di {r['lokasi']} ({r['arah']}); catatan menunjukkan kondisi macet.")
                elif r['kepadatan'] == 'Padat': recommendations.append(f"Pantau perubahan arus di {r['lokasi']} dan evaluasi kembali dalam interval pengamatan berikutnya.")
                if float(r['kecepatan']) < 20: recommendations.append(f"Periksa kemungkinan hambatan di {r['lokasi']} karena kecepatan tercatat di bawah 20 km/jam.")
        if not incidents.empty:
            for _, r in incidents.head(100).iterrows():
                if r['status'] != 'Selesai' and r['tingkat'] in ['Tinggi', 'Darurat']:
                    recommendations.append(f"Tindak lanjuti insiden {r['jenis']} di {r['lokasi']} (dampak {r['tingkat']}, status {r['status']}).")
        if not gates.empty:
            for _, r in gates.head(100).iterrows():
                if r['status'] in ['Padat', 'Gangguan', 'Ditutup sementara']:
                    recommendations.append(f"Koordinasikan pemeriksaan gerbang/akses {r['gerbang']} karena status {r['status']}.")
        if recommendations:
            for rec in dict.fromkeys(recommendations): st.warning(rec)
        else:
            st.success('Belum ada kondisi prioritas yang terdeteksi dari data yang dimasukkan. Tetap lakukan pemantauan lapangan.')
    st.caption('Rekomendasi bersifat aturan sederhana dari data input, bukan keputusan otomatis atau informasi lalu lintas real-time.')

elif page == 'Log Aktivitas':
    st.subheader('Riwayat aktivitas pengguna')
    st.dataframe(read_table('activity'), use_container_width=True, hide_index=True)

elif page == 'Ekspor Data':
    st.subheader('Unduh data untuk laporan')
    mapping = [('Data lalu lintas', 'traffic', 'data_lalu_lintas.csv'), ('Insiden', 'incidents', 'data_insiden.csv'), ('Gerbang tol', 'gates', 'data_gerbang_tol.csv'), ('Tugas petugas', 'tasks', 'data_tugas_petugas.csv'), ('Log aktivitas', 'activity', 'log_aktivitas.csv')]
    for label, table, filename in mapping:
        df = read_table(table)
        col1, col2 = st.columns([3, 1])
        col1.write(f'{label}: {len(df)} baris')
        col2.download_button(f'Unduh CSV', df.to_csv(index=False).encode('utf-8-sig'), filename, 'text/csv', key=table)

elif page == 'Panduan':
    st.subheader('Panduan penggunaan')
    st.markdown('''
1. **Login** dengan akun demo yang tercantum pada halaman masuk.
2. **Data Lalu Lintas**: masukkan waktu, lokasi, arah, volume, kecepatan, dan kondisi lalu lintas.
3. **Manajemen Insiden**: catat kecelakaan, kendaraan mogok, gangguan jalan, atau antrean panjang.
4. **Gerbang Tol**: masukkan kondisi gerbang dan perkiraan antrean.
5. **Tugas Petugas**: buat dan pantau penugasan lapangan.
6. **Rekomendasi**: lihat saran awal berdasarkan data yang telah dimasukkan.
7. **Ekspor Data**: unduh tabel dalam format CSV untuk Excel atau laporan.

**Penyimpanan:** data disimpan secara lokal pada `smartflow.db` di folder aplikasi. Jangan menghapus file ini jika ingin mempertahankan data.

**Batasan prototipe:** aplikasi ini tidak mengambil data langsung dari CCTV, sensor, GPS, atau sistem resmi Jasa Marga. Informasi yang ditampilkan bergantung pada input pengguna. Akun demo tidak dirancang untuk penggunaan publik atau produksi.
''')

st.divider()
st.caption('Waru–Perak SmartFlow · Prototipe akademik/lokal · Bukan sistem resmi operator jalan tol')

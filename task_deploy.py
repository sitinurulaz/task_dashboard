import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta
from pandas import json_normalize

# =============================
# 1️⃣ KONFIGURASI DASHBOARD
# =============================
st.set_page_config(page_title="Sales Performance Dashboard", layout="wide")
st.title("📊 Sales Performance Dashboard (Qontak CRM)")
st.markdown("Analisis performa sales berdasarkan data task CRM secara langsung.")

# =============================
# 2️⃣ MASUKKAN TOKEN LANGSUNG
# =============================
# 💡 Ganti token di bawah dengan token Qontak CRM (berlaku 6 jam)

API_TOKEN = st.secrets["Qontak"]["API_TOKEN"]

# =============================
# 3️⃣ AMBIL DATA LANGSUNG DARI API (TANPA FUNGSI DEF)
# =============================
url = "https://app.qontak.com/api/v3.1/tasks?filter=alltask&page=1&per_page=1000"

headers = {
    "Authorization": f"Bearer {API_TOKEN}",  # <-- Bearer token
    "Accept": "application/json"
}

# === 3. LAKUKAN REQUEST KE API ===
response = requests.get(url, headers=headers)

# === 4. CEK HASILNYA ===
content_type = response.headers.get("Content-Type", "")

if response.status_code == 200 and "application/json" in content_type:
    data = response.json()
    
    # Ubah ke DataFrame untuk tampilan tabel
df = json_normalize(data["response"])

# =============================
# 4️⃣ BERSIHKAN DAN SIAPKAN DATA
# =============================

# Ubah list of dict di kolom 'additional_fields' menjadi dict tunggal
df_expanded = (
    df['additional_fields']
    .apply(lambda x: {d['name']: d.get('value', None) for d in x})
    .apply(pd.Series)
)

# Gabungkan kembali dengan DataFrame asli
df_final = pd.concat([df.drop(columns=['additional_fields']), df_expanded], axis=1)

# Jika ingin menyatukan kolom hasil menjadi satu string dengan koma
df_final['merged'] = df_expanded.apply(lambda row: ', '.join([f"{k}: {v}" for k, v in row.items() if pd.notnull(v)]), axis=1)


if df_final.empty:
    st.warning("⚠️ Data kosong atau belum berhasil diambil.")
    st.stop()
if "due_date" in df_final.columns:
    df_final["due_date"] = pd.to_datetime(
        df_final["due_date"],
        errors="coerce",
        utc=True
    ).dt.tz_localize(None)
else:
    df_final["due_date"] = pd.NaT

df_final["convert_to"] = pd.to_numeric(df_final["convert_to"], errors="coerce").astype("Int64")
df_final["engagement_type"] = pd.to_numeric(df_final["engagement_type"], errors="coerce").astype("Int64")

# Ganti angka 1–5 dengan karakter (mapping status)
status_mapping = {
    1: "Belum Dimulai",
    2: "Dalam Proses",
    3: "Menunggu",
    4: "Selesai",
    5: "Ditunda"
}
df_final["crm_task_status"] = df_final["crm_task_status_id"].map(status_mapping)

mapping_convert = {
    3866814: "Lead Engaged",
    3866815: "Prospect",
    3866816: "Meeting Need",
    3866817: "Proposal Submitted",
    3866818: "Presentation",
    3866819: "Deal",
    3866820: "Invoice"}

df_final["convert_to_label"] = df_final["convert_to"].map(mapping_convert)

user_mapping = {
    171110: "Anin",
    171112: "Ega",
    171113: "Nita",
    171363: "Reza",
    222919: "Cantika",
    233929: "Rahma",
    251373: "Naim"
}

df_final["user_full_name"] = df_final["user_id"].map(user_mapping)



st.title("Report Task Due Today")

# --- Load Data ---
# Misalnya dari CSV
# df_final = pd.read_csv("data.csv")

# Pastikan datetime
df_final["due_date"] = pd.to_datetime(df_final["due_date"])

# --- Filter Due Today + Groupby ---
table = (
    df_final
    .loc[df_final["due_date"].dt.date == pd.Timestamp.today().date()]
    .groupby(["crm_person_full_name", "crm_task_status"])
    .size()
    .unstack(fill_value=0)
)

# Tambah total per orang
table["Total Keseluruhan"] = table.sum(axis=1)

# Tambah total bawah
table.loc["Total Keseluruhan"] = table.sum()

table = table.reset_index()

# --- Tampilkan ---
st.subheader(f"Due Date: {pd.Timestamp.today().date()}")
st.dataframe(table, use_container_width=True)



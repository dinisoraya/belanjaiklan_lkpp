import requests
import time
import pandas as pd
import re

# Konfigurasi awal
tahun = '2025'
headers = {'User-Agent': 'Mozilla/5.0'}

# Step 1: Ambil daftar satker
url_satker = "https://sirup.lkpp.go.id/sirup/datatablectr/datatableruprekapkldi"
params_satker = {
    'idKldi': 'K3',  # Ganti sesuai kebutuhan
    'tahun': tahun,
    'sEcho': '1',
    'iColumns': '10',
    'iDisplayStart': '0',
    'iDisplayLength': '100000',
}
res = requests.get(url_satker, params=params_satker, headers=headers)
satkers = res.json().get("aaData", [])
print(f"📋 Total Satuan Kerja ditemukan: {len(satkers)}")

# Fungsi ambil uraian pekerjaan
def get_detail_paket(id_paket):
    url_detail = f"https://sirup.lkpp.go.id/sirup/home/detailPaketPenyediaPublic2017/{id_paket}"
    try:
        resp = requests.get(url_detail, headers=headers)
        if resp.status_code == 200:
            html = resp.text
            start = html.find("Uraian Pekerjaan")
            if start == -1:
                return ""
            start = html.find("<td>", start) + 4
            end = html.find("</td>", start)
            return html[start:end].strip()
        else:
            return ""
    except:
        return ""

# Daftar keyword yang dicari (case-insensitive)
keywords = [
    "iklan", "surat kabar", "suratkabar", "koran", "cetak",
    "majalah", "publikasi", "radio", "televisi", "tv", 
    "online", "siber", "cyber", "talk show", "talkshow",
    "pariwara", "advertorial", "advertising", "ads", "adv",
    "advertiser", "kampanye", "campaign", "promosi", "diseminasi"
    "podcast", "sosialisasi", "edukasi",  "komunikasi", "elektronik"
]

# Step 2: Ambil data paket
all_rows = []
for idx, satker in enumerate(satkers, 1):
    id_satker = satker[0]
    nama_satker = satker[1]

    try:
        url_paket = "https://sirup.lkpp.go.id/sirup/datatablectr/dataruppenyediasatker"
        params_paket = {
            'tahun': tahun,
            'idSatker': id_satker,
            'sEcho': '1',
            'iColumns': '7',
            'iDisplayStart': '0',
            'iDisplayLength': '100000'
        }

        res_paket = requests.get(url_paket, params=params_paket, headers=headers)
        paket_list = res_paket.json().get("aaData", [])

        if not paket_list:
            # Tambahkan baris kosong untuk satker tanpa paket
            all_rows.append([nama_satker, None, None, None, None])
            print(f"{idx}/{len(satkers)} ❕ {nama_satker} (0 paket)")
            continue

        filtered_count = 0  # hitung jumlah paket yang lolos filter
        for paket in paket_list:
            id_paket = paket[0]
            nama_paket = paket[1]
            pagu = paket[2]
            jenis = paket[3]
            uraian = get_detail_paket(id_paket)

            # Cek apakah mengandung salah satu keyword
            combined_text = f"{nama_paket} {uraian}".lower()
            pattern = r'(?<!\w)(' + '|'.join(re.escape(k) for k in keywords) + r')(?!\w)'
            if re.search(pattern, combined_text):
                row = [nama_satker, nama_paket, uraian, jenis, pagu]
                all_rows.append(row)
                filtered_count += 1

        if filtered_count == 0:
            all_rows.append([nama_satker, None, None, None, None])
            print(f"{idx}/{len(satkers)} ❕ {nama_satker} (0 keywoard cocok)")
        else:
            print(f"{idx}/{len(satkers)} ✔ {nama_satker} ({filtered_count} keywoard cocok)")
        time.sleep(0.2)

    except Exception as e:
        print(f"{idx}/{len(satkers)} ❌ Error di {nama_satker}: {e}")
        all_rows.append([nama_satker, None, None, None, None])

# Step 3: Simpan ke Excel
df = pd.DataFrame(all_rows, columns=[
    'satuanKerja', 'namaPaket', 'uraianPekerjaan', 'metodePemilihan', 'pagu'
])
df.index += 1  # mulai dari 1
df.reset_index(inplace=True)
df.rename(columns={"index": "No"}, inplace=True)

excel_path = r'C:\Users\ASUS\Downloads\kemendagri_keywoard_2025.xlsx'
df.to_excel(excel_path, index=False)

print(f"\n✅ File berhasil disimpan di: {excel_path}")

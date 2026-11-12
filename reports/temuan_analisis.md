# Temuan Analisis: Pendidikan dan Kualitas SDM Indonesia

_Dibuat otomatis oleh `python -m src.analysis.analisis` pada 12-11-2026. Data: BPS, potret 2025 (38 provinsi);
uji konsistensi 2020-2025. Semua angka di bawah dihitung ulang setiap kali skrip dijalankan._

> **Catatan metodologis.** Semua hubungan adalah **asosiasi**, bukan sebab-akibat. n = 38 provinsi (kecil), sehingga
> setiap korelasi dilaporkan beserta interval kepercayaan bootstrap (2000x), hasil tanpa 2 provinsi pencilan ekstrem
> (Papua Tengah, Papua Pegunungan), dan konsistensinya antartahun. Korelasi memakai Spearman.

## Ringkasan: 5 temuan kunci

1. **Pendidikan berasosiasi dengan pekerjaan formal, dan lewat jalur itulah pendidikan berkaitan dengan kemiskinan.**
   RLS vs pekerja formal ρ = +0.54 (95% CI +0.21 s.d. +0.76; tanpa pencilan +0.46; rentang 2020-2025: +0.50 s.d. +0.55). Hubungan RLS dengan kemiskinan (ρ = -0.43) **hilang** setelah dikontrol
   persentase pekerja formal (ρ parsial = -0.06), sedangkan pekerja formal tetap kuat terhadap kemiskinan
   walau pendidikan dikontrol (ρ parsial = -0.67). Pendidikan hanya berkaitan dengan kesejahteraan bila diterjemahkan
   menjadi pekerjaan formal.
2. **TPT rendah bukan tanda pasar kerja sehat.** TPT justru searah dengan pekerja formal ρ = +0.45 (95% CI +0.11 s.d. +0.70; tanpa pencilan +0.39; rentang 2020-2025: +0.45 s.d. +0.57), dan hubungannya
   dengan kemiskinan lemah serta terus melemah ρ = -0.23 (95% CI -0.58 s.d. +0.15; tanpa pencilan -0.14; rentang 2020-2025: -0.41 s.d. -0.23). Sebaliknya pekerja formal vs kemiskinan ρ = -0.74 (95% CI -0.88 s.d. -0.51; tanpa pencilan -0.69; rentang 2020-2025: -0.76 s.d. -0.66). Contoh ekstrem: Papua Pegunungan
   memiliki TPT 1.68% (terendah kedua) tetapi pekerja formal hanya
   4.7%. **Implikasi: dashboard dan kebijakan sebaiknya
   memakai pekerja formal, bukan TPT, sebagai ukuran utama kualitas pasar kerja.**
3. **Provinsi berpendidikan lebih tinggi justru memiliki pengangguran lebih tinggi**, termasuk pengangguran lulusan perguruan
   tinggi. RLS vs TPT ρ = +0.45 (95% CI +0.14 s.d. +0.70; tanpa pencilan +0.40; rentang 2020-2025: +0.41 s.d. +0.50); RLS vs TPT lulusan PT ρ = +0.41 (95% CI +0.09 s.d. +0.67; tanpa pencilan +0.31; data hanya 2025). Hubungan RLS-TPT melemah dari ρ = +0.45 menjadi
   +0.15 setelah dikontrol TPAK: provinsi berpendidikan rendah umumnya agraris-subsisten dengan partisipasi kerja
   tinggi, sehingga hampir tidak ada "pengangguran terbuka".
4. **Masalah paling tajam ada di jalur vokasi.** TPT lulusan SMK lebih tinggi daripada SMA umum di 25 dari 37
   provinsi; TPT SMK tertimbang Jawa 9.40% vs Luar Jawa
   6.99%. Secara nasional TPT SMK selalu tertinggi sejak 2020
   (dari 13.55% menjadi 8.63%), meski selisihnya terhadap SMA menyempit
   (3.69 → 1.75 poin persen).
   TPT lulusan PT lebih rendah daripada SMA di 24 provinsi.
5. **Hampir semua kesenjangan antarprovinsi menyempit, kecuali NEET.** Koefisien variasi RLS turun
   9.9% → 9.0%, pekerja formal
   23.5% → 20.9%, tetapi kesenjangan NEET justru **melebar**
   15.7% → 24.3% dan kemiskinan nyaris tetap
   44.8% → 43.1% (32 provinsi dengan wilayah konsisten).
   NEET juga tidak berhubungan dengan capaian pendidikan ρ = +0.04 (95% CI -0.33 s.d. +0.42; tanpa pencilan -0.01; rentang 2020-2025: -0.18 s.d. +0.04): menambah lama sekolah tidak otomatis
   mengurangi pemuda yang menganggur dan tidak bersekolah. NEET adalah titik buta kebijakan pendidikan saat ini.

## 1. Uji hipotesis

| hipotesis | pernyataan | n | rho | ci95_bawah | ci95_atas | p_value | p_holm | rho_tanpa_pencilan | rho_min_antartahun | rho_maks_antartahun | kesimpulan |
|---|---|---|---|---|---|---|---|---|---|---|---|
| H1 | Provinsi dengan RLS lebih tinggi memiliki persentase pekerja formal lebih tinggi | 38 | 0.54 | 0.21 | 0.76 | 0.0005 | 0.002 | 0.46 | 0.502 | 0.554 | Didukung data |
| H2a | TPT rendah bukan tanda pasar kerja sehat: TPT justru searah dengan pekerja formal | 38 | 0.45 | 0.11 | 0.7 | 0.0046 | 0.0129 | 0.39 | 0.45 | 0.568 | Didukung data |
| H2b | TPT bukan penanda kesejahteraan: hubungannya dengan kemiskinan lemah dan tidak signifikan | 38 | -0.23 | -0.58 | 0.15 | 0.1578 |  | -0.14 | -0.413 | -0.234 | Didukung data |
| H2c | Pekerja formal (bukan TPT) yang berhubungan dengan kemiskinan lebih rendah | 38 | -0.74 | -0.88 | -0.51 | 0.0 | 0.0 | -0.69 | -0.755 | -0.661 | Didukung data |
| H3a | Pendidikan tinggi tidak otomatis menurunkan pengangguran: RLS searah dengan TPT | 38 | 0.45 | 0.14 | 0.7 | 0.0043 | 0.0129 | 0.4 | 0.409 | 0.503 | Didukung data |
| H3b | Provinsi berpendidikan tinggi justru memiliki TPT lulusan perguruan tinggi lebih tinggi | 38 | 0.41 | 0.09 | 0.67 | 0.0116 | 0.0129 | 0.31 | 0.405 | 0.405 | Didukung data |
| H3c | Capaian pendidikan tidak berhubungan dengan NEET | 38 | 0.04 | -0.33 | 0.42 | 0.826 |  | -0.01 | -0.176 | 0.037 | Didukung data |

`p_holm` = p-value setelah koreksi uji berganda (Holm) untuk hipotesis berarah. H2b dan H3c adalah hipotesis "tidak berhubungan":
didukung bila interval kepercayaan memuat nol (H2b: tidak negatif).

## 2. Korelasi parsial (mengontrol variabel ketiga)

| var_x | var_y | kontrol | rho | keterangan |
|---|---|---|---|---|
| RLS | MISKIN | - | -0.43 | Pendidikan vs kemiskinan (tanpa kontrol) |
| RLS | MISKIN | PEKERJA_FORMAL | -0.06 | Pendidikan vs kemiskinan, dikontrol pekerja formal |
| PEKERJA_FORMAL | MISKIN | RLS | -0.67 | Pekerja formal vs kemiskinan, dikontrol pendidikan |
| RLS | TPT | - | 0.45 | Pendidikan vs TPT (tanpa kontrol) |
| RLS | TPT | TPAK | 0.15 | Pendidikan vs TPT, dikontrol partisipasi angkatan kerja |
| RLS | PEKERJA_FORMAL | PENGELUARAN | 0.34 | Pendidikan vs pekerja formal, dikontrol pengeluaran per kapita |

## 3. Kesenjangan antarprovinsi (2025)

| indikator | terendah | nilai_terendah | tertinggi | nilai_tertinggi | rasio_tertinggi_terendah | rasio_p90_p10 | median_jawa | median_luar_jawa | tertimbang_jawa | tertimbang_luar_jawa |
|---|---|---|---|---|---|---|---|---|---|---|
| RLS | Papua Pegunungan | 4.3 | DKI Jakarta | 11.59 | 2.7 | 1.25 | 9.35 | 8.98 |  |  |
| HLS | Papua Tengah | 9.64 | DI Yogyakarta | 15.78 | 1.64 | 1.11 | 13.27 | 13.34 |  |  |
| APS_16_18 | Papua Tengah | 44.61 | DI Yogyakarta | 93.03 | 2.09 | 1.21 | 79.46 | 76.96 |  |  |
| APS_19_23 | Papua Pegunungan | 12.48 | DI Yogyakarta | 54.72 | 4.38 | 1.65 | 28.44 | 29.46 |  |  |
| IPM | Papua Pegunungan | 54.91 | DKI Jakarta | 85.05 | 1.55 | 1.14 | 76.69 | 74.47 |  |  |
| PEKERJA_FORMAL | Papua Pegunungan | 4.7 | Kepulauan Riau | 65.75 | 13.99 | 1.66 | 45.54 | 38.86 |  |  |
| TPT | Bali | 1.49 | Papua | 6.96 | 4.67 | 2.16 | 5.36 | 4.19 |  |  |
| NEET | Bali | 5.33 | Sulawesi Utara | 29.52 | 5.54 | 1.66 | 16.72 | 19.48 |  |  |
| MISKIN | Bali | 3.72 | Papua Pegunungan | 30.03 | 8.07 | 4.0 | 8.25 | 10.07 |  |  |
| TPT_SMA | Bali | 1.61 | Papua Barat Daya | 10.02 | 6.22 | 2.13 | 6.86 | 6.3 | 7.58 | 6.24 |
| TPT_SMK | Bali | 2.11 | Jawa Barat | 12.81 | 6.07 | 2.23 | 7.99 | 7.16 | 9.4 | 6.99 |
| TPT_PT | Papua Pegunungan | 1.99 | Sumatera Barat | 7.86 | 3.95 | 1.95 | 5.22 | 5.15 | 4.97 | 5.44 |

`tertimbang_*` dihitung dari jumlah penganggur / angkatan kerja (bukan rata-rata provinsi), sehingga mewakili kondisi penduduk.

Tren kesenjangan (koefisien variasi antarprovinsi):

| indikator | cv_awal | cv_akhir | perubahan_relatif_persen | arah |
|---|---|---|---|---|
| APS_16_18 | 7.65 | 7.27 | -5.0 | menyempit |
| APS_19_23 | 24.6 | 21.61 | -12.2 | menyempit |
| HLS | 5.08 | 4.78 | -5.9 | menyempit |
| MISKIN | 44.77 | 43.1 | -3.7 | relatif tetap |
| NEET | 15.7 | 24.26 | 54.6 | melebar |
| PEKERJA_FORMAL | 23.54 | 20.91 | -11.2 | menyempit |
| PENGELUARAN | 19.23 | 17.86 | -7.1 | menyempit |
| RLS | 9.9 | 9.02 | -8.8 | menyempit |
| TPT | 33.77 | 28.6 | -15.3 | menyempit |

## 4. Kasus menyimpang

Garis tren robust (Theil-Sen) antara RLS dan indikator hasil; provinsi dengan |robust z| ≥ 1.5 dianggap menyimpang.

**Pekerja formal vs pendidikan**

| provinsi | x | y_aktual | y_perkiraan | robust_z | arah | klaster |
|---|---|---|---|---|---|---|
| Maluku | 10.51 | 33.94 | 49.99 | -2.15 | Pekerja formal lebih rendah dari yang diperkirakan dari tingkat pendidikannya | B. Pendidikan cukup, pengangguran & NEET tinggi |
| Kepulauan Riau | 10.72 | 65.75 | 51.37 | 1.93 | Pekerja formal lebih tinggi dari yang diperkirakan dari tingkat pendidikannya | A. Pendidikan tinggi, terserap pasar kerja formal |

**TPT vs pendidikan**

| provinsi | x | y_aktual | y_perkiraan | robust_z | arah | klaster |
|---|---|---|---|---|---|---|
| Bali | 9.75 | 1.49 | 4.64 | -2.95 | Pengangguran lebih rendah dari perkiraan | A. Pendidikan tinggi, terserap pasar kerja formal |
| Papua | 10.01 | 6.96 | 4.8 | 1.73 | Pengangguran lebih tinggi dari perkiraan | B. Pendidikan cukup, pengangguran & NEET tinggi |
| Banten | 9.56 | 6.69 | 4.53 | 1.74 | Pengangguran lebih tinggi dari perkiraan | B. Pendidikan cukup, pengangguran & NEET tinggi |
| Jawa Barat | 9.14 | 6.77 | 4.27 | 2.04 | Pengangguran lebih tinggi dari perkiraan | B. Pendidikan cukup, pengangguran & NEET tinggi |
| Papua Barat Daya | 8.69 | 6.85 | 3.99 | 2.36 | Pengangguran lebih tinggi dari perkiraan | B. Pendidikan cukup, pengangguran & NEET tinggi |

**NEET vs pendidikan**

| provinsi | x | y_aktual | y_perkiraan | robust_z | arah | klaster |
|---|---|---|---|---|---|---|
| Bali | 9.75 | 5.33 | 19.68 | -3.98 | NEET lebih rendah dari perkiraan | A. Pendidikan tinggi, terserap pasar kerja formal |
| DI Yogyakarta | 10.2 | 11.25 | 19.9 | -2.39 | NEET lebih rendah dari perkiraan | A. Pendidikan tinggi, terserap pasar kerja formal |
| DKI Jakarta | 11.59 | 12.83 | 20.59 | -2.14 | NEET lebih rendah dari perkiraan | A. Pendidikan tinggi, terserap pasar kerja formal |
| Jawa Barat | 9.14 | 24.84 | 19.37 | 1.53 | NEET lebih tinggi dari perkiraan | B. Pendidikan cukup, pengangguran & NEET tinggi |
| Papua Barat | 8.07 | 24.64 | 18.84 | 1.62 | NEET lebih tinggi dari perkiraan | B. Pendidikan cukup, pengangguran & NEET tinggi |
| Papua Barat Daya | 8.69 | 24.97 | 19.15 | 1.63 | NEET lebih tinggi dari perkiraan | B. Pendidikan cukup, pengangguran & NEET tinggi |
| Maluku Utara | 9.5 | 25.65 | 19.55 | 1.71 | NEET lebih tinggi dari perkiraan | B. Pendidikan cukup, pengangguran & NEET tinggi |
| Papua | 10.01 | 26.34 | 19.81 | 1.83 | NEET lebih tinggi dari perkiraan | B. Pendidikan cukup, pengangguran & NEET tinggi |
| Maluku | 10.51 | 28.49 | 20.05 | 2.36 | NEET lebih tinggi dari perkiraan | B. Pendidikan cukup, pengangguran & NEET tinggi |
| Sulawesi Utara | 9.91 | 29.52 | 19.76 | 2.72 | NEET lebih tinggi dari perkiraan | B. Pendidikan cukup, pengangguran & NEET tinggi |

Pendidikan di atas median dan TPT juga di atas median (12 provinsi): Aceh, Sumatera Utara, Sumatera Barat, Kepulauan Riau, DKI Jakarta, Jawa Barat, Banten, Kalimantan Timur, Sulawesi Utara, Maluku, Maluku Utara, Papua.

**Kasus paling layak dipresentasikan:**
- **Maluku**: RLS peringkat 3 dari 38 (10.51 tahun), tetapi pekerja formal hanya
  33.9%, NEET 28.5%, dan TPT SMK 12.1%. Ini profil
  "pendidikan tidak terserap" yang paling jelas.
- **Bali**: TPT 1.49% dan NEET 5.33% (keduanya terendah nasional), jauh di bawah perkiraan dari pendidikannya. Ini kasus positif: ekonomi jasa/pariwisata menyerap
  tenaga kerja muda.
- **Jawa Barat & Banten**: pusat industri, tetapi TPT di atas perkiraan dan TPT SMK Jawa Barat tertinggi nasional
  (12.81%). Diduga pasokan lulusan melampaui penyerapan (perlu data lowongan untuk memastikan).

## 5. Klaster provinsi (K-Means, k = 4)

Variabel: RLS, APS_16_18, PEKERJA_FORMAL, TPT, NEET, MISKIN (distandarisasi robust median/IQR, dipangkas ±3).

| k | silhouette | ari_kmeans_vs_ward | ukuran |
|---|---|---|---|
| 2 | 0.61 | 1.0 | 36 / 2 |
| 3 | 0.423 | 0.882 | 31 / 5 / 2 |
| 4 | 0.31 | 0.752 | 22 / 9 / 5 / 2 |
| 5 | 0.243 | 0.639 | 13 / 10 / 8 / 5 / 2 |
| 6 | 0.268 | 0.639 | 13 / 10 / 8 / 3 / 2 / 2 |

k = 4 dipilih karena k = 2 hanya memisahkan 2 provinsi Papua (tidak informatif), sedangkan k = 4 memunculkan
kelompok "pendidikan cukup tetapi pengangguran tinggi" yang menjawab pertanyaan riset. **Kejujuran metodologis:** struktur
klaster tergolong lemah-sedang (silhouette 0.31; kesepakatan K-Means vs Ward ARI 0.75;
stabilitas bootstrap ARI 0.61). Klaster adalah **segmentasi untuk kebijakan**, bukan kelompok alami yang tegas.
Provinsi di perbatasan antarklaster (stabilitas < 0.7): Sumatera Utara, Sumatera Barat, Nusa Tenggara Timur, Kalimantan Utara, Gorontalo, Maluku Utara, Papua Barat, Papua Selatan.

| klaster | jumlah_provinsi | RLS | APS_16_18 | PEKERJA_FORMAL | TPT | NEET | MISKIN | IPM | TPT_SMK | TPT_PT |
|---|---|---|---|---|---|---|---|---|---|---|
| A. Pendidikan tinggi, terserap pasar kerja formal | 5 | 10.2 | 88.24 | 56.78 | 5.18 | 12.83 | 4.44 | 80.53 | 6.76 | 5.26 |
| B. Pendidikan cukup, pengangguran & NEET tinggi | 9 | 9.56 | 77.53 | 44.34 | 6.27 | 24.97 | 12.33 | 74.69 | 9.33 | 5.87 |
| C. Menengah: TPT rendah, mayoritas informal | 22 | 8.86 | 75.98 | 38.86 | 4.0 | 18.92 | 9.49 | 74.76 | 6.54 | 4.98 |
| D. Tertinggal struktural | 2 | 5.22 | 47.7 | 9.99 | 2.65 | 16.4 | 29.46 | 57.78 | 6.1 | 2.37 |

## 6. Rekomendasi per klaster

**A. Pendidikan tinggi, terserap pasar kerja formal** (5 provinsi: Kepulauan Riau, DKI Jakarta, DI Yogyakarta, Bali, Kalimantan Timur)

- Profil median: RLS 10.2 th, pekerja formal 56.8%, TPT 5.2%, TPT SMK 6.8%, NEET 12.8%, kemiskinan 4.4%
- Jaga kualitas penyerapan: fokus pada pencocokan lulusan perguruan tinggi dengan sektor bernilai tambah tinggi.
- Jadikan model rujukan kemitraan pendidikan-industri untuk klaster lain.

**B. Pendidikan cukup, pengangguran & NEET tinggi** (9 provinsi: Aceh, Jawa Barat, Banten, Sulawesi Utara, Maluku, Maluku Utara, Papua Barat, Papua Barat Daya, Papua)

- Profil median: RLS 9.6 th, pekerja formal 44.3%, TPT 6.3%, TPT SMK 9.3%, NEET 25.0%, kemiskinan 12.3%
- Prioritas utama kebijakan link-and-match: revitalisasi SMK berbasis kebutuhan industri lokal (TPT SMK tertinggi di klaster ini).
- Program transisi sekolah-ke-kerja untuk pemuda (magang, job matching) karena NEET tertinggi.
- Dorong penciptaan lapangan kerja formal; menambah lama sekolah saja tidak cukup.

**C. Menengah: TPT rendah, mayoritas informal** (22 provinsi: Sumatera Utara, Sumatera Barat, Riau, Jambi, Sumatera Selatan, Bengkulu, Lampung, Kepulauan Bangka Belitung, Jawa Tengah, Jawa Timur, Nusa Tenggara Barat, Nusa Tenggara Timur, Kalimantan Barat, Kalimantan Tengah, Kalimantan Selatan, Kalimantan Utara, Sulawesi Tengah, Sulawesi Selatan, Sulawesi Tenggara, Gorontalo, Sulawesi Barat, Papua Selatan)

- Profil median: RLS 8.9 th, pekerja formal 38.9%, TPT 4.0%, TPT SMK 6.5%, NEET 18.9%, kemiskinan 9.5%
- Formalisasi kerja (akses pembiayaan & legalitas usaha mikro) karena TPT rendah menutupi dominasi sektor informal.
- Naikkan partisipasi pendidikan menengah atas dan tinggi agar pendidikan bisa menjadi pintu ke kerja formal.

**D. Tertinggal struktural** (2 provinsi: Papua Tengah, Papua Pegunungan)

- Profil median: RLS 5.2 th, pekerja formal 10.0%, TPT 2.6%, TPT SMK 6.1%, NEET 16.4%, kemiskinan 29.5%
- Intervensi dasar: akses SD-SMP (APS 7-15 tahun masih 68-82%) dan infrastruktur sekolah.
- Jangan memakai TPT/NEET sebagai ukuran keberhasilan: TPT rendah di sini mencerminkan ekonomi subsisten.
- Program afirmasi lintas sektor (pendidikan, kesehatan, ekonomi) dengan target pekerja formal dan kemiskinan.

## 7. Keterbatasan

- Data agregat provinsi: pola antarprovinsi tidak otomatis berlaku untuk individu (ecological fallacy).
- n = 38; korelasi dengan |ρ| < 0.32 tidak signifikan pada α = 5%.
- TPT menurut pendidikan per provinsi hanya tersedia untuk 2025; sebagian sel memiliki RSE tinggi (lihat laporan kualitas data).
- Belum ada data permintaan tenaga kerja (lowongan) sehingga *mismatch* disimpulkan dari sisi hasil, bukan diukur langsung.

# Laporan Kualitas Data

_Dibuat otomatis oleh `python -m src.etl.pipeline` pada 12-11-2026._

**Status pipeline: LULUS**  |  Tahun analisis (cross-section): **2025**  |  Baris `master_long`: 4,142  |  File sumber: 72

## 1. Cek wajib (gerbang kualitas)

| cek | status | detail |
|---|---|---|
| Tidak ada duplikat (provinsi, tahun, indikator) | LULUS | 0 duplikat |
| Kolom kunci terisi | LULUS | 0 sel kosong pada kolom kunci |
| Jumlah provinsi = 38 | LULUS | 38 provinsi |
| Tahun dalam rentang 2020-2026 | LULUS | 0 baris di luar rentang |
| Nilai dalam rentang wajar per indikator | LULUS | semua nilai dalam rentang |
| Indikator inti lengkap 38 provinsi pada tahun analisis 2025 | LULUS | 9 indikator inti lengkap |
| Validasi silang CSV vs publikasi IPM | LULUS | 152 nilai identik |
| Rekonsiliasi nilai ganda antarsumber | LULUS | 436 nilai identik |

## 2. Kelengkapan data

Jumlah provinsi yang memiliki nilai, per indikator dan tahun (target 38):

| indikator | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|
| APS_13_15 | 34 | 34 | 34 | 34 | 38 | 38 | 0 |
| APS_16_18 | 34 | 34 | 34 | 34 | 38 | 38 | 0 |
| APS_19_23 | 34 | 34 | 34 | 34 | 38 | 38 | 0 |
| APS_7_12 | 34 | 34 | 34 | 34 | 38 | 38 | 0 |
| HLS | 34 | 34 | 34 | 34 | 38 | 38 | 38 |
| IPM | 0 | 0 | 38 | 38 | 38 | 38 | 0 |
| MISKIN | 34 | 34 | 34 | 34 | 38 | 38 | 38 |
| MISKIN_DESA | 33 | 33 | 33 | 33 | 37 | 37 | 37 |
| MISKIN_KOTA | 34 | 34 | 34 | 34 | 38 | 38 | 38 |
| MISKIN_SEP | 34 | 34 | 34 | 0 | 38 | 38 | 0 |
| NEET | 34 | 34 | 34 | 34 | 38 | 38 | 0 |
| PEKERJA_FORMAL | 34 | 34 | 34 | 34 | 38 | 38 | 0 |
| PENGELUARAN | 34 | 34 | 34 | 34 | 38 | 38 | 38 |
| RLS | 34 | 34 | 34 | 34 | 38 | 38 | 38 |
| TPAK | 34 | 34 | 34 | 34 | 38 | 38 | 0 |
| TPT | 34 | 34 | 34 | 34 | 38 | 38 | 38 |
| TPT_FEB | 34 | 34 | 34 | 34 | 38 | 38 | 38 |

| status_data | jumlah_baris |
|---|---|
| tersedia | 3807 |
| tidak_tersedia | 328 |
| tidak_berlaku | 7 |

Catatan:
- 2020-2023: provinsi pemekaran Papua belum memiliki data (34 provinsi), kecuali IPM yang dihitung ulang BPS untuk 38 provinsi sejak 2022.
- 2026: baru tersedia untuk RLS, HLS, Pengeluaran, Kemiskinan Maret, dan TPT -> dipakai untuk tren saja, bukan cross-section.
- Kemiskinan September 2023 kosong pada tabel sumber; karena itu kemiskinan memakai periode **Maret** (lengkap 2020-2026).

Sel yang secara struktural tidak ada (bukan data hilang):

| indikator | provinsi | tahun |
|---|---|---|
| MISKIN_DESA | DKI Jakarta | 2020 |
| MISKIN_DESA | DKI Jakarta | 2021 |
| MISKIN_DESA | DKI Jakarta | 2022 |
| MISKIN_DESA | DKI Jakarta | 2023 |
| MISKIN_DESA | DKI Jakarta | 2024 |
| MISKIN_DESA | DKI Jakarta | 2025 |
| MISKIN_DESA | DKI Jakarta | 2026 |

## 3. Outlier tahun 2025 (ditandai, TIDAK dihapus)

Metode: Tukey IQR (k=1.5) dan robust z-score berbasis median/MAD (|z|>3.5). `ekstrem` = terdeteksi kedua metode.

| provinsi | jumlah_outlier |
|---|---|
| Papua Pegunungan | 12 |
| Papua Tengah | 10 |
| DI Yogyakarta | 4 |
| Papua Selatan | 3 |
| Papua | 2 |
| DKI Jakarta | 2 |
| Papua Barat | 2 |
| Bali | 1 |
| Kepulauan Riau | 1 |
| Papua Barat Daya | 1 |

| indikator | provinsi | nilai | robust_z | flag_outlier |
|---|---|---|---|---|
| APS_13_15 | Papua Tengah | 67.86 | -20.41 | rendah_ekstrem |
| APS_13_15 | Papua Pegunungan | 71.08 | -18.1 | rendah_ekstrem |
| APS_13_15 | Papua Selatan | 89.29 | -5.03 | rendah_ekstrem |
| APS_16_18 | Papua Tengah | 44.61 | -6.17 | rendah_ekstrem |
| APS_16_18 | Papua Pegunungan | 50.79 | -5.0 | rendah_ekstrem |
| APS_16_18 | DI Yogyakarta | 93.03 | 2.95 | tinggi_moderat |
| APS_19_23 | DI Yogyakarta | 54.72 | 3.95 | tinggi_ekstrem |
| APS_7_12 | Papua Tengah | 80.13 | -49.74 | rendah_ekstrem |
| APS_7_12 | Papua Pegunungan | 82.24 | -44.27 | rendah_ekstrem |
| APS_7_12 | Papua Selatan | 91.65 | -19.86 | rendah_ekstrem |
| APS_7_12 | Papua | 97.51 | -4.66 | rendah_ekstrem |
| APS_7_12 | Papua Barat | 97.59 | -4.45 | rendah_ekstrem |
| HLS | Papua Tengah | 9.64 | -5.94 | rendah_ekstrem |
| HLS | Papua Pegunungan | 9.98 | -5.4 | rendah_ekstrem |
| HLS | DI Yogyakarta | 15.78 | 3.92 | tinggi_ekstrem |
| IPM | Papua Pegunungan | 54.91 | -8.5 | rendah_ekstrem |
| IPM | Papua Tengah | 60.64 | -6.05 | rendah_ekstrem |
| IPM | DI Yogyakarta | 82.48 | 3.27 | tinggi_moderat |
| IPM | DKI Jakarta | 85.05 | 4.37 | tinggi_ekstrem |
| MISKIN | Papua Tengah | 28.9 | 3.52 | tinggi_ekstrem |
| MISKIN | Papua Pegunungan | 30.03 | 3.73 | tinggi_ekstrem |
| MISKIN_DESA | Papua Barat | 25.88 | 2.69 | tinggi_moderat |
| MISKIN_DESA | Papua Selatan | 28.86 | 3.21 | tinggi_moderat |
| MISKIN_DESA | Papua Barat Daya | 29.71 | 3.36 | tinggi_moderat |
| MISKIN_DESA | Papua Pegunungan | 31.36 | 3.64 | tinggi_ekstrem |
| MISKIN_DESA | Papua Tengah | 36.54 | 4.55 | tinggi_ekstrem |
| MISKIN_DESA | Papua | 38.47 | 4.88 | tinggi_ekstrem |
| MISKIN_SEP | Papua Pegunungan | 27.21 | 3.38 | tinggi_moderat |
| MISKIN_SEP | Papua Tengah | 29.45 | 3.8 | tinggi_ekstrem |
| NEET | Bali | 5.33 | -3.81 | rendah_ekstrem |
| PEKERJA_FORMAL | Papua Pegunungan | 4.7 | -4.3 | rendah_ekstrem |
| PEKERJA_FORMAL | Papua Tengah | 15.28 | -3.02 | rendah_moderat |
| PEKERJA_FORMAL | Kepulauan Riau | 65.75 | 3.06 | tinggi_moderat |
| PENGELUARAN | Papua Pegunungan | 5861.0 | -3.06 | rendah_moderat |
| PENGELUARAN | DKI Jakarta | 20676.0 | 4.35 | tinggi_ekstrem |
| RLS | Papua Pegunungan | 4.3 | -4.68 | rendah_ekstrem |
| RLS | Papua Tengah | 6.13 | -2.88 | rendah_moderat |
| TPAK | Papua Pegunungan | 90.66 | 5.79 | tinggi_ekstrem |

Implikasi analisis:
- Outlier didominasi provinsi Papua (kondisi nyata, bukan salah input) -> akan mendominasi korelasi Pearson dan K-Means.
- Gunakan **Spearman** untuk korelasi dan **standarisasi robust** (median/IQR) untuk klaster.
- Jalankan analisis **dengan dan tanpa** provinsi `kandidat_uji_sensitivitas = TRUE` di `master_wide_2025.csv`; laporkan bila kesimpulan berubah.

## 4. Patahan seri akibat pemekaran

Angka provinsi induk pada tahun berikut masih mencakup wilayah provinsi baru -> **jangan dibandingkan** dengan tahun sesudahnya.

| provinsi | indikator | tahun_tidak_sebanding |
|---|---|---|
| Papua | APS_13_15 | 2020-2023 |
| Papua | APS_16_18 | 2020-2023 |
| Papua | APS_19_23 | 2020-2023 |
| Papua | APS_7_12 | 2020-2023 |
| Papua | HLS | 2020-2023 |
| Papua | MISKIN | 2020-2023 |
| Papua | MISKIN_DESA | 2020-2023 |
| Papua | MISKIN_KOTA | 2020-2023 |
| Papua | MISKIN_SEP | 2020-2022 |
| Papua | NEET | 2020-2023 |
| Papua | PEKERJA_FORMAL | 2020-2023 |
| Papua | PENGELUARAN | 2020-2023 |
| Papua | RLS | 2020-2023 |
| Papua | TPAK | 2020-2023 |
| Papua | TPT | 2020-2023 |
| Papua | TPT_FEB | 2020-2023 |
| Papua Barat | APS_13_15 | 2020-2023 |
| Papua Barat | APS_16_18 | 2020-2023 |
| Papua Barat | APS_19_23 | 2020-2023 |
| Papua Barat | APS_7_12 | 2020-2023 |
| Papua Barat | HLS | 2020-2023 |
| Papua Barat | MISKIN | 2020-2023 |
| Papua Barat | MISKIN_DESA | 2020-2023 |
| Papua Barat | MISKIN_KOTA | 2020-2023 |
| Papua Barat | MISKIN_SEP | 2020-2022 |
| Papua Barat | NEET | 2020-2023 |
| Papua Barat | PEKERJA_FORMAL | 2020-2023 |
| Papua Barat | PENGELUARAN | 2020-2023 |
| Papua Barat | RLS | 2020-2023 |
| Papua Barat | TPAK | 2020-2023 |
| Papua Barat | TPT | 2020-2023 |
| Papua Barat | TPT_FEB | 2020-2023 |

## 5. Lonjakan antartahun tidak lazim

Perubahan antartahun yang menyimpang dari perubahan median provinsi lain pada tahun yang sama
(|robust z| > 5) dan perubahan relatif >= 15%.
Guncangan bersama (mis. COVID) tidak ikut ditandai. Flag ini berarti "perlu dicek", bukan "salah".

| indikator | provinsi | tahun | nilai | perubahan_antartahun |
|---|---|---|---|---|
| APS_19_23 | Kepulauan Riau | 2024 | 26.28 | 3.85 |
| APS_19_23 | DKI Jakarta | 2024 | 32.98 | 4.55 |
| APS_19_23 | Maluku | 2025 | 29.66 | -9.92 |
| APS_19_23 | Papua Pegunungan | 2025 | 12.48 | -5.36 |
| MISKIN_DESA | Kalimantan Utara | 2025 | 5.98 | -3.25 |
| MISKIN_KOTA | Papua Pegunungan | 2025 | 13.0 | -3.56 |
| MISKIN_KOTA | Papua Pegunungan | 2026 | 16.72 | 3.72 |
| NEET | Papua Tengah | 2025 | 21.18 | -10.02 |
| TPT | Riau | 2021 | 4.42 | -1.9 |
| TPT | DKI Jakarta | 2021 | 8.5 | -2.45 |
| TPT | Banten | 2021 | 8.98 | -1.66 |
| TPT | Kepulauan Riau | 2022 | 8.23 | -1.68 |
| TPT | Bali | 2023 | 2.69 | -2.11 |
| TPT_FEB | Kepulauan Riau | 2021 | 10.12 | 4.14 |
| TPT_FEB | DKI Jakarta | 2021 | 8.51 | 3.36 |
| TPT_FEB | Bali | 2021 | 5.42 | 4.17 |
| TPT_FEB | Kalimantan Utara | 2021 | 4.67 | -1.04 |
| TPT_FEB | Kepulauan Riau | 2022 | 8.02 | -2.1 |
| TPT_FEB | DKI Jakarta | 2024 | 6.03 | -1.54 |
| TPT_FEB | Bali | 2024 | 1.87 | -1.86 |
| TPT_FEB | Papua | 2025 | 6.92 | 1.11 |

Ditandai manual untuk diverifikasi:

| indikator | provinsi | tahun | nilai |
|---|---|---|---|
| APS_19_23 | Maluku | 2025 | 29.66 |

## 6. Keandalan estimasi (RSE)

Nilai yang ditandai BPS dengan RSE 25-50% (estimasi kurang andal karena sampel kecil):

| indikator | provinsi | tahun | nilai |
|---|---|---|---|
| TPT_FEB | Sulawesi Barat | 2024 | 3.02 |
| TPT_FEB | Papua Selatan | 2024 | 4.75 |
| TPT_FEB | Papua Pegunungan | 2024 | 1.18 |

## 7. Validasi silang antarsumber

Nilai CSV dibandingkan dengan Lampiran 1 publikasi IPM (sumber berbeda, seharusnya identik):

| indikator | tahun | dibandingkan | tidak_cocok | selisih_maks |
|---|---|---|---|---|
| RLS | 2025 | 38 | 0 | 0.0 |
| HLS | 2025 | 38 | 0 | 0.0 |
| PENGELUARAN | 2025 | 38 | 0 | 0.0 |
| IPM | 2025 | 38 | 0 | 0.0 |

Rekonsiliasi nilai ganda (indikator yang sama tersedia di lebih dari satu tabel BPS; nilai sumber
prioritas utama yang dipakai, sumber lain hanya mengisi yang kosong):

| indikator | sumber_id_dipakai | sumber_id_pembanding | tahun | dibandingkan | berbeda | selisih_maks |
|---|---|---|---|---|---|---|
| TPT | tpt | tpt_provinsi | 2020-2025 | 218 | 0 | 0.0 |
| TPT_FEB | tpt | tpt_provinsi | 2020-2025 | 218 | 0 | 0.0 |

## 8. Sebaran data tahun 2025

| indikator | count | mean | std | min | median | max | skewness | saran_korelasi |
|---|---|---|---|---|---|---|---|---|
| APS_13_15 | 38.0 | 94.659 | 6.359 | 67.86 | 96.3 | 99.6 | -3.547 | Spearman (sebaran miring) |
| APS_16_18 | 38.0 | 76.745 | 8.951 | 44.61 | 77.35 | 93.03 | -1.619 | Spearman (sebaran miring) |
| APS_19_23 | 38.0 | 29.482 | 7.208 | 12.48 | 29.075 | 54.72 | 0.653 | Pearson/Spearman |
| APS_7_12 | 38.0 | 98.057 | 4.249 | 80.13 | 99.305 | 99.74 | -3.685 | Spearman (sebaran miring) |
| HLS | 38.0 | 13.262 | 1.028 | 9.64 | 13.34 | 15.78 | -1.655 | Spearman (sebaran miring) |
| IPM | 38.0 | 74.248 | 5.196 | 54.91 | 74.815 | 85.05 | -1.582 | Spearman (sebaran miring) |
| MISKIN | 38.0 | 10.611 | 6.551 | 3.72 | 9.49 | 30.03 | 1.456 | Spearman (sebaran miring) |
| MISKIN_DESA | 37.0 | 13.666 | 9.467 | 4.25 | 10.46 | 38.47 | 1.325 | Spearman (sebaran miring) |
| MISKIN_KOTA | 38.0 | 6.683 | 2.575 | 3.27 | 6.185 | 13.0 | 0.803 | Pearson/Spearman |
| MISKIN_SEP | 38.0 | 10.269 | 6.269 | 3.42 | 9.345 | 29.45 | 1.449 | Spearman (sebaran miring) |
| NEET | 38.0 | 19.752 | 4.813 | 5.33 | 19.33 | 29.52 | -0.491 | Pearson/Spearman |
| PEKERJA_FORMAL | 38.0 | 40.942 | 11.278 | 4.7 | 40.38 | 65.75 | -0.64 | Pearson/Spearman |
| PENGELUARAN | 38.0 | 11962.474 | 2543.098 | 5861.0 | 11977.5 | 20676.0 | 0.773 | Pearson/Spearman |
| RLS | 38.0 | 9.029 | 1.24 | 4.3 | 9.05 | 11.59 | -1.529 | Spearman (sebaran miring) |
| TPAK | 38.0 | 70.517 | 4.765 | 63.98 | 69.56 | 90.66 | 2.08 | Spearman (sebaran miring) |
| TPT | 38.0 | 4.468 | 1.381 | 1.49 | 4.21 | 6.96 | 0.112 | Pearson/Spearman |
| TPT_FEB | 38.0 | 4.43 | 1.389 | 1.58 | 4.19 | 6.92 | 0.201 | Pearson/Spearman |

## 9. Sensitivitas pilihan periode survei

Apakah memakai TPT Agustus (bukan Februari) dan kemiskinan Maret (bukan September) mengubah peringkat provinsi?

| indikator_utama | pembanding | tahun | n | spearman | rata2_selisih_abs | geser_peringkat_maks | provinsi_paling_bergeser |
|---|---|---|---|---|---|---|---|
| TPT | TPT_FEB | 2024 | 38 | 0.943 | 0.3 | 9 | Kepulauan Bangka Belitung |
| TPT | TPT_FEB | 2025 | 38 | 0.966 | 0.23 | 9 | Papua Selatan |
| MISKIN | MISKIN_SEP | 2024 | 38 | 0.993 | 0.67 | 4 | Kalimantan Utara |
| MISKIN | MISKIN_SEP | 2025 | 38 | 0.999 | 0.38 | 1 | Jawa Tengah |

Spearman mendekati 1 berarti urutan provinsi praktis sama -> kesimpulan korelasi/klaster tidak bergantung pada pilihan periode.

## 10. Ketimpangan komposisi sampel

| kelompok_wilayah | jumlah_provinsi |
|---|---|
| Jawa | 6 |
| Luar Jawa | 32 |

- Jawa hanya 6 dari 38 provinsi; provinsi Papua 6 dari 38 meski penduduknya kecil.
- Rata-rata sederhana antarprovinsi **bukan** angka nasional. Untuk kartu KPI gunakan baris Indonesia di `nasional_long.csv`.
- Bandingkan kelompok wilayah dengan **median**, bukan rata-rata.

## 11. Keterbatasan & data yang belum tersedia

- Indikator terdaftar tetapi belum ada datanya: `INTERNET` (Persentase Penduduk yang Mengakses Internet).
- TPT menurut pendidikan saat ini hanya level **nasional** (`nasional_long.csv`); versi per provinsi menunggu data tambahan.
- Upah hanya nasional per sektor (KBLI), dipakai sebagai konteks.
- Periode tabel TPT menurut pendidikan tidak tertulis di file; diasumsikan Agustus (perlu dicek di metadata tabel BPS).

# Kamus Data

_Dibuat otomatis oleh pipeline ETL pada 12-11-2026._

## Indikator level provinsi

| kode | nama | lapisan | satuan | periode | arah | peran | min | max |
|---|---|---|---|---|---|---|---|---|
| RLS | Rata-rata Lama Sekolah | Input pendidikan | tahun | Tahunan (Susenas Maret) | positif | inti | 0 | 16 |
| APS_7_12 | Angka Partisipasi Sekolah 7-12 tahun | Input pendidikan | persen | Tahunan (Susenas Maret) | positif | pendukung | 0 | 100 |
| APS_13_15 | Angka Partisipasi Sekolah 13-15 tahun | Input pendidikan | persen | Tahunan (Susenas Maret) | positif | pendukung | 0 | 100 |
| APS_16_18 | Angka Partisipasi Sekolah 16-18 tahun | Input pendidikan | persen | Tahunan (Susenas Maret) | positif | inti | 0 | 100 |
| APS_19_23 | Angka Partisipasi Sekolah 19-23 tahun | Input pendidikan | persen | Tahunan (Susenas Maret) | positif | inti | 0 | 100 |
| HLS | Harapan Lama Sekolah | Input pendidikan | tahun | Tahunan (Susenas Maret) | positif | inti | 0 | 18 |
| IPM | Indeks Pembangunan Manusia | Output SDM | indeks | Tahunan | positif | inti | 0 | 100 |
| PENGELUARAN | Pengeluaran per Kapita Disesuaikan | Outcome ekonomi | ribu rupiah/orang/tahun | Tahunan (Susenas Maret) | positif | pendukung | 1000 | 50000 |
| TPT | Tingkat Pengangguran Terbuka (Agustus) | Outcome ekonomi | persen | Agustus (Sakernas) | negatif | inti | 0 | 100 |
| TPT_FEB | Tingkat Pengangguran Terbuka (Februari) | Outcome ekonomi | persen | Februari (Sakernas) | negatif | sensitivitas | 0 | 100 |
| TPAK | Tingkat Partisipasi Angkatan Kerja (Agustus) | Outcome ekonomi | persen | Agustus (Sakernas) | positif | pendukung | 0 | 100 |
| PEKERJA_FORMAL | Persentase Tenaga Kerja Formal | Outcome ekonomi | persen | Agustus (Sakernas) | positif | inti | 0 | 100 |
| NEET | Persentase Pemuda 15-24 Tahun NEET | Outcome ekonomi | persen | Agustus (Sakernas) | negatif | inti | 0 | 100 |
| TPT_SD | TPT Lulusan SD ke bawah (Agustus) | Outcome ekonomi | persen | Agustus (Sakernas) | negatif | pendukung | 0 | 100 |
| TPT_SMP | TPT Lulusan SMP (Agustus) | Outcome ekonomi | persen | Agustus (Sakernas) | negatif | pendukung | 0 | 100 |
| TPT_SMA | TPT Lulusan SMA umum (Agustus) | Outcome ekonomi | persen | Agustus (Sakernas) | negatif | inti | 0 | 100 |
| TPT_SMK | TPT Lulusan SMK (Agustus) | Outcome ekonomi | persen | Agustus (Sakernas) | negatif | inti | 0 | 100 |
| TPT_PT | TPT Lulusan Perguruan Tinggi (Diploma I-IV, S1-S3) (Agustus) | Outcome ekonomi | persen | Agustus (Sakernas) | negatif | inti | 0 | 100 |
| MISKIN | Persentase Penduduk Miskin (Maret) | Outcome ekonomi | persen | Maret (Susenas) | negatif | inti | 0 | 100 |
| MISKIN_KOTA | Persentase Penduduk Miskin Perkotaan (Maret) | Inklusivitas | persen | Maret (Susenas) | negatif | pendukung | 0 | 100 |
| MISKIN_DESA | Persentase Penduduk Miskin Perdesaan (Maret) | Inklusivitas | persen | Maret (Susenas) | negatif | pendukung | 0 | 100 |
| MISKIN_SEP | Persentase Penduduk Miskin (September) | Outcome ekonomi | persen | September (Susenas) | negatif | sensitivitas | 0 | 100 |
| INTERNET | Persentase Penduduk yang Mengakses Internet | Output SDM | persen | Tahunan (Susenas Maret) | positif | inti | 0 | 100 |

## Kolom penting `master_long.csv`

| kolom | keterangan |
|---|---|
| kode_provinsi | Kode wilayah BPS (berbeda dengan kode Kemendagri untuk provinsi Papua) |
| iso_3166_2 | Kode ISO provinsi, untuk peta (provinsi baru Papua mungkin belum dikenali sebagian platform peta) |
| pulau / kelompok_wilayah | Kolom bantu filter (Jawa vs Luar Jawa) |
| peran | inti = analisis utama; pendukung = konteks; sensitivitas = uji ketahanan saja |
| status_data | tersedia | tidak_tersedia (BPS menulis '-' atau '...') | tidak_berlaku (mis. desa di DKI) |
| catatan_keandalan | Diisi bila BPS menandai estimasi dengan RSE 25-50% |
| robust_z | Jarak dari median antarprovinsi dalam satuan MAD (|z|>3,5 = outlier) |
| flag_outlier | tinggi/rendah + moderat (1 metode) atau ekstrem (IQR dan robust z) |
| flag_patahan_seri | TRUE bila angka provinsi induk masih mencakup wilayah sebelum pemekaran |
| perubahan_antartahun | Selisih terhadap tahun sebelumnya (kosong bila tidak sebanding) |
| flag_lonjakan | TRUE bila perubahan antartahun tidak lazim dibanding provinsi lain |
| flag_kualitas | Gabungan seluruh flag dalam satu teks, untuk filter cepat di dashboard |
| tahun_analisis | TRUE untuk baris tahun potret cross-section |

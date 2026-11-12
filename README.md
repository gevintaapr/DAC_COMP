# DAC_COMP: Pendidikan dan Pembangunan SDM Indonesia

Pipeline ETL untuk menyiapkan data BPS sebagai bahan dashboard dan analisis
(kerangka lengkap ada di `KERANGKA DATA SLAYER.md`).

## Menjalankan

```bash
pip install -r requirements.txt
python -m src.etl.pipeline     # ETL penuh, sekitar 1 menit (membaca 3 PDF)
python -m pytest -q            # uji otomatis
```

Pipeline berhenti dengan status gagal bila ada cek wajib yang tidak lulus.
Laporan kualitas data tetap ditulis supaya penyebabnya bisa dilihat.

## Alur

| Tahap | Isi | File |
|---|---|---|
| Extract | Membaca CSV dan PDF BPS apa adanya, lalu memastikan format file tidak berubah (`cek_header`, tahun di nama file harus sama dengan isi) | `src/etl/extract.py` |
| Transform | Menyamakan nama provinsi ke 38 nama baku berkode BPS, mengubah sel `-`/`...`/`(a)` menjadi angka, menambahkan metadata, lalu menyusun format panjang | `src/etl/transform.py` |
| Validate | **Cek wajib**: duplikat, rentang wajar, kelengkapan 38 provinsi. **Penandaan**: outlier, patahan seri pemekaran, lonjakan antartahun, RSE, validasi silang dengan publikasi IPM | `src/etl/validate.py` |
| Load | Menulis dataset dan laporan | `src/etl/load.py` |

Semua aturan ada di `config/`: master provinsi, metadata indikator, sumber file, dan ambang batas.

## Output

| File | Kegunaan |
|---|---|
| `data/processed/master_long.csv` | Tabel utama dashboard: 38 provinsi × tahun × indikator, lengkap dengan flag |
| `data/processed/master_wide_2025.csv` | Satu baris per provinsi (potret 2025), bahan korelasi dan klaster |
| `data/processed/nasional_long.csv` | Angka nasional (untuk kartu KPI), TPT menurut pendidikan, upah per sektor |
| `data/processed/angkatan_kerja_pendidikan_provinsi_2025.csv` | Jumlah angkatan kerja & penganggur per provinsi × pendidikan (bobot untuk agregasi tertimbang) |
| `reports/laporan_kualitas_data.md` | Hasil seluruh pemeriksaan data |
| `reports/kamus_data.md` | Definisi indikator dan kolom |
| `reports/flag_kualitas.csv` | Daftar nilai yang diberi flag |
| `reports/inventaris_sumber.csv` | Daftar file sumber beserta hash SHA-256 (jejak audit) |

## Keputusan data

- **Tahun analisis 2025**: tahun terbaru yang lengkap untuk 38 provinsi. Data 2026 (RLS, HLS, Pengeluaran, Kemiskinan Maret, TPT) hanya dipakai untuk tren.
- **TPT/TPAK periode Agustus**, **kemiskinan periode Maret**. Periode Februari dan September tetap disimpan dengan peran `sensitivitas` untuk uji ketahanan.
- **Outlier ditandai, tidak dihapus.** Gunakan Spearman dan standarisasi robust, lalu jalankan analisis dengan dan tanpa `kandidat_uji_sensitivitas`.
- **Patahan seri Papua**: angka Papua dan Papua Barat sebelum 2024 masih mencakup wilayah pemekaran, sehingga tidak boleh dibandingkan dengan tahun sesudahnya.
- **Sumber ganda**: TPT tersedia di dua tabel BPS (`TPT UMUM` dan `TPT provinsi`). Nilai dari sumber prioritas utama yang dipakai, sumber kedua hanya mengisi tahun yang kosong (2026), dan semua nilai yang tumpang tindih dicek kesamaannya.
- **TPT menurut pendidikan per provinsi** (`TPT_SD`, `TPT_SMP`, `TPT_SMA`, `TPT_SMK`, `TPT_PT`) dihitung dari publikasi *Keadaan Angkatan Kerja Agustus 2025* (Tabel 44 & 123): penganggur / angkatan kerja × 100. PT = Diploma I–IV + S1–S3 (tabel pengangguran BPS tidak memisahkannya). Hasilnya dicek ulang: TPT total per provinsi identik dengan TPT Agustus di tabel BPS dan TPT nasional per jenjang identik dengan tabel nasional. Publikasi Februari 2026 belum dipakai.
- **Akses internet di luar cakupan** sementara (keputusan tim); entri sumbernya tetap disiapkan dan nonaktif sampai foldernya ada.
- Kode provinsi memakai **kode BPS**, yang berbeda dengan kode Kemendagri untuk provinsi Papua. Untuk peta, gunakan nama atau `iso_3166_2`.

## Menambah data baru

1. Simpan file ekspor BPS di `Dataset/<nama folder>/`, dengan tahun di akhir nama file (contoh: `..., 2025.csv`).
2. Tambahkan entri di `config/sumber.yaml` dan metadata di `config/indikator.yaml`.
   Entri **Akses Internet** sudah disiapkan dan aktif otomatis begitu folder `Dataset/Akses Internet/` ada.
3. Jalankan ulang pipeline dan tes.

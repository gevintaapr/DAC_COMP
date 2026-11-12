"""LOAD: menulis dataset siap pakai (dashboard & analisis) serta laporan kualitas data."""
from __future__ import annotations

import logging
from datetime import date

import pandas as pd

from .utils import Config

log = logging.getLogger(__name__)

KOLOM_FLAG = ["robust_z", "flag_outlier", "flag_patahan_seri", "perubahan_antartahun",
              "flag_lonjakan", "flag_perlu_verifikasi", "flag_kualitas"]


def _md(df: pd.DataFrame, index: bool = False) -> str:
    """Tabel markdown sederhana (tanpa dependensi tambahan)."""
    if df is None or df.empty:
        return "_(tidak ada)_\n"
    d = df.reset_index() if index else df
    d = d.astype(object).where(d.notna(), "")
    head = "| " + " | ".join(map(str, d.columns)) + " |"
    sep = "|" + "|".join("---" for _ in d.columns) + "|"
    body = ["| " + " | ".join(str(v) for v in row) + " |" for row in d.itertuples(index=False)]
    return "\n".join([head, sep, *body]) + "\n"


def buat_wide(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Satu baris per provinsi untuk tahun analisis: input korelasi & klaster."""
    ta = cfg.settings["tahun_analisis"]
    d = df[df["tahun"] == ta]
    w = d.pivot_table(index="kode_provinsi", columns="indikator", values="nilai")
    urutan = [i for i in cfg.indikator if i in w.columns]
    w = w[urutan]
    atribut = cfg.provinsi.rename(columns={"kode_bps": "kode_provinsi"}).set_index("kode_provinsi")
    inti = [i for i, m in cfg.indikator.items() if m["peran"] == "inti"]
    eks = d[d["flag_outlier"].str.endswith("ekstrem") & d["indikator"].isin(inti)]
    ringkas = eks.groupby("kode_provinsi").agg(
        n_outlier_ekstrem_inti=("indikator", "size"),
        indikator_outlier_ekstrem=("indikator", lambda s: ";".join(sorted(s))))
    out = atribut.join(w).join(ringkas)
    out["n_outlier_ekstrem_inti"] = out["n_outlier_ekstrem_inti"].fillna(0).astype(int)
    out["indikator_outlier_ekstrem"] = out["indikator_outlier_ekstrem"].fillna("")
    # Provinsi yang ekstrem di banyak indikator inti -> kandidat uji sensitivitas (analisis dengan & tanpa)
    out["kandidat_uji_sensitivitas"] = out["n_outlier_ekstrem_inti"] >= 3
    out.insert(0, "tahun", ta)
    return out.reset_index()


def _kamus(cfg: Config) -> str:
    meta = pd.DataFrame.from_dict(cfg.indikator, orient="index")
    meta.index.name = "kode"
    meta = meta[["nama", "lapisan", "satuan", "periode", "arah", "peran", "min", "max"]]
    kolom = pd.DataFrame([
        ("kode_provinsi", "Kode wilayah BPS (berbeda dengan kode Kemendagri untuk provinsi Papua)"),
        ("iso_3166_2", "Kode ISO provinsi, untuk peta (provinsi baru Papua mungkin belum dikenali sebagian platform peta)"),
        ("pulau / kelompok_wilayah", "Kolom bantu filter (Jawa vs Luar Jawa)"),
        ("peran", "inti = analisis utama; pendukung = konteks; sensitivitas = uji ketahanan saja"),
        ("status_data", "tersedia | tidak_tersedia (BPS menulis '-' atau '...') | tidak_berlaku (mis. desa di DKI)"),
        ("catatan_keandalan", "Diisi bila BPS menandai estimasi dengan RSE 25-50%"),
        ("robust_z", "Jarak dari median antarprovinsi dalam satuan MAD (|z|>3,5 = outlier)"),
        ("flag_outlier", "tinggi/rendah + moderat (1 metode) atau ekstrem (IQR dan robust z)"),
        ("flag_patahan_seri", "TRUE bila angka provinsi induk masih mencakup wilayah sebelum pemekaran"),
        ("perubahan_antartahun", "Selisih terhadap tahun sebelumnya (kosong bila tidak sebanding)"),
        ("flag_lonjakan", "TRUE bila perubahan antartahun tidak lazim dibanding provinsi lain"),
        ("flag_kualitas", "Gabungan seluruh flag dalam satu teks, untuk filter cepat di dashboard"),
        ("tahun_analisis", "TRUE untuk baris tahun potret cross-section"),
    ], columns=["kolom", "keterangan"])
    return (f"# Kamus Data\n\n_Dibuat otomatis oleh pipeline ETL pada {date.today():%d-%m-%Y}._\n\n"
            "## Indikator level provinsi\n\n" + _md(meta, index=True) +
            "\n## Kolom penting `master_long.csv`\n\n" + _md(kolom))


def _laporan(df, wide, nasional, laporan, inventaris, cfg) -> str:
    ta = cfg.settings["tahun_analisis"]
    cek = laporan["cek"]
    status = "LULUS" if laporan["lulus"] else "GAGAL"
    tersedia = df["status_data"].value_counts().rename_axis("status_data").reset_index(name="jumlah_baris")

    out_ta = df[(df["tahun"] == ta) & (df["flag_outlier"] != "")]
    out_ta = out_ta[["indikator", "provinsi", "nilai", "robust_z", "flag_outlier"]].sort_values(["indikator", "robust_z"])
    per_prov = (out_ta.groupby("provinsi").size().sort_values(ascending=False)
                .rename_axis("provinsi").reset_index(name="jumlah_outlier"))

    patah = (df[df["flag_patahan_seri"]].groupby(["provinsi", "indikator"])["tahun"]
             .agg(lambda s: f"{s.min()}-{s.max()}").reset_index(name="tahun_tidak_sebanding"))
    lonjak = df[df["flag_lonjakan"]][["indikator", "provinsi", "tahun", "nilai", "perubahan_antartahun"]]
    rse = df[df["flag_kualitas"].str.contains("rse_tinggi")][["indikator", "provinsi", "tahun", "nilai"]]
    verif = df[df["flag_perlu_verifikasi"]][["indikator", "provinsi", "tahun", "nilai"]]
    tb = df[df["status_data"] == "tidak_berlaku"][["indikator", "provinsi", "tahun"]]

    kel = wide.groupby("kelompok_wilayah").size().rename_axis("kelompok_wilayah").reset_index(name="jumlah_provinsi")
    ind_ada = set(df["indikator"])
    belum = [f"`{i}` ({m['nama']})" for i, m in cfg.indikator.items() if i not in ind_ada]

    teks = f"""# Laporan Kualitas Data

_Dibuat otomatis oleh `python -m src.etl.pipeline` pada {date.today():%d-%m-%Y}._

**Status pipeline: {status}**  |  Tahun analisis (cross-section): **{ta}**  |  Baris `master_long`: {len(df):,}  |  File sumber: {len(inventaris)}

## 1. Cek wajib (gerbang kualitas)

{_md(cek)}
## 2. Kelengkapan data

Jumlah provinsi yang memiliki nilai, per indikator dan tahun (target {cfg.settings['jumlah_provinsi']}):

{_md(laporan['cakupan'], index=True)}
{_md(tersedia)}
Catatan:
- 2020-2023: provinsi pemekaran Papua belum memiliki data (34 provinsi), kecuali IPM yang dihitung ulang BPS untuk 38 provinsi sejak 2022.
- 2026: baru tersedia untuk RLS, HLS, Pengeluaran, Kemiskinan Maret, dan TPT -> dipakai untuk tren saja, bukan cross-section.
- Kemiskinan September 2023 kosong pada tabel sumber; karena itu kemiskinan memakai periode **Maret** (lengkap 2020-2026).

Sel yang secara struktural tidak ada (bukan data hilang):

{_md(tb)}
## 3. Outlier tahun {ta} (ditandai, TIDAK dihapus)

Metode: Tukey IQR (k={cfg.settings['outlier']['iqr_k']}) dan robust z-score berbasis median/MAD (|z|>{cfg.settings['outlier']['robust_z']}). `ekstrem` = terdeteksi kedua metode.

{_md(per_prov)}
{_md(out_ta)}
Implikasi analisis:
- Outlier didominasi provinsi Papua (kondisi nyata, bukan salah input) -> akan mendominasi korelasi Pearson dan K-Means.
- Gunakan **Spearman** untuk korelasi dan **standarisasi robust** (median/IQR) untuk klaster.
- Jalankan analisis **dengan dan tanpa** provinsi `kandidat_uji_sensitivitas = TRUE` di `master_wide_{ta}.csv`; laporkan bila kesimpulan berubah.

## 4. Patahan seri akibat pemekaran

Angka provinsi induk pada tahun berikut masih mencakup wilayah provinsi baru -> **jangan dibandingkan** dengan tahun sesudahnya.

{_md(patah)}
## 5. Lonjakan antartahun tidak lazim

Perubahan antartahun yang menyimpang dari perubahan median provinsi lain pada tahun yang sama
(|robust z| > {cfg.settings['lonjakan_antartahun']['robust_z']}) dan perubahan relatif >= {cfg.settings['lonjakan_antartahun']['min_perubahan_persen']}%.
Guncangan bersama (mis. COVID) tidak ikut ditandai. Flag ini berarti "perlu dicek", bukan "salah".

{_md(lonjak)}
Ditandai manual untuk diverifikasi:

{_md(verif)}
## 6. Keandalan estimasi (RSE)

Nilai yang ditandai BPS dengan RSE 25-50% (estimasi kurang andal karena sampel kecil):

{_md(rse)}
## 7. Validasi silang antarsumber

Nilai CSV dibandingkan dengan Lampiran 1 publikasi IPM (sumber berbeda, seharusnya identik):

{_md(laporan['silang'])}
Rekonsiliasi nilai ganda (indikator yang sama tersedia di lebih dari satu tabel BPS; nilai sumber
prioritas utama yang dipakai, sumber lain hanya mengisi yang kosong):

{_md(laporan['rekonsiliasi'])}
Konsistensi tabel *Keadaan Angkatan Kerja Agustus 2025* (sumber TPT menurut pendidikan per provinsi):

{_md(laporan['kak'])}
TPT menurut pendidikan per provinsi dihitung = penganggur / angkatan kerja x 100 (definisi BPS).
Jenjang Perguruan Tinggi (PT) menggabungkan Diploma I-IV dan S1-S3 karena tabel pengangguran BPS tidak memisahkannya.
Sel yang ditandai BPS RSE 25-50% diberi flag `rse_tinggi`; sel NA (RSE > 50%) dibiarkan kosong.

## 8. Sebaran data tahun {ta}

{_md(laporan['distribusi'], index=True)}
## 9. Sensitivitas pilihan periode survei

Apakah memakai TPT Agustus (bukan Februari) dan kemiskinan Maret (bukan September) mengubah peringkat provinsi?

{_md(laporan['sensitivitas'])}
Spearman mendekati 1 berarti urutan provinsi praktis sama -> kesimpulan korelasi/klaster tidak bergantung pada pilihan periode.

## 10. Ketimpangan komposisi sampel

{_md(kel)}
- Jawa hanya 6 dari 38 provinsi; provinsi Papua 6 dari 38 meski penduduknya kecil.
- Rata-rata sederhana antarprovinsi **bukan** angka nasional. Untuk kartu KPI gunakan baris Indonesia di `nasional_long.csv`.
- Bandingkan kelompok wilayah dengan **median**, bukan rata-rata.

## 11. Keterbatasan & data yang belum tersedia

- Indikator terdaftar tetapi belum ada datanya: {', '.join(belum) if belum else '-'}.
- TPT menurut pendidikan **per provinsi** hanya tersedia untuk Agustus 2025 (5 jenjang); tren 2020-2025 hanya level nasional.
- Banyak sel TPT per pendidikan di provinsi kecil (terutama Papua) berstatus RSE tinggi -> tafsirkan hati-hati, utamakan perbandingan kelompok provinsi.
- Upah hanya nasional per sektor (KBLI), dipakai sebagai konteks.
- Periode tabel TPT menurut pendidikan (nasional) terverifikasi **Agustus**: identik dengan hitungan dari publikasi Keadaan Angkatan Kerja Agustus 2025.
"""
    return teks


def load(df: pd.DataFrame, nasional: pd.DataFrame, laporan: dict, inventaris: pd.DataFrame, cfg: Config,
         kak: pd.DataFrame | None = None) -> dict:
    ta = cfg.settings["tahun_analisis"]
    pdir, rdir = cfg.processed_dir, cfg.reports_dir
    pdir.mkdir(parents=True, exist_ok=True)
    rdir.mkdir(parents=True, exist_ok=True)

    df = df.copy()
    df["tahun_analisis"] = df["tahun"] == ta
    wide = buat_wide(df, cfg)

    paths = {
        "master_long": pdir / "master_long.csv",
        "master_wide": pdir / f"master_wide_{ta}.csv",
        "nasional_long": pdir / "nasional_long.csv",
        "kak": pdir / f"angkatan_kerja_pendidikan_provinsi_{ta}.csv",
        "laporan": rdir / "laporan_kualitas_data.md",
        "kamus": rdir / "kamus_data.md",
        "flag": rdir / "flag_kualitas.csv",
        "cakupan": rdir / "cakupan_data.csv",
        "inventaris": rdir / "inventaris_sumber.csv",
    }
    df.to_csv(paths["master_long"], index=False)
    wide.to_csv(paths["master_wide"], index=False)
    nasional.to_csv(paths["nasional_long"], index=False)
    if kak is not None and not kak.empty:
        # Jumlah orang (bobot) untuk agregasi tertimbang, mis. TPT SMK Jawa vs Luar Jawa
        kak[["kode_provinsi", "provinsi", "tahun", "jenis", "pendidikan", "jumlah", "rse_tinggi",
             "disembunyikan_bps", "tabel", "sumber", "file_sumber"]].sort_values(
            ["jenis", "kode_provinsi", "pendidikan"]).to_csv(paths["kak"], index=False)
    else:
        paths.pop("kak")
    flag_cols = ["kode_provinsi", "provinsi", "tahun", "indikator", "nilai", "satuan", "status_data",
                 "catatan_keandalan", *KOLOM_FLAG]
    df.loc[df["flag_kualitas"] != "", flag_cols].to_csv(paths["flag"], index=False)
    laporan["cakupan"].to_csv(paths["cakupan"])
    inventaris.to_csv(paths["inventaris"], index=False)
    paths["laporan"].write_text(_laporan(df, wide, nasional, laporan, inventaris, cfg), encoding="utf-8")
    paths["kamus"].write_text(_kamus(cfg), encoding="utf-8")
    for k, p in paths.items():
        log.info("Load: %-13s -> %s", k, p.relative_to(cfg.processed_dir.parents[1]))
    return paths

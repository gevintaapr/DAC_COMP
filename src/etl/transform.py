"""TRANSFORM: standarisasi nama wilayah, parsing angka, metadata, dan format panjang."""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from .utils import KODE_NASIONAL, Config, PipelineError, kunci_nama, parse_nilai, peta_wilayah

log = logging.getLogger(__name__)

KBLI = {
    "A": "Pertanian, Kehutanan, dan Perikanan",
    "B": "Pertambangan dan Penggalian",
    "C": "Industri Pengolahan",
    "D": "Pengadaan Listrik dan Gas",
    "E": "Pengadaan Air, Pengelolaan Sampah, Limbah, dan Daur Ulang",
    "F": "Konstruksi",
    "G": "Perdagangan Besar dan Eceran; Reparasi Mobil dan Sepeda Motor",
    "H": "Transportasi dan Pergudangan",
    "I": "Penyediaan Akomodasi dan Makan Minum",
    "J": "Informasi dan Komunikasi",
    "K": "Jasa Keuangan dan Asuransi",
    "L": "Real Estat",
    "M, N": "Jasa Perusahaan",
    "O": "Administrasi Pemerintahan, Pertahanan, dan Jaminan Sosial Wajib",
    "P": "Jasa Pendidikan",
    "Q": "Jasa Kesehatan dan Kegiatan Sosial",
    "R, S, T, U": "Jasa Lainnya",
    "Rata-Rata": "Rata-rata seluruh sektor",
}

KOLOM_LONG = [
    "kode_provinsi", "provinsi", "iso_3166_2", "pulau", "kelompok_wilayah", "tahun",
    "indikator", "nama_indikator", "lapisan", "peran", "nilai", "satuan", "periode",
    "status_data", "catatan_keandalan", "sumber", "file_sumber",
]


def _map_wilayah(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    peta = peta_wilayah(cfg.provinsi)
    kunci = df["wilayah_raw"].map(kunci_nama)
    tidak_dikenal = sorted(df.loc[~kunci.isin(peta), "wilayah_raw"].unique())
    if tidak_dikenal:
        raise PipelineError(f"Nama wilayah tidak dikenali (tambahkan ke config/provinsi.csv): {tidak_dikenal}")
    df = df.copy()
    df["kode_provinsi"] = kunci.map(lambda k: peta[k][0])
    return df


def _parse(df: pd.DataFrame) -> pd.DataFrame:
    hasil = df["nilai_raw"].map(parse_nilai)
    df = df.copy()
    df["nilai"] = [h[0] for h in hasil]
    df["status_data"] = [h[1] for h in hasil]
    df["catatan_keandalan"] = [h[2] for h in hasil]
    return df


def rekonsiliasi_sumber(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Satukan nilai ganda dari beberapa sumber untuk (wilayah, tahun, indikator) yang sama.

    Aturan: pakai sumber prioritas tertinggi yang nilainya tersedia; sumber lain menjadi pembanding.
    Kembalikan (data tanpa duplikat, tabel rekonsiliasi berisi setiap pasangan nilai yang tumpang tindih).
    """
    kunci = ["kode_provinsi", "tahun", "indikator"]
    df = df.assign(_urut=(df["status_data"] != "tersedia").astype(int))
    df = df.sort_values([*kunci, "_urut", "prioritas"], kind="stable")
    terpilih = df.drop_duplicates(kunci, keep="first")
    sisanya = df.drop(terpilih.index)
    rekon = pd.DataFrame()
    if not sisanya.empty:
        rekon = sisanya[[*kunci, "sumber_id", "nilai"]].merge(
            terpilih[[*kunci, "sumber_id", "nilai"]], on=kunci, suffixes=("_pembanding", "_dipakai"))
        rekon["selisih"] = (rekon["nilai_dipakai"] - rekon["nilai_pembanding"]).abs()
    return terpilih.drop(columns="_urut"), rekon


def _lengkapi_grid(df: pd.DataFrame, kode_prov: list[int]) -> pd.DataFrame:
    """Pastikan setiap (indikator, tahun) memuat ke-38 provinsi; yang tidak ada di file
    ditulis eksplisit sebagai 'tidak_tersedia' agar data hilang terlihat, bukan tersembunyi."""
    pasangan = df[["indikator", "tahun"]].drop_duplicates()
    grid = pasangan.merge(pd.DataFrame({"kode_provinsi": kode_prov}), how="cross")
    out = grid.merge(df, on=["indikator", "tahun", "kode_provinsi"], how="left")
    kosong = out["status_data"].isna()
    out.loc[kosong, "status_data"] = "tidak_tersedia"
    out.loc[kosong, "catatan_keandalan"] = ""
    for c in ("sumber", "file_sumber"):
        out[c] = out[c].fillna(out.groupby(["indikator", "tahun"])[c].transform("first"))
    return out


def transform_provinsi(raw: pd.DataFrame, cfg: Config) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Kembalikan (tabel panjang 38 provinsi, baris nasional 'Indonesia', tabel rekonsiliasi antarsumber)."""
    df, rekon = rekonsiliasi_sumber(_parse(_map_wilayah(raw, cfg)))

    tak_dikenal = sorted(set(df["indikator"]) - set(cfg.indikator))
    if tak_dikenal:
        raise PipelineError(f"Indikator tanpa metadata di config/indikator.yaml: {tak_dikenal}")

    nasional = df[df["kode_provinsi"] == KODE_NASIONAL].copy()
    prov = df[df["kode_provinsi"] != KODE_NASIONAL].copy()
    prov = _lengkapi_grid(prov, cfg.provinsi["kode_bps"].tolist())

    atribut = cfg.provinsi.rename(columns={"kode_bps": "kode_provinsi"})
    prov = prov.drop(columns=["wilayah_raw", "nilai_raw"], errors="ignore").merge(atribut, on="kode_provinsi", how="left")

    meta = pd.DataFrame.from_dict(cfg.indikator, orient="index")
    meta.index.name = "indikator"
    meta = meta.rename(columns={"nama": "nama_indikator"})[["nama_indikator", "lapisan", "peran", "satuan", "periode"]]
    prov = prov.merge(meta, left_on="indikator", right_index=True, how="left")
    nasional = nasional.merge(meta, left_on="indikator", right_index=True, how="left")

    # Sel yang secara struktural memang tidak ada (bukan data hilang)
    for aturan in cfg.settings.get("tidak_berlaku", []):
        m = (prov["provinsi"] == aturan["provinsi"]) & (prov["indikator"] == aturan["indikator"]) & prov["nilai"].isna()
        prov.loc[m, "status_data"] = "tidak_berlaku"

    prov["tahun"] = prov["tahun"].astype(int)
    prov = prov[KOLOM_LONG].sort_values(["indikator", "tahun", "kode_provinsi"]).reset_index(drop=True)
    log.info("Transform: %d baris provinsi (%d tersedia), %d nilai ganda direkonsiliasi",
             len(prov), (prov["status_data"] == "tersedia").sum(), len(rekon))
    return prov, nasional, rekon


def transform_nasional(raw_nas: pd.DataFrame, nasional_dari_prov: pd.DataFrame) -> pd.DataFrame:
    """Gabungkan baris 'Indonesia' dari tabel provinsi dengan tabel nasional (TPT pendidikan, upah)."""
    a = nasional_dari_prov.assign(kategori="Total", nama=nasional_dari_prov["nama_indikator"])
    a = a[["tahun", "indikator", "nama", "kategori", "periode", "nilai", "satuan", "status_data", "sumber", "file_sumber"]]

    b = _parse(raw_nas)
    b["kategori"] = b["kategori"].map(lambda k: f"{k} - {KBLI[k]}" if k in KBLI and k != "Rata-Rata" else KBLI.get(k, k))
    # periode: upah punya kolom Feb/Agu; TPT pendidikan memakai periode acuan dari config
    b["periode"] = np.where(b["periode"] == "Tahunan", b["periode_ref"], b["periode"])
    b = b[["tahun", "indikator", "nama", "kategori", "periode", "nilai", "satuan", "status_data", "sumber", "file_sumber"]]

    out = pd.concat([a, b], ignore_index=True)
    out["tahun"] = out["tahun"].astype(int)
    return out.sort_values(["indikator", "kategori", "periode", "tahun"]).reset_index(drop=True)

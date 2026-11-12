"""TRANSFORM: standarisasi nama wilayah, parsing angka, metadata, dan format panjang."""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from .utils import CATATAN_RSE, KODE_NASIONAL, Config, PipelineError, kunci_nama, parse_nilai, peta_wilayah

CATATAN_RSE_50 = "RSE > 50% (angka tidak dipublikasikan BPS)"

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


def siapkan_kak(kak: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Jumlah angkatan kerja & penganggur per provinsi x pendidikan dengan nama baku.

    Tabel pengangguran BPS menggabungkan Diploma dan Universitas, sehingga angkatan kerja
    Diploma + Universitas dijumlahkan menjadi PT agar pembilang dan penyebut sebanding.
    """
    if kak.empty:
        return kak
    df = _map_wilayah(kak, cfg)
    ak = df[df["jenis"] == "angkatan_kerja"]
    pt = (ak[ak["pendidikan"].isin(["DIPLOMA", "UNIVERSITAS"])]
          .groupby(["kode_provinsi", "wilayah_raw", "tahun", "jenis", "tabel", "file_sumber", "sumber", "sumber_id"], as_index=False)
          .agg(jumlah=("jumlah", "sum"), rse_tinggi=("rse_tinggi", "any"), disembunyikan_bps=("disembunyikan_bps", "any"))
          .assign(pendidikan="PT"))
    df = pd.concat([df, pt], ignore_index=True)
    nama = dict(zip(cfg.provinsi["kode_bps"], cfg.provinsi["provinsi"]))
    df["provinsi"] = df["kode_provinsi"].map(nama).fillna("Indonesia")
    return df.drop(columns="wilayah_raw")


def turunkan_tpt_pendidikan(kak_std: pd.DataFrame) -> pd.DataFrame:
    """TPT_<jenjang> = penganggur / angkatan kerja x 100 (definisi BPS)."""
    if kak_std.empty:
        return pd.DataFrame()
    kunci = ["kode_provinsi", "tahun", "pendidikan"]
    p = kak_std[kak_std["jenis"] == "pengangguran"].set_index(kunci)
    a = kak_std[kak_std["jenis"] == "angkatan_kerja"].set_index(kunci)
    j = p.join(a[["jumlah", "rse_tinggi", "disembunyikan_bps"]], rsuffix="_ak", how="inner").reset_index()
    j = j[j["pendidikan"] != "TOTAL"]
    tersembunyi = j["disembunyikan_bps"] | j["disembunyikan_bps_ak"]
    rse = (j["rse_tinggi"] | j["rse_tinggi_ak"]) & ~tersembunyi
    return pd.DataFrame(dict(
        kode_provinsi=j["kode_provinsi"], tahun=j["tahun"], indikator="TPT_" + j["pendidikan"],
        nilai=(j["jumlah"] / j["jumlah_ak"] * 100).round(2).where(~tersembunyi),
        status_data=np.where(tersembunyi, "tidak_tersedia", "tersedia"),
        catatan_keandalan=np.select([tersembunyi, rse], [CATATAN_RSE_50, CATATAN_RSE], ""),
        sumber=j["sumber"], file_sumber=j["file_sumber"], sumber_id=j["sumber_id"], prioritas=1))


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


def transform_provinsi(raw: pd.DataFrame, cfg: Config, turunan: pd.DataFrame | None = None
                       ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Kembalikan (tabel panjang 38 provinsi, baris nasional 'Indonesia', tabel rekonsiliasi antarsumber).

    `turunan`: indikator yang dihitung dari sumber lain (sudah berupa angka), mis. TPT menurut pendidikan.
    """
    df = _parse(_map_wilayah(raw, cfg))
    if turunan is not None and not turunan.empty:
        df = pd.concat([df, turunan], ignore_index=True)
    df, rekon = rekonsiliasi_sumber(df)

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

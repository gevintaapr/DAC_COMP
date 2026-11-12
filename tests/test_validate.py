"""Uji aturan validasi dengan data sintetis kecil (tidak bergantung pada file BPS)."""
import numpy as np
import pandas as pd

from src.etl.utils import load_config
from src.etl.validate import cek_wajib, tandai_lonjakan, tandai_outlier, tandai_patahan_seri

CFG = load_config()


def _frame(nilai_per_prov: dict, indikator="RLS", tahun=2025):
    return pd.DataFrame([
        dict(kode_provinsi=i, provinsi=p, tahun=tahun, indikator=indikator, nilai=v,
             status_data="tersedia" if pd.notna(v) else "tidak_tersedia", catatan_keandalan="")
        for i, (p, v) in enumerate(nilai_per_prov.items(), start=1)
    ])


def test_outlier_ditandai_bukan_dihapus():
    nilai = {f"P{i}": 9.0 + 0.1 * (i % 5) for i in range(20)}
    nilai["Ekstrem"] = 4.3
    df = tandai_outlier(_frame(nilai), CFG)
    assert len(df) == 21                                   # tidak ada baris yang hilang
    assert df.loc[df.provinsi == "Ekstrem", "flag_outlier"].item() == "rendah_ekstrem"
    assert (df.loc[df.provinsi != "Ekstrem", "flag_outlier"] == "").all()


def test_patahan_seri_pemekaran():
    rows = []
    for t, anak in [(2023, np.nan), (2024, 30.0)]:
        rows += _frame({"Papua": 20.0, "Papua Selatan": anak, "Papua Tengah": anak,
                        "Papua Pegunungan": anak, "Aceh": 10.0}, tahun=t).to_dict("records")
    df = tandai_patahan_seri(pd.DataFrame(rows), CFG)
    papua = df[df.provinsi == "Papua"].set_index("tahun")["flag_patahan_seri"]
    assert papua[2023] and not papua[2024]
    assert not df[df.provinsi == "Aceh"]["flag_patahan_seri"].any()


def test_lonjakan_abaikan_guncangan_bersama():
    rows = []
    for i in range(30):
        naik = 2.0                                           # semua provinsi naik bersama (mis. COVID)
        if i == 0:
            naik = 12.0                                      # satu provinsi menyimpang
        rows.append(dict(kode_provinsi=i, provinsi=f"P{i}", indikator="TPT", tahun=2020, nilai=5.0 + 0.01 * i))
        rows.append(dict(kode_provinsi=i, provinsi=f"P{i}", indikator="TPT", tahun=2021, nilai=5.0 + 0.01 * i + naik + 0.05 * (i % 3)))
    df = pd.DataFrame(rows).assign(flag_patahan_seri=False)
    df = tandai_lonjakan(df, CFG)
    ditandai = set(df[df.flag_lonjakan].provinsi)
    assert ditandai == {"P0"}


def test_cek_wajib_mendeteksi_duplikat_dan_rentang():
    base = _frame({p: 9.0 for p in CFG.provinsi["provinsi"]})
    base["kode_provinsi"] = CFG.provinsi["kode_bps"].values
    rusak = pd.concat([base, base.iloc[[0]]], ignore_index=True)
    rusak.loc[1, "nilai"] = 25.0                             # RLS > 16 tahun: mustahil
    hasil = cek_wajib(rusak, CFG).set_index("cek")["status"]
    assert hasil["Tidak ada duplikat (provinsi, tahun, indikator)"] == "GAGAL"
    assert hasil["Nilai dalam rentang wajar per indikator"] == "GAGAL"

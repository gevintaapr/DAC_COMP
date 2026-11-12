"""Uji integrasi: jalankan pipeline penuh pada data BPS di Dataset/ dan cek angka kunci."""
import pandas as pd
import pytest

from src.etl.pipeline import run


@pytest.fixture(scope="module")
def hasil():
    return run()


def _nilai(df, prov, ind, tahun):
    return df[(df.provinsi == prov) & (df.indikator == ind) & (df.tahun == tahun)]["nilai"].item()


def test_cek_wajib_lulus(hasil):
    assert hasil["laporan"]["lulus"]


def test_kunci_unik(hasil):
    assert not hasil["master"].duplicated(["kode_provinsi", "tahun", "indikator"]).any()


def test_angka_cocok_dengan_sumber(hasil):
    m = hasil["master"]
    assert _nilai(m, "DKI Jakarta", "RLS", 2025) == 11.59        # CSV RLS
    assert _nilai(m, "Papua Pegunungan", "IPM", 2025) == 54.91   # PDF Lampiran 3
    assert _nilai(m, "Aceh", "TPT", 2025) == 5.64                # TPT Agustus, bukan Februari
    assert _nilai(m, "Aceh", "MISKIN", 2025) == 12.33            # Kemiskinan Maret (kolom Jumlah)


def test_tahun_analisis_lengkap_38(hasil):
    w = pd.read_csv(hasil["paths"]["master_wide"])
    assert len(w) == 38
    for ind in ["RLS", "HLS", "APS_16_18", "IPM", "TPT", "PEKERJA_FORMAL", "NEET", "MISKIN"]:
        assert w[ind].notna().all(), ind


def test_flag_kualitas(hasil):
    m = hasil["master"]
    dki = m[(m.provinsi == "DKI Jakarta") & (m.indikator == "MISKIN_DESA")]
    assert (dki.status_data == "tidak_berlaku").all()
    assert m[(m.provinsi == "Papua") & (m.tahun == 2023) & (m.indikator == "RLS")]["flag_patahan_seri"].item()
    assert not m[(m.provinsi == "Papua") & (m.indikator == "IPM")]["flag_patahan_seri"].any()
    assert _nilai(m, "Papua Pegunungan", "RLS", 2025) == 4.30   # outlier tetap ada (tidak dihapus)


def test_validasi_silang_ipm(hasil):
    silang = hasil["laporan"]["silang"]
    assert silang["tidak_cocok"].sum() == 0 and silang["dibandingkan"].sum() == 152


def test_nasional(hasil):
    n = hasil["nasional"]
    smk = n[(n.indikator == "TPT_PENDIDIKAN") & (n.kategori == "SMA Kejuruan") & (n.tahun == 2025)]["nilai"].item()
    assert smk == 8.63
    assert set(n[n.indikator == "UPAH_SEKTOR"]["periode"]) == {"Februari", "Agustus"}

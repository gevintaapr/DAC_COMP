"""Uji tahap analisis (memakai keluaran pipeline ETL di data/processed/)."""
import pandas as pd
import pytest

from src.analysis import analisis as A


@pytest.fixture(scope="module")
def data():
    return A.muat()


def test_spearman_diagonal_dan_simetris(data):
    k = A.matriks_korelasi(data["wide"])
    assert (k[k.var_x == k.var_y]["rho"] == 1).all()
    p = k.pivot(index="var_x", columns="var_y", values="rho")
    assert (p - p.T).abs().max().max() < 1e-9


def test_klaster_lengkap_dan_bernama(data):
    kl = A.klaster(data["wide"])
    prov = kl["provinsi"]
    assert len(prov) == 38 and prov["klaster"].nunique() == A.K_KLASTER
    assert set(prov["kunci_klaster"]) == set(A.NAMA_KLASTER)
    tertinggal = prov[prov["kunci_klaster"] == "tertinggal"]["provinsi"]
    assert "Papua Pegunungan" in set(tertinggal)
    assert prov["stabilitas_keanggotaan"].between(0, 1).all()


def test_korelasi_parsial_pendidikan_kemiskinan(data):
    par = A.korelasi_parsial(data["wide"]).set_index("keterangan")["rho"]
    # temuan kunci 1: hubungan RLS-kemiskinan melemah tajam setelah dikontrol pekerja formal
    assert abs(par["Pendidikan vs kemiskinan, dikontrol pekerja formal"]) < abs(par["Pendidikan vs kemiskinan (tanpa kontrol)"])


def test_konvergensi_tanpa_wilayah_patahan(data):
    kon = A.konvergensi(data["long"], data["ta"])
    assert kon["n_provinsi"].iloc[0] == 32      # 34 provinsi lama minus Papua & Papua Barat (patahan seri)
    assert set(kon["arah"]) <= {"menyempit", "melebar", "relatif tetap"}

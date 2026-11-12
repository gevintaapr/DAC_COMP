import numpy as np
import pandas as pd
import pytest

from src.etl.utils import CATATAN_RSE, PipelineError, kunci_nama, parse_angka_id, parse_nilai, peta_wilayah, load_config


@pytest.mark.parametrize("raw, nilai, status, catatan", [
    ("5.64", 5.64, "tersedia", ""),
    ("11414", 11414.0, "tersedia", ""),
    ("1.18 (a)", 1.18, "tersedia", CATATAN_RSE),
    ("3.2*", 3.2, "tersedia", CATATAN_RSE),
])
def test_parse_nilai_angka(raw, nilai, status, catatan):
    assert parse_nilai(raw) == (nilai, status, catatan)


@pytest.mark.parametrize("raw", ["-", "...", "", None, "NA"])
def test_parse_nilai_kosong(raw):
    v, status, _ = parse_nilai(raw)
    assert np.isnan(v) and status == "tidak_tersedia"


def test_parse_nilai_tidak_dikenal_gagal():
    with pytest.raises(PipelineError):
        parse_nilai("12,5 %")


def test_parse_angka_format_indonesia():
    assert parse_angka_id("11.191") == 11191.0
    assert parse_angka_id("76,23") == 76.23


@pytest.mark.parametrize("varian, baku", [
    ("D I YOGYAKARTA", "DI Yogyakarta"),
    ("D.I. Yogyakarta", "DI Yogyakarta"),
    ("KEP. BANGKA BELITUNG", "Kepulauan Bangka Belitung"),
    ("Kepulauan Bangka Belitung", "Kepulauan Bangka Belitung"),
    ("KEPULAUAN RIAU", "Kepulauan Riau"),
    ("DKI JAKARTA", "DKI Jakarta"),
    ("PAPUA PEGUNUNGAN", "Papua Pegunungan"),
    ("INDONESIA", "Indonesia"),
])
def test_normalisasi_nama_provinsi(varian, baku):
    peta = peta_wilayah(load_config().provinsi)
    assert peta[kunci_nama(varian)][1] == baku


def test_master_provinsi_38_unik():
    prov = load_config().provinsi
    assert len(prov) == 38
    assert prov["kode_bps"].is_unique and prov["provinsi"].is_unique
    assert prov["provinsi"].map(kunci_nama).is_unique

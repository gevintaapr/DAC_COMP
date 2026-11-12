"""Fungsi bantu: konfigurasi, normalisasi nama wilayah, dan parsing angka BPS."""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"

NASIONAL = "Indonesia"
KODE_NASIONAL = 0

# Token BPS untuk sel tanpa angka
TOKEN_KOSONG = {"", "-", "–", "...", "…", "NA", "na", "n.a."}
# Penanda keandalan estimasi (Relative Standard Error)
CATATAN_RSE = "RSE 25-50% (estimasi kurang andal)"


class PipelineError(Exception):
    """Kesalahan fatal: pipeline harus berhenti agar data cacat tidak lolos."""


def load_yaml(name: str) -> dict:
    with open(CONFIG_DIR / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


@dataclass
class Config:
    settings: dict
    indikator: dict
    sumber: dict
    provinsi: pd.DataFrame

    @property
    def raw_dir(self) -> Path:
        return ROOT / self.settings["paths"]["raw_dir"]

    @property
    def processed_dir(self) -> Path:
        return ROOT / self.settings["paths"]["processed_dir"]

    @property
    def reports_dir(self) -> Path:
        return ROOT / self.settings["paths"]["reports_dir"]


def load_config() -> Config:
    prov = pd.read_csv(CONFIG_DIR / "provinsi.csv", dtype={"kode_bps": int})
    return Config(
        settings=load_yaml("settings.yaml"),
        indikator=load_yaml("indikator.yaml"),
        sumber=load_yaml("sumber.yaml"),
        provinsi=prov,
    )


def kunci_nama(nama: str) -> str:
    """Kunci pencocokan nama wilayah yang tahan variasi penulisan BPS.

    'D I YOGYAKARTA', 'D.I. Yogyakarta', 'DI Yogyakarta' -> 'DIYOGYAKARTA'
    'KEP. BANGKA BELITUNG', 'Kepulauan Bangka Belitung'   -> 'KEPBANGKABELITUNG'
    """
    s = str(nama).upper().strip()
    s = re.sub(r"<[^>]+>", "", s)               # sisa tag HTML
    s = s.replace("DAERAH ISTIMEWA", "DI")
    s = re.sub(r"\bKEPULAUAN\b", "KEP", s)
    s = re.sub(r"[^A-Z]", "", s)                # buang spasi, titik, angka
    return s


def peta_wilayah(provinsi: pd.DataFrame) -> dict[str, tuple[int, str]]:
    """kunci_nama -> (kode, nama baku), termasuk baris nasional."""
    peta = {kunci_nama(r.provinsi): (int(r.kode_bps), r.provinsi) for r in provinsi.itertuples()}
    peta[kunci_nama(NASIONAL)] = (KODE_NASIONAL, NASIONAL)
    return peta


_ANGKA = re.compile(r"^(-?\d+(?:\.\d+)?)\s*(\([a-z]\)|\*+)?$")


def parse_nilai(raw) -> tuple[float, str, str]:
    """Ubah sel CSV BPS menjadi (nilai, status_data, catatan_keandalan).

    status_data: 'tersedia' | 'tidak_tersedia'
    Contoh: '5.64' -> (5.64, 'tersedia', ''); '1.18 (a)' -> (1.18, 'tersedia', RSE);
            '-' / '...' -> (nan, 'tidak_tersedia', '')
    """
    s = "" if raw is None or (isinstance(raw, float) and np.isnan(raw)) else str(raw).strip()
    if s in TOKEN_KOSONG:
        return np.nan, "tidak_tersedia", ""
    m = _ANGKA.match(s)
    if not m:
        raise PipelineError(f"Nilai tidak dikenali: {raw!r}")
    catatan = CATATAN_RSE if m.group(2) else ""
    return float(m.group(1)), "tersedia", catatan


def parse_angka_id(s: str) -> float:
    """Angka format Indonesia dari PDF: '11.191' -> 11191.0, '76,23' -> 76.23."""
    return float(s.replace(".", "").replace(",", "."))


def tahun_dari_nama(path: Path) -> int:
    m = re.search(r"(20\d{2})\D*$", path.stem)
    if not m:
        raise PipelineError(f"Tahun tidak ditemukan pada nama file: {path.name}")
    return int(m.group(1))


def robust_z(s: pd.Series) -> pd.Series:
    """Modified z-score (Iglewicz & Hoaglin): 0.6745 * (x - median) / MAD."""
    med = s.median()
    mad = (s - med).abs().median()
    if not mad or np.isnan(mad):
        return pd.Series(0.0, index=s.index)
    return 0.6745 * (s - med) / mad


def spearman(a: pd.Series, b: pd.Series) -> float:
    """Korelasi Spearman tanpa dependensi scipy (Pearson atas peringkat)."""
    d = pd.concat([a, b], axis=1).dropna()
    return float(d.iloc[:, 0].rank().corr(d.iloc[:, 1].rank()))

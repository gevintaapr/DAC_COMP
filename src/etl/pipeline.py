"""Orkestrasi ETL: python -m src.etl.pipeline

Extract  -> baca CSV/PDF BPS apa adanya (dengan cek format file)
Transform-> nama provinsi baku + kode BPS, parsing angka, metadata, format panjang
Validate -> cek wajib (pipeline berhenti bila gagal) + penandaan outlier/patahan seri/lonjakan
Load     -> master_long.csv, master_wide_<tahun>.csv, nasional_long.csv, laporan kualitas data
"""
from __future__ import annotations

import argparse
import logging
import sys

from .extract import extract
from .load import load
from .transform import transform_nasional, transform_provinsi
from .utils import PipelineError, load_config
from .validate import pastikan_lulus, validate

log = logging.getLogger("etl")


def run() -> dict:
    cfg = load_config()
    raw = extract(cfg)
    prov, nas_prov = transform_provinsi(raw["provinsi"], cfg)
    nasional = transform_nasional(raw["nasional"], nas_prov)
    prov, laporan = validate(prov, raw["ipm_komponen"], cfg)
    paths = load(prov, nasional, laporan, raw["inventaris"], cfg)   # laporan tetap ditulis walau gagal
    pastikan_lulus(laporan)
    return dict(master=prov, nasional=nasional, laporan=laporan, paths=paths)


def main(argv=None) -> int:
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)-7s %(name)s: %(message)s")
    try:
        run()
    except PipelineError as e:
        log.error("PIPELINE GAGAL: %s", e)
        return 1
    log.info("Pipeline selesai tanpa kegagalan. Lihat reports/laporan_kualitas_data.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())

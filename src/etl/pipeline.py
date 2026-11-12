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
from .transform import siapkan_kak, transform_nasional, transform_provinsi, turunkan_tpt_pendidikan
from .utils import PipelineError, load_config
from .validate import pastikan_lulus, validate

log = logging.getLogger("etl")


def run() -> dict:
    cfg = load_config()
    raw = extract(cfg)
    kak = siapkan_kak(raw["kak"], cfg)
    prov, nas_prov, rekon = transform_provinsi(raw["provinsi"], cfg, turunan=turunkan_tpt_pendidikan(kak))
    nasional = transform_nasional(raw["nasional"], nas_prov)
    prov, laporan = validate(prov, raw["ipm_komponen"], rekon, cfg, kak=kak, nasional=nasional)
    paths = load(prov, nasional, laporan, raw["inventaris"], cfg, kak=kak)   # laporan tetap ditulis walau gagal
    pastikan_lulus(laporan)
    return dict(master=prov, nasional=nasional, kak=kak, laporan=laporan, paths=paths)


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

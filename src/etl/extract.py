"""EXTRACT: membaca file mentah BPS (CSV & PDF) apa adanya ke tabel seragam.

Tahap ini tidak mengubah nilai; hanya memilih baris/kolom yang relevan dan
memastikan format file sesuai harapan (cek_header) agar perubahan format BPS
langsung ketahuan, bukan diam-diam menghasilkan angka salah.
"""
from __future__ import annotations

import csv
import hashlib
import logging
import re
from pathlib import Path

import numpy as np
import pandas as pd
import pdfplumber

from .utils import Config, PipelineError, ROOT, parse_angka_id, tahun_dari_nama

log = logging.getLogger(__name__)


def _baca_csv(path: Path) -> list[list[str]]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [[c.strip() for c in row] for row in csv.reader(f)]


def _sel(rows, r, c) -> str:
    try:
        return rows[r][c]
    except IndexError:
        return ""


def _cek_header(rows, aturan, path: Path) -> None:
    for r, c, teks in aturan or []:
        if teks.lower() not in _sel(rows, r, c).lower():
            raise PipelineError(
                f"Format file berubah: {path.name} baris {r} kolom {c} "
                f"seharusnya memuat '{teks}', ditemukan '{_sel(rows, r, c)}'"
            )


def _cek_tahun_header(rows, mulai: int, tahun: int, path: Path) -> None:
    """Jika baris judul memuat tahun, harus sama dengan tahun di nama file."""
    teks = " ".join(" ".join(r) for r in rows[:mulai])
    ditemukan = {int(t) for t in re.findall(r"\b(20\d{2})\b", teks)}
    if ditemukan and tahun not in ditemukan:
        raise PipelineError(f"Tahun di nama file ({tahun}) tidak cocok dengan isi {path.name}: {ditemukan}")


def _baris_data(rows, mulai: int):
    """Baris data berhenti pada baris kosong / keterangan (catatan kaki BPS)."""
    for row in rows[mulai:]:
        if not row or not row[0] or row[0].lower().startswith("keterangan"):
            break
        yield row


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for blok in iter(lambda: f.read(1 << 20), b""):
            h.update(blok)
    return h.hexdigest()


def baca_bps_kolom(path: Path, src: dict) -> list[dict]:
    rows = _baca_csv(path)
    tahun = tahun_dari_nama(path)
    mulai = src["baris_data_mulai"]
    _cek_header(rows, src.get("cek_header"), path)
    _cek_tahun_header(rows, mulai, tahun, path)
    out = []
    for row in _baris_data(rows, mulai):
        nama = row[0]
        if src.get("hanya_provinsi") and nama != nama.upper():
            continue  # baris kabupaten/kota (ditulis huruf kecil oleh BPS)
        for col, ind in src["kolom"].items():
            if int(col) >= len(row):
                raise PipelineError(f"{path.name}: baris '{nama}' tidak punya kolom {col}")
            out.append(dict(wilayah_raw=nama, tahun=tahun, indikator=ind, nilai_raw=row[int(col)],
                            sumber=src["sumber"], file_sumber=_rel(path)))
    return out


_BARIS_PDF = re.compile(r"^(?P<nama>[A-Za-z][A-Za-z .]*?)\s+(?P<angka>[\d.,]+(?:\s+[\d.,]+)*)$")


def _halaman_bersih(page):
    # Watermark diagonal "https://www.bps.go.id" memakai font Arial-Bold berukuran besar;
    # karakter tabel memakai Myriad Pro. Watermark dibuang agar angka tidak terpotong.
    return page.filter(lambda o: not (o.get("object_type") == "char" and "Arial" in o.get("fontname", "")))


def baca_ipm_pdf(path: Path, src: dict) -> tuple[list[dict], pd.DataFrame]:
    """Lampiran 3 -> IPM provinsi 2022-2025; Lampiran 1 -> komponen IPM (untuk validasi silang)."""
    seri, komponen = [], []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            teks = page.extract_text() or ""
            if re.search(r"Lampiran\s*3\s+Perkembangan Indeks Pembangunan Manusia \(IPM\) Menurut Provinsi", teks):
                lines = (_halaman_bersih(page).extract_text() or "").splitlines()
                hdr = next(l for l in lines if l.startswith("Provinsi") and re.search(r"20\d{2}", l))
                tahun_kolom = [int(t) for t in re.findall(r"20\d{2}", hdr)]
                for l in lines:
                    m = _BARIS_PDF.match(l.strip())
                    if not m:
                        continue
                    angka = m.group("angka").split()
                    if len(angka) != len(tahun_kolom) or m.group("nama").startswith("Provinsi"):
                        continue
                    for t, a in zip(tahun_kolom, angka):
                        seri.append(dict(wilayah_raw=m.group("nama"), tahun=t, indikator="IPM", nilai_raw=str(parse_angka_id(a)),
                                         sumber=src["sumber"] + " - Lampiran 3", file_sumber=_rel(path)))
            elif re.search(r"Lampiran\s*1\s+Indeks Pembangunan Manusia \(IPM\) Menurut Provinsi, (20\d{2})", teks):
                tahun = int(re.search(r"Menurut Provinsi, (20\d{2})", teks).group(1))
                for l in (_halaman_bersih(page).extract_text() or "").splitlines():
                    m = _BARIS_PDF.match(l.strip())
                    if m and len(m.group("angka").split()) == 6:
                        uhh, hls, rls, peng, ipm, _ = (parse_angka_id(a) for a in m.group("angka").split())
                        komponen.append(dict(wilayah_raw=m.group("nama"), tahun=tahun, UHH=uhh, HLS=hls,
                                             RLS=rls, PENGELUARAN=peng, IPM=ipm))
    if not seri or not komponen:
        raise PipelineError(f"Tabel IPM tidak ditemukan di {path.name}")
    return seri, pd.DataFrame(komponen)


def _angka_atau_na(teks: str) -> bool:
    return teks == "NA" or re.fullmatch(r"\d{1,3}(?:\.\d{3})*", teks) is not None


def _baris_tabel_kak(page, n_kolom: int) -> list[dict]:
    """Baris tabel Sakernas dari satu halaman PDF.

    Superskrip '1' (penanda RSE 25-50%) memakai font lebih kecil; dipisahkan dari angka
    lewat atribut ukuran font, lalu dicatat sebagai flag pada sel angka di sebelah kirinya.
    """
    words = _halaman_bersih(page).extract_words(extra_attrs=["size"])
    besar = [w for w in words if w["size"] >= 7]
    kecil = [w for w in words if w["size"] < 7 and w["text"] == "1"]
    baris: list[list[dict]] = []
    for w in sorted(besar, key=lambda w: (w["top"], w["x0"])):
        if baris and abs(w["top"] - baris[-1][0]["top"]) < 3:
            baris[-1].append(w)
        else:
            baris.append([w])
    out, nama_tertunda = [], None
    for ws in baris:
        ws.sort(key=lambda w: w["x0"])
        angka = [w for w in ws if _angka_atau_na(w["text"])]
        nama = " ".join(w["text"] for w in ws if w not in angka).strip()
        if len(angka) != n_kolom:
            # baris 'Jumlah' di PDF: label dan angkanya berada di baris visual berbeda
            nama_tertunda = nama if nama in ("Jumlah",) else nama_tertunda
            continue
        if not nama and nama_tertunda:
            nama, nama_tertunda = nama_tertunda, None
        if not re.fullmatch(r"[A-Za-z][A-Za-z .]*", nama or ""):
            continue
        rse = [any(abs(k["x0"] - a["x1"]) < 2 and abs(k["top"] - a["top"]) < 6 for k in kecil) for a in angka]
        out.append(dict(wilayah_raw="Indonesia" if nama == "Jumlah" else nama,
                        nilai=[a["text"] for a in angka], rse=rse))
    return out


def baca_kak_pdf(path: Path, src: dict) -> pd.DataFrame:
    """Tabel angkatan kerja & pengangguran menurut provinsi x pendidikan (publikasi Keadaan Angkatan Kerja).

    Keluaran berupa jumlah orang (bukan rasio); TPT dihitung di tahap transform.
    """
    tahun = tahun_dari_nama(path)
    hasil = []
    tabel = [("angkatan_kerja", src["tabel_angkatan_kerja"], src["kolom_angkatan_kerja"]),
             ("pengangguran", src["tabel_pengangguran"], src["kolom_pengangguran"])]
    with pdfplumber.open(path) as pdf:
        teks_halaman = [(p, p.extract_text() or "") for p in pdf.pages]   # satu kali baca (PDF ratusan halaman)
        for jenis, no, kolom in tabel:
            pola = re.compile(rf"(^Tabel {no} Penduduk.*Menurut Provinsi dan Pendidikan|Lanjutan Tabel/Continued Table {no}\b)", re.M)
            halaman = [p for p, t in teks_halaman if pola.search(t)]
            if not halaman:
                raise PipelineError(f"Tabel {no} tidak ditemukan di {path.name}")
            judul = halaman[0].extract_text()
            if f"Agustus {tahun}" not in judul and f"Februari {tahun}" not in judul:
                raise PipelineError(f"Tahun Tabel {no} tidak cocok dengan nama file {path.name}")
            n_kolom = len(kolom) + 1                        # + kolom Jumlah/Total
            rows = [r for p in halaman for r in _baris_tabel_kak(p, n_kolom)]
            for r in rows:
                for kat, v, flag in zip([*kolom, "TOTAL"], r["nilai"], r["rse"]):
                    hasil.append(dict(wilayah_raw=r["wilayah_raw"], tahun=tahun, jenis=jenis, pendidikan=kat,
                                      jumlah=np.nan if v == "NA" else float(v.replace(".", "")),
                                      rse_tinggi=flag, disembunyikan_bps=v == "NA",
                                      tabel=f"Tabel {no}", file_sumber=_rel(path)))
    df = pd.DataFrame(hasil)
    n = df.groupby("jenis")["wilayah_raw"].nunique()
    if (n < 39).any():
        raise PipelineError(f"Baris tabel KAK tidak lengkap (target 38 provinsi + Indonesia): {n.to_dict()}")
    return df


def baca_nasional(path: Path, src: dict) -> list[dict]:
    rows = _baca_csv(path)
    tahun = tahun_dari_nama(path)
    mulai = src["baris_data_mulai"]
    _cek_header(rows, src.get("cek_header"), path)
    _cek_tahun_header(rows, mulai, tahun, path)
    out = []
    for row in _baris_data(rows, mulai):
        for col, periode in src["kolom"].items():
            out.append(dict(tahun=tahun, indikator=src["indikator"], kategori=row[0], periode=periode,
                            nilai_raw=row[int(col)], sumber=src["sumber"], file_sumber=_rel(path)))
    return out


def _file_sumber(cfg: Config, src: dict) -> list[Path]:
    folder = cfg.raw_dir / src["folder"]
    if not folder.exists():
        if src.get("wajib", True):
            raise PipelineError(f"Folder sumber wajib tidak ditemukan: {folder}")
        log.warning("Sumber '%s' dilewati: folder '%s' belum ada", src["id"], src["folder"])
        return []
    files = sorted(folder.glob(src["pola"]))
    if not files and src.get("wajib", True):
        raise PipelineError(f"Tidak ada file '{src['pola']}' di {folder}")
    return files


def extract(cfg: Config) -> dict:
    """Kembalikan data mentah provinsi, nasional, pembanding IPM, jumlah AK/penganggur (KAK), dan inventaris file."""
    prov, nas, inventaris = [], [], []
    ipm_komponen, kak = pd.DataFrame(), pd.DataFrame()
    for src in cfg.sumber["provinsi"]:
        for path in _file_sumber(cfg, src):
            if src["reader"] == "bps_kolom":
                recs = baca_bps_kolom(path, src)
            elif src["reader"] == "ipm_pdf":
                recs, ipm_komponen = baca_ipm_pdf(path, src)
            elif src["reader"] == "kak_pdf":
                kak = pd.concat([kak, baca_kak_pdf(path, src).assign(sumber=src["sumber"], sumber_id=src["id"])])
                inventaris.append(dict(sumber_id=src["id"], file=_rel(path), baris_diambil=len(kak), sha256=sha256(path)))
                continue
            else:
                raise PipelineError(f"Reader tidak dikenal: {src['reader']}")
            prov += [dict(r, sumber_id=src["id"], prioritas=src.get("prioritas", 1)) for r in recs]
            inventaris.append(dict(sumber_id=src["id"], file=_rel(path), baris_diambil=len(recs), sha256=sha256(path)))
    for src in cfg.sumber["nasional"]:
        for path in _file_sumber(cfg, src):
            recs = baca_nasional(path, src)
            nas += [dict(r, nama=src["nama"], satuan=src["satuan"], periode_ref=src["periode"]) for r in recs]
            inventaris.append(dict(sumber_id=src["id"], file=_rel(path), baris_diambil=len(recs), sha256=sha256(path)))
    log.info("Extract: %d nilai provinsi, %d nilai nasional dari %d file", len(prov), len(nas), len(inventaris))
    return dict(provinsi=pd.DataFrame(prov), nasional=pd.DataFrame(nas),
                ipm_komponen=ipm_komponen, kak=kak.reset_index(drop=True), inventaris=pd.DataFrame(inventaris))

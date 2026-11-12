"""VALIDATE: gerbang kualitas data.

Dua jenis pemeriksaan:
- Cek WAJIB  -> jika gagal, pipeline berhenti (data cacat tidak boleh masuk dashboard).
- Penandaan  -> nilai tetap dipertahankan, tetapi diberi flag (outlier, patahan seri,
                lonjakan antartahun, RSE tinggi, perlu verifikasi) untuk keputusan analisis.
Outlier TIDAK dihapus: pada data agregat provinsi, outlier umumnya kondisi nyata
(mis. Papua Pegunungan) dan justru menjadi bahan insight.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from .utils import CATATAN_RSE, Config, PipelineError, kunci_nama, peta_wilayah, robust_z, spearman

log = logging.getLogger(__name__)

TERSEDIA = "tersedia"


# --------------------------------------------------------------------------- cek wajib
def cek_wajib(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    s = cfg.settings
    hasil = []

    def catat(nama, ok, detail):
        hasil.append(dict(cek=nama, status="LULUS" if ok else "GAGAL", detail=detail))

    kunci = ["kode_provinsi", "tahun", "indikator"]
    dup = df[df.duplicated(kunci, keep=False)]
    catat("Tidak ada duplikat (provinsi, tahun, indikator)", dup.empty,
          f"{len(dup)} baris duplikat" if len(dup) else "0 duplikat")

    wajib_isi = ["kode_provinsi", "provinsi", "tahun", "indikator", "status_data"]
    n_null = int(df[wajib_isi].isna().sum().sum())
    catat("Kolom kunci terisi", n_null == 0, f"{n_null} sel kosong pada kolom kunci")

    n_prov = df["kode_provinsi"].nunique()
    catat(f"Jumlah provinsi = {s['jumlah_provinsi']}", n_prov == s["jumlah_provinsi"], f"{n_prov} provinsi")

    luar = df[(df["tahun"] < s["tahun_min"]) | (df["tahun"] > s["tahun_max"])]
    catat(f"Tahun dalam rentang {s['tahun_min']}-{s['tahun_max']}", luar.empty, f"{len(luar)} baris di luar rentang")

    pelanggaran = []
    for ind, meta in cfg.indikator.items():
        d = df[(df["indikator"] == ind) & df["nilai"].notna()]
        bad = d[(d["nilai"] < meta["min"]) | (d["nilai"] > meta["max"])]
        pelanggaran += [f"{r.indikator} {r.provinsi} {r.tahun}={r.nilai}" for r in bad.itertuples()]
    catat("Nilai dalam rentang wajar per indikator", not pelanggaran,
          "; ".join(pelanggaran[:10]) or "semua nilai dalam rentang")

    ta = s["tahun_analisis"]
    inti = [i for i, m in cfg.indikator.items() if m["peran"] == "inti" and i in set(df["indikator"])]
    kurang, disembunyikan = [], []
    for ind in inti:
        d = df[(df["indikator"] == ind) & (df["tahun"] == ta)]
        n = d[d["status_data"] == TERSEDIA]["kode_provinsi"].nunique()
        # sel yang sengaja tidak dipublikasikan BPS (RSE > 50%) bukan kegagalan pipeline
        sembunyi = d[d["catatan_keandalan"].str.startswith("RSE > 50%")]
        disembunyikan += [f"{ind} {r.provinsi}" for r in sembunyi.itertuples()]
        if n + len(sembunyi) < s["jumlah_provinsi"]:
            kurang.append(f"{ind}: {n}/{s['jumlah_provinsi']}")
    detail = "; ".join(kurang) or f"{len(inti)} indikator inti lengkap"
    if disembunyikan and not kurang:
        detail += f" (disembunyikan BPS karena RSE > 50%: {', '.join(disembunyikan)})"
    catat(f"Indikator inti lengkap 38 provinsi pada tahun analisis {ta}", not kurang, detail)

    return pd.DataFrame(hasil)


# --------------------------------------------------------------------------- penandaan
def tandai_outlier(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    k = cfg.settings["outlier"]["iqr_k"]
    zmax = cfg.settings["outlier"]["robust_z"]
    df = df.copy()
    df["robust_z"] = np.nan
    df["flag_outlier"] = ""
    ada = df["status_data"] == TERSEDIA
    for (_, _), idx in df[ada].groupby(["indikator", "tahun"]).groups.items():
        s = df.loc[idx, "nilai"]
        if len(s) < 8:          # terlalu sedikit untuk statistik sebaran
            continue
        q1, q3 = s.quantile([0.25, 0.75])
        iqr = q3 - q1
        z = robust_z(s)
        df.loc[idx, "robust_z"] = z.round(2)
        kena_iqr = (s < q1 - k * iqr) | (s > q3 + k * iqr)
        kena_z = z.abs() > zmax
        arah = np.where(s > s.median(), "tinggi", "rendah")
        tingkat = np.where(kena_iqr & kena_z, "ekstrem", "moderat")
        label = pd.Series([f"{a}_{t}" for a, t in zip(arah, tingkat)], index=s.index)
        df.loc[idx, "flag_outlier"] = label.where(kena_iqr | kena_z, "")
    return df


def tandai_patahan_seri(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Provinsi induk diberi flag pada (indikator, tahun) ketika provinsi hasil pemekaran
    belum memiliki data -> angka induk masih mencakup wilayah lama (tidak sebanding)."""
    df = df.copy()
    df["flag_patahan_seri"] = False
    tersedia = df["status_data"] == TERSEDIA
    for induk, anak in cfg.settings.get("pemekaran", {}).items():
        ada_anak = df[df["provinsi"].isin(anak) & tersedia].groupby(["indikator", "tahun"]).size()
        m_induk = (df["provinsi"] == induk) & tersedia
        idx_pair = pd.MultiIndex.from_frame(df.loc[m_induk, ["indikator", "tahun"]])
        tanpa_anak = ~idx_pair.isin(ada_anak.index)
        df.loc[df.index[m_induk][tanpa_anak], "flag_patahan_seri"] = True
    return df


def tandai_lonjakan(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    zmax = cfg.settings["lonjakan_antartahun"]["robust_z"]
    pmin = cfg.settings["lonjakan_antartahun"]["min_perubahan_persen"]
    df = df.sort_values(["indikator", "kode_provinsi", "tahun"]).copy()
    g = df.groupby(["indikator", "kode_provinsi"])
    prev_nilai = g["nilai"].shift()
    prev_tahun = g["tahun"].shift()
    prev_patah = g["flag_patahan_seri"].shift().fillna(False).astype(bool)
    sah = (df["tahun"] - prev_tahun == 1) & df["nilai"].notna() & prev_nilai.notna() & ~prev_patah & ~df["flag_patahan_seri"]
    df["perubahan_antartahun"] = (df["nilai"] - prev_nilai).where(sah).round(4)
    pct = ((df["nilai"] / prev_nilai - 1) * 100).where(sah)
    # Hilangkan guncangan bersama (mis. COVID 2020-2021 menaikkan TPT di semua provinsi):
    # yang dicari adalah perubahan yang menyimpang dari perubahan median provinsi lain pada tahun yang sama.
    d = df.loc[sah, ["indikator", "tahun", "perubahan_antartahun"]]
    deviasi = d["perubahan_antartahun"] - d.groupby(["indikator", "tahun"])["perubahan_antartahun"].transform("median")
    z = deviasi.groupby(d["indikator"]).transform(robust_z)
    df["flag_lonjakan"] = False
    df.loc[z.index, "flag_lonjakan"] = (z.abs() > zmax) & (pct.loc[z.index].abs() >= pmin)
    return df.sort_index()


def gabung_flag(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    df = df.copy()
    verif = pd.Series(False, index=df.index)
    for a in cfg.settings.get("perlu_verifikasi", []):
        verif |= (df["provinsi"] == a["provinsi"]) & (df["indikator"] == a["indikator"]) & (df["tahun"] == a["tahun"])
    df["flag_perlu_verifikasi"] = verif

    def label(r):
        f = []
        if r.flag_outlier:
            f.append(f"outlier_{r.flag_outlier}")
        if r.flag_patahan_seri:
            f.append("patahan_seri_pemekaran")
        if r.flag_lonjakan:
            f.append("lonjakan_antartahun")
        if r.catatan_keandalan == CATATAN_RSE:
            f.append("rse_tinggi")
        if r.flag_perlu_verifikasi:
            f.append("perlu_verifikasi")
        return ";".join(f)

    df["flag_kualitas"] = [label(r) for r in df.itertuples()]
    return df


# --------------------------------------------------------------------------- pemeriksaan pendukung
def cek_silang_ipm(df: pd.DataFrame, komponen: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Bandingkan angka CSV vs Lampiran 1 publikasi IPM (sumber berbeda, harus identik)."""
    if komponen.empty:
        return pd.DataFrame()
    peta = peta_wilayah(cfg.provinsi)
    komp = komponen.copy()
    komp["kode_provinsi"] = komp["wilayah_raw"].map(lambda n: peta[kunci_nama(n)][0])
    komp = komp[komp["kode_provinsi"] != 0]
    toleransi = {"RLS": 0.005, "HLS": 0.005, "PENGELUARAN": 0.5, "IPM": 0.005}
    rows = []
    for ind, tol in toleransi.items():
        a = df[df["indikator"] == ind][["kode_provinsi", "tahun", "provinsi", "nilai"]]
        m = komp[["kode_provinsi", "tahun", ind]].merge(a, on=["kode_provinsi", "tahun"], how="left")
        m["selisih"] = (m["nilai"] - m[ind]).abs()
        rows.append(dict(indikator=ind, tahun=int(m["tahun"].iloc[0]), dibandingkan=int(m["nilai"].notna().sum()),
                         tidak_cocok=int((m["selisih"] > tol).sum()), selisih_maks=float(m["selisih"].max())))
    return pd.DataFrame(rows)


def ringkas_distribusi(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    ta = cfg.settings["tahun_analisis"]
    w = df[(df["tahun"] == ta)].pivot_table(index="provinsi", columns="indikator", values="nilai")
    d = w.describe().T[["count", "mean", "std", "min", "50%", "max"]].rename(columns={"50%": "median"})
    d["skewness"] = w.skew()
    d["saran_korelasi"] = np.where(d["skewness"].abs() > 1, "Spearman (sebaran miring)", "Pearson/Spearman")
    return d.round(3)


def sensitivitas_periode(df: pd.DataFrame, cfg: Config) -> pd.DataFrame:
    """Seberapa berbeda peringkat provinsi bila periode survei diganti (Agustus vs Februari, Maret vs September)."""
    pasangan = [("TPT", "TPT_FEB"), ("MISKIN", "MISKIN_SEP")]
    ta = cfg.settings["tahun_analisis"]
    rows = []
    for utama, alt in pasangan:
        for t in (ta - 1, ta):
            w = df[df["tahun"] == t].pivot_table(index="provinsi", columns="indikator", values="nilai")
            if utama not in w or alt not in w:
                continue
            d = w[[utama, alt]].dropna()
            if len(d) < 8:
                continue
            geser = (d[utama].rank(ascending=False) - d[alt].rank(ascending=False)).abs()
            rows.append(dict(indikator_utama=utama, pembanding=alt, tahun=t, n=len(d),
                             spearman=round(spearman(d[utama], d[alt]), 3),
                             rata2_selisih_abs=round((d[utama] - d[alt]).abs().mean(), 2),
                             geser_peringkat_maks=int(geser.max()), provinsi_paling_bergeser=geser.idxmax()))
    return pd.DataFrame(rows)


def cakupan(df: pd.DataFrame) -> pd.DataFrame:
    return (df[df["status_data"] == TERSEDIA]
            .pivot_table(index="indikator", columns="tahun", values="kode_provinsi", aggfunc="nunique")
            .fillna(0).astype(int))


def cek_kak(kak: pd.DataFrame, df: pd.DataFrame, nasional: pd.DataFrame) -> pd.DataFrame:
    """Uji konsistensi tabel Keadaan Angkatan Kerja sebelum TPT menurut pendidikan dipakai."""
    if kak is None or kak.empty:
        return pd.DataFrame()
    rows = []
    tahun = int(kak["tahun"].iloc[0])
    # PT pada angkatan kerja adalah turunan (Diploma + Universitas); pada pengangguran PT adalah kolom asli BPS
    dasar = kak[~((kak["jenis"] == "angkatan_kerja") & (kak["pendidikan"] == "PT"))]

    # 1. Jumlah per jenjang = kolom Jumlah pada setiap baris
    tot = dasar[dasar["pendidikan"] == "TOTAL"].set_index(["jenis", "kode_provinsi"])["jumlah"]
    g = dasar[dasar["pendidikan"] != "TOTAL"].groupby(["jenis", "kode_provinsi"])["jumlah"]
    ada_na = g.apply(lambda x: x.isna().any())               # baris dengan sel NA tidak bisa dijumlahkan
    jumlah = g.sum()[~ada_na]
    sel = (jumlah - tot.reindex(jumlah.index)).abs()
    rows.append(dict(cek="Jumlah jenjang = total baris", dibandingkan=len(sel), tidak_cocok=int((sel > 5).sum()),
                     selisih_maks=float(sel.max()), satuan="orang"))

    # 2. Jumlah 38 provinsi = baris Indonesia
    prov = dasar[dasar["kode_provinsi"] != 0].groupby(["jenis", "pendidikan"])["jumlah"].sum()
    indo = dasar[dasar["kode_provinsi"] == 0].set_index(["jenis", "pendidikan"])["jumlah"]
    rel = ((prov - indo.reindex(prov.index)).abs() / indo.reindex(prov.index) * 100).dropna()
    rows.append(dict(cek="Jumlah 38 provinsi = Indonesia", dibandingkan=len(rel), tidak_cocok=int((rel > 0.1).sum()),
                     selisih_maks=round(float(rel.max()), 3), satuan="% dari total"))

    # 3. TPT total per provinsi dari KAK = TPT Agustus pada tabel TPT provinsi
    t = kak[kak["pendidikan"] == "TOTAL"].pivot_table(index="kode_provinsi", columns="jenis", values="jumlah")
    tpt_kak = (t["pengangguran"] / t["angkatan_kerja"] * 100).round(2)
    tpt_csv = df[(df["indikator"] == "TPT") & (df["tahun"] == tahun)].set_index("kode_provinsi")["nilai"]
    d = (tpt_kak.drop(0, errors="ignore") - tpt_csv).abs().dropna()
    rows.append(dict(cek="TPT total KAK = TPT Agustus (CSV)", dibandingkan=len(d), tidak_cocok=int((d > 0.011).sum()),
                     selisih_maks=round(float(d.max()), 3), satuan="poin persen"))

    # 4. TPT nasional per jenjang dari KAK = tabel TPT menurut pendidikan (nasional)
    n = nasional[(nasional["indikator"] == "TPT_PENDIDIKAN") & (nasional["tahun"] == tahun)].set_index("kategori")["nilai"]
    peta = {"SD": "Tidak/Belum Pernah Sekolah/Belum Tamat & Tamat SD", "SMP": "SMP", "SMA": "SMA umum", "SMK": "SMA Kejuruan"}
    i = kak[kak["kode_provinsi"] == 0].pivot_table(index="pendidikan", columns="jenis", values="jumlah")
    tpt_i = i["pengangguran"] / i["angkatan_kerja"] * 100
    pembanding = {k: n.get(v) for k, v in peta.items()}
    if {"Diploma I/II/III", "Universitas"} <= set(n.index):   # PT = rata-rata tertimbang AK Diploma & Universitas
        ak_d, ak_u = i.loc["DIPLOMA", "angkatan_kerja"], i.loc["UNIVERSITAS", "angkatan_kerja"]
        pembanding["PT"] = (n["Diploma I/II/III"] * ak_d + n["Universitas"] * ak_u) / (ak_d + ak_u)
    d = pd.Series({k: abs(tpt_i[k] - v) for k, v in pembanding.items() if v is not None})
    rows.append(dict(cek="TPT nasional per jenjang KAK = tabel nasional", dibandingkan=len(d),
                     tidak_cocok=int((d > 0.011).sum()), selisih_maks=round(float(d.max()), 3), satuan="poin persen"))
    return pd.DataFrame(rows)


def ringkas_rekonsiliasi(rekon: pd.DataFrame) -> pd.DataFrame:
    if rekon.empty:
        return pd.DataFrame()
    r = rekon.dropna(subset=["nilai_dipakai", "nilai_pembanding"])
    return (r.assign(beda=r["selisih"] > 1e-6)
            .groupby(["indikator", "sumber_id_dipakai", "sumber_id_pembanding"])
            .agg(tahun=("tahun", lambda s: f"{s.min()}-{s.max()}"), dibandingkan=("selisih", "size"),
                 berbeda=("beda", "sum"), selisih_maks=("selisih", "max"))
            .reset_index())


def validate(df: pd.DataFrame, ipm_komponen: pd.DataFrame, rekon: pd.DataFrame, cfg: Config,
             kak: pd.DataFrame | None = None, nasional: pd.DataFrame | None = None) -> tuple[pd.DataFrame, dict]:
    hasil_cek = cek_wajib(df, cfg)
    for r in hasil_cek.itertuples():
        log.info("[%s] %s - %s", r.status, r.cek, r.detail)

    df = tandai_outlier(df, cfg)
    df = tandai_patahan_seri(df, cfg)
    df = tandai_lonjakan(df, cfg)
    df = gabung_flag(df, cfg)

    silang = cek_silang_ipm(df, ipm_komponen, cfg)
    if not silang.empty and silang["tidak_cocok"].sum():
        hasil_cek.loc[len(hasil_cek)] = dict(cek="Validasi silang CSV vs publikasi IPM", status="PERINGATAN",
                                             detail=f"{int(silang['tidak_cocok'].sum())} nilai berbeda")
    elif not silang.empty:
        hasil_cek.loc[len(hasil_cek)] = dict(cek="Validasi silang CSV vs publikasi IPM", status="LULUS",
                                             detail=f"{int(silang['dibandingkan'].sum())} nilai identik")

    rek = ringkas_rekonsiliasi(rekon)
    if not rek.empty:
        n_beda = int(rek["berbeda"].sum())
        hasil_cek.loc[len(hasil_cek)] = dict(
            cek="Rekonsiliasi nilai ganda antarsumber", status="PERINGATAN" if n_beda else "LULUS",
            detail=f"{n_beda} dari {int(rek['dibandingkan'].sum())} nilai berbeda" if n_beda
            else f"{int(rek['dibandingkan'].sum())} nilai identik")

    kakc = cek_kak(kak, df, nasional) if nasional is not None else pd.DataFrame()
    if not kakc.empty:
        n_beda = int(kakc["tidak_cocok"].sum())
        hasil_cek.loc[len(hasil_cek)] = dict(
            cek="Konsistensi tabel Keadaan Angkatan Kerja (TPT menurut pendidikan)",
            status="PERINGATAN" if n_beda else "LULUS",
            detail=f"{n_beda} ketidakcocokan dari {len(kakc)} uji" if n_beda else f"{len(kakc)} uji konsistensi cocok")

    laporan = dict(cek=hasil_cek, silang=silang, rekonsiliasi=rek, kak=kakc, distribusi=ringkas_distribusi(df, cfg),
                   sensitivitas=sensitivitas_periode(df, cfg), cakupan=cakupan(df),
                   lulus=not (hasil_cek["status"] == "GAGAL").any())
    return df, laporan


def pastikan_lulus(laporan: dict) -> None:
    """Hentikan pipeline bila ada cek wajib yang gagal (dipanggil setelah laporan ditulis)."""
    if not laporan["lulus"]:
        gagal = laporan["cek"][laporan["cek"]["status"] == "GAGAL"]
        raise PipelineError("Cek wajib gagal:\n" + gagal.to_string(index=False))

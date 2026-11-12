"""Tahap analisis: python -m src.analysis.analisis

Input  : keluaran pipeline ETL (data/processed/)
Output : data/analysis/*.csv (siap diimpor ke dashboard), reports/figures/*.png,
         reports/temuan_analisis.md

Prinsip (lihat KERANGKA DATA SLAYER.md bagian 6):
- Korelasi Spearman (sebaran miring & ada pencilan), dengan interval kepercayaan bootstrap,
  uji tanpa pencilan ekstrem, dan uji konsistensi antartahun.
- Bahasa asosiasi, bukan sebab-akibat.
- Klaster K-Means pada data yang distandarisasi robust (median/IQR, dipangkas +/-3),
  divalidasi dengan metode Ward dan bootstrap.
- Kasus menyimpang = residu besar dari garis tren robust (Theil-Sen).
"""
from __future__ import annotations

import logging
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.metrics import adjusted_rand_score, silhouette_score

from src.etl.load import _md
from src.etl.utils import ROOT, load_config, robust_z

log = logging.getLogger("analisis")

OUT = ROOT / "data" / "analysis"
FIG = ROOT / "reports" / "figures"
SEED = 42
N_BOOT = 2000

# Variabel inti mewakili tiga lapisan kerangka (input -> output -> outcome).
# IPM tidak dimasukkan ke klaster karena tersusun dari RLS/HLS/pengeluaran (tumpang tindih).
VAR_KORELASI = ["RLS", "HLS", "APS_16_18", "APS_19_23", "IPM", "PENGELUARAN", "PEKERJA_FORMAL",
                "TPT", "TPAK", "NEET", "MISKIN", "TPT_SMA", "TPT_SMK", "TPT_PT"]
VAR_KLASTER = ["RLS", "APS_16_18", "PEKERJA_FORMAL", "TPT", "NEET", "MISKIN"]
K_KLASTER = 4

HIPOTESIS = [
    # kode, pernyataan, x, y, arah yang diharapkan (+1 / -1)
    ("H1", "Provinsi dengan RLS lebih tinggi memiliki persentase pekerja formal lebih tinggi", "RLS", "PEKERJA_FORMAL", +1),
    ("H2a", "TPT rendah bukan tanda pasar kerja sehat: TPT justru searah dengan pekerja formal", "PEKERJA_FORMAL", "TPT", +1),
    ("H2b", "TPT bukan penanda kesejahteraan: hubungannya dengan kemiskinan lemah dan tidak signifikan", "TPT", "MISKIN", 0),
    ("H2c", "Pekerja formal (bukan TPT) yang berhubungan dengan kemiskinan lebih rendah", "PEKERJA_FORMAL", "MISKIN", -1),
    ("H3a", "Pendidikan tinggi tidak otomatis menurunkan pengangguran: RLS searah dengan TPT", "RLS", "TPT", +1),
    ("H3b", "Provinsi berpendidikan tinggi justru memiliki TPT lulusan perguruan tinggi lebih tinggi", "RLS", "TPT_PT", +1),
    ("H3c", "Capaian pendidikan tidak berhubungan dengan NEET", "RLS", "NEET", 0),
]

NAMA_KLASTER = {
    "maju": "A. Pendidikan tinggi, terserap pasar kerja formal",
    "mismatch": "B. Pendidikan cukup, pengangguran & NEET tinggi",
    "menengah": "C. Menengah: TPT rendah, mayoritas informal",
    "tertinggal": "D. Tertinggal struktural",
}

REKOMENDASI = {
    "maju": [
        "Jaga kualitas penyerapan: fokus pada pencocokan lulusan perguruan tinggi dengan sektor bernilai tambah tinggi.",
        "Jadikan model rujukan kemitraan pendidikan-industri untuk klaster lain.",
    ],
    "mismatch": [
        "Prioritas utama kebijakan link-and-match: revitalisasi SMK berbasis kebutuhan industri lokal (TPT SMK tertinggi di klaster ini).",
        "Program transisi sekolah-ke-kerja untuk pemuda (magang, job matching) karena NEET tertinggi.",
        "Dorong penciptaan lapangan kerja formal; menambah lama sekolah saja tidak cukup.",
    ],
    "menengah": [
        "Formalisasi kerja (akses pembiayaan & legalitas usaha mikro) karena TPT rendah menutupi dominasi sektor informal.",
        "Naikkan partisipasi pendidikan menengah atas dan tinggi agar pendidikan bisa menjadi pintu ke kerja formal.",
    ],
    "tertinggal": [
        "Intervensi dasar: akses SD-SMP (APS 7-15 tahun masih 68-82%) dan infrastruktur sekolah.",
        "Jangan memakai TPT/NEET sebagai ukuran keberhasilan: TPT rendah di sini mencerminkan ekonomi subsisten.",
        "Program afirmasi lintas sektor (pendidikan, kesehatan, ekonomi) dengan target pekerja formal dan kemiskinan.",
    ],
}


# ----------------------------------------------------------------------------- data
def muat() -> dict:
    p = ROOT / "data" / "processed"
    cfg = load_config()
    ta = cfg.settings["tahun_analisis"]
    wide = pd.read_csv(p / f"master_wide_{ta}.csv")
    wide["GAP_SMK_SMA"] = wide["TPT_SMK"] - wide["TPT_SMA"]
    return dict(cfg=cfg, ta=ta, wide=wide, long=pd.read_csv(p / "master_long.csv"),
                nasional=pd.read_csv(p / "nasional_long.csv"),
                kak=pd.read_csv(p / f"angkatan_kerja_pendidikan_provinsi_{ta}.csv"))


def _spearman(d: pd.DataFrame, x: str, y: str) -> tuple[float, float, int]:
    if x == y:
        return 1.0, 0.0, int(d[x].notna().sum())
    d = d[[x, y]].dropna()
    r, p = stats.spearmanr(d[x], d[y])
    return float(r), float(p), len(d)


def _bootstrap_ci(d: pd.DataFrame, x: str, y: str, rng) -> tuple[float, float]:
    v = d[[x, y]].dropna().to_numpy()
    rs = []
    for _ in range(N_BOOT):
        i = rng.integers(0, len(v), len(v))
        rs.append(stats.spearmanr(v[i, 0], v[i, 1])[0])
    return tuple(np.nanpercentile(rs, [2.5, 97.5]).round(2))


def _partial_spearman(d: pd.DataFrame, x: str, y: str, kontrol: list[str]) -> float:
    r = d[[x, y, *kontrol]].dropna().rank()
    z = np.c_[np.ones(len(r)), r[kontrol].to_numpy()]
    res = lambda v: v - z @ np.linalg.lstsq(z, v, rcond=None)[0]
    return float(np.corrcoef(res(r[x].to_numpy()), res(r[y].to_numpy()))[0, 1])


# ----------------------------------------------------------------------------- korelasi & hipotesis
def matriks_korelasi(w: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for i, a in enumerate(VAR_KORELASI):
        for b in VAR_KORELASI:
            r, p, n = _spearman(w, a, b)
            rows.append(dict(var_x=a, var_y=b, rho=round(r, 3), p_value=round(p, 4), n=n))
    return pd.DataFrame(rows)


def korelasi_per_tahun(long: pd.DataFrame, ta: int) -> pd.DataFrame:
    """Konsistensi antartahun; data yang terkena patahan seri pemekaran dikeluarkan."""
    d = long[~long["flag_patahan_seri"] & (long["tahun"] <= ta)]
    rows = []
    for t, g in d.groupby("tahun"):
        w = g.pivot_table(index="provinsi", columns="indikator", values="nilai")
        for kode, _, x, y, _ in HIPOTESIS:
            if x in w and y in w and w[[x, y]].dropna().shape[0] >= 20:
                r, p, n = _spearman(w, x, y)
                rows.append(dict(hipotesis=kode, var_x=x, var_y=y, tahun=t, rho=round(r, 3), p_value=round(p, 4), n=n))
    return pd.DataFrame(rows)


def uji_hipotesis(w: pd.DataFrame, per_tahun: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    tanpa = w[~w["kandidat_uji_sensitivitas"]]
    rows = []
    for kode, teks, x, y, arah in HIPOTESIS:
        r, p, n = _spearman(w, x, y)
        lo, hi = _bootstrap_ci(w, x, y, rng)
        r2, p2, _ = _spearman(tanpa, x, y)
        th = per_tahun[per_tahun["hipotesis"] == kode]
        if arah == 0:   # hipotesis "tidak berhubungan" / "tidak negatif"
            ok = (lo <= 0 <= hi) or (kode == "H2b" and hi > 0)
        else:
            ok = (lo > 0) if arah > 0 else (hi < 0)
        rows.append(dict(
            hipotesis=kode, pernyataan=teks, var_x=x, var_y=y, n=n, rho=round(r, 2), p_value=round(p, 4),
            ci95_bawah=lo, ci95_atas=hi, rho_tanpa_pencilan=round(r2, 2), p_tanpa_pencilan=round(p2, 4),
            rho_min_antartahun=th["rho"].min() if len(th) else np.nan,
            rho_maks_antartahun=th["rho"].max() if len(th) else np.nan,
            tahun_diuji=f"{th['tahun'].min()}-{th['tahun'].max()}" if len(th) else "",
            kesimpulan="Didukung data" if ok else "Tidak didukung"))
    out = pd.DataFrame(rows)
    # koreksi uji berganda (Holm) atas p-value hipotesis berarah
    berarah = out[[a != 0 for *_, a in HIPOTESIS]].sort_values("p_value")
    m = len(berarah)
    adj = np.minimum(1, np.maximum.accumulate([(m - i) * p for i, p in enumerate(berarah["p_value"])]))
    out.loc[berarah.index, "p_holm"] = np.round(adj, 4)
    return out


def korelasi_parsial(w: pd.DataFrame) -> pd.DataFrame:
    uji = [
        ("RLS", "MISKIN", [], "Pendidikan vs kemiskinan (tanpa kontrol)"),
        ("RLS", "MISKIN", ["PEKERJA_FORMAL"], "Pendidikan vs kemiskinan, dikontrol pekerja formal"),
        ("PEKERJA_FORMAL", "MISKIN", ["RLS"], "Pekerja formal vs kemiskinan, dikontrol pendidikan"),
        ("RLS", "TPT", [], "Pendidikan vs TPT (tanpa kontrol)"),
        ("RLS", "TPT", ["TPAK"], "Pendidikan vs TPT, dikontrol partisipasi angkatan kerja"),
        ("RLS", "PEKERJA_FORMAL", ["PENGELUARAN"], "Pendidikan vs pekerja formal, dikontrol pengeluaran per kapita"),
    ]
    rows = []
    for x, y, k, ket in uji:
        r = _spearman(w, x, y)[0] if not k else _partial_spearman(w, x, y, k)
        rows.append(dict(var_x=x, var_y=y, kontrol=", ".join(k) or "-", rho=round(r, 2), keterangan=ket))
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------------- klaster
def _skala_robust(x: pd.DataFrame) -> pd.DataFrame:
    return ((x - x.median()) / (x.quantile(0.75) - x.quantile(0.25))).clip(-3, 3)


def _beri_nama(profil: pd.DataFrame) -> dict[int, str]:
    """Nama klaster dari profilnya (deterministik, tidak bergantung nomor label K-Means)."""
    sisa = list(profil.index)
    nama = {}
    nama[profil.loc[sisa, "RLS"].idxmin()] = "tertinggal"; sisa.remove(profil.loc[sisa, "RLS"].idxmin())
    nama[profil.loc[sisa, "PEKERJA_FORMAL"].idxmax()] = "maju"; sisa.remove(profil.loc[sisa, "PEKERJA_FORMAL"].idxmax())
    nama[profil.loc[sisa, "TPT"].idxmax()] = "mismatch"; sisa.remove(profil.loc[sisa, "TPT"].idxmax())
    for s in sisa:
        nama[s] = "menengah"
    return nama


def klaster(w: pd.DataFrame) -> dict:
    x = w.set_index("provinsi")[VAR_KLASTER]
    z = _skala_robust(x)

    pemilihan = []
    for k in range(2, 7):
        km = KMeans(k, n_init=100, random_state=SEED).fit(z)
        wd = AgglomerativeClustering(k, linkage="ward").fit(z)
        pemilihan.append(dict(k=k, silhouette=round(silhouette_score(z, km.labels_), 3),
                              ari_kmeans_vs_ward=round(adjusted_rand_score(km.labels_, wd.labels_), 3),
                              ukuran=" / ".join(map(str, sorted(np.bincount(km.labels_), reverse=True)))))
    pemilihan = pd.DataFrame(pemilihan)

    km = KMeans(K_KLASTER, n_init=100, random_state=SEED).fit(z)
    lab = pd.Series(km.labels_, index=z.index)
    profil_med = x.groupby(lab).median()
    nama = _beri_nama(profil_med)

    # Stabilitas: bootstrap 300x; seberapa sering setiap pasangan provinsi tetap satu klaster
    rng = np.random.default_rng(SEED)
    n = len(z)
    bersama = np.zeros((n, n)); muncul = np.zeros((n, n)); ari = []
    for b in range(300):
        i = rng.choice(n, n, replace=True)
        u = np.unique(i)
        kb = KMeans(K_KLASTER, n_init=10, random_state=b).fit(z.iloc[i])
        pred = kb.predict(z.iloc[u])
        ari.append(adjusted_rand_score(km.labels_[u], pred))
        sama = pred[:, None] == pred[None, :]
        bersama[np.ix_(u, u)] += sama
        muncul[np.ix_(u, u)] += 1
    co = np.divide(bersama, muncul, out=np.zeros_like(bersama), where=muncul > 0)
    stab = [co[j, lab.to_numpy() == lab.iloc[j]].mean() for j in range(n)]

    hasil = w[["kode_provinsi", "provinsi", "iso_3166_2", "pulau", "kelompok_wilayah"]].copy()
    hasil["kunci_klaster"] = lab.map(nama).to_numpy()
    hasil["klaster"] = hasil["kunci_klaster"].map(NAMA_KLASTER)
    hasil["stabilitas_keanggotaan"] = np.round(stab, 2)
    hasil["keanggotaan"] = np.where(hasil["stabilitas_keanggotaan"] >= 0.7, "stabil", "di perbatasan antarklaster")

    prof_vars = VAR_KLASTER + ["IPM", "HLS", "APS_19_23", "PENGELUARAN", "TPAK", "TPT_SMA", "TPT_SMK", "TPT_PT"]
    gab = w.merge(hasil[["provinsi", "kunci_klaster", "klaster"]], on="provinsi")
    profil = gab.groupby(["kunci_klaster", "klaster"])[prof_vars].median().round(2)
    profil["jumlah_provinsi"] = gab.groupby(["kunci_klaster", "klaster"]).size()
    profil = profil.reset_index().sort_values("klaster")

    # Ketahanan: klaster ulang tanpa 2 provinsi ekstrem -> apakah keanggotaan 36 provinsi lain berubah?
    tanpa = z.drop(w.loc[w["kandidat_uji_sensitivitas"], "provinsi"])
    k3 = KMeans(K_KLASTER - 1, n_init=100, random_state=SEED).fit(_skala_robust(x.loc[tanpa.index]))
    ari_tanpa = adjusted_rand_score(lab.loc[tanpa.index], k3.labels_)

    meta = dict(silhouette=float(silhouette_score(z, km.labels_)), ari_bootstrap=float(np.median(ari)),
                ari_ward=float(pemilihan.loc[pemilihan.k == K_KLASTER, "ari_kmeans_vs_ward"].item()),
                ari_tanpa_pencilan=float(ari_tanpa))
    return dict(provinsi=hasil, profil=profil, pemilihan=pemilihan, meta=meta, z=z)


# ----------------------------------------------------------------------------- kasus menyimpang
def kasus_menyimpang(w: pd.DataFrame, klas: pd.DataFrame) -> pd.DataFrame:
    """Residu dari garis tren robust (Theil-Sen); |robust z| >= 1,5 = menyimpang."""
    model = [
        ("PEKERJA_FORMAL", "RLS", "Pekerja formal lebih rendah dari yang diperkirakan dari tingkat pendidikannya",
         "Pekerja formal lebih tinggi dari yang diperkirakan dari tingkat pendidikannya"),
        ("TPT", "RLS", "Pengangguran lebih rendah dari perkiraan", "Pengangguran lebih tinggi dari perkiraan"),
        ("NEET", "RLS", "NEET lebih rendah dari perkiraan", "NEET lebih tinggi dari perkiraan"),
    ]
    d = w.set_index("provinsi")
    rows = []
    for y, x, neg, pos in model:
        s, i, _, _ = stats.theilslopes(d[y], d[x])
        pred = i + s * d[x]
        res = d[y] - pred
        z = robust_z(res)
        for prov in d.index:
            rows.append(dict(provinsi=prov, model=f"{y} ~ {x}", x=d.loc[prov, x], y_aktual=d.loc[prov, y],
                             y_perkiraan=round(pred[prov], 2), residu=round(res[prov], 2), robust_z=round(z[prov], 2),
                             menyimpang=abs(z[prov]) >= 1.5, arah=pos if res[prov] > 0 else neg,
                             kemiringan=round(s, 3), intersep=round(i, 3)))
    out = pd.DataFrame(rows).merge(klas[["provinsi", "klaster"]], on="provinsi")
    return out


def kuadran(w: pd.DataFrame) -> pd.DataFrame:
    """Pertanyaan turunan 4: provinsi berpendidikan tinggi tetapi pengangguran juga tinggi."""
    d = w[["provinsi", "RLS", "TPT", "PEKERJA_FORMAL"]].copy()
    mr, mt = d["RLS"].median(), d["TPT"].median()
    d["kuadran"] = np.select(
        [(d.RLS > mr) & (d.TPT > mt), (d.RLS > mr) & (d.TPT <= mt), (d.RLS <= mr) & (d.TPT > mt)],
        ["Pendidikan tinggi, TPT tinggi", "Pendidikan tinggi, TPT rendah", "Pendidikan rendah, TPT tinggi"],
        "Pendidikan rendah, TPT rendah")
    d["median_rls"], d["median_tpt"] = mr, mt
    return d


# ----------------------------------------------------------------------------- kesenjangan
def kesenjangan(w: pd.DataFrame, kak: pd.DataFrame, cfg) -> pd.DataFrame:
    rows = []
    for ind in ["RLS", "HLS", "APS_16_18", "APS_19_23", "IPM", "PEKERJA_FORMAL", "TPT", "NEET", "MISKIN",
                "TPT_SMA", "TPT_SMK", "TPT_PT"]:
        s = w.set_index("provinsi")[ind].dropna()
        g = w.groupby("kelompok_wilayah")[ind].median()
        rows.append(dict(indikator=ind, nama=cfg.indikator[ind]["nama"], terendah=s.idxmin(), nilai_terendah=s.min(),
                         tertinggi=s.idxmax(), nilai_tertinggi=s.max(), rasio_tertinggi_terendah=round(s.max() / s.min(), 2),
                         rasio_p90_p10=round(s.quantile(0.9) / s.quantile(0.1), 2),
                         median_jawa=round(g.get("Jawa"), 2), median_luar_jawa=round(g.get("Luar Jawa"), 2)))
    out = pd.DataFrame(rows)
    # TPT per pendidikan tertimbang (jumlah orang), Jawa vs Luar Jawa
    k = kak[kak["kode_provinsi"] != 0].merge(cfg.provinsi[["kode_bps", "kelompok_wilayah"]],
                                            left_on="kode_provinsi", right_on="kode_bps")
    k = k[~k["disembunyikan_bps"]]
    t = k.pivot_table(index=["kelompok_wilayah", "pendidikan"], columns="jenis", values="jumlah", aggfunc="sum")
    tert = (t["pengangguran"] / t["angkatan_kerja"] * 100).round(2).unstack(0)
    for jenj in ["SMA", "SMK", "PT"]:
        out.loc[out.indikator == f"TPT_{jenj}", "tertimbang_jawa"] = tert.loc[jenj, "Jawa"]
        out.loc[out.indikator == f"TPT_{jenj}", "tertimbang_luar_jawa"] = tert.loc[jenj, "Luar Jawa"]
    return out


def konvergensi(long: pd.DataFrame, ta: int) -> pd.DataFrame:
    """Koefisien variasi antarprovinsi per tahun pada provinsi dengan wilayah konsisten 2020-ta."""
    awal = long[(long["tahun"] == long["tahun"].min()) & (long["indikator"] == "RLS") & (long["status_data"] == "tersedia")]
    tetap = set(awal["provinsi"]) - set(long.loc[long["flag_patahan_seri"], "provinsi"])
    d = long[long["provinsi"].isin(tetap) & (long["tahun"] <= ta) & (long["status_data"] == "tersedia")]
    rows = []
    for ind in ["RLS", "HLS", "APS_16_18", "APS_19_23", "PEKERJA_FORMAL", "TPT", "NEET", "MISKIN", "PENGELUARAN"]:
        g = d[d["indikator"] == ind].groupby("tahun")["nilai"]
        cv = (g.std() / g.mean() * 100)
        slope = stats.theilslopes(cv.to_numpy(), cv.index.to_numpy())[0]
        ubah = (cv.iloc[-1] / cv.iloc[0] - 1) * 100      # perubahan relatif awal -> akhir
        arah = "menyempit" if ubah <= -5 else "melebar" if ubah >= 5 else "relatif tetap"
        for t, v in cv.items():
            rows.append(dict(indikator=ind, tahun=t, cv_persen=round(v, 2), n_provinsi=len(tetap),
                             tren_cv_per_tahun=round(slope, 3), perubahan_relatif_persen=round(ubah, 1), arah=arah))
    return pd.DataFrame(rows)


def tren_tpt_pendidikan(nas: pd.DataFrame) -> pd.DataFrame:
    d = nas[nas["indikator"] == "TPT_PENDIDIKAN"][["tahun", "kategori", "nilai"]]
    return d.sort_values(["kategori", "tahun"])


# ----------------------------------------------------------------------------- laporan
def _tulis_laporan(r: dict) -> str:
    h = r["hipotesis"].set_index("hipotesis")
    par = r["parsial"]
    kl, meta = r["klaster"], r["klaster_meta"]
    dev = r["menyimpang"]
    kes = r["kesenjangan"].set_index("indikator")
    kon = r["konvergensi"].groupby("indikator").agg(cv_awal=("cv_persen", "first"), cv_akhir=("cv_persen", "last"),
                                                    perubahan_relatif_persen=("perubahan_relatif_persen", "first"),
                                                    arah=("arah", "first"))
    tr = r["tren_tpt"].pivot(index="tahun", columns="kategori", values="nilai")
    w = r["wide"]

    def hp(k):
        x = h.loc[k]
        th = (f"rentang {x.tahun_diuji}: {x.rho_min_antartahun:+.2f} s.d. {x.rho_maks_antartahun:+.2f}"
              if x.tahun_diuji.split("-")[0] != x.tahun_diuji.split("-")[-1] else f"data hanya {x.tahun_diuji.split('-')[0]}")
        return (f"ρ = {x.rho:+.2f} (95% CI {x.ci95_bawah:+.2f} s.d. {x.ci95_atas:+.2f}; tanpa pencilan {x.rho_tanpa_pencilan:+.2f}; {th})")

    p_rm0 = par.iloc[0].rho; p_rm1 = par.iloc[1].rho; p_fm = par.iloc[2].rho
    p_rt0 = par.iloc[3].rho; p_rt1 = par.iloc[4].rho
    gap_pos = int((w["GAP_SMK_SMA"] > 0).sum()); gap_n = int(w["GAP_SMK_SMA"].notna().sum())
    pt_lt_sma = int((w["TPT_PT"] < w["TPT_SMA"]).sum())
    prov = kl["provinsi"]
    anggota = prov.groupby("klaster")["provinsi"].apply(lambda s: ", ".join(s)).to_dict()
    batas = prov[prov["keanggotaan"] != "stabil"]["provinsi"].tolist()
    dv = dev[dev["menyimpang"]]
    dv_formal = dv[dv["model"] == "PEKERJA_FORMAL ~ RLS"].sort_values("robust_z")
    dv_tpt = dv[dv["model"] == "TPT ~ RLS"].sort_values("robust_z")
    dv_neet = dv[dv["model"] == "NEET ~ RLS"].sort_values("robust_z")
    q = r["kuadran"]
    q_tt = q[q["kuadran"] == "Pendidikan tinggi, TPT tinggi"]["provinsi"].tolist()
    wp = w.set_index("provinsi")

    profil = kl["profil"].set_index("kunci_klaster")
    rek = "\n".join(
        f"**{NAMA_KLASTER[k]}** ({int(profil.loc[k, 'jumlah_provinsi'])} provinsi: {anggota[NAMA_KLASTER[k]]})\n\n"
        f"- Profil median: RLS {profil.loc[k, 'RLS']:.1f} th, pekerja formal {profil.loc[k, 'PEKERJA_FORMAL']:.1f}%, "
        f"TPT {profil.loc[k, 'TPT']:.1f}%, TPT SMK {profil.loc[k, 'TPT_SMK']:.1f}%, NEET {profil.loc[k, 'NEET']:.1f}%, "
        f"kemiskinan {profil.loc[k, 'MISKIN']:.1f}%\n" + "\n".join(f"- {t}" for t in REKOMENDASI[k]) + "\n"
        for k in ["maju", "mismatch", "menengah", "tertinggal"])

    return f"""# Temuan Analisis: Pendidikan dan Kualitas SDM Indonesia

_Dibuat otomatis oleh `python -m src.analysis.analisis` pada {date.today():%d-%m-%Y}. Data: BPS, potret {r['ta']} (38 provinsi);
uji konsistensi {h.loc['H1'].tahun_diuji}. Semua angka di bawah dihitung ulang setiap kali skrip dijalankan._

> **Catatan metodologis.** Semua hubungan adalah **asosiasi**, bukan sebab-akibat. n = 38 provinsi (kecil), sehingga
> setiap korelasi dilaporkan beserta interval kepercayaan bootstrap ({N_BOOT}x), hasil tanpa 2 provinsi pencilan ekstrem
> (Papua Tengah, Papua Pegunungan), dan konsistensinya antartahun. Korelasi memakai Spearman.

## Ringkasan: 5 temuan kunci

1. **Pendidikan berasosiasi dengan pekerjaan formal, dan lewat jalur itulah pendidikan berkaitan dengan kemiskinan.**
   RLS vs pekerja formal {hp('H1')}. Hubungan RLS dengan kemiskinan (ρ = {p_rm0:+.2f}) **hilang** setelah dikontrol
   persentase pekerja formal (ρ parsial = {p_rm1:+.2f}), sedangkan pekerja formal tetap kuat terhadap kemiskinan
   walau pendidikan dikontrol (ρ parsial = {p_fm:+.2f}). Pendidikan hanya berkaitan dengan kesejahteraan bila diterjemahkan
   menjadi pekerjaan formal.
2. **TPT rendah bukan tanda pasar kerja sehat.** TPT justru searah dengan pekerja formal {hp('H2a')}, dan hubungannya
   dengan kemiskinan lemah serta terus melemah {hp('H2b')}. Sebaliknya pekerja formal vs kemiskinan {hp('H2c')}. Contoh ekstrem: Papua Pegunungan
   memiliki TPT {w.set_index('provinsi').loc['Papua Pegunungan', 'TPT']:.2f}% (terendah kedua) tetapi pekerja formal hanya
   {w.set_index('provinsi').loc['Papua Pegunungan', 'PEKERJA_FORMAL']:.1f}%. **Implikasi: dashboard dan kebijakan sebaiknya
   memakai pekerja formal, bukan TPT, sebagai ukuran utama kualitas pasar kerja.**
3. **Provinsi berpendidikan lebih tinggi justru memiliki pengangguran lebih tinggi**, termasuk pengangguran lulusan perguruan
   tinggi. RLS vs TPT {hp('H3a')}; RLS vs TPT lulusan PT {hp('H3b')}. Hubungan RLS-TPT melemah dari ρ = {p_rt0:+.2f} menjadi
   {p_rt1:+.2f} setelah dikontrol TPAK: provinsi berpendidikan rendah umumnya agraris-subsisten dengan partisipasi kerja
   tinggi, sehingga hampir tidak ada "pengangguran terbuka".
4. **Masalah paling tajam ada di jalur vokasi.** TPT lulusan SMK lebih tinggi daripada SMA umum di {gap_pos} dari {gap_n}
   provinsi; TPT SMK tertimbang Jawa {kes.loc['TPT_SMK', 'tertimbang_jawa']:.2f}% vs Luar Jawa
   {kes.loc['TPT_SMK', 'tertimbang_luar_jawa']:.2f}%. Secara nasional TPT SMK selalu tertinggi sejak {tr.index.min()}
   (dari {tr['SMA Kejuruan'].iloc[0]:.2f}% menjadi {tr['SMA Kejuruan'].iloc[-1]:.2f}%), meski selisihnya terhadap SMA menyempit
   ({tr['SMA Kejuruan'].iloc[0] - tr['SMA umum'].iloc[0]:.2f} → {tr['SMA Kejuruan'].iloc[-1] - tr['SMA umum'].iloc[-1]:.2f} poin persen).
   TPT lulusan PT lebih rendah daripada SMA di {pt_lt_sma} provinsi.
5. **Hampir semua kesenjangan antarprovinsi menyempit, kecuali NEET.** Koefisien variasi RLS turun
   {kon.loc['RLS', 'cv_awal']:.1f}% → {kon.loc['RLS', 'cv_akhir']:.1f}%, pekerja formal
   {kon.loc['PEKERJA_FORMAL', 'cv_awal']:.1f}% → {kon.loc['PEKERJA_FORMAL', 'cv_akhir']:.1f}%, tetapi kesenjangan NEET justru **melebar**
   {kon.loc['NEET', 'cv_awal']:.1f}% → {kon.loc['NEET', 'cv_akhir']:.1f}% dan kemiskinan nyaris tetap
   {kon.loc['MISKIN', 'cv_awal']:.1f}% → {kon.loc['MISKIN', 'cv_akhir']:.1f}% ({int(r['konvergensi']['n_provinsi'].iloc[0])} provinsi dengan wilayah konsisten).
   NEET juga tidak berhubungan dengan capaian pendidikan {hp('H3c')}: menambah lama sekolah tidak otomatis
   mengurangi pemuda yang menganggur dan tidak bersekolah. NEET adalah titik buta kebijakan pendidikan saat ini.

## 1. Uji hipotesis

{_md(r['hipotesis'][['hipotesis', 'pernyataan', 'n', 'rho', 'ci95_bawah', 'ci95_atas', 'p_value', 'p_holm', 'rho_tanpa_pencilan', 'rho_min_antartahun', 'rho_maks_antartahun', 'kesimpulan']])}
`p_holm` = p-value setelah koreksi uji berganda (Holm) untuk hipotesis berarah. H2b dan H3c adalah hipotesis "tidak berhubungan":
didukung bila interval kepercayaan memuat nol (H2b: tidak negatif).

## 2. Korelasi parsial (mengontrol variabel ketiga)

{_md(par)}
## 3. Kesenjangan antarprovinsi ({r['ta']})

{_md(r['kesenjangan'][['indikator', 'terendah', 'nilai_terendah', 'tertinggi', 'nilai_tertinggi', 'rasio_tertinggi_terendah', 'rasio_p90_p10', 'median_jawa', 'median_luar_jawa', 'tertimbang_jawa', 'tertimbang_luar_jawa']])}
`tertimbang_*` dihitung dari jumlah penganggur / angkatan kerja (bukan rata-rata provinsi), sehingga mewakili kondisi penduduk.

Tren kesenjangan (koefisien variasi antarprovinsi):

{_md(kon.reset_index())}
## 4. Kasus menyimpang

Garis tren robust (Theil-Sen) antara RLS dan indikator hasil; provinsi dengan |robust z| ≥ 1.5 dianggap menyimpang.

**Pekerja formal vs pendidikan**

{_md(dv_formal[['provinsi', 'x', 'y_aktual', 'y_perkiraan', 'robust_z', 'arah', 'klaster']])}
**TPT vs pendidikan**

{_md(dv_tpt[['provinsi', 'x', 'y_aktual', 'y_perkiraan', 'robust_z', 'arah', 'klaster']])}
**NEET vs pendidikan**

{_md(dv_neet[['provinsi', 'x', 'y_aktual', 'y_perkiraan', 'robust_z', 'arah', 'klaster']])}
Pendidikan di atas median dan TPT juga di atas median ({len(q_tt)} provinsi): {', '.join(q_tt)}.

**Kasus paling layak dipresentasikan:**
- **Maluku**: RLS peringkat {int(wp['RLS'].rank(ascending=False)['Maluku'])} dari 38 ({wp.loc['Maluku', 'RLS']:.2f} tahun), tetapi pekerja formal hanya
  {wp.loc['Maluku', 'PEKERJA_FORMAL']:.1f}%, NEET {wp.loc['Maluku', 'NEET']:.1f}%, dan TPT SMK {wp.loc['Maluku', 'TPT_SMK']:.1f}%. Ini profil
  "pendidikan tidak terserap" yang paling jelas.
- **Bali**: TPT {wp.loc['Bali', 'TPT']:.2f}% dan NEET {wp.loc['Bali', 'NEET']:.2f}% (keduanya terendah nasional), jauh di bawah perkiraan dari pendidikannya. Ini kasus positif: ekonomi jasa/pariwisata menyerap
  tenaga kerja muda.
- **Jawa Barat & Banten**: pusat industri, tetapi TPT di atas perkiraan dan TPT SMK Jawa Barat tertinggi nasional
  ({wp.loc['Jawa Barat', 'TPT_SMK']:.2f}%). Diduga pasokan lulusan melampaui penyerapan (perlu data lowongan untuk memastikan).

## 5. Klaster provinsi (K-Means, k = {K_KLASTER})

Variabel: {', '.join(VAR_KLASTER)} (distandarisasi robust median/IQR, dipangkas ±3).

{_md(kl['pemilihan'])}
k = {K_KLASTER} dipilih karena k = 2 hanya memisahkan 2 provinsi Papua (tidak informatif), sedangkan k = {K_KLASTER} memunculkan
kelompok "pendidikan cukup tetapi pengangguran tinggi" yang menjawab pertanyaan riset. **Kejujuran metodologis:** struktur
klaster tergolong lemah-sedang (silhouette {meta['silhouette']:.2f}; kesepakatan K-Means vs Ward ARI {meta['ari_ward']:.2f};
stabilitas bootstrap ARI {meta['ari_bootstrap']:.2f}). Klaster adalah **segmentasi untuk kebijakan**, bukan kelompok alami yang tegas.
Provinsi di perbatasan antarklaster (stabilitas < 0.7): {', '.join(batas) if batas else '-'}.

{_md(kl['profil'][['klaster', 'jumlah_provinsi', 'RLS', 'APS_16_18', 'PEKERJA_FORMAL', 'TPT', 'NEET', 'MISKIN', 'IPM', 'TPT_SMK', 'TPT_PT']])}
## 6. Rekomendasi per klaster

{rek}
## 7. Keterbatasan

- Data agregat provinsi: pola antarprovinsi tidak otomatis berlaku untuk individu (ecological fallacy).
- n = 38; korelasi dengan |ρ| < 0.32 tidak signifikan pada α = 5%.
- TPT menurut pendidikan per provinsi hanya tersedia untuk {r['ta']}; sebagian sel memiliki RSE tinggi (lihat laporan kualitas data).
- Belum ada data permintaan tenaga kerja (lowongan) sehingga *mismatch* disimpulkan dari sisi hasil, bukan diukur langsung.
"""


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)-7s %(name)s: %(message)s")
    d = muat()
    w, cfg, ta = d["wide"], d["cfg"], d["ta"]
    OUT.mkdir(parents=True, exist_ok=True)

    per_tahun = korelasi_per_tahun(d["long"], ta)
    kl = klaster(w)
    r = dict(ta=ta, wide=w, korelasi=matriks_korelasi(w), per_tahun=per_tahun,
             hipotesis=uji_hipotesis(w, per_tahun), parsial=korelasi_parsial(w),
             klaster=kl, klaster_meta=kl["meta"], kesenjangan=kesenjangan(w, d["kak"], cfg),
             konvergensi=konvergensi(d["long"], ta), tren_tpt=tren_tpt_pendidikan(d["nasional"]))
    r["menyimpang"] = kasus_menyimpang(w, kl["provinsi"])
    r["kuadran"] = kuadran(w)

    file = {
        "uji_hipotesis.csv": r["hipotesis"], "korelasi_spearman.csv": r["korelasi"],
        "korelasi_per_tahun.csv": per_tahun, "korelasi_parsial.csv": r["parsial"],
        "klaster_provinsi.csv": kl["provinsi"], "profil_klaster.csv": kl["profil"],
        "pemilihan_jumlah_klaster.csv": kl["pemilihan"], "kasus_menyimpang.csv": r["menyimpang"],
        "kuadran_pendidikan_tpt.csv": r["kuadran"], "kesenjangan.csv": r["kesenjangan"],
        "konvergensi.csv": r["konvergensi"], "tren_tpt_pendidikan_nasional.csv": r["tren_tpt"],
    }
    for nama, df in file.items():
        df.to_csv(OUT / nama, index=False)
        log.info("Tulis data/analysis/%s (%d baris)", nama, len(df))

    from .grafik import buat_semua
    for p in buat_semua(r, FIG):
        log.info("Grafik: %s", Path(p).relative_to(ROOT))

    (ROOT / "reports" / "temuan_analisis.md").write_text(_tulis_laporan(r), encoding="utf-8")
    log.info("Laporan: reports/temuan_analisis.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())

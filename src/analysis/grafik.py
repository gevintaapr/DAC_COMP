"""Grafik statis (PNG) untuk laporan & draf presentasi. Dashboard interaktif dibuat terpisah di platform pilihan tim.

Aturan warna mengikuti palet tervalidasi (cek CVD): maksimal 3 warna kategori pada scatter;
klaster ke-4 memakai abu-abu netral + bentuk penanda berbeda + label langsung (bukan warna saja).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap

SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT2 = "#52514e"
GRID = "#e1e0d9"
BLUE, ORANGE, AQUA, RED = "#2a78d6", "#eb6834", "#1baf7a", "#e34948"
NEUTRAL_MID = "#f0efec"

GAYA_KLASTER = {   # warna mengikuti entitas (nama klaster), bukan nomor label
    "A. Pendidikan tinggi, terserap pasar kerja formal": (BLUE, "o"),
    "B. Pendidikan cukup, pengangguran & NEET tinggi": (ORANGE, "s"),
    "C. Menengah: TPT rendah, mayoritas informal": (AQUA, "^"),
    "D. Tertinggal struktural": (TEXT2, "D"),
}
DIVERGING = LinearSegmentedColormap.from_list("biru_merah", [RED, NEUTRAL_MID, BLUE])

LABEL = {"RLS": "RLS", "HLS": "HLS", "APS_16_18": "APS 16-18", "APS_19_23": "APS 19-23", "IPM": "IPM",
         "PENGELUARAN": "Pengeluaran/kap", "PEKERJA_FORMAL": "Pekerja formal", "TPT": "TPT", "TPAK": "TPAK",
         "NEET": "NEET", "MISKIN": "Kemiskinan", "TPT_SMA": "TPT SMA", "TPT_SMK": "TPT SMK", "TPT_PT": "TPT PT"}
SUMBER = "Sumber: BPS (diolah). Potret 2025, 38 provinsi."


def _gaya():
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "axes.edgecolor": GRID, "axes.labelcolor": TEXT2, "xtick.color": TEXT2, "ytick.color": TEXT2,
        "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": GRID,
        "grid.linewidth": 0.6, "axes.axisbelow": True, "font.size": 10, "axes.titlesize": 12,
        "axes.titleweight": "bold", "axes.titlecolor": TEXT, "axes.titlelocation": "left", "legend.frameon": False,
    })


def _judul(fig, ax, judul: str, sub: str) -> None:
    """Judul = pesan (tebal), subjudul = apa yang diukur (normal, tinta sekunder)."""
    fig.suptitle(judul, x=0.01, ha="left", fontsize=13, fontweight="bold", color=TEXT)
    ax.set_title(sub, fontsize=10, fontweight="normal", color=TEXT2, loc="left")


def _simpan(fig, path: Path, bawah: float = 0.03) -> Path:
    """Tata letak rapat; tight_layout sudah menyediakan ruang untuk judul utama (suptitle)."""
    fig.tight_layout(rect=(0, bawah, 1, 1))
    fig.savefig(path, dpi=200)
    plt.close(fig)
    return path


def _catatan(fig, teks=SUMBER):
    fig.text(0.01, 0.01, teks, fontsize=8, color=TEXT2, ha="left", va="bottom")


def heatmap_korelasi(kor: pd.DataFrame, path: Path) -> Path:
    vars_ = list(dict.fromkeys(kor["var_x"]))
    m = kor.pivot(index="var_x", columns="var_y", values="rho").loc[vars_, vars_]
    fig, ax = plt.subplots(figsize=(10, 8.4))
    ax.grid(False)
    m = m.iloc[1:, :-1]                                  # segitiga bawah tanpa diagonal (selalu 1)
    mask = np.triu(np.ones_like(m, dtype=bool), k=1)
    data = np.ma.array(m.to_numpy(), mask=mask)
    im = ax.imshow(data, cmap=DIVERGING, vmin=-1, vmax=1)
    for i in range(m.shape[0]):
        for j in range(i + 1):
            v = m.iloc[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=7.5,
                    color="white" if abs(v) > 0.6 else TEXT)
    ax.set_xticks(range(m.shape[1]), [LABEL[v] for v in m.columns], rotation=45, ha="right")
    ax.set_yticks(range(m.shape[0]), [LABEL[v] for v in m.index])
    for s in ax.spines.values():
        s.set_visible(False)
    cb = fig.colorbar(im, ax=ax, shrink=0.7, pad=0.02)
    cb.set_label("ρ Spearman (biru = searah, merah = berlawanan)", color=TEXT2)
    cb.outline.set_visible(False)
    _judul(fig, ax, "Pekerja formal, bukan TPT, yang searah dengan kesejahteraan",
           "Korelasi Spearman antarindikator, 38 provinsi (|ρ| ≥ 0.32 signifikan pada α = 5%)")
    _catatan(fig)
    return _simpan(fig, path, 0.03)


def _scatter_klaster(ax, d, x, y, label_prov=(), garis=None):
    for nama, (warna, mk) in GAYA_KLASTER.items():
        g = d[d["klaster"] == nama]
        ax.scatter(g[x], g[y], s=46, c=warna, marker=mk, edgecolors=SURFACE, linewidths=1.2, label=nama, zorder=3)
    if garis is not None:
        xs = np.linspace(d[x].min(), d[x].max(), 50)
        ax.plot(xs, garis[1] + garis[0] * xs, color=TEXT2, lw=1.2, ls="--", zorder=2, label="Garis tren robust (Theil-Sen)")
    for p in label_prov:
        r = d[d["provinsi"] == p].iloc[0]
        ax.annotate(p, (r[x], r[y]), xytext=(6, 4), textcoords="offset points", fontsize=8.5, color=TEXT)


def scatter_pendidikan_formal(w, dev, path: Path) -> Path:
    m = dev[dev["model"] == "PEKERJA_FORMAL ~ RLS"]
    label = set(m[m["menyimpang"]]["provinsi"]) | {"Papua Pegunungan", "Papua Tengah", "DKI Jakarta"}
    fig, ax = plt.subplots(figsize=(9, 6.2))
    _scatter_klaster(ax, w, "RLS", "PEKERJA_FORMAL", sorted(label), (m["kemiringan"].iloc[0], m["intersep"].iloc[0]))
    ax.set_xlabel("Rata-rata lama sekolah (tahun)")
    ax.set_ylabel("Pekerja formal (% pekerja)")
    _judul(fig, ax, "Makin lama bersekolah, makin besar porsi pekerja formal, kecuali Maluku",
           "Rata-rata lama sekolah vs pekerja formal per provinsi, diwarnai klaster")
    ax.legend(loc="upper left", fontsize=8)
    _catatan(fig)
    return _simpan(fig, path, 0.03)


def paradoks_tpt(w, hip, path: Path) -> Path:
    h = hip.set_index("hipotesis")
    fig, axes = plt.subplots(1, 2, figsize=(11, 5), sharey=True)
    for ax, x, kode, judul in [(axes[0], "TPT", "H2b", "TPT hanya lemah terkait kemiskinan"),
                               (axes[1], "PEKERJA_FORMAL", "H2c", "Pekerja formal terkait kemiskinan rendah")]:
        _scatter_klaster(ax, w, x, "MISKIN", ["Papua Pegunungan", "Bali", "DKI Jakarta"])
        r = h.loc[kode]
        ax.set_title(f"{judul}\nρ = {r.rho:+.2f} (95% CI {r.ci95_bawah:+.2f} s.d. {r.ci95_atas:+.2f})", fontsize=10.5,
                     fontweight="normal", color=TEXT2)
        ax.set_xlabel("TPT Agustus (%)" if x == "TPT" else "Pekerja formal (% pekerja)")
    axes[0].set_ylabel("Penduduk miskin, Maret (%)")
    axes[1].legend(loc="upper right", fontsize=7.5)
    fig.suptitle("TPT rendah bukan tanda kesejahteraan; pekerja formal lebih bermakna", x=0.01, ha="left",
                 fontsize=13, fontweight="bold", color=TEXT)
    _catatan(fig)
    return _simpan(fig, path, 0.03)


def dumbbell_smk_sma(w, path: Path) -> Path:
    d = w[["provinsi", "TPT_SMA", "TPT_SMK"]].dropna().sort_values("TPT_SMK")
    fig, ax = plt.subplots(figsize=(8.5, 10))
    y = np.arange(len(d))
    ax.hlines(y, d["TPT_SMA"], d["TPT_SMK"], color=GRID, lw=2, zorder=1)
    ax.scatter(d["TPT_SMA"], y, s=40, c=BLUE, edgecolors=SURFACE, linewidths=1.2, zorder=3, label="SMA umum")
    ax.scatter(d["TPT_SMK"], y, s=40, c=ORANGE, marker="s", edgecolors=SURFACE, linewidths=1.2, zorder=3, label="SMK")
    ax.set_yticks(y, d["provinsi"], fontsize=8.5)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel("Tingkat pengangguran terbuka lulusan (%), Agustus 2025")
    n_pos = int((d["TPT_SMK"] > d["TPT_SMA"]).sum())
    _judul(fig, ax, f"Lulusan SMK lebih sulit terserap daripada SMA di {n_pos} dari {len(d)} provinsi",
           "TPT lulusan SMA umum vs SMK per provinsi, Agustus 2025 (diurutkan menurut TPT SMK)")
    ax.legend(loc="lower right")
    _catatan(fig, "Sumber: BPS, Keadaan Angkatan Kerja Agustus 2025 (diolah). Papua Pegunungan: TPT SMK tidak dipublikasikan (RSE > 50%).")
    return _simpan(fig, path, 0.02)


def tren_tpt_pendidikan(tren: pd.DataFrame, path: Path) -> Path:
    t = tren.pivot(index="tahun", columns="kategori", values="nilai")
    seri = [("SMA Kejuruan", "SMK", ORANGE), ("SMA umum", "SMA umum", BLUE), ("Universitas", "Universitas", AQUA)]
    lain = [c for c in t.columns if c not in [s[0] for s in seri]]
    fig, ax = plt.subplots(figsize=(9, 5.4))
    singkat = {"Tidak/Belum Pernah Sekolah/Belum Tamat & Tamat SD": "SD ke bawah", "Diploma I/II/III": "Diploma"}
    for c in lain:
        ax.plot(t.index, t[c], color="#c3c2b7", lw=1.5, zorder=1)
        ax.annotate(f"{singkat.get(c, c)} {t[c].iloc[-1]:.2f}%", (t.index[-1], t[c].iloc[-1]), xytext=(8, 0),
                    textcoords="offset points", va="center", fontsize=8, color=TEXT2)
    for kol, nama, warna in seri:
        ax.plot(t.index, t[kol], color=warna, lw=2, marker="o", ms=5, zorder=3, label=nama)
        ax.annotate(f"{nama} {t[kol].iloc[-1]:.2f}%", (t.index[-1], t[kol].iloc[-1]), xytext=(8, 0),
                    textcoords="offset points", va="center", fontsize=9, color=TEXT)
    ax.set_xlim(t.index.min() - 0.2, t.index.max() + 1.3)
    ax.set_ylabel("TPT (%)")
    ax.set_xticks(t.index)
    _judul(fig, ax, "TPT lulusan SMK selalu tertinggi sejak 2020, meski terus turun",
           "TPT nasional menurut pendidikan tertinggi, Agustus 2020-2025")
    ax.legend(loc="upper right", fontsize=8.5)
    _catatan(fig, "Sumber: BPS, TPT menurut pendidikan tertinggi (Sakernas Agustus).")
    return _simpan(fig, path, 0.03)


def profil_klaster(kl: dict, path: Path) -> Path:
    prof = kl["profil"].set_index("klaster")
    vars_ = VAR_KLASTER_PLOT
    # warna = posisi relatif terhadap median 38 provinsi, dibalik untuk indikator 'makin rendah makin baik'
    z = kl["z"]
    lab = kl["provinsi"].set_index("provinsi")["klaster"]
    zmed = z.groupby(lab.loc[z.index]).median()
    negatif = {"TPT", "NEET", "MISKIN"}
    skor = pd.DataFrame({v: (-zmed[v] if v in negatif else zmed[v]) for v in VAR_KLASTER_PLOT if v in zmed}).loc[prof.index]
    fig, ax = plt.subplots(figsize=(11, 4.2))
    ax.grid(False)
    tampil = [v for v in vars_ if v in skor]
    im = ax.imshow(skor[tampil].to_numpy(), cmap=DIVERGING, vmin=-2, vmax=2, aspect="auto")
    for i, k in enumerate(prof.index):
        for j, v in enumerate(tampil):
            ax.text(j, i, f"{prof.loc[k, v]:.1f}", ha="center", va="center", fontsize=9,
                    color="white" if abs(skor.loc[k, v]) > 1.4 else TEXT)
    ax.set_xticks(range(len(tampil)), [LABEL[v] for v in tampil])
    ax.set_yticks(range(len(prof)), [f"{k} ({int(prof.loc[k, 'jumlah_provinsi'])})" for k in prof.index])
    for s in ax.spines.values():
        s.set_visible(False)
    _judul(fig, ax, "Empat profil provinsi: masalah klaster B adalah penyerapan, klaster D adalah akses dasar",
           "Angka = median klaster. Biru = lebih baik, merah = lebih buruk dari median 38 provinsi")
    _catatan(fig, "Catatan: TPT klaster D tampak 'baik' karena ekonomi subsisten (hampir semua orang tercatat bekerja), bukan karena pasar kerja sehat.")
    return _simpan(fig, path, 0.05)


VAR_KLASTER_PLOT = ["RLS", "APS_16_18", "PEKERJA_FORMAL", "TPT", "NEET", "MISKIN"]


def buat_semua(r: dict, folder: Path) -> list[Path]:
    _gaya()
    folder.mkdir(parents=True, exist_ok=True)
    w = r["wide"].merge(r["klaster"]["provinsi"][["provinsi", "klaster"]], on="provinsi")
    return [
        heatmap_korelasi(r["korelasi"], folder / "01_korelasi_spearman.png"),
        scatter_pendidikan_formal(w, r["menyimpang"], folder / "02_pendidikan_vs_pekerja_formal.png"),
        paradoks_tpt(w, r["hipotesis"], folder / "03_paradoks_tpt.png"),
        dumbbell_smk_sma(w, folder / "04_tpt_smk_vs_sma_provinsi.png"),
        tren_tpt_pendidikan(r["tren_tpt"], folder / "05_tren_tpt_pendidikan_nasional.png"),
        profil_klaster(r["klaster"], folder / "06_profil_klaster.png"),
    ]

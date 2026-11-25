#!/usr/bin/env python3
"""1 TeV vs 10 TeV karşılaştırmalı analiz.

Kullanım:  python3 analysis/compare.py build/data/1TeV build/data/10TeV
Çıktı:     <ilk prefix'in dizini>/comparison.png
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import common as cm


def load_run(prefix):
    d = cm.load(prefix)
    path = f"{prefix}_reconstruction.csv"
    reco = pd.read_csv(path) if os.path.exists(path) else cm.reconstruct_all(d)
    return d["events"], reco, d["muon_energy_loss"]


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    prefixes = sys.argv[1:]
    runs = [load_run(p) for p in prefixes]
    labels = [f"{ev['E0_MeV'].iloc[0]/1e6:g} TeV" for ev, _, _ in runs]
    colors = ["#1f77b4", "#d62728", "#2ca02c", "#9467bd"]

    fig, axs = plt.subplots(3, 2, figsize=(13, 15.5))
    fig.suptitle("Karşılaştırmalı analiz: " + " vs ".join(labels), fontsize=15)

    # 1. Enerji kaybı dağılımı
    ax = axs.flat[0]
    bins = np.logspace(2, 6.5, 50)
    for (ev, _, _), lab, c in zip(runs, labels, colors):
        ax.hist(ev["E_loss_MeV"], bins=bins, histtype="step", lw=2, color=c,
                label=f"{lab}: ortalama {ev['E_loss_MeV'].mean()/1e3:.1f} GeV")
    ax.set_xscale("log"); ax.set_xlabel("buzdaki enerji kaybı [MeV]"); ax.set_ylabel("olay")
    ax.set_title("1. Enerji kaybı farkı"); ax.legend(fontsize=9)

    # 2. dE/dx: teori ve simülasyon
    ax = axs.flat[1]
    E = np.logspace(2, 8, 200)
    ion, rad = cm.muon_dedx_ice(E)
    ax.loglog(E/1e3, ion + rad, "k", label="Bethe-Bloch + radyatif")
    ax.loglog(E/1e3, ion, "k:", label="yalnız iyonizasyon")
    for (ev, _, el), lab, c in zip(runs, labels, colors):
        mean = el["dE_MeV"].sum()/(el["step_mm"].sum()/10)
        med = (ev["E_loss_MeV"]/(ev["track_len_mm"]/10)).median()
        E0 = ev["E0_MeV"].iloc[0]/1e3
        ax.plot(E0, mean, "o", color=c, ms=10, label=f"{lab} ortalama {mean:.2f} MeV/cm")
        ax.plot(E0, med, "v", color=c, ms=9, mfc="none", label=f"{lab} medyan {med:.2f} MeV/cm")
    ax.set_xlabel("müon enerjisi [GeV]"); ax.set_ylabel("dE/dx [MeV/cm]")
    ax.set_title("2. Bethe-Bloch: radyatif kayıp yüksek enerjide baskın"); ax.legend(fontsize=8)
    ax.grid(alpha=0.3, which="both")

    # 3. Foton üretimi
    ax = axs.flat[2]
    for i, ((ev, _, _), lab, c) in enumerate(zip(runs, labels, colors)):
        ax.boxplot([ev["n_photons_primary"], ev["n_photons"]], positions=[i*3, i*3 + 1],
                   widths=0.8, patch_artist=True, boxprops=dict(facecolor=c, alpha=0.4))
    ax.set_xticks([i*3 + k for i in range(len(runs)) for k in (0, 1)])
    ax.set_xticklabels([f"{lab}\nbirincil" if k == 0 else f"{lab}\ntoplam"
                        for lab in labels for k in (0, 1)])
    ax.set_yscale("log"); ax.set_ylabel("Cherenkov foton / olay")
    ax.set_title("3. Foton üretim farkı (birincil müon ≈ sabit, kaskadlar artar)")

    # 4. Sensör hit oranı
    ax = axs.flat[3]
    bins = np.logspace(1, 7, 50)
    for (ev, _, _), lab, c in zip(runs, labels, colors):
        eff = ev["n_hits"].sum()/ev["n_photons"].sum()
        ax.hist(ev["n_hits"], bins=bins, histtype="step", lw=2, color=c,
                label=f"{lab}: {ev['n_hits'].mean():,.0f} hit/olay, verim {100*eff:.2f}%")
    ax.set_xscale("log"); ax.set_xlabel("sensör hit / olay"); ax.set_ylabel("olay")
    ax.set_title("4. Sensör hit oranı farkı"); ax.legend(fontsize=9)

    # 5. Rekonstrüksiyon hatası
    ax = axs.flat[4]
    bins = np.logspace(-2, 2, 50)
    for (_, reco, _), lab, c in zip(runs, labels, colors):
        ok = reco.dropna(subset=["err_fit_deg"])
        ax.hist(ok["err_fit_deg"], bins=bins, histtype="step", lw=2, color=c,
                label=f"{lab}: medyan {ok['err_fit_deg'].median():.2f}°")
        ax.hist(ok["err_linefit_deg"], bins=bins, histtype="step", lw=1, ls="--", color=c)
    ax.set_xscale("log"); ax.set_xlabel("açısal hata [°] (kesik: LineFit)"); ax.set_ylabel("olay")
    ax.set_title("5. Yön rekonstrüksiyonu"); ax.legend(fontsize=9)

    # 6. AGN teşhis güvenilirliği
    ax = axs.flat[5]
    rows = []
    for (_, reco, _), lab in zip(runs, labels):
        src = cm.combined_source(reco)
        if not src:
            continue
        dists = sorted((cm.ang_dist(src[0], src[1], a[1], a[2]), a[0], a[3]) for a in cm.AGN_CATALOG)
        ok = reco.dropna(subset=["err_fit_deg"])
        frac = (ok["err_fit_deg"] < 1.0).mean()
        rows.append((lab, src, dists[0], frac))
    y = np.arange(len(rows))
    ax.barh(y - 0.2, [r[1][2] for r in rows], 0.4, label="birleşik hata yarıçapı [°]")
    ax.barh(y + 0.2, [r[2][0] for r in rows], 0.4, label="en yakın AGN'ye uzaklık [°]")
    for yi, r in zip(y, rows):
        ax.text(max(r[1][2], r[2][0])*1.1, yi,
                f"{r[2][1]} ({r[2][2]})\nolayların %{100*r[3]:.0f}'i < 1°", va="center", fontsize=9)
    ax.set_yticks(y); ax.set_yticklabels([r[0] for r in rows])
    ax.set_xlabel("derece"); ax.set_xlim(0, max([max(r[1][2], r[2][0]) for r in rows] + [0.1])*2.5)
    ax.set_title("6. AGN teşhis güvenilirliği"); ax.legend(fontsize=8, loc="lower right")

    fig.tight_layout(rect=[0, 0, 1, 0.975])
    out = os.path.join(os.path.dirname(prefixes[0]) or ".", "comparison.png")
    fig.savefig(out, dpi=110)
    print("Kaydedildi:", out)

    print("\n{:<10}{:>16}{:>16}{:>14}{:>12}{:>14}".format(
        "Enerji", "E kaybı [GeV]", "foton/olay", "hit/olay", "verim [%]", "medyan hata"))
    for (ev, reco, _), lab in zip(runs, labels):
        ok = reco.dropna(subset=["err_fit_deg"])
        print("{:<10}{:>16.2f}{:>16,.0f}{:>14,.0f}{:>12.3f}{:>13.2f}°".format(
            lab, ev["E_loss_MeV"].mean()/1e3, ev["n_photons"].mean(), ev["n_hits"].mean(),
            100*ev["n_hits"].sum()/ev["n_photons"].sum(), ok["err_fit_deg"].median()))


if __name__ == "__main__":
    main()

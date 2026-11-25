#!/usr/bin/env python3
"""Tez analizleri: enerji taraması, literatür doğrulaması, çözünürlük, enerji rekonstrüksiyonu,
parametre çalışması.

Kullanım:  python3 analysis/thesis.py            (önce: bash run_thesis.sh)
Girdi:     build/data/scan/E*TeV_*.csv, build/data/param/*_*.csv
Çıktı:     build/data/thesis/*.png ve thesis_summary.csv
"""
import glob
import os
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import common as cm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "build", "data")
SCAN = os.path.join(DATA, "scan")
PARAM = os.path.join(DATA, "param")
OUT = os.path.join(DATA, "thesis")
os.makedirs(OUT, exist_ok=True)

GROOM = cm.load_groom()


# ======================================================================= veri hazırlığı
def scan_prefixes():
    runs = []
    for f in glob.glob(os.path.join(SCAN, "E*TeV_events.csv")):
        m = re.search(r"E([\d.]+)TeV_events\.csv$", f)
        runs.append((float(m.group(1)), f[:-len("_events.csv")]))
    return sorted(runs)


def reco_cached(prefix, data, mode="detected"):
    """Rekonstrüksiyon pahalı olduğu için sonuç CSV olarak saklanır."""
    path = f"{prefix}_reco_{mode}.csv"
    if os.path.exists(path):
        return pd.read_csv(path)
    print(f"  rekonstrüksiyon ({mode}): {os.path.basename(prefix)} ...", flush=True)
    reco = cm.reconstruct_all(data, mode=mode)
    reco.to_csv(path, index=False)
    return reco


def time_residuals(data):
    """İlk algılanan fotonun, gerçek iz için beklenen doğrudan varış zamanına göre gecikmesi (ns)."""
    ev, s, sens = data["events"], data["sensor_summary"], data["sensors"]
    s = s[s["n_detected"] > 0].merge(sens[["sensor_id", "x_mm", "y_mm", "z_mm"]], on="sensor_id")
    s = s.merge(ev[["event", "x0_mm", "y0_mm", "z0_mm", "dir_x", "dir_y", "dir_z"]], on="event")
    pos = s[["x_mm", "y_mm", "z_mm"]].to_numpy()/1000
    vtx = s[["x0_mm", "y0_mm", "z0_mm"]].to_numpy()/1000
    d = s[["dir_x", "dir_y", "dir_z"]].to_numpy()
    w = pos - vtx
    l = np.sum(w*d, axis=1)
    rho = np.linalg.norm(w - l[:, None]*d, axis=1)
    t_exp = (l - rho/np.tan(cm.THETA_C))/cm.C_VAC + rho/np.sin(cm.THETA_C)*cm.NG_REF/cm.C_VAC
    return s["t_first_det_ns"].to_numpy() - t_exp, rho


def run_stats(E, prefix):
    d = cm.load(prefix)
    ev = d["events"]
    L_cm = ev["track_len_mm"]/10
    reco = reco_cached(prefix, d, "detected")
    ok = reco.dropna(subset=["err_fit_deg"])
    st = dict(E_TeV=E, N=len(ev), L_m=L_cm.mean()/100)
    for name, col in [("tot", ev["E_loss_MeV"]), ("rad", ev["E_loss_rad_MeV"]),
                      ("ion", ev["E_loss_MeV"] - ev["E_loss_rad_MeV"])]:
        st[f"dedx_{name}"], st[f"dedx_{name}_err"] = cm.mean_sem(col/L_cm)
    st["dedx_tot_med"] = np.median(ev["E_loss_MeV"]/L_cm)
    st["groom_tot"] = float(cm.groom_dedx_ice(E*1e6, "total", GROOM))
    st["groom_ion"] = float(cm.groom_dedx_ice(E*1e6, "ion", GROOM))
    st["groom_rad"] = float(cm.groom_dedx_ice(E*1e6, "rad", GROOM))
    for key, col in [("ph", "n_photons"), ("ph_prim", "n_photons_primary"),
                     ("hits", "n_hits"), ("det", "n_detected")]:
        st[key], st[key + "_err"] = cm.mean_sem(ev[col])
    st["eff_hit"] = ev["n_hits"].sum()/ev["n_photons"].sum()
    st["eff_det"] = ev["n_detected"].sum()/ev["n_photons"].sum()
    st["ph_per_GeV"], st["ph_per_GeV_err"] = cm.mean_sem(ev["n_photons"]/(ev["edep_total_MeV"]/1e3))
    for key, col in [("lf", "err_linefit_deg"), ("fit", "err_fit_deg")]:
        st[key], st[key + "_lo"], st[key + "_hi"] = cm.median_ci(ok[col])
    st["frac_lt1"] = (ok["err_fit_deg"] < 1).mean()
    st["n_reco"] = len(ok)
    src = cm.combined_source(reco)
    st["src_dist_TXS"] = cm.ang_dist(src[0], src[1], 77.358, 5.693) if src else np.nan
    st["src_r90"] = src[2] if src else np.nan
    return st, d, reco


def errbar(ax, x, y, e, **kw):
    return ax.errorbar(x, y, yerr=e, fmt=kw.pop("fmt", "o"), capsize=3, ms=6, **kw)


# ======================================================================= figürler
def dedx_check():
    """Optik fotonlar kapalı, 4000'er olaylık enerji kaybı doğrulama koşuları (build/data/dedxcheck)."""
    rows = []
    for f in sorted(glob.glob(os.path.join(DATA, "dedxcheck", "E*TeV_events.csv"))):
        E = float(re.search(r"E([\d.]+)TeV_events\.csv$", f).group(1))
        ev = pd.read_csv(f)
        x = ev["E_loss_MeV"]/(ev["track_len_mm"]/10)
        g = float(cm.groom_dedx_ice(E*1e6, "total", GROOM))
        rng = np.random.default_rng(0)
        sub = np.array([rng.choice(x, 20).mean() for _ in range(5000)])/g
        m, e = cm.mean_sem(x)
        rows.append(dict(E_TeV=E, N=len(ev), dedx=m, dedx_err=e, median=np.median(x), groom=g, ratio=m/g,
                         sub20_med=np.median(sub), sub20_lo=np.quantile(sub, 0.16), sub20_hi=np.quantile(sub, 0.84)))
    return pd.DataFrame(rows)


def fig_dedx(S, C=None):
    E = S["E_TeV"].to_numpy()
    grid = np.logspace(4, 8.3, 300)  # MeV
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(8.5, 9), sharex=True,
                                 gridspec_kw=dict(height_ratios=[3, 1.4]))
    for col, lab, c in [("total", "toplam", "k"), ("ion", "iyonizasyon", "C0"), ("rad", "radyatif", "C3")]:
        a1.loglog(grid/1e6, cm.groom_dedx_ice(grid, col, GROOM), color=c, lw=1.5,
                  label=f"Groom/PDG: {lab}")
    errbar(a1, E, S["dedx_tot"], S["dedx_tot_err"], color="k", label="simülasyon: toplam (ortalama)")
    errbar(a1, E, S["dedx_ion"], S["dedx_ion_err"], color="C0", fmt="s", label="simülasyon: iyonizasyon")
    errbar(a1, E, S["dedx_rad"], S["dedx_rad_err"], color="C3", fmt="^", label="simülasyon: radyatif")
    a1.plot(E, S["dedx_tot_med"], "kx", ms=9, label="simülasyon: toplam (medyan)")
    if C is not None and len(C):
        errbar(a1, C["E_TeV"], C["dedx"], C["dedx_err"], color="C2", fmt="D", mfc="none",
               label="doğrulama: 4000 olay (ışık kapalı)")
    a1.axvline(1.029, color="gray", ls=":", lw=1)
    a1.text(1.08, 0.08, "E$_c$ = 1.03 TeV", color="gray", transform=a1.get_xaxis_transform())
    a1.set_ylabel("dE/dx [MeV/cm]")
    a1.set_title("Müon enerji kaybı: simülasyon ve Groom/PDG tablosu (buz, ρ = 0.917 g/cm³)")
    a1.legend(fontsize=8.5, ncol=2); a1.grid(alpha=0.3, which="both")

    for col, gcol, c, fmt in [("dedx_tot", "groom_tot", "k", "o"), ("dedx_ion", "groom_ion", "C0", "s"),
                              ("dedx_rad", "groom_rad", "C3", "^")]:
        errbar(a2, E*(1 + 0.04*["k", "C0", "C3"].index(c)), S[col]/S[gcol], S[col + "_err"]/S[gcol],
               color=c, fmt=fmt)
    a2.axhline(1, color="gray")
    if C is not None and len(C):
        errbar(a2, C["E_TeV"], C["ratio"], C["dedx_err"]/C["groom"], color="C2", fmt="D", mfc="none")
    a2.set_xscale("log"); a2.set_ylim(0, 2)
    a2.set_xlabel("müon enerjisi [TeV]"); a2.set_ylabel("simülasyon / Groom")
    a2.grid(alpha=0.3, which="both")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_dedx_validation.png"), dpi=130); plt.close(fig)


def fig_light(S):
    E = S["E_TeV"].to_numpy()
    fig, axs = plt.subplots(2, 2, figsize=(12, 9))
    ax = axs[0, 0]
    errbar(ax, E, S["ph"], S["ph_err"], color="C0", label="toplam")
    errbar(ax, E, S["ph_prim"], S["ph_prim_err"], color="C1", fmt="s", label="birincil müon")
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_ylabel("Cherenkov foton / olay")
    ax.set_title("(a) Foton üretimi"); ax.legend(); ax.grid(alpha=0.3, which="both")

    ax = axs[0, 1]
    errbar(ax, E, S["hits"], S["hits_err"], color="C2", label="DOM'a ulaşan (hit)")
    errbar(ax, E, S["det"], S["det_err"], color="C4", fmt="s", label="algılanan (kuantum verimi sonrası)")
    ax.set_xscale("log"); ax.set_yscale("log"); ax.set_ylabel("olay başına sayı")
    ax.set_title("(b) Sensör sinyali"); ax.legend(); ax.grid(alpha=0.3, which="both")

    ax = axs[1, 0]
    ax.plot(E, 100*S["eff_hit"], "o-", color="C2", label="η$_{hit}$ = N$_{hit}$/N$_γ$")
    ax.plot(E, 100*S["eff_det"], "s-", color="C4", label="η$_{det}$ = N$_{det}$/N$_γ$")
    ax.set_xscale("log"); ax.set_ylim(0, None); ax.set_ylabel("verim [%]")
    ax.set_xlabel("müon enerjisi [TeV]"); ax.set_title("(c) Algılama verimi"); ax.legend()
    ax.grid(alpha=0.3, which="both")

    ax = axs[1, 1]
    errbar(ax, E, S["ph_per_GeV"]/1e3, S["ph_per_GeV_err"]/1e3, color="C0")
    ax.set_xscale("log"); ax.set_ylabel("foton / GeV (×10³)")
    ax.set_xlabel("müon enerjisi [TeV]")
    ax.set_title("(d) Bırakılan enerji başına foton (kalorimetrik ışık verimi)")
    ax.grid(alpha=0.3, which="both")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_light_yield.png"), dpi=130); plt.close(fig)


def fig_resolution(S, recos):
    E = S["E_TeV"].to_numpy()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5))
    for key, lab, c, fmt in [("lf", "LineFit", "C1", "s"), ("fit", "Cherenkov zaman fiti", "C0", "o")]:
        y = S[key].to_numpy()
        a1.errorbar(E, y, yerr=[y - S[key + "_lo"], S[key + "_hi"] - y], fmt=fmt + "-", color=c,
                    capsize=3, label=lab)
    a1.axhline(0.5, color="gray", ls=":", label="enjekte edilen sapma (0.5°)")
    a1.set_xscale("log"); a1.set_yscale("log")
    a1.set_xlabel("müon enerjisi [TeV]"); a1.set_ylabel("medyan açısal hata [°] (%68 GA)")
    a1.set_title("(a) Açısal çözünürlük (kuantum verimi sonrası)"); a1.legend(); a1.grid(alpha=0.3, which="both")

    bins = np.logspace(-1.5, 2, 45)
    for (Ei, reco), c in zip(recos, plt.cm.viridis(np.linspace(0, 0.9, len(recos)))):
        ok = reco.dropna(subset=["err_fit_deg"])
        a2.hist(ok["err_fit_deg"], bins=bins, histtype="step", lw=1.6, color=c, density=True,
                label=f"{Ei:g} TeV")
    a2.set_xscale("log"); a2.set_xlabel("açısal hata [°]"); a2.set_ylabel("normalize olay")
    a2.set_title("(b) Cherenkov fiti hata dağılımları"); a2.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_angular_resolution.png"), dpi=130); plt.close(fig)


def truncated_light(summary, n_sensors=36, drop=0.2):
    """Kesilmiş ışık: her olayda en parlak %drop DOM atılıp kalan DOM'ların algıladığı fotonlar toplanır.
    Böylece ize çok yakın oluşan tek bir büyük kaskadın ışığı enerji kestirimini bozmaz (IceCube 'truncated
    energy' fikri)."""
    keep = int(round(n_sensors*(1 - drop)))
    out = {}
    for e, g in summary.groupby("event"):
        q = np.sort(np.concatenate([g["n_detected"].to_numpy(float), np.zeros(n_sensors - len(g))]))
        out[e] = q[:keep].sum()
    return pd.Series(out)


def energy_reconstruction(datas):
    """Üç yöntem karşılaştırılır (eğitim: çift olaylar, test: tek olaylar):
    (1) fiziksel: N_det -> ortalama dE/dx -> Groom eğrisinin tersi (tipik olay ortalamadan az ışık verir)
    (2) regresyon: log E = a + b log(N/L) doğrusu (saçılma büyükken ortalamaya çekme sapması yaratır)
    (3) kalibrasyon eğrisi: her eğitim enerjisinde kesilmiş ışığın medyanı ölçülür, eğri ters çevrilir."""
    parts = []
    for E, d in datas:
        ev = d["events"].assign(E_TeV=E)
        ev["N_tr"] = ev["event"].map(truncated_light(d["sensor_summary"])).fillna(0)
        parts.append(ev)
    ev = pd.concat(parts, ignore_index=True)
    ev = ev[ev["n_detected"] > 0].copy()
    ev["L_cm"] = ev["track_len_mm"]/10
    ev["x_tot"] = np.log10(ev["n_detected"]/ev["L_cm"])
    ev["x_tr"] = np.log10(np.maximum(ev["N_tr"], 1)/ev["L_cm"])
    train = ev[ev["event"] % 2 == 0]
    test = ev[ev["event"] % 2 == 1].copy()
    Es = np.sort(ev["E_TeV"].unique())

    # (1) fiziksel
    k = train["edep_total_MeV"].sum()/train["n_detected"].sum()
    grid = np.logspace(3, 9, 600)
    curve = cm.groom_dedx_ice(grid, "total", GROOM)
    test["E_phys_TeV"] = np.exp(np.interp(k*test["n_detected"]/test["L_cm"], curve, np.log(grid)))/1e6

    # (2) regresyon
    b, a = np.polyfit(train["x_tot"], np.log10(train["E_TeV"]), 1)
    test["E_reg_TeV"] = 10**(a + b*test["x_tot"])

    # (3) kalibrasyon eğrisi (monoton olması için birikimli maksimum alınır), tersine log-log interpolasyon
    med = train.groupby("E_TeV")["x_tr"].median().reindex(Es).to_numpy()
    lo = train.groupby("E_TeV")["x_tr"].quantile(0.16).reindex(Es).to_numpy()
    hi = train.groupby("E_TeV")["x_tr"].quantile(0.84).reindex(Es).to_numpy()
    mono = np.maximum.accumulate(med + 1e-6*np.arange(len(med)))
    test["E_cal_TeV"] = 10**np.interp(test["x_tr"], mono, np.log10(Es))

    methods = [("phys", "fiziksel (Groom tersi)", "C1"), ("reg", "regresyon", "C2"),
               ("cal", "kalibrasyon eğrisi + kesilmiş ışık", "C0")]
    rows = []
    for E, g in test.groupby("E_TeV"):
        r = dict(E_TeV=E, n=len(g))
        for m, _, _ in methods:
            lr = np.log10(g[f"E_{m}_TeV"]/E)
            q16, q50, q84 = np.quantile(lr, [0.16, 0.5, 0.84])
            r[f"{m}_bias"], r[f"{m}_sigma"] = q50, (q84 - q16)/2
        rows.append(r)
    res = pd.DataFrame(rows)
    # Işığın enerjiye duyarlılığı (kalibrasyon eğrisinin yerel eğimi)
    slope = np.diff(med)/np.diff(np.log10(Es))
    res["slope_to_next"] = list(slope) + [np.nan]

    fig, axs = plt.subplots(1, 3, figsize=(18, 5.2))
    ax = axs[0]
    ax.fill_between(Es, 10**lo, 10**hi, color="C0", alpha=0.2, label="%16–%84 aralığı (olaydan olaya)")
    ax.loglog(Es, 10**med, "o-", color="C0", label="medyan = kalibrasyon eğrisi")
    ax.axvspan(Es.min()*0.8, 1.0, color="gray", alpha=0.12)
    ax.text(0.13, 10**hi.max()*0.75, "ışık enerjiye\nneredeyse duyarsız", fontsize=9, color="dimgray")
    ax.set_xlabel("gerçek E$_μ$ [TeV]"); ax.set_ylabel("kesilmiş algılanan ışık / iz boyu [foton/cm]")
    ax.set_title("(a) Kalibrasyon: ışık – enerji ilişkisi (eğitim yarısı)"); ax.legend(fontsize=9)
    ax.grid(alpha=0.3, which="both")

    ax = axs[1]
    jitter = 10**np.random.default_rng(0).normal(0, 0.03, len(test))
    ax.loglog(test["E_TeV"]*jitter, test["E_cal_TeV"], ".", alpha=0.35, ms=4, color="C0",
              label="kalibrasyon eğrisi + kesilmiş ışık")
    lim = [0.05, Es.max()*3]
    ax.plot(lim, lim, "k--", lw=1); ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel("gerçek E$_μ$ [TeV]"); ax.set_ylabel("rekonstrükte E$_μ$ [TeV]")
    ax.set_title("(b) Enerji rekonstrüksiyonu (test yarısı)"); ax.legend(fontsize=9)
    ax.grid(alpha=0.3, which="both")

    ax = axs[2]
    for i, (m, lab, c) in enumerate(methods):
        ax.errorbar(res["E_TeV"]*(1 + 0.05*(i - 1)), res[f"{m}_bias"], yerr=res[f"{m}_sigma"], fmt="o-",
                    capsize=3, color=c, label=lab)
    ax.axhline(0, color="gray")
    ax.set_xscale("log"); ax.set_xlabel("gerçek E$_μ$ [TeV]")
    ax.set_ylabel("log$_{10}$(E$_{reko}$/E$_{gerçek}$): medyan ± %68 yarı genişlik")
    ax.set_title("(c) Yöntemlerin sapması ve çözünürlüğü"); ax.legend(fontsize=9); ax.grid(alpha=0.3, which="both")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_energy_reconstruction.png"), dpi=130); plt.close(fig)
    return res, k, (a, b)


def fig_params(base_prefix):
    configs = [("4 m", os.path.join(PARAM, "spacing4m")), ("6 m", base_prefix),
               ("8 m", os.path.join(PARAM, "spacing8m"))]
    rows, delays = [], {}
    for lab, p in configs:
        if not os.path.exists(p + "_events.csv"):
            continue
        d = cm.load(p)
        reco = reco_cached(p, d, "detected")
        ok = reco.dropna(subset=["err_fit_deg"])
        med, lo, hi = cm.median_ci(ok["err_fit_deg"])
        ev = d["events"]
        rows.append(dict(config=f"aralık {lab}", spacing=float(lab.split()[0]), ice="Rayleigh",
                         fit=med, fit_lo=lo, fit_hi=hi, det=ev["n_detected"].mean(),
                         eff_det=ev["n_detected"].sum()/ev["n_photons"].sum(),
                         lf=ok["err_linefit_deg"].median()))
    ice_rows = []
    for lab, p in [("Rayleigh", base_prefix), ("Mie (g = 0.9)", os.path.join(PARAM, "mie"))]:
        if not os.path.exists(p + "_events.csv"):
            continue
        d = cm.load(p)
        reco = reco_cached(p, d, "detected")
        ok = reco.dropna(subset=["err_fit_deg"])
        med, lo, hi = cm.median_ci(ok["err_fit_deg"])
        ev = d["events"]
        delays[lab] = time_residuals(d)
        ice_rows.append(dict(config=lab, spacing=6.0, ice=lab, fit=med, fit_lo=lo, fit_hi=hi,
                             det=ev["n_detected"].mean(),
                             eff_det=ev["n_detected"].sum()/ev["n_photons"].sum(),
                             lf=ok["err_linefit_deg"].median()))
    P = pd.DataFrame(rows); I = pd.DataFrame(ice_rows)

    fig, axs = plt.subplots(2, 2, figsize=(12, 9))
    if len(P):
        ax = axs[0, 0]
        ax.errorbar(P["spacing"], P["fit"], yerr=[P["fit"] - P["fit_lo"], P["fit_hi"] - P["fit"]],
                    fmt="o-", capsize=3, label="Cherenkov fiti")
        ax.plot(P["spacing"], P["lf"], "s--", label="LineFit")
        ax.set_xlabel("string aralığı [m]"); ax.set_ylabel("medyan açısal hata [°]")
        ax.set_title("(a) String aralığı – açısal çözünürlük (1 TeV)"); ax.legend(); ax.grid(alpha=0.3)
        ax = axs[0, 1]
        ax.plot(P["spacing"], P["det"], "o-", color="C4")
        ax.set_xlabel("string aralığı [m]"); ax.set_ylabel("algılanan foton / olay", color="C4")
        ax2 = ax.twinx(); ax2.plot(P["spacing"], 100*P["eff_det"], "s--", color="C2")
        ax2.set_ylabel("η$_{det}$ [%]", color="C2")
        ax.set_title("(b) String aralığı – algılanan ışık"); ax.grid(alpha=0.3)
    ax = axs[1, 0]
    bins = np.linspace(-20, 200, 89)
    for (lab, (r, rho)), c in zip(delays.items(), ["C0", "C3"]):
        ax.hist(r, bins=bins, histtype="step", lw=2, density=True, color=c,
                label=f"{lab}: medyan {np.median(r):.1f} ns")
    ax.set_yscale("log"); ax.set_xlabel("ilk foton gecikmesi t$_{ilk}$ − t$_{doğrudan}$ [ns]")
    ax.set_ylabel("normalize DOM sayısı"); ax.set_title("(c) Buz modeli – zaman gecikmesi (1 TeV)")
    ax.legend()
    ax = axs[1, 1]
    if len(I):
        x = np.arange(len(I))
        ax.bar(x - 0.2, I["fit"], 0.4, yerr=[I["fit"] - I["fit_lo"], I["fit_hi"] - I["fit"]],
               capsize=4, label="medyan açısal hata [°]")
        ax.bar(x + 0.2, I["det"]/1000, 0.4, label="algılanan foton / olay (×10³)")
        ax.set_xticks(x); ax.set_xticklabels(I["config"])
        ax.set_title("(d) Buz modeli – çözünürlük ve ışık (1 TeV)"); ax.legend()
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_parameter_study.png"), dpi=130); plt.close(fig)
    return pd.concat([P, I], ignore_index=True)


# ======================================================================= ana program
def main():
    runs = scan_prefixes()
    if not runs:
        raise SystemExit("build/data/scan altında veri yok. Önce: bash run_thesis.sh")
    stats, datas, recos = [], [], []
    for E, p in runs:
        print(f"{E:g} TeV işleniyor...", flush=True)
        st, d, reco = run_stats(E, p)
        stats.append(st); datas.append((E, d)); recos.append((E, reco))
    S = pd.DataFrame(stats)
    S.to_csv(os.path.join(OUT, "thesis_summary.csv"), index=False)

    C = dedx_check()
    C.to_csv(os.path.join(OUT, "dedx_check.csv"), index=False)
    fig_dedx(S, C)
    fig_light(S)
    fig_resolution(S, recos)
    eres, k, (a, b) = energy_reconstruction(datas)
    eres.to_csv(os.path.join(OUT, "energy_resolution.csv"), index=False)
    base = dict(runs).get(1.0)
    P = fig_params(base) if base else pd.DataFrame()
    P.to_csv(os.path.join(OUT, "parameter_study.csv"), index=False)

    pd.set_option("display.width", 200)
    print("\n=== Enerji taraması ===")
    print(S[["E_TeV", "N", "dedx_tot", "dedx_tot_err", "groom_tot", "dedx_ion", "groom_ion",
             "dedx_rad", "groom_rad", "ph", "det", "eff_det", "fit", "lf", "src_dist_TXS"]]
          .round(4).to_string(index=False))
    print(f"\n=== Enerji rekonstrüksiyonu (k = {k:.3f} MeV/foton, ampirik: log10E = {a:.3f} + {b:.3f} log10(N/L)) ===")
    print(eres.round(3).to_string(index=False))
    print("\n=== Parametre çalışması (1 TeV) ===")
    print(P.round(3).to_string(index=False))
    print("\nFigürler:", OUT)


if __name__ == "__main__":
    main()

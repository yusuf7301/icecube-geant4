#!/usr/bin/env python3
"""Tek bir koşunun analizi.

Kullanım:  python3 analysis/analyze.py build/data/1TeV
           python3 analysis/analyze.py build/data/detail/E3TeV build/data/scan/E3TeV
           (ikinci önek verilirse 5–6. paneller ve rekonstrüksiyon o koşudan, yani tam tarama
            istatistiğinden; 1–4. paneller ve fizik figürü ayrıntılı kayıtlı ilk koşudan alınır)
Çıktılar:  <prefix>_agn_reconstruction.png   (6 panel)
           <prefix>_physics.png              (fiziksel yorumlar, 8 panel)
           <prefix>_reconstruction.csv       (olay başına yön rekonstrüksiyonu)
"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm
from matplotlib.patches import Circle, Patch

import common as cm

LAYER_COLORS = ["#08306b", "#2171b5", "#9e9ac8", "#6baed6"]  # katman 0 (derin) -> 3 (sığ)


def summary(prefix, d, reco):
    ev = d["events"]
    eff = ev["n_hits"].sum()/ev["n_photons"].sum()
    print(f"\n===== {prefix} =====")
    print(f"Olay sayısı                 : {len(ev)}")
    print(f"Müon enerjisi               : {ev['E0_MeV'].iloc[0]/1e6:g} TeV")
    print(f"Ortalama iz uzunluğu (buz)  : {ev['track_len_mm'].mean()/1000:.2f} m")
    print(f"Enerji kaybı  ortalama      : {ev['E_loss_MeV'].mean():.0f} MeV "
          f"({100*ev['E_loss_MeV'].mean()/ev['E0_MeV'].iloc[0]:.3f}%)")
    print(f"Enerji kaybı  medyan        : {ev['E_loss_MeV'].median():.0f} MeV")
    print(f"Cherenkov foton / olay      : {ev['n_photons'].mean():,.0f} "
          f"(birincil müondan: {ev['n_photons_primary'].mean():,.0f})")
    print(f"Sensör hit / olay           : {ev['n_hits'].mean():,.0f}")
    print(f"Deteksiyon verimliliği      : {100*eff:.3f}%")
    ok = reco.dropna(subset=["err_fit_deg"])
    if len(ok):
        print(f"Rekonstrüksiyon (medyan)    : LineFit {ok['err_linefit_deg'].median():.2f}°, "
              f"Cherenkov fit {ok['err_fit_deg'].median():.2f}° ({len(ok)}/{len(reco)} olay)")
    src = cm.combined_source(reco)
    if src:
        print(f"Birleşik kaynak             : RA {src[0]:.2f}°, Dec {src[1]:.2f}° (±{src[2]:.2f}°)")
        dists = [(cm.ang_dist(src[0], src[1], ra, dec), n, c) for n, ra, dec, c in cm.AGN_CATALOG]
        dmin, name, cls = min(dists)
        print(f"En yakın AGN                : {name} [{cls}], {dmin:.2f}° uzakta")


def save_panels(fig, axs, out_dir):
    """Her paneli (ikiz eksen ve renk çubuğuyla birlikte) ayrı PNG olarak kaydeder: out_dir/1.png, 2.png..."""
    import os
    from matplotlib.transforms import Bbox
    os.makedirs(out_dir, exist_ok=True)
    r = fig.canvas.get_renderer()
    for i, ax in enumerate(axs.flat, 1):
        p = ax.get_position()
        parts = [ax]
        for o in fig.axes:
            q = o.get_position()
            twin = o is not ax and abs(q.x0 - p.x0) < 1e-3 and abs(q.y0 - p.y0) < 1e-3
            cbar = (o is not ax and q.width < 0.05 and p.x1 - 0.01 <= q.x0 <= p.x1 + 0.08
                    and q.y0 < p.y1 and q.y1 > p.y0)
            if twin or cbar:
                parts.append(o)
        bb = Bbox.union([a.get_tightbbox(r) for a in parts]).padded(8)
        fig.savefig(f"{out_dir}/{i}.png", dpi=fig.dpi, bbox_inches=bb.transformed(fig.dpi_scale_trans.inverted()))


# ======================================================================= AGN figürü
def fig_agn(prefix, d, reco):
    ev, hits, ph, sens = d["events"], d["sensor_hits"], d["cherenkov_photons"], d["sensors"]
    fig, axs = plt.subplots(3, 2, figsize=(13, 15.5))
    E_TeV = ev["E0_MeV"].iloc[0]/1e6
    n_txt = (f"{len(ev)} olay" if len(reco) == len(ev)
             else f"rekonstrüksiyon {len(reco)} olay, panel 1–4: {len(ev)} olay")
    fig.suptitle(f"IceCube simülasyonu — {E_TeV:g} TeV müon, AGN kaynak rekonstrüksiyonu "
                 f"({n_txt})", fontsize=15)

    # 1. Foton dağılımı (ilk kaydedilen olay, üstten görünüm)
    ax = axs.flat[0]
    if ph is not None and len(ph):
        e0 = ph["event"].iloc[0]
        p = ph[ph["event"] == e0]
        h = ax.hist2d(p["x_mm"]/1000, p["y_mm"]/1000, bins=120, range=[[-10, 10], [-10, 10]],
                      norm=LogNorm(), cmap="viridis")
        fig.colorbar(h[3], ax=ax, label="foton sayısı")
        ax.set_title(f"1. Foton dağılımı (olay {e0}, {len(p):,} foton)")
    ax.scatter(sens["x_mm"]/1000, sens["y_mm"]/1000, marker="o", s=60, facecolor="none",
               edgecolor="orange", lw=1.5, label="string (4 DOM)")
    ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]"); ax.set_aspect("equal"); ax.legend(loc="upper right")

    # 2. Enerji spektrumu: üretilen vs algılanan fotonlar
    ax = axs.flat[1]
    bins = np.linspace(2.0, 4.2, 45)
    if ph is not None:
        ax.hist(ph["energy_eV"], bins=bins, density=True, histtype="step", lw=2, label="üretilen")
    if hits is not None:
        ax.hist(hits["energy_eV"], bins=bins, density=True, histtype="step", lw=2, label="DOM'a ulaşan")
        if "detected" in hits and hits["detected"].any():
            ax.hist(hits.loc[hits["detected"] == 1, "energy_eV"], bins=bins, density=True, histtype="step",
                    lw=2, ls="--", label="kuantum verimi sonrası algılanan")
    ax.set_xlabel("foton enerjisi [eV]"); ax.set_ylabel("normalize sayı")
    ax.set_title("2. Enerji spektrumu")
    sec = ax.secondary_xaxis("top", functions=(lambda e: cm.HC/np.maximum(e, 1e-3),
                                                lambda l: cm.HC/np.maximum(l, 1e-3)))
    sec.set_xlabel("dalga boyu [nm]")
    ax.legend()

    # 3. Zaman dağılımı (her olayda ilk hit'e göre)
    ax = axs.flat[2]
    if hits is not None and len(hits):
        t_rel = hits["time_ns"] - hits.groupby("event")["time_ns"].transform("min")
        for layer in range(4):
            sel = hits["dom_id"] == layer
            ax.hist(t_rel[sel], bins=np.linspace(0, 400, 81), histtype="step", lw=1.8,
                    color=LAYER_COLORS[layer], label=f"katman {layer} ({sens[sens.dom_id==layer].depth_m.iloc[0]:.1f} m)")
        ax.set_yscale("log")
    ax.set_xlabel("t − t$_{ilk}$ [ns]"); ax.set_ylabel("hit sayısı")
    ax.set_title("3. Zaman dağılımı (DOM derinliğine göre)"); ax.legend(fontsize=8)

    # 4. Sensör verimliliği
    ax = axs.flat[3]
    per_sensor = (hits.groupby("sensor_id").size() if hits is not None else None)
    per_sensor = per_sensor.reindex(range(len(sens)), fill_value=0)/len(ev)
    ax.bar(per_sensor.index, per_sensor.values, color=[LAYER_COLORS[i % 4] for i in per_sensor.index])
    eff = ev["n_hits"].sum()/ev["n_photons"].sum()
    ax.set_xlabel("sensör ID (string×4 + DOM)"); ax.set_ylabel("ortalama hit / olay")
    ax.set_title(f"4. Sensör verimliliği — toplam {100*eff:.2f}% "
                 f"({ev['n_hits'].mean():,.0f} / {ev['n_photons'].mean():,.0f})")
    for s in range(1, 9):
        ax.axvline(4*s - 0.5, color="gray", lw=0.5)

    # 5. AGN işaretleri: kataloğa açısal uzaklık
    ax = axs.flat[4]
    src = cm.combined_source(reco)
    if src:
        ra, dec, r90, nused = src
        names = [a[0] for a in cm.AGN_CATALOG]
        dist = np.array([cm.ang_dist(ra, dec, a[1], a[2]) for a in cm.AGN_CATALOG])
        cols = [cm.CLASS_COLORS[a[3]] for a in cm.AGN_CATALOG]
        order = np.argsort(dist)
        ax.barh([names[i] for i in order], dist[order], color=[cols[i] for i in order])
        ax.axvline(max(r90, 1e-3), color="k", ls="--", label=f"hata yarıçapı ≈ {r90:.2f}°")
        ax.set_xscale("log"); ax.invert_yaxis()
        ax.set_xlabel("rekonstrükte kaynağa açısal uzaklık [°]")
        best = order[0]
        verdict = (f"Eşleşme: {names[best]}\n{cm.AGN_CATALOG[best][3]}"
                   if dist[best] < max(3*r90, 1.0) else "Katalogda eşleşme yok")
        ax.text(0.97, 0.05, verdict, transform=ax.transAxes, ha="right", va="bottom",
                fontsize=11, bbox=dict(fc="white", ec="gray"))
        handles = [ax.get_legend_handles_labels()[0][0]]
        handles += [Patch(color=c, label=cls) for cls, c in cm.CLASS_COLORS.items()]
        ax.legend(handles=handles, fontsize=8, loc="center right")
    ax.set_title("5. AGN işaretleri (Blazar: BL Lac / FSRQ)")

    # 6. Konum belirleme: gökyüzü haritası
    ax = axs.flat[5]
    ok = reco.dropna(subset=["ra_reco"])
    ra_t, dec_t = reco["ra_true"].mean(), reco["dec_true"].mean()
    ax.scatter(ok["ra_reco"], ok["dec_reco"], s=12, alpha=0.6, label="olay başına rekonstrüksiyon")
    if src:
        ax.plot(src[0], src[1], "k+", ms=14, mew=2, label=f"birleşik kaynak ({src[3]} olay)")
        ax.add_patch(Circle((src[0], src[1]), max(src[2], 0.05), fill=False, ec="k", ls="--"))
    for n, ra, dec, c in cm.AGN_CATALOG:
        if abs(ra - ra_t) < 8 and abs(dec - dec_t) < 8:
            ax.plot(ra, dec, "*", ms=18, color=cm.CLASS_COLORS[c], mec="k")
            ax.annotate(n, (ra, dec), xytext=(6, 6), textcoords="offset points", fontsize=9)
    ax.set_xlim(ra_t - 6, ra_t + 6); ax.set_ylim(dec_t - 6, dec_t + 6)
    ax.set_xlabel("RA [°]"); ax.set_ylabel("Dec [°]"); ax.legend(fontsize=8, loc="lower left")
    med = ok["err_fit_deg"].median() if len(ok) else np.nan
    ax.set_title(f"6. Konum belirleme — medyan açısal hata {med:.2f}°")
    ax.grid(alpha=0.3)

    fig.tight_layout(rect=[0, 0, 1, 0.975])
    out = f"{prefix}_agn_reconstruction.png"
    fig.savefig(out, dpi=120)
    save_panels(fig, axs, f"{prefix}_panels/agn")
    plt.close(fig)
    print("Kaydedildi:", out)


# ======================================================================= fizik figürü
def fig_physics(prefix, d):
    ev, el, ph, ice, hits = (d["events"], d["muon_energy_loss"], d["cherenkov_photons"],
                             d["ice_properties"], d["sensor_hits"])
    fig, axs = plt.subplots(4, 2, figsize=(13, 19))
    E0 = ev["E0_MeV"].iloc[0]
    fig.suptitle(f"Fiziksel yorumlar — {E0/1e6:g} TeV müon, buz", fontsize=15)

    # (a) Bethe-Bloch + radyatif kayıp eğrisi
    ax = axs.flat[0]
    E = np.logspace(1, 8, 300)
    ion, rad = cm.muon_dedx_ice(E)
    ax.loglog(E/1e3, ion, label="iyonizasyon (Bethe-Bloch)")
    ax.loglog(E/1e3, rad, label="radyatif (b·E)")
    ax.loglog(E/1e3, ion + rad, "k", label="toplam")
    mean_dedx = el["dE_MeV"].sum()/(el["step_mm"].sum()/10)
    ax.plot(E0/1e3, mean_dedx, "ro", ms=10, label=f"simülasyon: {mean_dedx:.2f} MeV/cm")
    ax.set_xlabel("müon enerjisi [GeV]"); ax.set_ylabel("⟨dE/dx⟩ [MeV/cm]")
    ax.set_title("(a) Bethe-Bloch eğrisi"); ax.legend(fontsize=8); ax.grid(alpha=0.3, which="both")

    # (b) Adım başına kayıp: stokastik kuyruk
    ax = axs.flat[1]
    dedx = el["dE_MeV"]/(el["step_mm"]/10).clip(lower=1e-6)
    bins = np.logspace(-1, 6, 70)
    for proc in el["process"].value_counts().index[:6]:
        sel = el["process"] == proc
        ax.hist(dedx[sel], bins=bins, histtype="step", lw=1.5, label=proc)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("adım dE/dx [MeV/cm]"); ax.set_ylabel("adım sayısı")
    ax.set_title("(b) Adım enerji kaybı (sürece göre)"); ax.legend(fontsize=8)

    # (c) Frank-Tamm: dN/dxdE ≈ sabit
    ax = axs.flat[2]
    if ph is not None:
        prim = ph[ph["parent_id"] == 1]
        L_cm = ev.set_index("event").loc[prim["event"].unique(), "track_len_mm"].sum()/10
        bins = np.linspace(cm.HC/600, cm.HC/300, 40)
        cnt, edges = np.histogram(prim["energy_eV"], bins=bins)
        ctr = 0.5*(edges[1:] + edges[:-1])
        ax.step(ctr, cnt/np.diff(edges)/L_cm, where="mid", lw=2, label="simülasyon (birincil müon)")
        n = cm.n_phase(cm.HC/ctr)
        ax.plot(ctr, 369.8*(1 - 1/n**2), "k--", label="Frank-Tamm: 370·(1−1/n²)")
        ax.set_ylim(0, None)
        tot = len(prim)/L_cm
        ax.set_title(f"(c) Frank-Tamm — {tot:.0f} foton/cm (300–600 nm)")
    ax.set_xlabel("foton enerjisi [eV]"); ax.set_ylabel("dN / dx dE [1/(cm·eV)]"); ax.legend(fontsize=8)

    # (d) Dispersiyon
    ax = axs.flat[3]
    lam = np.linspace(300, 600, 200)
    ax.plot(lam, cm.n_phase(lam), label="faz indisi n")
    ax.plot(lam, cm.n_group(lam), label="grup indisi n$_g$")
    ax.axhline(1.325, color="gray", ls=":", label="n = 1.325")
    ax.set_xlabel("dalga boyu [nm]"); ax.set_ylabel("kırılma indisi")
    ax2 = ax.twinx()
    ax2.plot(lam, np.degrees(np.arccos(1/cm.n_phase(lam))), "r--", label="θ$_C$")
    ax2.set_ylabel("Cherenkov açısı θ$_C$ [°]", color="r")
    ax.set_title("(d) Dispersiyon (renkli ışığın farklı hızları)"); ax.legend(fontsize=8, loc="upper right")

    # (e) Cherenkov açısı ölçümü
    ax = axs.flat[4]
    if ph is not None:
        prim = ph[ph["parent_id"] == 1]
        mu = ev.set_index("event").loc[prim["event"], ["dir_x", "dir_y", "dir_z"]].to_numpy()
        cosang = np.sum(prim[["px", "py", "pz"]].to_numpy()*mu, axis=1)
        ax.hist(np.degrees(np.arccos(np.clip(cosang, -1, 1))), bins=np.linspace(38, 44, 61),
                histtype="stepfilled", alpha=0.6)
        th = np.degrees(np.arccos(1/cm.n_phase(np.array([600, 300]))))
        ax.axvspan(th[0], th[1], color="r", alpha=0.15, label="beklenen 300–600 nm")
        ax.legend(fontsize=8)
    ax.set_xlabel("foton–müon açısı [°]"); ax.set_ylabel("foton sayısı")
    ax.set_title("(e) Cherenkov konisi açısı")

    # (f) Rayleigh saçılması
    ax = axs.flat[5]
    for layer, g in ice.groupby("layer"):
        ax.semilogy(g["wavelength_nm"], g["rayleigh_length_m"], color=LAYER_COLORS[layer],
                    label=f"katman {layer} ({g.depth_m.iloc[0]:.1f} m)")
    ax.set_xlabel("dalga boyu [nm]"); ax.set_ylabel("saçılma uzunluğu [m]")
    ax.set_title("(f) Rayleigh saçılması ∝ λ⁻⁴ (mavi daha çok saçılır)"); ax.legend(fontsize=8)

    # (g) Derinliğe bağlı soğurma
    ax = axs.flat[6]
    at400 = ice[ice["wavelength_nm"] == 400].sort_values("depth_m")
    ax.plot(at400["abs_length_m"], at400["depth_m"], "o-", label="soğurma uzunluğu (400 nm)")
    ax.plot(at400["rayleigh_length_m"], at400["depth_m"], "s-", label="Rayleigh uzunluğu (400 nm)")
    ax.invert_yaxis(); ax.set_xlabel("uzunluk [m]"); ax.set_ylabel("derinlik [m]")
    if hits is not None:
        ax2 = ax.twiny()
        per_layer = hits.groupby("dom_id").size()/len(ev)/9
        depth = d["sensors"].groupby("dom_id")["depth_m"].first()
        ax2.plot(per_layer.values, depth.loc[per_layer.index].values, "r^--", label="hit / DOM / olay")
        ax2.set_xlabel("ortalama hit / DOM / olay", color="r")
    ax.set_title("(g) Derinliğe bağlı soğurma", pad=8); ax.legend(fontsize=8, loc="lower right")

    # (h) Işık verimi ∝ enerji kaybı
    ax = axs.flat[7]
    ax.loglog(ev["E_loss_MeV"]/1e3, ev["n_photons"], "o", alpha=0.6, label="foton sayısı")
    ax.loglog(ev["E_loss_MeV"]/1e3, ev["n_hits"], "s", alpha=0.6, label="sensör hit")
    ax.set_xlabel("müonun buzdaki enerji kaybı [GeV]"); ax.set_ylabel("olay başına sayı")
    ax.set_title("(h) Işık verimi ∝ enerji kaybı"); ax.legend(fontsize=8); ax.grid(alpha=0.3, which="both")

    fig.tight_layout(rect=[0, 0, 1, 0.975])
    out = f"{prefix}_physics.png"
    fig.savefig(out, dpi=110)
    save_panels(fig, axs, f"{prefix}_panels/physics")
    plt.close(fig)
    print("Kaydedildi:", out)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    prefix = sys.argv[1]
    reco_prefix = sys.argv[2] if len(sys.argv) > 2 else prefix
    d = cm.load(prefix)
    dr = d if reco_prefix == prefix else cm.load(reco_prefix)
    reco = cm.reconstruct_all(dr)
    reco.to_csv(f"{reco_prefix}_reconstruction.csv", index=False)
    summary(reco_prefix, dr, reco)
    fig_agn(prefix, d, reco)
    fig_physics(prefix, d)


if __name__ == "__main__":
    main()

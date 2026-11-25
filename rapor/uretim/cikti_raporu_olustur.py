#!/usr/bin/env python3
"""Dedektör çıktılarının sade ve anlaşılır raporu (PDF)."""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rapor_olustur as br  # noqa: E402
from rapor_olustur import P, bullets, figure, table, h1, h2, body, NAVY  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_CENTER  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.lib.units import cm  # noqa: E402
from reportlab.platypus import (CondPageBreak, KeepTogether, NextPageTemplate, PageBreak,  # noqa: E402
                                Paragraph, Spacer, Table, TableStyle)

PROJ = br.PROJ
DATA = f"{PROJ}/build/data"
SCAN, PARAM, TH = f"{DATA}/scan", f"{DATA}/param", f"{DATA}/thesis"
HERE = os.path.dirname(os.path.abspath(__file__))
FIG = f"{HERE}/outfig"
os.makedirs(FIG, exist_ok=True)
OUT = f"{PROJ}/rapor/02_Dedektor_Raporlari/Dedektor_Cikti_Raporu.pdf"
TITLE = "Dedektör Çıktı Raporu"
sys.path.insert(0, f"{PROJ}/analysis")
import common as cm_  # noqa: E402

plt.rcParams.update({"font.size": 11, "axes.titlesize": 12, "axes.spines.top": False,
                     "axes.spines.right": False})
BLUE, ORANGE, GREEN, PURPLE, RED = "#2563a8", "#e8833a", "#3a9a5b", "#7b5ea7", "#c0392b"


def f(x, d=0):
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


class OutDoc(br.ReportDoc):
    def _decor(self, canv, doc):
        canv.saveState()
        canv.setFont("Serif", 8.5); canv.setFillColor(colors.HexColor("#555555"))
        canv.drawString(self.leftMargin, A4[1] - 1.4*cm, "IceCube tipi Geant4 simülasyonu – " + TITLE)
        canv.drawRightString(A4[0] - self.rightMargin, A4[1] - 1.4*cm, br.STUDENT)
        canv.setStrokeColor(colors.HexColor("#9aa5b1")); canv.setLineWidth(0.4)
        canv.line(self.leftMargin, A4[1] - 1.55*cm, A4[0] - self.rightMargin, A4[1] - 1.55*cm)
        canv.drawCentredString(A4[0]/2, 1.2*cm, str(doc.page - 1))
        canv.restoreState()


# ------------------------------------------------------------------ kutular
box_txt = ParagraphStyle("box", parent=body, fontSize=10, leading=14, spaceAfter=0)


def callout(title, text, color="#2563a8", bg="#eef4fb"):
    content = [Paragraph(f"<b>{title}</b>", ParagraphStyle("bt", parent=box_txt, textColor=colors.HexColor(color))),
               Paragraph(text, box_txt)]
    t = Table([[content]], colWidths=[16.2*cm])
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(bg)),
                           ("LINEBEFORE", (0, 0), (0, -1), 3, colors.HexColor(color)),
                           ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                           ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    return KeepTogether([t, Spacer(1, 8)])


def see(text):
    return callout("Ne görüyoruz?", text, "#2563a8", "#eef4fb")


def means(text):
    return callout("Ne anlama geliyor?", text, "#3a9a5b", "#eef8f1")


def kpi_cards(items):
    """Büyük sayı + açıklama kartları (3 sütun)."""
    big = ParagraphStyle("big", fontName="Serif-B", fontSize=19, leading=23, alignment=TA_CENTER, textColor=NAVY)
    lab = ParagraphStyle("lab", fontName="Serif", fontSize=8.8, leading=11.5, alignment=TA_CENTER,
                         textColor=colors.HexColor("#333333"))
    cells = [[Paragraph(v, big), Spacer(1, 3), Paragraph(l, lab)] for v, l in items]
    rows = [cells[i:i+3] for i in range(0, len(cells), 3)]
    t = Table(rows, colWidths=[5.4*cm]*3, rowHeights=[2.6*cm]*len(rows))
    t.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#c5d0dc")),
                           ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c5d0dc")),
                           ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f7f9fc")),
                           ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    return t


# ------------------------------------------------------------------ veri
def load_all():
    S = pd.read_csv(f"{TH}/thesis_summary.csv").sort_values("E_TeV")
    Pm = pd.read_csv(f"{TH}/parameter_study.csv")
    one = cm_.load(f"{SCAN}/E1TeV")
    reco1 = pd.read_csv(f"{SCAN}/E1TeV_reco_detected.csv")
    return S, Pm, one, reco1


# ------------------------------------------------------------------ figürler
def fig_event(one, path):
    ev, summ, sens = one["events"], one["sensor_summary"], one["sensors"]
    # medyan ışıklı bir olay seç
    target = ev["n_detected"].median()
    e = ev.iloc[(ev["n_detected"] - target).abs().argsort().iloc[0]]
    s = summ[(summ.event == e.event) & (summ.n_detected > 0)].merge(sens, on="sensor_id")
    d = e[["dir_x", "dir_y", "dir_z"]].to_numpy(float)
    v = e[["x0_mm", "y0_mm", "z0_mm"]].to_numpy(float)/1000
    pos = s[["x_mm", "y_mm", "z_mm"]].to_numpy()/1000
    l = (pos - v) @ d
    rho = np.linalg.norm((pos - v) - np.outer(l, d), axis=1)
    t = s["t_first_det_ns"].to_numpy()
    t0 = t.min()

    fig = plt.figure(figsize=(13, 5.6))
    ax = fig.add_subplot(1, 2, 1, projection="3d")
    allp = sens[["x_mm", "y_mm", "z_mm"]].to_numpy()/1000
    ax.scatter(*allp.T, s=12, c="lightgray", depthshade=False)
    sc = ax.scatter(*pos.T, s=15 + 10*np.sqrt(s["n_detected"]), c=t - t0, cmap="plasma", edgecolor="k",
                    depthshade=False)
    seg = np.array([v, v + 28*d])
    ax.plot(*seg.T, color=RED, lw=2, label="gerçek müon izi")
    for xs, ys in {(p[0], p[1]) for p in allp}:
        ax.plot([xs, xs], [ys, ys], [-10, 10], color="gray", lw=0.5)
    ax.set_xlim(-12, 12); ax.set_ylim(-12, 12); ax.set_zlim(-11, 11)
    ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]"); ax.set_zlabel("z [m]")
    ax.view_init(elev=20, azim=-60)
    cb = fig.colorbar(sc, ax=ax, shrink=0.6, pad=0.08); cb.set_label("ilk sinyal zamanı [ns]")
    ax.set_title(f"(a) Olay görüntüsü: {f(e.n_detected)} algılanan foton\n(daire boyu ∝ ışık, renk = zaman)")
    ax.legend(loc="upper left", fontsize=9)

    ax2 = fig.add_subplot(1, 2, 2)
    sc2 = ax2.scatter(l, t - t0, c=rho, s=20 + 8*np.sqrt(s["n_detected"]), cmap="viridis", edgecolor="k")
    xx = np.linspace(l.min(), l.max(), 10)
    ax2.plot(xx, (xx - l.min())/cm_.C_VAC + 0, "--", color=RED, label="ışık hızıyla ilerleyen müon (eğim 1/c)")
    cb2 = fig.colorbar(sc2, ax=ax2); cb2.set_label("DOM'un ize uzaklığı [m]")
    ax2.set_xlabel("DOM'un iz boyunca konumu [m]"); ax2.set_ylabel("ilk sinyal zamanı [ns]")
    ax2.set_title("(b) Sinyal, müonla birlikte dedektörü tarar"); ax2.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(path, dpi=150); plt.close(fig)
    return e, len(s)


def fig_heatmap(one, path):
    summ, ev = one["summary"] if "summary" in one else one["sensor_summary"], one["events"]
    per = summ.groupby("sensor_id")["n_detected"].sum()/len(ev)
    per = per.reindex(range(36), fill_value=0)
    M = np.zeros((4, 9))
    for sid, val in per.items():
        M[3 - sid % 4, sid // 4] = val   # üst satır = en sığ katman
    fig, ax = plt.subplots(figsize=(11, 4.3))
    im = ax.imshow(M, cmap="Blues", aspect="auto")
    for r in range(4):
        for c in range(9):
            ax.text(c, r, f"{M[r, c]:.0f}", ha="center", va="center",
                    color="white" if M[r, c] > M.max()*0.55 else "black", fontsize=10)
    ax.set_xticks(range(9)); ax.set_xticklabels([f"S{i}" for i in range(9)])
    depths = [2002.5, 2007.5, 2012.5, 2017.5]
    ax.set_yticks(range(4)); ax.set_yticklabels([f"DOM {3-r}\n{depths[r]} m" for r in range(4)])
    ax.set_xlabel("string"); ax.set_title("1 TeV: her DOM'un olay başına ortalama algıladığı foton sayısı")
    fig.colorbar(im, ax=ax, label="foton / olay")
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)
    return M


def fig_light(S, path):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.5, 4.8))
    E = S.E_TeV
    a1.errorbar(E, S.ph, S.ph_err, fmt="o-", color=BLUE, capsize=3, label="üretilen Cherenkov fotonu")
    a1.errorbar(E, S.hits, S.hits_err, fmt="s-", color=ORANGE, capsize=3, label="DOM'a ulaşan")
    a1.errorbar(E, S.det, S.det_err, fmt="^-", color=GREEN, capsize=3, label="algılanan (fotoçoğaltıcı)")
    a1.set_xscale("log"); a1.set_yscale("log")
    a1.set_xlabel("müon enerjisi [TeV]"); a1.set_ylabel("olay başına ortalama sayı")
    a1.set_title("(a) Foton sayıları"); a1.legend(fontsize=9); a1.grid(alpha=0.3, which="both")
    a2.plot(E, 100*S.eff_hit, "s-", color=ORANGE, label="DOM'a ulaşma oranı")
    a2.plot(E, 100*S.eff_det, "^-", color=GREEN, label="algılanma oranı")
    a2.set_xscale("log"); a2.set_ylim(0, None)
    a2.set_xlabel("müon enerjisi [TeV]"); a2.set_ylabel("üretilen fotonlara oranı [%]")
    a2.set_title("(b) Dedektör verimi"); a2.legend(fontsize=9); a2.grid(alpha=0.3, which="both")
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


def fig_dedx(S, path):
    fig, ax = plt.subplots(figsize=(8.5, 5))
    grid = np.logspace(4.5, 8.2, 200)
    ax.loglog(grid/1e6, cm_.groom_dedx_ice(grid, "total"), "k", label="literatür (Groom/PDG): toplam")
    ax.loglog(grid/1e6, cm_.groom_dedx_ice(grid, "ion"), "k:", label="literatür: yalnız iyonizasyon")
    ax.errorbar(S.E_TeV, S.dedx_tot, S.dedx_tot_err, fmt="o", color=BLUE, capsize=3, ms=7,
                label="simülasyon: ortalama")
    ax.plot(S.E_TeV, S.dedx_tot_med, "x", color=ORANGE, ms=9, mew=2, label="simülasyon: medyan (tipik olay)")
    C = pd.read_csv(f"{TH}/dedx_check.csv")
    ax.errorbar(C.E_TeV, C.dedx, C.dedx_err, fmt="D", color=GREEN, mfc="none", capsize=3, ms=9, mew=1.8,
                label="doğrulama: 4000 olay (ışık kapalı)")
    ax.set_xlabel("müon enerjisi [TeV]"); ax.set_ylabel("enerji kaybı dE/dx [MeV/cm]")
    ax.set_title("Müonun buzda birim yol başına enerji kaybı"); ax.legend(fontsize=9)
    ax.grid(alpha=0.3, which="both")
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


def fig_direction(S, reco1, path):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.5, 4.9))
    for key, lab, c, m in [("lf", "basit yöntem (LineFit)", ORANGE, "s"), ("fit", "Cherenkov zaman fiti", BLUE, "o")]:
        y = S[key]
        a1.errorbar(S.E_TeV, y, [y - S[key + "_lo"], S[key + "_hi"] - y], fmt=m + "-", color=c,
                    capsize=3, label=lab)
    a1.set_xscale("log"); a1.set_yscale("log")
    a1.set_xlabel("müon enerjisi [TeV]"); a1.set_ylabel("tipik yön hatası [°] (medyan)")
    a1.set_title("(a) Tek bir olayın yön hatası"); a1.legend(fontsize=9); a1.grid(alpha=0.3, which="both")

    ok = reco1.dropna(subset=["ra_reco"])
    a2.scatter(ok.ra_reco, ok.dec_reco, s=10, alpha=0.5, color=BLUE, label="tek tek olaylar (1 TeV)")
    src = cm_.combined_source(reco1)
    a2.plot(src[0], src[1], "k+", ms=16, mew=2.5, label=f"{src[3]} olayın birleşimi")
    a2.add_patch(plt.Circle((src[0], src[1]), max(src[2], 0.1), fill=False, ls="--", color="k"))
    a2.plot(77.358, 5.693, "*", ms=20, color=ORANGE, mec="k", label="TXS 0506+056 (gerçek kaynak)")
    a2.set_xlim(77.36 - 9, 77.36 + 9); a2.set_ylim(5.69 - 9, 5.69 + 9)
    a2.set_xlabel("RA [°]"); a2.set_ylabel("Dec [°]"); a2.legend(fontsize=8.5, loc="lower left")
    a2.set_title("(b) Gökyüzünde kaynağın bulunması"); a2.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)
    return src


def fig_time(path):
    import thesis as T
    fig, ax = plt.subplots(figsize=(8.5, 4.6))
    out = {}
    for lab, p, c in [("Rayleigh buz", f"{SCAN}/E1TeV", BLUE), ("Mie buz (gerçeğe yakın)", f"{PARAM}/mie", RED)]:
        r, _ = T.time_residuals(cm_.load(p))
        out[lab] = (np.median(r), np.percentile(r, 90), 100*(r > 20).mean())
        ax.hist(r, bins=np.linspace(-10, 150, 81), histtype="step", lw=2, color=c, density=True,
                label=f"{lab}: medyan {np.median(r):.1f} ns")
    ax.set_yscale("log"); ax.set_xlabel("ilk fotonun gecikmesi (saçılmasaydı gelecekti zamana göre) [ns]")
    ax.set_ylabel("DOM oranı"); ax.set_title("1 TeV: saçılmanın sinyali geciktirmesi"); ax.legend()
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)
    return out


# ------------------------------------------------------------------ içerik
def build():
    S, Pm, one, reco1 = load_all()
    figs = {k: f"{FIG}/{k}.png" for k in ("event", "heat", "light", "dedx", "dir", "time")}
    if not os.path.exists(f"{HERE}/codefig/3d.png"):
        import kod_raporu_olustur as kr
        os.makedirs(kr.FIG, exist_ok=True); kr.fig_3d(f"{kr.FIG}/3d.png")
    e_shown, n_dom = fig_event(one, figs["event"])
    M = fig_heatmap(one, figs["heat"])
    fig_light(S, figs["light"]); fig_dedx(S, figs["dedx"])
    src = fig_direction(S, reco1, figs["dir"])
    delays = fig_time(figs["time"])
    r1 = S[S.E_TeV == 1].iloc[0]
    r3, r10, r30, r100 = (S[S.E_TeV == e].iloc[0] for e in (3, 10, 30, 100))
    C = pd.read_csv(f"{TH}/dedx_check.csv").sort_values("E_TeV")
    _s = one['sensor_summary']
    ndom_det = _s[_s.n_detected > 0].groupby('event').size().mean()
    Emin, Emax = S.E_TeV.min(), S.E_TeV.max()
    nE = len(S)
    pending = [e for e in (10, 30) if e not in set(S.E_TeV)]  # 100 TeV koşusu yapılmadı

    st = []
    title = ParagraphStyle("tt", fontName="Serif-B", fontSize=24, leading=32, alignment=TA_CENTER, textColor=NAVY)
    cs = ParagraphStyle("cs", fontName="Serif", fontSize=12.5, leading=19, alignment=TA_CENTER)
    st += [Spacer(1, 5*cm), P(TITLE.upper(), title), Spacer(1, 0.6*cm),
           P("IceCube tipi buz dedektörünün Geant4 simülasyonundan elde edilen sonuçlar", cs),
           Spacer(1, 6*cm), P(f"<b>Hazırlayan:</b> {br.STUDENT} ({br.STUDENT_NO})", cs),
           P(f"<b>Danışman:</b> {br.ADVISOR}", cs), Spacer(1, 3*cm), P("Erciyes Üniversitesi – " + br.DATE, cs),
           NextPageTemplate("normal"), PageBreak()]

    # ---------------------------------------------------------- bir bakışta
    eloss1 = r1.dedx_tot*r1.L_m*100/1e3
    st += [P("BİR BAKIŞTA", h1),
           P(f"Bu raporda, buz içine yerleştirilmiş <b>36 optik sensörlü (DOM)</b> bir dedektörün, "
             f"TXS 0506+056 blazarı yönünden gelen müonları nasıl gördüğü anlatılmaktadır. "
             f"{nE} farklı enerjide ({f(Emin,1)}–{f(Emax,0)} TeV) toplam {f(S.N.sum())} müon simüle edilmiştir. "
             f"Aşağıdaki kartlar 1 TeV müon için tipik değerlerdir."),
           Spacer(1, 4),
           kpi_cards([(f"{f(r1.ph/1e6,2)} milyon", "müonun buzda ürettiği<br/>Cherenkov fotonu (olay başına)"),
                      (f"{f(r1.hits)}", "DOM'lara ulaşan foton"),
                      (f"{f(r1.det)}", "fotoçoğaltıcıların algıladığı<br/>foton (kuantum verimi sonrası)"),
                      (f"%{f(100*r1.eff_det,3)}", "algılanma oranı<br/>(her ~{0} fotondan 1'i)".format(f(1/r1.eff_det))),
                      (f"{f(eloss1,1)} GeV", f"buzda kaybedilen enerji<br/>({f(r1.L_m,1)} m yolda, enerjinin %{f(eloss1/10,2)}'i)"),
                      (f"{f(r1.fit,1)}°", "tek olayda tipik yön hatası")]),
           Spacer(1, 10),
           P("<b>Beş temel sonuç</b>", h2),
           *bullets([
               f"Dedektör her müonu görür: 1 TeV'de her olayda 36 DOM'un hepsine ışık ulaşır, ortalama {f(ndom_det,1)} DOM gerçekten sinyal üretir.",
               "Algılanan ışık enerjiyle artar; ışık miktarından müonun enerjisi kestirilebilir.",
               "Simülasyonun enerji kaybı 1 TeV'e kadar literatürle (Groom/PDG) %5 içinde uyumludur; daha yüksek "
               "enerjide ortalama, seyrek ama çok büyük kayıplar yüzünden güçlü dalgalanır ve tipik (medyan) olay "
               "ortalamadan çok daha az enerji kaybeder.",
               f"Tek bir olayın yönü ~{f(r1.fit,0)}° hatayla bulunur; {f(src[3])} olay birleştirilince kaynak "
               f"TXS 0506+056'ya {f(r1.src_dist_TXS,2)}° uzaklıkta bulunur.",
               "Buzdaki saçılma ışığı geciktirir; gecikmenin büyüklüğü saçılmanın türüne bağlıdır. Sensörleri sıklaştırmak ışığı artırır ve yön hatasını azaltır."]),
           ]
    if pending:
        st += [callout("Not", f"{', '.join(f(e) for e in pending)} TeV koşuları henüz sürmektedir; bittiklerinde "
                       "bu rapordaki tablo ve grafikler aynı betikle yeniden üretilip güncellenecektir.",
                       "#b7791f", "#fdf6e3")]
    st += [PageBreak()]

    # ---------------------------------------------------------- 1 dedektör
    st += [P("1. DEDEKTÖR VE ÇIKTISI", h1),
           P("Dedektör, 20 m × 20 m × 20 m'lik bir buz bloğu ve içine 6 m aralıklarla dizilmiş 9 dikey kablodan "
             "(string) oluşur. Her stringde farklı derinliklerde 4 DOM bulunur. Buz derinliğe göre dört katmana "
             "ayrılmıştır; üstten ikinci katman tozludur, ışığı daha çok soğurur ve saçar."),
           figure(f"{HERE}/codefig/3d.png", 11.5, "Dedektörün yapısı: 9 string, 36 DOM (turuncu), 4 buz katmanı "
                  "ve örnek bir müon izi (kırmızı)."),
           P("Bir müon buzdan geçerken ışıktan hızlı hareket ettiği için mavi-mor <b>Cherenkov ışığı</b> yayar. "
             "Bu ışığın küçük bir kısmı DOM'lara ulaşır. Dedektör her olay için şu bilgileri kaydeder:"),
           table([["Çıktı", "Ne anlatır?"],
                  ["Her DOM'un algıladığı foton sayısı", "Işığın nerede yoğun olduğu → müonun nereden geçtiği, ne kadar enerji bıraktığı"],
                  ["Her DOM'un ilk sinyal zamanı", "Işığın hangi sırayla geldiği → müonun hangi yöne gittiği"],
                  ["Olaydaki toplam ışık", "Müonun buzda bıraktığı enerji → müonun enerjisi"]],
                 [6.0, 10.4], "Dedektörün temel çıktıları."),
           ]

    # ---------------------------------------------------------- 2 tek olay
    st += [PageBreak(), P("2. TEK BİR OLAY NASIL GÖRÜNÜR?", h1),
           figure(figs["event"], 16.2, f"1 TeV'lik tipik bir olay (olay no {int(e_shown.event)}). (a) Işık alan DOM'lar: "
                  "daire büyüklüğü algılanan foton sayısını, renk ilk sinyal zamanını gösterir. (b) Her DOM'un ilk "
                  "sinyal zamanı, DOM'un müon izi boyunca konumuna karşı."),
           see(f"Bu olayda {n_dom} DOM ışık algılamış, toplam {f(e_shown.n_detected)} foton sayılmıştır. Müon izine "
               "yakın DOM'lar (büyük daireler) çok daha fazla ışık görür. Sağdaki grafikte noktalar kabaca düz bir "
               "çizgi üzerindedir: müonun girdiği taraftaki DOM'lar önce, çıktığı taraftakiler sonra sinyal verir."),
           means("Işığın <i>nerede</i> ve <i>ne zaman</i> görüldüğü, müonun yolunu ortaya çıkarır. Rekonstrüksiyon "
                 "algoritması tam olarak bu zaman–konum ilişkisini kullanarak müonun yönünü hesaplar. İzden uzak "
                 "DOM'lar (açık renkli noktalar) düz çizginin biraz üstündedir; çünkü onlara ulaşan ışık buzda daha "
                 "uzun yol alır ve saçılarak gecikir."),
           ]

    # ---------------------------------------------------------- 3 hangi DOM
    top = np.unravel_index(np.argmax(M), M.shape)
    st += [CondPageBreak(12*cm), P("3. HANGİ DOM NE KADAR IŞIK GÖRDÜ?", h1),
           figure(figs["heat"], 16.0, "1 TeV'de her DOM'un olay başına ortalama algıladığı foton sayısı. "
                  "Satırlar derinliği (üstte en sığ), sütunlar stringleri gösterir."),
           see(f"En çok ışığı ortadaki stringler (S3–S5) ve orta derinlikteki DOM'lar (DOM 1 ve 2) alır; en "
               f"parlak DOM olay başına ~{f(M.max())} foton görürken en sönük olanlar ~{f(M.min())} foton görür. "
               "Kenardaki ve en üst/en alttaki DOM'lar daha az ışık alır."),
           means("Müonlar dedektörün ortasından, yaklaşık yatay geçecek şekilde gönderilmiştir. Işık uzaklıkla hızla "
                 "azaldığı için ize yakın DOM'lar parlak görünür. Toz katmanındaki DOM 2, ize benzer uzaklıkta olsa da "
                 "DOM 1'den biraz daha az ışık alır: tozlu buz ışığı daha çok soğurur."),
           ]

    # ---------------------------------------------------------- 4 enerji tablosu
    rows = [["Enerji (TeV)", "Olay", "Üretilen foton", "DOM'a ulaşan", "Algılanan", "Algılanma oranı",
             "Enerji kaybı (GeV)", "Yön hatası"]]
    for _, r in S.iterrows():
        rows.append([f(r.E_TeV, 1) if r.E_TeV < 1 else f(r.E_TeV), f(r.N), f(r.ph), f(r.hits), f(r.det),
                     f"%{f(100*r.eff_det,3)}", f(r.dedx_tot*r.L_m*100/1e3, 1), f"{f(r.fit,1)}°"])
    ratio_det = S.det.iloc[-1]/S.det.iloc[0]
    st += [PageBreak(), P("4. ENERJİYE GÖRE DEDEKTÖR ÇIKTISI", h1),
           table(rows, [1.7, 1.2, 2.4, 2.0, 1.9, 2.3, 2.5, 1.9],
                 "Her enerji için olay başına ortalama değerler (yön hatası: medyan, Cherenkov fiti).",
                 align_center_cols=tuple(range(8))),
           figure(figs["light"], 16.2, "(a) Olay başına üretilen, DOM'a ulaşan ve algılanan foton sayısı. "
                  "(b) Üretilen fotonların yüzde kaçının DOM'a ulaştığı ve algılandığı."),
           see(f"Enerji {f(Emin,1)} TeV'den {f(Emax,0)} TeV'e çıkınca algılanan foton sayısı yaklaşık "
               f"{f(ratio_det,1)} kat artar. Üretilen fotonların yalnızca yaklaşık binde biri algılanır; bu oran "
               f"çoğu enerjide %{f(100*S.eff_det.median(),2)} civarındadır ve en düşük değerini "
               f"{f(S.E_TeV[S.eff_det.idxmin()],0)} TeV'de alır (%{f(100*S.eff_det.min(),3)})."),
           means("Düşük enerjide ışığın çoğu doğrudan müondan gelir ve müon başına neredeyse sabittir. Enerji arttıkça "
                 "müon, buzda elektron–pozitron çiftleri ve frenleme ışıması ile <i>ışık sağanakları</i> (kaskad) "
                 "oluşturur; toplam ışığı artıran budur. Algılanma oranının düşük olmasının nedeni geometridir: "
                 "36 DOM'un toplam yüzeyi yalnızca ~3 m²'dir; ışığın çoğu buzdan dışarı kaçar ya da soğurulur. "
                 "Yüksek enerjide kaskadlar iz boyunca rastgele yerlerde, bazen DOM'lardan uzakta oluştuğu için "
                 "toplanan ışık oranı olaydan olaya değişir; az olaylı yüksek enerji noktalarında oran bu yüzden "
                 "dalgalanır."),
           ]

    # ---------------------------------------------------------- 5 enerji kaybı
    st += [PageBreak(), P("5. MÜONUN ENERJİ KAYBI – LİTERATÜRLE KARŞILAŞTIRMA", h1),
           figure(figs["dedx"], 13.5, "Simülasyondaki ortalama ve medyan enerji kaybı ile PDG/Groom "
                  "tablosundan (su, buz yoğunluğuna ölçeklenmiş) alınan değerler."),
           see(f"1 TeV'e kadar simülasyon ortalaması literatür eğrisiyle %5 içinde örtüşür (1 TeV'de {f(r1.dedx_tot,2)} "
               f"MeV/cm, literatür {f(r1.groom_tot,2)} MeV/cm). Daha yüksek enerjide ortalama literatür eğrisinin "
               f"etrafında büyük dalgalanır: 3 TeV'de %{f(100*(1 - r3.dedx_tot/r3.groom_tot),0)} altında, 10 ve 30 "
               f"TeV'de %{f(100*(r10.dedx_tot/r10.groom_tot - 1),0)} ve %{f(100*(r30.dedx_tot/r30.groom_tot - 1),0)} "
               f"üstündedir; yalnızca 20 olayın koşulduğu 100 TeV'de ise %{f(100*(1 - r100.dedx_tot/r100.groom_tot),0)} "
               f"altındadır. Medyan (tipik olay) değerleri ortalamadan çok daha düşüktür. Yeşil noktalar, ışık "
               f"kapatılarak yapılan 4000'er olaylık doğrulama koşularıdır: literatürle "
               f"{' ve '.join(f(r.E_TeV) + ' TeV' for _, r in C.iterrows())}'de %"
               f"{f(100*(1 - C.ratio.min()),0)} içinde örtüşürler."),
           means("~1 TeV'in üstünde enerji kaybına <i>radyatif</i> süreçler hakim olur. Bu kayıplar seyrek ama çok "
                 "büyüktür: çoğu olay az, birkaç olay çok enerji kaybeder. Bu yüzden ortalama, birkaç büyük kaskadın "
                 "olup olmamasına göre yukarı ya da aşağı sapar ve az olayla yeterince örneklenemez. Doğrulama "
                 f"koşuları bunu kanıtlar: 4000 olayın ortalaması literatüre oturur, ama aynı veriden rastgele 20 olay "
                 f"seçildiğinde ortalama tipik olarak literatürün yalnızca %{f(100*C.sub20_med.iloc[-1],0)}'i kadar "
                 "çıkar. Yani simülasyonun fiziği doğrudur; sapmalar sınırlı olay sayısından kaynaklanır."),
           callout("Teknik not: 100 TeV ve fizik tabloları",
                   "Geant4'ün fizik tabloları varsayılan olarak 100 TeV'e kadar hesaplanır. İlk 100 TeV koşusunda müon "
                   "tam bu sınırda başladığı için enerji kaybı çok düşük çıktı; tablolar 10 PeV'e genişletilerek koşu "
                   "yenilendi. Bu rapordaki 100 TeV sonuçları düzeltilmiş koşuya aittir.", "#b7791f", "#fdf6e3"),
           ]

    # ---------------------------------------------------------- 6 zaman
    st += [CondPageBreak(14*cm), P("6. SİNYALİN ZAMANI VE BUZUN ETKİSİ", h1),
           figure(figs["time"], 13.0, "Her DOM'a ulaşan ilk fotonun, saçılmadan doğrudan gelseydi ulaşacağı "
                  "zamana göre gecikmesi. Mavi: Rayleigh saçılmalı buz, kırmızı: ileri yönlü Mie saçılmalı buz."),
           see(f"Her iki modelde de DOM'ların çoğuna ilk foton neredeyse zamanında ulaşır (medyan ~0 ns). Fark "
               f"kuyruktadır: Rayleigh buzunda DOM'ların %{f(delays['Rayleigh buz'][2],0)}'inde ilk foton 20 ns'den "
               f"geç gelirken Mie buzunda bu oran %{f(delays['Mie buz (gerçeğe yakın)'][2],1)}'tir; %90'lık gecikme "
               f"{f(delays['Rayleigh buz'][1],0)} ns'den {f(delays['Mie buz (gerçeğe yakın)'][1],0)} ns'ye iner."),
           means("Saçılan ışık daha uzun yol aldığı için geç gelir. İki modelde ışığın yönünü 'unutması' için gereken "
                 "etkin mesafe aynı seçilmiştir; ancak Mie saçılması ileri yönlüdür (her saçılmada yön biraz değişir), "
                 "Rayleigh ise ışığı her yöne saçar. Bu yüzden Mie buzunda ilk fotonlar daha az gecikir ve zaman "
                 "bilgisi daha temiz kalır. Sıfırın biraz altındaki değerler, ışığın DOM'un merkezine değil 16,5 cm "
                 "önündeki yüzeyine çarpmasından kaynaklanır."),
           ]

    # ---------------------------------------------------------- 7 yön
    st += [PageBreak(), P("7. MÜONUN YÖNÜ VE KAYNAĞIN BULUNMASI", h1),
           figure(figs["dir"], 16.2, "(a) Enerjiye göre tek bir olayın tipik yön hatası (hata çubukları: %68 güven "
                  "aralığı). (b) 1 TeV'de her olayın gösterdiği kaynak yönü ve olayların birleşimi."),
           see(f"Basit LineFit yöntemi ~{f(r1.lf,0)}° hata verirken, Cherenkov ışığının geometrisini kullanan fit "
               f"hatayı ~{f(r1.fit,1)}°'ye düşürür. Tek tek olaylar gökyüzünde geniş bir alana dağılır; ancak "
               f"{f(src[3])} olay birleştirildiğinde kaynak ({f(src[0],2)}°, {f(src[1],2)}°) konumunda, gerçek "
               f"kaynağa {f(r1.src_dist_TXS,2)}° uzaklıkta bulunur."),
           means("Küçük bir dedektörde tek bir olay kaynağı belirlemek için yeterli değildir. Ancak aynı kaynaktan "
                 "gelen olaylar birleştirildikçe hata √N ile küçülür. Katalogdaki diğer AGN'ler onlarca derece "
                 "uzakta olduğu için kaynak açık farkla TXS 0506+056 (BL Lac türü blazar) ile eşleşir. Gerçek "
                 "IceCube çok daha büyük olduğu için tek olayda 1°'nin altına iner."),
           ]

    # ---------------------------------------------------------- 8 ayarlar
    rows = [["Ayar (1 TeV)", "Yön hatası (medyan)", "Algılanan foton / olay", "Algılanma oranı"]]
    for _, r in Pm.iterrows():
        rows.append([r.config.replace("aralık", "string aralığı"), f"{f(r.fit,2)}°", f(r.det), f"%{f(100*r.eff_det,3)}"])
    sp = Pm[Pm.ice == "Rayleigh"].sort_values("spacing")
    st += [PageBreak(), P("8. DEDEKTÖR AYARLARI DEĞİŞİNCE NE OLUYOR?", h1),
           P("Aynı 1 TeV müonlar, dedektörün iki ayarı değiştirilerek yeniden simüle edildi: stringler arası mesafe "
             "(4, 6, 8 m) ve buzun saçılma modeli (Rayleigh, Mie)."),
           table(rows, [5.0, 3.6, 4.0, 3.8], "Ayarlara göre dedektör başarımı (6 m ve Rayleigh, temel ayardır).",
                 align_center_cols=(1, 2, 3)),
           see(f"Stringler 4 m aralıkla dizildiğinde algılanan ışık belirgin artar ({f(sp.det.iloc[0])} foton; 6 ve 8 m'de "
               f"~{f(sp.det.iloc[1])}). Yön hatası aralık büyüdükçe kötüleşir ({f(sp.fit.iloc[0],1)}° → "
               f"{f(sp.fit.iloc[1],1)}° → {f(sp.fit.iloc[2],1)}°). Mie buzunda algılanan ışık ~%"
               f"{f(100*(1-Pm.det.iloc[-1]/sp.det.iloc[1]))} azalır; yön hatası ise istatistiksel belirsizlik "
               "içinde benzerdir."),
           means("Daha sık sensör ize daha yakın olduğu için daha fazla ve daha az gecikmiş ışık toplar; ama aynı sayıda "
                 "sensörle daha küçük bir hacmi kaplar. Gerçek dedektörlerde bu bir maliyet–başarım dengesidir. Mie "
                 "buzunda ilk fotonlar daha az geciktiği için (Bölüm 6) yön hatası biraz daha küçüktür; ancak ileri "
                 "yönlü saçılan ışığın bir kısmı DOM'lara uğramadan buzdan çıktığı için algılanan ışık azalır."),
           ]

    # ---------------------------------------------------------- sonuç + sözlük
    st += [PageBreak(), P("SONUÇ", h1),
           *bullets([
               f"Dedektör, {f(Emin,1)}–{f(Emax,0)} TeV aralığındaki tüm müonları görmüş; olay başına ortalama "
               f"{f(S.det.min())} ile {f(S.det.max())} foton algılamıştır.",
               "Algılanan ışık miktarı müonun enerjisiyle artar; artışın kaynağı radyatif kayıpların oluşturduğu kaskadlardır.",
               "Müonun enerji kaybı 1 TeV'e kadar literatürle uyumludur; ortalama ile tipik olay arasındaki fark, radyatif "
               "kayıpların seyrek ve büyük olmasından kaynaklanır.",
               "Sinyal zamanları müonun yönünü verir; olaylar birleştirilince kaynak doğru şekilde TXS 0506+056 "
               "olarak bulunur.",
               "Sensör aralığı ışık toplamayı ve yön bulmayı belirgin etkiler; buzun saçılma türü sinyal zamanlarını ve toplanan ışığı değiştirir."]),
           Spacer(1, 10), P("TERİMLER SÖZLÜĞÜ", h1),
           table([["Terim", "Anlamı"],
                  ["DOM", "Digital Optical Module: içinde fotoçoğaltıcı tüp bulunan cam küre; ışık sensörü."],
                  ["String", "Üzerine DOM'ların dizildiği dikey kablo."],
                  ["Cherenkov ışığı", "Yüklü parçacık ortamdaki ışık hızından hızlı gittiğinde yayılan mavi ışık."],
                  ["Hit / DOM'a ulaşan foton", "DOM yüzeyine çarpan foton."],
                  ["Algılanan foton", "Fotoçoğaltıcının gerçekten sinyale çevirdiği foton (kuantum verimi ~%25)."],
                  ["Kuantum verimi", "Bir fotonun algılanma olasılığı; dalga boyuna bağlıdır."],
                  ["dE/dx", "Müonun birim yol başına kaybettiği enerji (MeV/cm)."],
                  ["Radyatif kayıp", "Çift üretimi, frenleme ışıması gibi seyrek ama büyük enerji kayıpları."],
                  ["Kaskad (sağanak)", "Büyük bir enerji kaybının oluşturduğu çok sayıda parçacık ve ışık."],
                  ["Rayleigh / Mie saçılması", "Işığın buzdaki küçük parçacıklarla yön değiştirmesi; Mie ileri yönlüdür."],
                  ["Rekonstrüksiyon", "Dedektör verisinden müonun yönünü/enerjisini geri hesaplama."],
                  ["Medyan", "Sıralı verinin ortadaki değeri; 'tipik' değer."],
                  ["TXS 0506+056", "2017'de bir IceCube nötrinosuyla ilişkilendirilen BL Lac türü blazar."]],
                 [4.4, 12.0], "Raporda geçen terimler."),
           ]

    doc = OutDoc(OUT, title=TITLE, author=br.STUDENT, subject="Dedektör çıktıları")
    doc.multiBuild(st)
    print("PDF:", OUT)


if __name__ == "__main__":
    build()

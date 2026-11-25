#!/usr/bin/env python3
"""Dedektör geometrisi ve tüm kodları anlatan teknik belge (PDF)."""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch, Rectangle

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rapor_olustur as br  # noqa: E402  (yazı tipleri, stiller, yardımcılar)
from rapor_olustur import P, bullets, eq, figure, table, h1, h2, body, code, NAVY  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_CENTER  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.lib.units import cm  # noqa: E402
from reportlab.platypus import (CondPageBreak, NextPageTemplate, PageBreak, Preformatted,  # noqa: E402
                                Spacer)
from reportlab.platypus.tableofcontents import TableOfContents  # noqa: E402

PROJ = br.PROJ
HERE = os.path.dirname(os.path.abspath(__file__))
FIG = f"{HERE}/codefig"
os.makedirs(FIG, exist_ok=True)
OUT = f"{PROJ}/rapor/02_Dedektor_Raporlari/Kod_ve_Geometri_Aciklamasi.pdf"
DOC_TITLE = "Dedektör Geometrisi ve Simülasyon Kodlarının Açıklaması"

h3 = ParagraphStyle("h3", fontName="Serif-B", fontSize=10.8, leading=14, textColor=colors.HexColor("#2d4a73"),
                    spaceBefore=8, spaceAfter=3)
small_code = ParagraphStyle("scode", parent=code, fontSize=6.6, leading=8.2)


class CodeDoc(br.ReportDoc):
    def _decor(self, canv, doc):
        canv.saveState()
        canv.setFont("Serif", 8.5)
        canv.setFillColor(colors.HexColor("#555555"))
        canv.drawString(self.leftMargin, A4[1] - 1.4*cm, DOC_TITLE)
        canv.drawRightString(A4[0] - self.rightMargin, A4[1] - 1.4*cm, br.STUDENT)
        canv.setStrokeColor(colors.HexColor("#9aa5b1")); canv.setLineWidth(0.4)
        canv.line(self.leftMargin, A4[1] - 1.55*cm, A4[0] - self.rightMargin, A4[1] - 1.55*cm)
        canv.drawCentredString(A4[0]/2, 1.2*cm, str(doc.page - 1))
        canv.restoreState()


def src(path):
    with open(os.path.join(PROJ, path), encoding="utf-8") as f:
        return f.read()


def snippet(path, start, end):
    """Dosyadan satır aralığı (1 tabanlı, uçlar dahil)."""
    lines = src(path).splitlines()[start - 1:end]
    return C("\n".join(lines))


def C(text):
    # Sayfa genişliğini aşan satırlar girintili devam satırıyla bölünür
    return Preformatted(text, code, maxLineLength=96, newLineChars="    ")


# ======================================================================= diyagramlar
SPACING = 6.0
SENS = [(i, (((i//4)//3) - 1)*SPACING, (((i//4) % 3) - 1)*SPACING, -10 + ((i % 4) + 0.5)*5) for i in range(36)]


def fig_3d(path):
    fig = plt.figure(figsize=(9, 7.5))
    ax = fig.add_subplot(111, projection="3d")
    # buz katmanları
    cols = ["#08306b", "#2171b5", "#9e9ac8", "#6baed6"]
    for L in range(4):
        z0, z1 = -10 + 5*L, -5 + 5*L
        for z in (z0, z1):
            xx, yy = np.meshgrid([-10, 10], [-10, 10])
            ax.plot_surface(xx, yy, np.full_like(xx, z, dtype=float), alpha=0.05, color=cols[L])
        for (x, y) in [(-10, -10), (10, -10), (10, 10), (-10, 10)]:
            ax.plot([x, x], [y, y], [z0, z1], color="#2171b5", lw=0.6)
        for z in (z0, z1):
            ax.plot([-10, 10, 10, -10, -10], [-10, -10, 10, 10, -10], [z]*5, color="#2171b5", lw=0.6)
        ax.text(10.5, -10, (z0 + z1)/2, f"katman {L}", fontsize=8, color=cols[L])
    # stringler ve DOM'lar
    for s in range(9):
        x, y = SENS[4*s][1], SENS[4*s][2]
        ax.plot([x, x], [y, y], [-10, 10], color="k", lw=0.8)
        ax.text(x, y, 10.8, f"S{s}", fontsize=8, ha="center")
    xs = [p[1] for p in SENS]; ys = [p[2] for p in SENS]; zs = [p[3] for p in SENS]
    ax.scatter(xs, ys, zs, s=45, c="orange", edgecolor="k", depthshade=False)
    # örnek müon izi (TXS 0506+056 yönü)
    alt, az = np.radians(-5.693), np.radians(77.358)
    d = -np.array([np.cos(alt)*np.cos(az), np.cos(alt)*np.sin(az), np.sin(alt)])
    p0 = np.array([1.5, 0.5, -0.5]) - 14*d
    seg = np.array([p0, p0 + 28*d])
    ax.plot(seg[:, 0], seg[:, 1], seg[:, 2], color="crimson", lw=2.2, label="örnek müon izi")
    ax.quiver(*(p0 + 23*d), *(3*d), color="crimson", arrow_length_ratio=0.5, lw=2)
    ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]"); ax.set_zlabel("z [m] (yukarı)")
    ax.set_xlim(-15, 15); ax.set_ylim(-15, 15); ax.set_zlim(-12, 12)
    ax.view_init(elev=22, azim=-58)
    ax.legend(loc="upper left")
    ax.set_title("Dedektörün üç boyutlu görünümü (dünya hacmi: ±15 m vakum)")
    fig.tight_layout()
    fig.savefig(path, dpi=150); plt.close(fig)


def fig_numbering(path):
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 5.4))
    a1.add_patch(Rectangle((-10, -10), 20, 20, fc="#dbeefc", ec="#2171b5"))
    for s in range(9):
        ix, iy = s // 3, s % 3
        x, y = (ix - 1)*SPACING, (iy - 1)*SPACING
        a1.scatter(x, y, s=260, c="orange", ec="k", zorder=3)
        a1.text(x, y, f"S{s}", ha="center", va="center", fontsize=9, zorder=4)
        a1.text(x, y - 1.6, f"(ix={ix}, iy={iy})\nID {4*s}–{4*s+3}", ha="center", va="top", fontsize=7.5)
    a1.annotate("", xy=(13, -13), xytext=(8.5, -13), arrowprops=dict(arrowstyle="->"))
    a1.text(13.3, -13, "x", va="center"); a1.annotate("", xy=(-13, 13), xytext=(-13, 8.5),
                                                      arrowprops=dict(arrowstyle="->"))
    a1.text(-13, 13.4, "y", ha="center")
    a1.set_xlim(-15, 15); a1.set_ylim(-15, 15); a1.set_aspect("equal")
    a1.set_xlabel("x [m]"); a1.set_ylabel("y [m]")
    a1.set_title("(a) Üstten: string numarası  s = 3·ix + iy")

    for L in range(4):
        a2.add_patch(Rectangle((-10, -10 + 5*L), 20, 5, fc=["#c6dbef", "#9ecae1", "#bcbddc", "#deebf7"][L],
                               ec="#2171b5"))
        a2.text(10.4, -7.5 + 5*L, f"katman {L} = DOM {L}\nz = {-7.5+5*L:+.1f} m\nderinlik {2017.5-5*L:.1f} m",
                va="center", fontsize=8)
    for s, x in [(1, -6), (4, 0), (7, 6)]:
        a2.plot([x, x], [-10, 10], "k", lw=0.8)
        for L in range(4):
            a2.scatter(x, -7.5 + 5*L, s=200, c="orange", ec="k", zorder=3)
            a2.text(x, -7.5 + 5*L, f"{4*s+L}", ha="center", va="center", fontsize=8, zorder=4)
        a2.text(x, 10.6, f"S{s}", ha="center")
    a2.set_xlim(-14, 18); a2.set_ylim(-12, 12); a2.set_aspect("equal")
    a2.set_xlabel("x [m] (y = 0 kesiti)"); a2.set_ylabel("z [m]")
    a2.set_title("(b) Yandan: sensör ID = 4·s + DOM")
    fig.tight_layout()
    fig.savefig(path, dpi=150); plt.close(fig)


def box(ax, x, y, w, h, text, fc="#e8eef7", ec=NAVY.hexval().replace("0x", "#"), fs=9, bold=False):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=fc, ec=ec, lw=1.2))
    ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", wrap=True)


def arrow(ax, x0, y0, x1, y1, text=None, color="#333333"):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="->", color=color, lw=1.3))
    if text:
        ax.text((x0 + x1)/2 + 0.05, (y0 + y1)/2, text, fontsize=7.5, color=color, va="center")


def fig_hierarchy(path):
    fig, ax = plt.subplots(figsize=(10, 4.6))
    ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 4.6)
    box(ax, 3.5, 3.6, 3, 0.8, "World (G4Box ±15 m)\nG4_Galactic – vakum", fc="#f0f0f0", bold=True)
    for L in range(4):
        x = 0.2 + 2.45*L
        box(ax, x, 1.9, 2.2, 0.9, f"IceLayer kopya {L}\nG4Box 20×20×5 m\nIce_L{L} (ρ=0.917)", fc="#dbeefc", fs=8)
        arrow(ax, 5, 3.6, x + 1.1, 2.8)
        box(ax, x + 0.15, 0.2, 1.9, 1.0, f"9 × Sensor\nG4Orb r=16.51 cm\nPyrex, ID {L},{L+4},…,{L+32}",
            fc="#ffe9b3", fs=7.5)
        arrow(ax, x + 1.1, 1.9, x + 1.1, 1.2)
    ax.text(5, 4.55, "Hacim hiyerarşisi (anne → kız hacimler)", ha="center", fontsize=11, fontweight="bold")
    fig.savefig(path, dpi=150, bbox_inches="tight"); plt.close(fig)


def fig_flow(path):
    fig, ax = plt.subplots(figsize=(10, 9.5))
    ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 10)
    Y = [9.2, 8.2, 7.2, 6.2, 5.0, 3.85, 2.7, 1.55, 0.4]
    items = [
        ("main() – sim.cc", "RunManager, Config, fizik listesi, ActionInitialization oluşturulur", "#f0f0f0"),
        ("/run/initialize (makro)", "DetectorConstruction::Construct() + ConstructSDandField()\nfizik tabloları kurulur", "#dbeefc"),
        ("/run/beamOn N  →  RunAction::BeginOfRunAction", "ana thread: geometri CSV'leri; işçiler: CSV parça dosyalarını açar", "#e3f1e3"),
        ("PrimaryGeneratorAction::GeneratePrimaries", "Config'ten enerji ve AGN yönü → müon başlangıç noktası ve yönü", "#ffe9b3"),
        ("EventAction::BeginOfEventAction", "OutputManager::BeginEvent – olay sayaçları sıfırlanır", "#fde0dc"),
        ("İzleme döngüsü (her iz, her adım)", "StackingAction::ClassifyNewTrack → Cherenkov fotonu kaydı\n"
         "SteppingAction::UserSteppingAction → müon enerji kaybı\nSensorSD::ProcessHits → DOM'a giren foton (hit)", "#fff3cd"),
        ("EventAction::EndOfEventAction", "events.csv ve sensor_summary.csv satırları yazılır", "#fde0dc"),
        ("RunAction::EndOfRunAction", "işçiler dosyaları kapatır; ana thread parçaları birleştirir", "#e3f1e3"),
        ("Python analizi", "analyze.py / compare.py / thesis.py → grafikler ve tablolar", "#ede7f6"),
    ]
    for (title, desc, fc), y in zip(items, Y):
        h = 0.95 if "İzleme" in title else 0.75
        box(ax, 0.3, y - h/2, 3.6, h, title, fc=fc, fs=8.5, bold=True)
        ax.text(4.15, y, desc, va="center", fontsize=8.2)
    for y0, y1 in zip(Y[:-1], Y[1:]):
        arrow(ax, 2.1, y0 - 0.4, 2.1, y1 + 0.42)
    ax.annotate("", xy=(0.15, Y[3]), xytext=(0.15, Y[6]),
                arrowprops=dict(arrowstyle="->", color="crimson", lw=1.5, connectionstyle="arc3,rad=-0.4"))
    ax.text(-0.25, (Y[3] + Y[6])/2, "N olay\ntekrarı", color="crimson", fontsize=8, ha="center", rotation=90)
    fig.savefig(path, dpi=150, bbox_inches="tight"); plt.close(fig)


def fig_mt(path):
    fig, ax = plt.subplots(figsize=(10, 3.8))
    ax.axis("off"); ax.set_xlim(0, 10); ax.set_ylim(0, 3.8)
    box(ax, 0.2, 1.4, 2.1, 1.0, "Ana thread (master)\nmakro komutları\nConfig değerleri", fc="#f0f0f0", fs=8.5)
    for i, y in enumerate([2.9, 1.9, 0.3]):
        lab = f"İşçi {i}" if i < 2 else "İşçi N−1"
        box(ax, 3.2, y, 2.0, 0.6, f"{lab}: olaylar", fc="#e3f1e3", fs=8)
        box(ax, 5.9, y, 2.0, 0.6, f"*.part{i if i < 2 else 'N−1'}.csv", fc="#fff3cd", fs=8)
        arrow(ax, 2.3, 1.9, 3.2, y + 0.3)
        arrow(ax, 5.2, y + 0.3, 5.9, y + 0.3)
        arrow(ax, 7.9, y + 0.3, 8.4, 1.9)
    ax.text(4.2, 1.45, "⋮", fontsize=16, ha="center")
    box(ax, 8.4, 1.4, 1.5, 1.0, "MergeParts\n→ tek CSV", fc="#ede7f6", fs=8.5)
    fig.savefig(path, dpi=150, bbox_inches="tight"); plt.close(fig)


def fig_optics(path):
    ice = pd.read_csv(f"{PROJ}/build/data/param/spacing4m_ice_properties.csv")
    cols = ["#08306b", "#2171b5", "#9e9ac8", "#6baed6"]
    fig, axs = plt.subplots(2, 2, figsize=(11, 8))
    g0 = ice[ice.layer == 0]
    axs[0, 0].plot(g0.wavelength_nm, g0.n_phase, "k")
    axs[0, 0].set_title("(a) Kırılma indisi n(λ) (tüm katmanlarda aynı)")
    axs[0, 0].set_ylabel("n")
    for L, g in ice.groupby("layer"):
        lab = f"katman {L} ({g.depth_m.iloc[0]:.1f} m)"
        axs[0, 1].semilogy(g.wavelength_nm, g.abs_length_m, color=cols[L], label=lab)
        axs[1, 0].semilogy(g.wavelength_nm, g.rayleigh_length_m, color=cols[L], label=f"Rayleigh, {lab}")
        axs[1, 0].semilogy(g.wavelength_nm, g.mie_length_m, color=cols[L], ls="--")
    axs[0, 1].set_title("(b) Soğurma uzunluğu λ$_{abs}$"); axs[0, 1].set_ylabel("m"); axs[0, 1].legend(fontsize=8)
    axs[1, 0].set_title("(c) Saçılma uzunluğu: Rayleigh (düz), Mie geometrik (kesikli)")
    axs[1, 0].set_ylabel("m"); axs[1, 0].legend(fontsize=7)
    qx = [300, 320, 340, 360, 380, 400, 420, 450, 480, 500, 530, 560, 600]
    qy = [0.06, 0.15, 0.22, 0.25, 0.26, 0.255, 0.24, 0.21, 0.17, 0.14, 0.10, 0.065, 0.03]
    axs[1, 1].plot(qx, np.array(qy)*100, "o-", color="C4")
    axs[1, 1].set_title("(d) DOM kuantum verimi (SensorSD.cc)"); axs[1, 1].set_ylabel("QE [%]")
    for ax in axs.flat:
        ax.set_xlabel("dalga boyu [nm]"); ax.grid(alpha=0.3, which="both")
    fig.tight_layout()
    fig.savefig(path, dpi=140); plt.close(fig)


# ======================================================================= içerik
def build():
    figs = {k: f"{FIG}/{k}.png" for k in ("3d", "num", "hier", "flow", "mt", "optics")}
    fig_3d(figs["3d"]); fig_numbering(figs["num"]); fig_hierarchy(figs["hier"])
    fig_flow(figs["flow"]); fig_mt(figs["mt"]); fig_optics(figs["optics"])

    S = []
    title = ParagraphStyle("tt", fontName="Serif-B", fontSize=21, leading=29, alignment=TA_CENTER, textColor=NAVY)
    cs = ParagraphStyle("cs", fontName="Serif", fontSize=12, leading=18, alignment=TA_CENTER)
    S += [Spacer(1, 4*cm), P(DOC_TITLE.upper(), title), Spacer(1, 0.8*cm),
          P("IceCube tipi Geant4 simülasyonu – teknik belge", cs), Spacer(1, 5*cm),
          P(f"<b>Hazırlayan:</b> {br.STUDENT} ({br.STUDENT_NO})", cs),
          P(f"<b>Danışman:</b> {br.ADVISOR}", cs), Spacer(1, 3.5*cm),
          P("Erciyes Üniversitesi – " + br.DATE, cs),
          NextPageTemplate("normal"), PageBreak()]

    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle("t0", fontName="Serif-B", fontSize=10.5, leading=16),
                       ParagraphStyle("t1", fontName="Serif", fontSize=10, leading=14, leftIndent=18)]
    S += [P("İÇİNDEKİLER", ParagraphStyle("tch", parent=h1)), toc, PageBreak()]

    # ---------------------------------------------------------------- 1
    S += [P("1. BU BELGE NE ANLATIYOR?", h1),
          P("Bu belge, IceCube benzeri buz dedektörü simülasyonunun <b>geometrisini</b> ve onu oluşturan "
            "<b>bütün kodları</b> (C++ / Geant4 ve Python analiz betikleri) satır satır olmasa da fonksiyon "
            "fonksiyon açıklar. Amaç, programın her parçasının <i>ne yaptığını</i>, <i>neden öyle yazıldığını</i> "
            "ve <i>hangi sırayla çalıştığını</i> anlamaktır. Kod parçalarında gösterilen satırlar projedeki "
            "dosyalardan doğrudan alınmıştır; tam C++ kodu Ek A'dadır."),
          P("1.1 Dosya Yapısı", h2),
          C("Geant4_2/\n"
            "├── CMakeLists.txt          derleme tarifi (CMake)\n"
            "├── sim.cc                  main(): programın giriş noktası\n"
            "├── include/  (.hh)         sınıf bildirimleri\n"
            "├── src/      (.cc)         sınıf gövdeleri\n"
            "│   ├── Config              /icecube/... ayarları (singleton)\n"
            "│   ├── DetectorConstruction geometri, malzeme, optik özellikler\n"
            "│   ├── SensorSD            DOM'ları hassas dedektör yapan sınıf\n"
            "│   ├── PrimaryGeneratorAction  müon tabancası (AGN yönü)\n"
            "│   ├── ActionInitialization    kullanıcı eylemlerinin kaydı\n"
            "│   ├── RunAction / EventAction / SteppingAction / StackingAction\n"
            "│   └── OutputManager       thread'e özel CSV yazıcı\n"
            "├── *.mac, macros/          Geant4 makro dosyaları\n"
            "├── run_thesis.sh           tez koşularını sırayla çalıştırır\n"
            "├── analysis/               Python: common, analyze, compare, thesis\n"
            "│   └── ref/                PDG/Groom müon tablosu (su)\n"
            "└── build/                  derlenmiş program ve data/ çıktıları"),
          P("1.2 Derleme ve Çalıştırma", h2),
          C("cd build && cmake .. && make -j      # derle\n"
            "./sim                                # görsel arayüz (vis.mac çalışır)\n"
            "./sim run1TeV.mac 12                 # batch: makro + thread sayısı\n"
            "bash ../run_thesis.sh 12             # tüm tez koşuları\n"
            "python3 ../analysis/thesis.py        # tez analizleri"),
          P("CMakeLists.txt; Geant4'ü <font name='Mono'>find_package(Geant4 REQUIRED ui_all vis_all)</font> ile "
            "bulur, <font name='Mono'>src/*.cc</font> ve <font name='Mono'>sim.cc</font> dosyalarını derleyip "
            "<font name='Mono'>sim</font> adlı programı oluşturur ve makro dosyalarını build dizinine kopyalar."),
          ]

    # ---------------------------------------------------------------- 2
    S += [P("2. GEANT4'ÜN TEMEL KAVRAMLARI", h1),
          P("Kodları okumadan önce Geant4'ün birkaç temel kavramını bilmek gerekir:"),
          table([["Kavram", "Anlamı", "Bizim projede"],
                 ["Run", "Aynı koşullarda yapılan olaylar dizisi (/run/beamOn N)", "100–300 olay"],
                 ["Event (olay)", "Tek bir birincil parçacığın ve tüm ikincillerinin benzetimi", "1 müon + tüm fotonlar"],
                 ["Track (iz)", "Tek bir parçacığın hayatı boyunca izlenmesi", "müon, e<super>±</super>, optik foton"],
                 ["Step (adım)", "İzin iki etkileşim/sınır arasındaki parçası", "müon için ~1,5 cm"],
                 ["Solid", "Şekil (boyut) tanımı", "G4Box, G4Orb"],
                 ["Logical volume", "Şekil + malzeme (+ hassas dedektör)", "World, IceLayer, Sensor"],
                 ["Physical volume", "Bir logical volume'un anne hacim içinde konumlandırılmış kopyası", "G4PVPlacement"],
                 ["Process (süreç)", "Fiziksel etkileşim modeli", "muIoni, Cerenkov, OpRayleigh…"],
                 ["User action", "Kullanıcının olayın belirli anlarına müdahalesi", "Run/Event/Stepping/Stacking"],
                 ["Sensitive detector", "Belirli bir hacimdeki adımları işleyen sınıf", "SensorSD"],
                 ["Messenger", "Makro komutu ↔ C++ değişkeni bağlantısı", "/icecube/... (Config)"]],
                [3.0, 7.4, 6.0], "Geant4'te sık kullanılan kavramlar."),
          P("<b>Birimler:</b> Geant4 içeride mm, ns ve MeV kullanır. Kodda her sayı bir birimle çarpılarak yazılır "
            "(<font name='Mono'>10.0*m</font>, <font name='Mono'>1.0*TeV</font>) ve çıktıya yazarken birime bölünür "
            "(<font name='Mono'>pos.x()/mm</font>). Bu, birim hatalarını önleyen Geant4 alışkanlığıdır."),
          P("<b>Zorunlu ve isteğe bağlı sınıflar:</b> Geant4 üç zorunlu sınıf ister: geometri "
            "(G4VUserDetectorConstruction), fizik listesi (G4VUserPhysicsList) ve birincil parçacık üreteci "
            "(G4VUserPrimaryGeneratorAction). Diğer tüm user action sınıfları isteğe bağlıdır; biz veri kaydetmek "
            "için dördünü kullanıyoruz."),
          ]

    # ---------------------------------------------------------------- 3
    S += [PageBreak(), P("3. DEDEKTÖR GEOMETRİSİ", h1),
          P("3.1 Genel Yapı ve Koordinat Sistemi", h2),
          P("Koordinat sisteminin merkezi buz bloğunun merkezidir; <b>z ekseni yukarıyı</b> gösterir. Yani z "
            "arttıkça derinlik azalır. Dedektör üç düzeyli bir hacim hiyerarşisinden oluşur (Şekil 2): en dışta 30 m "
            "kenarlı vakum <b>dünya</b> kutusu, onun içinde üst üste dizilmiş dört <b>buz katmanı</b> ve her "
            "katmanın içinde 9 <b>DOM</b> (toplam 36)."),
          figure(figs["3d"], 13.5, "Dedektörün üç boyutlu görünümü: dört buz katmanı, 9 string (S0–S8), "
                 "36 DOM (turuncu) ve TXS 0506+056 yönünden gelen örnek bir müon izi (kırmızı)."),
          figure(figs["hier"], 15.5, "Hacim hiyerarşisi. Her IceLayer aynı şekle (solid) ama farklı malzemeye "
                 "sahiptir; aynı Sensor logical volume'u 36 kez farklı kopya numarasıyla yerleştirilir."),
          P("3.2 Boyutlar", h2),
          table([["Hacim", "Şekil (solid)", "Boyut", "Malzeme", "Neden?"],
                 ["World", "G4Box", "±15 m", "G4_Galactic (vakum)",
                  "Müonun başlangıç noktasını içerir; RINDEX tanımlı olmadığı için buzdan çıkan fotonlar burada yok olur."],
                 ["IceLayer ×4", "G4Box", "±10 × ±10 × ±2,5 m", "Ice_L0…Ice_L3",
                  "Derinliğe bağlı optik özellikler için her katman ayrı malzeme."],
                 ["Sensor ×36", "G4Orb", "r = 16,51 cm", "G4_Pyrex_Glass (n = 1,48)",
                  "Gerçek IceCube DOM boyutu; cama kırılma indisi verilir ki foton içeri girebilsin."]],
                [2.2, 1.9, 2.9, 3.2, 6.2], "Geometrideki hacimler."),
          P("3.3 Sensör Numaralandırması", h2),
          P("Her DOM'un benzersiz bir <b>sensör ID</b>'si (0–35) vardır. Bu numara G4PVPlacement'ın "
            "<i>kopya numarası</i> olarak verilir ve SensorSD, bir fotonun hangi DOM'a girdiğini bu numarayla "
            "anlar. Numaralandırma şöyle tanımlanmıştır:"),
          eq(r"\mathrm{ID} = 4\,s + \mathrm{DOM},\qquad s = 3\,i_x + i_y,\qquad "
             r"x = (i_x-1)\,d,\quad y = (i_y-1)\,d,\quad z = -10\,\mathrm{m} + (\mathrm{DOM}+0.5)\cdot 5\,\mathrm{m}"),
          P("Burada d string aralığıdır (varsayılan 6 m, <font name='Mono'>/icecube/stringSpacing</font> ile "
            "değiştirilebilir). DOM numarası aynı zamanda içinde bulunduğu buz katmanının numarasıdır: DOM 0 en "
            "alttaki (en derin) katmandadır. Ters dönüşüm <font name='Mono'>SensorPosition()</font> fonksiyonundadır:"),
          snippet("src/DetectorConstruction.cc", 44, 57),
          figure(figs["num"], 16.0, "Sensör numaralandırması. (a) Üstten görünümde string numaraları ve her "
                 "stringe düşen ID aralığı. (b) y = 0 kesitinde (S1, S4, S7) DOM ID'leri ve katmanlar."),
          P("Nominal derinlik, buz bloğunun üst yüzeyi 2000 m derinlikte kabul edilerek "
            "<font name='Mono'>LayerDepth()</font> ile hesaplanır: derinlik = 2000 m + (10 m − z). "
            "Böylece katman merkezleri 2002,5 / 2007,5 / 2012,5 / 2017,5 m derinliktedir."),

          P("3.4 Malzemeler ve Optik Özellikler", h2),
          P("Geant4'te optik fotonların bir malzemede var olabilmesi için malzemeye bir "
            "<b>G4MaterialPropertiesTable</b> (MPT) eklenmeli ve en azından <b>RINDEX</b> (kırılma indisi) "
            "tanımlanmalıdır. RINDEX'i olmayan bir malzemeye giren foton sınırda soğurulur. Cherenkov süreci de "
            "fotonları yalnızca RINDEX'i olan malzemelerde üretir. Bizim buz katmanlarımızda tanımlanan "
            "özellikler şunlardır:"),
          table([["MPT anahtarı", "Fonksiyon", "Fiziksel anlamı"],
                 ["RINDEX", "IceRefractiveIndex(λ)", "Faz kırılma indisi (dispersiyon); Cherenkov açısını ve foton sayısını belirler"],
                 ["ABSLENGTH", "IceAbsLength(λ, katman)", "Ortalama soğurma uzunluğu: toz (λ<super>−1,08</super>) + buz (kızılötesi)"],
                 ["RAYLEIGH", "IceRayleighLength(λ, katman)", "Rayleigh saçılma uzunluğu ∝ λ<super>4</super>"],
                 ["MIEHG", "IceMieLength(λ, katman)", "Mie geometrik saçılma uzunluğu ∝ λ<super>0,9</super>·(1−g)"],
                 ["MIEHG_FORWARD / BACKWARD / FORWARD_RATIO", "sabit", "Henyey-Greenstein açı dağılımı: g = 0,9, tamamı ileri"]],
                [4.6, 4.6, 7.2], "Buz malzemelerine eklenen optik özellikler."),
          P("Tablolar 300–600 nm arasında 61 noktada hesaplanır. Geant4 optik özellikleri <i>foton enerjisinin</i> "
            "fonksiyonu olarak ister ve enerji dizisinin artan sırada olması gerekir; bu yüzden döngü 600 nm'den "
            "300 nm'ye doğru gider (E = 1239,84 eV·nm / λ):"),
          snippet("src/DetectorConstruction.cc", 102, 108),
          P("Fiziksel formüller tek bir yerde, statik fonksiyonlar olarak yazılmıştır. Aynı fonksiyonlar hem "
            "Geant4 malzemelerini oluşturmak için hem de analizde kullanılan <font name='Mono'>ice_properties.csv</font> "
            "dosyasını yazmak için çağrılır; böylece analizde kullanılan sayılar simülasyondakilerle kesinlikle aynıdır:"),
          snippet("src/DetectorConstruction.cc", 66, 93),
          figure(figs["optics"], 15.5, "Kodda tanımlı optik özellikler: (a) kırılma indisi, (b) katmanlara göre "
                 "soğurma uzunluğu, (c) Rayleigh ve Mie (geometrik) saçılma uzunlukları, (d) DOM kuantum verimi."),
          P("Katmanların 400 nm değerleri dosyanın başında iki dizi olarak tanımlıdır (katman 0 en derin). "
            "Katman 2 daha kısa uzunluklarıyla 'toz katmanı'nı temsil eder:"),
          snippet("src/DetectorConstruction.cc", 28, 32),
          P("<b>Buz modelinin seçimi:</b> Her katman hem RAYLEIGH hem MIEHG tablosuna sahiptir. Hangi saçılmanın "
            "kullanılacağı makroda, başlatmadan sonra bir süreci kapatarak seçilir: "
            "<font name='Mono'>/process/inactivate OpMieHG</font> → yalnız Rayleigh (varsayılan); "
            "<font name='Mono'>/process/inactivate OpRayleigh</font> → yalnız Mie. Mie için Geant4'e verilen "
            "uzunluk <i>geometrik</i> saçılma uzunluğudur; ileri yönlü saçılmada (g = 0,9) ışığın yönünü fiilen "
            "değiştiren <i>etkin</i> uzunluk λ<sub>e</sub> = λ<sub>s</sub>/(1−g)'dir. Kod λ<sub>e</sub>'yi Rayleigh modelindeki "
            "değerlere eşit tutarak iki modeli karşılaştırılabilir kılar."),
          P("<b>Sensör camı:</b> Pyrex'e yalnızca sabit RINDEX = 1,48 verilir. Bu sayede foton buz–cam sınırında "
            "Fresnel kurallarına göre kırılır veya yansır ve cama girebilir; içeri girdiği anda SensorSD onu "
            "kaydedip yok eder."),

          P("3.5 Hacimlerin Yerleştirilmesi", h2),
          P("Aşağıdaki döngü her katman için ayrı bir buz malzemesi ve logical volume oluşturur, katmanı dünya "
            "hacmine yerleştirir ve o katmana düşen 9 DOM'u katmanın <i>içine</i> yerleştirir. DOM konumu katmanın "
            "kendi koordinat sistemine göre verildiği için z'den katman merkezi (zc) çıkarılır. G4PVPlacement'ın "
            "son argümanı (<font name='Mono'>true</font>) çakışma (overlap) kontrolünü açar; koşu başında tüm "
            "hacimler için 'OK!' mesajı görülür."),
          snippet("src/DetectorConstruction.cc", 128, 170),
          P("<b>Hassas dedektör:</b> <font name='Mono'>ConstructSDandField()</font> her thread için ayrı çağrılır "
            "ve Sensor logical volume'una bir SensorSD nesnesi bağlar. Böylece bir parçacık herhangi bir DOM'un "
            "içinde adım attığında SensorSD::ProcessHits çağrılır."),
          snippet("src/DetectorConstruction.cc", 172, 177),
          ]

    # ---------------------------------------------------------------- 4
    S += [PageBreak(), P("4. PROGRAMIN AKIŞI", h1),
          P("Şekil 5, bir koşu sırasında hangi fonksiyonun hangi sırayla çağrıldığını gösterir. Bu akışı bilmek, "
            "her sınıfın neden var olduğunu anlamanın en kolay yoludur."),
          figure(figs["flow"], 15.0, "Programın akışı: başlatma, koşu, olay döngüsü ve her adımda çağrılan "
                 "kullanıcı sınıfları. Kırmızı ok, her olay için tekrarlanan kısmı gösterir."),
          P("4.1 Çok İş Parçacıklı (Multi-thread) Çalışma", h2),
          P("Program <font name='Mono'>G4RunManagerType::Default</font> ile oluşturulur; bu, Geant4 11'de "
            "görev tabanlı (tasking) çok iş parçacıklı çalışma demektir. Olaylar işçi thread'lere dağıtılır. Her "
            "işçinin kendi user action nesneleri ve kendi <b>OutputManager</b>'ı (G4ThreadLocal) vardır; bu yüzden "
            "aynı dosyaya aynı anda yazma sorunu yaşanmaz. Her işçi <font name='Mono'>*.partK.csv</font> dosyasına "
            "yazar, koşu bitince ana thread bunları tek dosyada birleştirir (Şekil 6)."),
          figure(figs["mt"], 15.0, "Çok iş parçacıklı veri yazımı ve birleştirme."),
          P("Config ise tüm thread'lerin ortak okuduğu tek bir nesnedir. Makro komutları yalnızca ana thread'de "
            "çalışır (<font name='Mono'>SetToBeBroadcasted(false)</font>) ve değerler koşudan önce değiştiği için "
            "işçiler okurken bir yarış (race) durumu oluşmaz."),
          ]

    # ---------------------------------------------------------------- 5
    S += [PageBreak(), P("5. KAYNAK DOSYALARIN AYRINTILI AÇIKLAMASI", h1),
          P("5.1 sim.cc – main()", h2),
          P("Programın giriş noktasıdır. Sırasıyla: (1) argüman yoksa görsel arayüz (G4UIExecutive) hazırlanır; "
            "(2) run manager oluşturulup thread sayısı ayarlanır (2. argüman veya işlemci çekirdek sayısı); "
            "(3) Config oluşturularak /icecube/ komutları tanıtılır; (4) QBBC fizik listesine G4OpticalPhysics "
            "eklenir, elektromanyetik tabloların üst enerjisi 10 PeV'e çıkarılır ve optik parametreler ayarlanır; (5) üç zorunlu sınıf run manager'a verilir; (6) makro "
            "çalıştırılır."),
          snippet("sim.cc", 30, 47),
          table([["Optik parametre", "Değer", "Açıklama"],
                 ["CerenkovMaxPhotonsPerStep", "500", "Bir adımda en fazla 500 foton üretilir; müon adımı ~1,5 cm ile sınırlanır."],
                 ["CerenkovMaxBetaChange", "10 (%)", "Hız bir adımda en fazla %10 değişebilir (yavaş parçacıklar için önemli)."],
                 ["CerenkovTrackSecondariesFirst", "true", "Fotonlar, onları üreten parçacıktan önce izlenir (bellek tasarrufu)."],
                 ["Scintillation, OpWLS, OpWLS2", "kapalı", "Buzda sintilasyon ve dalga boyu kaydırma yoktur."],
                 ["OpRayleigh, OpMieHG", "açık", "İkisi de kurulur; biri makroda kapatılır."]],
                [5.0, 2.0, 9.4], "sim.cc'de ayarlanan optik parametreler."),
          P("<b>Elektromanyetik tabloların üst sınırı:</b> Geant4, enerji kaybı ve tesir kesiti tablolarını "
            "varsayılan olarak yalnızca 100 TeV'e kadar hesaplar. 100 TeV müon tam bu sınırda olduğu için ilk 100 TeV "
            "koşusunda radyatif kayıplar yaklaşık dört kat eksik çıkmıştır. "
            "<font name='Mono'>G4EmParameters::Instance()-&gt;SetMaxEnergy(10*PeV)</font> satırı tabloları 10 PeV'e "
            "genişletir; bu ayar fizik listesi run manager'a verilmeden önce yapılmalıdır."),
          P("<b>Not:</b> <font name='Mono'>runManager->Initialize()</font> main içinde değil makroda "
            "(<font name='Mono'>/run/initialize</font>) çağrılır. Böylece geometriyi etkileyen ayarlar "
            "(string aralığı) başlatmadan önce makrodan değiştirilebilir. Bu yüzden her makro "
            "<font name='Mono'>/run/initialize</font> içermelidir."),

          CondPageBreak(6*cm), P("5.2 Config – simülasyon ayarları", h2),
          P("<b>Singleton</b> tasarım kalıbıyla yazılmıştır: programda tek bir Config nesnesi vardır ve her yerden "
            "<font name='Mono'>Config::Instance()</font> ile erişilir. G4GenericMessenger, sınıfın üye "
            "değişkenlerini doğrudan makro komutlarına bağlar. Birimli komutlar (energy, sourceRA…) Geant4'ün iç "
            "birimlerine otomatik çevrilir."),
          table([["Komut", "Varsayılan", "Görevi"],
                 ["/icecube/particle", "mu-", "Birincil parçacık türü"],
                 ["/icecube/energy", "1 TeV", "Kinetik enerji"],
                 ["/icecube/sourceRA, sourceDec", "77,358°, 5,693°", "AGN'nin gök koordinatları (TXS 0506+056)"],
                 ["/icecube/angularSpread", "0,5°", "Yöne eklenen Gauss sapma (nötrino–müon açısı)"],
                 ["/icecube/offsetRadius", "3 m", "İzin merkezden rastgele kayması"],
                 ["/icecube/stringSpacing", "6 m", "String aralığı (yalnız /run/initialize'dan önce)"],
                 ["/icecube/prefix", "data/run", "Çıktı dosyalarının ön eki (klasör/isim)"],
                 ["/icecube/photonSaveEvents", "1", "Fotonları tek tek yazılacak ilk olay sayısı"],
                 ["/icecube/saveHitPhotons", "true", "Sensör fotonlarını tek tek yaz"],
                 ["/icecube/saveMuonSteps", "true", "Müon adımlarını yaz"]],
                [5.2, 3.0, 8.2], "Config'in makro komutları."),
          snippet("src/Config.cc", 19, 27),

          CondPageBreak(6*cm), P("5.3 PrimaryGeneratorAction – müon tabancası", h2),
          P("Her olayın başında çağrılır ve bir G4ParticleGun ile tek bir müon üretir. Yön hesabı üç adımdır:"),
          *bullets([
              "<b>Kaynak yönü:</b> <font name='Mono'>MuonDirectionFromSource(RA, Dec)</font>. Güney Kutbu'nda "
              "kaynağın yüksekliği h = −Dec, azimut A = RA alınır (yerel yıldız zamanı = 0). Kaynağa bakan birim "
              "vektör ŝ = (cos h cos A, cos h sin A, sin h); müon bunun tersi yönde hareket eder: d̂ = −ŝ.",
              "<b>Açısal sapma:</b> d̂'ye dik iki birim vektör (u, v) bulunur ve d̂ + g<sub>1</sub>u + g<sub>2</sub>v normalize "
              "edilir; g<sub>1</sub>, g<sub>2</sub> ortalaması 0, standart sapması angularSpread olan Gauss sayılardır.",
              "<b>Kayma ve başlangıç noktası:</b> yöne dik, yarıçapı offsetRadius olan bir diskte düzgün dağılmış "
              "rastgele bir nokta seçilir (r = R√U). Müon bu noktanın 14 m gerisinden başlatılır; böylece her zaman "
              "buzun dışında ama dünya hacminin içindedir."]),
          snippet("src/PrimaryGeneratorAction.cc", 23, 60),

          CondPageBreak(6*cm), P("5.4 ActionInitialization", h2),
          P("Kullanıcı eylemlerini kaydeder. <font name='Mono'>BuildForMaster()</font> yalnız ana thread için "
            "çağrılır ve sadece RunAction ister (dosya birleştirme). <font name='Mono'>Build()</font> her işçi için "
            "çağrılır ve beş eylemin hepsini oluşturur."),
          snippet("src/ActionInitialization.cc", 11, 23),

          CondPageBreak(6*cm), P("5.5 RunAction – koşu başı ve sonu", h2),
          *bullets([
              "<b>BeginOfRunAction:</b> ön ek (prefix) kopyalanır. Ana thread çıktı klasörünü oluşturur, "
              "<font name='Mono'>sensors.csv</font> ve <font name='Mono'>ice_properties.csv</font> dosyalarını yazar. "
              "Olayları işleyen thread (MT'de işçi, seri modda ana thread) kendi CSV dosyalarını açar.",
              "<b>EndOfRunAction:</b> işçiler dosyalarını kapatır. Ana thread, Geant4 tarafından tüm işçiler "
              "bittikten sonra çağrıldığı için güvenle <font name='Mono'>MergeParts()</font> ile parçaları "
              "birleştirir."]),
          snippet("src/RunAction.cc", 34, 47),

          CondPageBreak(6*cm), P("5.6 EventAction – olay başı ve sonu", h2),
          P("Olay başında OutputManager sayaçlarını sıfırlar ve bu olayın fotonlarının tek tek yazılıp "
            "yazılmayacağına karar verir (olay no < photonSaveEvents). Olay sonunda birincil müonun başlangıç "
            "enerjisini, konumunu ve yönünü G4Event'ten okuyup özet satırını yazdırır."),
          snippet("src/EventAction.cc", 12, 25),

          CondPageBreak(6*cm), P("5.7 StackingAction – Cherenkov fotonlarının yakalanması", h2),
          P("Geant4'te yeni oluşan her iz önce 'yığına' (stack) konur ve bu sırada "
            "<font name='Mono'>ClassifyNewTrack()</font> çağrılır. Biz burada izin optik foton olup olmadığına ve "
            "onu oluşturan sürecin 'Cerenkov' olup olmadığına bakarız. Böylece her foton <i>doğduğu anda</i>, "
            "konum, yön, enerji ve zamanıyla kaydedilir. Fonksiyon her zaman <font name='Mono'>fUrgent</font> "
            "döndürür; yani hiçbir iz silinmez veya ertelenmez. parent_id = 1 olan fotonlar doğrudan birincil "
            "müondan gelir."),
          snippet("src/StackingAction.cc", 11, 22),

          CondPageBreak(6*cm), P("5.8 SteppingAction – müonun enerji kaybı", h2),
          P("Her adımın sonunda çağrılır; bu programda en sık çağrılan fonksiyondur (milyonlarca kez). Bu yüzden "
            "optik fotonlar için ilk satırda hemen çıkılır. Buz içindeki tüm yüklü parçacıkların depoladığı enerji "
            "toplanır. Birincil müon (TrackID = 1) için adımın başlangıç ve bitiş kinetik enerjileri, depolanan "
            "enerji, adım boyu ve adımı sonlandıran süreç kaydedilir. Müon dünya hacmine geçtiğinde çıkış enerjisi "
            "saklanır."),
          snippet("src/SteppingAction.cc", 13, 38),
          P("<b>Dikkat:</b> 'process' sütunu adımı <i>sonlandıran</i> süreçtir. Sürekli iyonizasyon kaybı her "
            "adımda uygulanır; bu yüzden 'Cerenkov' tarafından sonlandırılan adımlarda görülen ΔE aslında "
            "iyonizasyon kaybıdır. OutputManager, muPairProd, muBrems ve muonNuclear adımlarındaki kaybı "
            "<i>radyatif kayıp</i> olarak ayrıca toplar."),

          CondPageBreak(6*cm), P("5.9 SensorSD – optik sensör", h2),
          P("G4VSensitiveDetector'dan türetilmiştir. DOM içinde adım atan her parçacık için "
            "<font name='Mono'>ProcessHits()</font> çağrılır. İşleyiş:"),
          *bullets([
              "Parçacık optik foton değilse (ör. DOM'dan geçen müon) hiçbir şey yapılmaz.",
              "Foton her durumda yok edilir (fStopAndKill): cam içinde daha fazla izlenmesine gerek yoktur.",
              "Yalnızca adımın başı geometri sınırındaysa (<font name='Mono'>fGeomBoundary</font>), yani foton "
              "dışarıdan içeri girmişse kaydedilir. Cam içinde Cherenkov ile oluşan fotonlar sayılmaz.",
              "Kopya numarasından sensör ID'si okunur, kuantum verimi uygulanır: dalga boyuna göre QE(λ) "
              "doğrusal ara değerlemeyle bulunur ve G4UniformRand() &lt; QE ise foton <i>algılandı</i> "
              "(detected = 1) sayılır."]),
          snippet("src/SensorSD.cc", 33, 54),

          CondPageBreak(6*cm), P("5.10 OutputManager – veri kaydı", h2),
          P("Her thread için ayrı bir örneği olan (<font name='Mono'>static G4ThreadLocal</font>) yazıcıdır. Beş "
            "dosyayı yönetir ve olay boyunca sayaçları (foton, hit, algılanan foton, müon iz uzunluğu, enerji "
            "kaybı, radyatif kayıp, depolanan enerji) ve sensör başına özet bilgilerini (hit sayısı, algılanan "
            "sayı, ilk vuruş zamanı, ilk algılanan vuruş zamanı, ortalama zaman) tutar."),
          snippet("src/OutputManager.cc", 40, 45),
          P("Sensör özeti, yüksek enerjilerde milyonlarca satır tutacak fotonları tek tek yazmak yerine her olay "
            "için en fazla 36 satır yazar; rekonstrüksiyon için gereken bilgi (ilk zaman ve sayı) bu özette "
            "bulunduğu için tez taramasında yalnız özet kullanılır."),
          snippet("src/OutputManager.cc", 122, 131),
          ]

    # ---------------------------------------------------------------- 6
    S += [PageBreak(), P("6. ÇIKTI DOSYALARI", h1),
          P("Her koşu <font name='Mono'>&lt;prefix&gt;_&lt;ad&gt;.csv</font> biçiminde dosyalar üretir. Sütunlar:"),
          table([["Dosya", "Sütunlar", "Ne zaman yazılır"],
                 ["events", "event, E0_MeV, E_exit_MeV, E_loss_MeV, track_len_mm, edep_total_MeV, n_photons, "
                  "n_photons_primary, n_hits, x0_mm, y0_mm, z0_mm, dir_x, dir_y, dir_z, n_detected, E_loss_rad_MeV",
                  "her olay sonunda 1 satır"],
                 ["sensor_summary", "event, sensor_id, string_id, dom_id, n_hits, n_detected, t_first_ns, "
                  "t_first_det_ns (algılanan yoksa −1), t_mean_ns", "her olayda foton alan her DOM için"],
                 ["cherenkov_photons", "event, parent_id, x/y/z_mm, px/py/pz, energy_eV, wavelength_nm, time_ns",
                  "photonSaveEvents kadar olay"],
                 ["sensor_hits", "event, sensor_id, string_id, dom_id, x/y/z_mm (giriş noktası), energy_eV, "
                  "wavelength_nm, time_ns, parent_id, detected", "saveHitPhotons açıksa"],
                 ["muon_energy_loss", "event, step, x/y/z_mm, E_pre_MeV, E_post_MeV, dE_MeV, edep_MeV, step_mm, process",
                  "saveMuonSteps açıksa"],
                 ["sensors", "sensor_id, string_id, dom_id, x/y/z_mm, radius_mm, depth_m", "koşu başında"],
                 ["ice_properties", "layer, depth_m, zmin/zmax_mm, wavelength_nm, n_phase, abs_length_m, "
                  "rayleigh_length_m, mie_length_m", "koşu başında"]],
                [3.1, 9.6, 3.7], "Çıktı dosyaları ve sütunları."),
          P("<b>Zaman tanımı:</b> Tüm zamanlar, müonun başlangıç noktasından çıktığı an t = 0 kabul edilerek "
            "ölçülen 'global time'dır (ns). <b>Konumlar</b> mm cinsinden ve dedektör merkezine göredir."),
          ]

    # ---------------------------------------------------------------- 7
    S += [P("7. MAKRO DOSYALARI VE KOŞU BETİKLERİ", h1),
          table([["Dosya", "İçerik"],
                 ["vis.mac", "Görsel arayüz: OpenGL, müon kırmızı, e<super>−</super> sarı; optik fotonlar çizimde gizlenir. 100 GeV müon."],
                 ["test.mac", "4 olaylık hızlı deneme (data/test)."],
                 ["run1TeV.mac, run10TeV.mac", "İlk rapordaki 100'er olaylık koşular; tüm dosyalar yazılır."],
                 ["macros/make_macros.sh", "Tez makrolarını üretir: enerji taraması (0,1–100 TeV) ve parametre çalışması."],
                 ["macros/scan_*TeV.mac", "Enerji taraması; foton/hit/adım dosyaları kapalı, yalnız özetler."],
                 ["macros/param_*.mac", "1 TeV'de string aralığı 4 m, 8 m ve Mie buz modeli."],
                 ["macros/detail_*TeV.mac", "Her enerji için foton, hit ve müon adımı kaydı açık kısa koşular "
                  "(0,1–3 TeV: 100, 30 TeV: 30, 100 TeV: 10 olay); fizik ve AGN figürlerinin 1–4. panelleri için."],
                 ["run_thesis.sh", "Tüm tez makrolarını sırayla çalıştırır, tamamlanmış koşuları atlar, süreleri build/logs/times.txt'e yazar."]],
                [4.8, 11.6], "Makro dosyaları ve betikler."),
          P("Örnek bir tarama makrosu (make_macros.sh tarafından üretilir):"),
          C(src("macros/scan_1TeV.mac")),
          ]

    # ---------------------------------------------------------------- 8
    S += [PageBreak(), P("8. PYTHON ANALİZ KODLARI", h1),
          P("Analiz dört dosyadan oluşur. <b>common.py</b> ortak fonksiyonları içerir; diğerleri bunları kullanarak "
            "grafik üretir."),
          P("8.1 common.py", h2),
          table([["Fonksiyon", "Görevi"],
                 ["load(prefix)", "Bir koşunun tüm CSV dosyalarını pandas tablosu olarak okur (eksik olan None)."],
                 ["n_phase(λ), n_group(λ)", "Faz ve grup kırılma indisi (C++ ile aynı formül); n<sub>g</sub> = n − λ dn/dλ sayısal türevle."],
                 ["source_dir_from_radec, radec_from_muon_dir", "PrimaryGeneratorAction'daki koordinat dönüşümü ve tersi."],
                 ["ang_dist, angle_between", "Gök küresinde iki nokta / iki vektör arasındaki açı."],
                 ["line_fit", "LineFit: r(t) = r<sub>0</sub> + v t doğrusunun ağırlıklı en küçük kareler çözümü."],
                 ["expected_time", "Cherenkov konisi geometrisiyle doğrudan fotonun beklenen varış zamanı."],
                 ["reconstruct_from_sensors", "LineFit tohumundan başlayıp 5 parametreli Nelder-Mead fiti (θ, φ, 2 kayma, t<sub>0</sub>); maliyet Σ√q·ln(1+(Δt/10 ns)²)."],
                 ["reconstruct_all(data, mode)", "Tüm olayları rekonstrükte eder; mode = hits / all / detected."],
                 ["combined_source", "Olayların kaynak yönlerini aykırıları atarak ortalar, hata yarıçapını verir."],
                 ["muon_dedx_ice", "Bethe-Bloch (yoğunluk etkili) + b·E teorik dE/dx."],
                 ["load_groom, groom_dedx_ice", "PDG/Groom su tablosunu okur, buz yoğunluğuyla MeV/cm'ye çevirir."],
                 ["mean_sem, median_ci", "Ortalama ± standart hata; medyan ve bootstrap güven aralığı."]],
                [5.4, 11.0], "common.py fonksiyonları."),
          P("8.2 analyze.py, compare.py ve thesis.py", h2),
          *bullets([
              "<b>analyze.py &lt;prefix&gt;</b>: tek bir koşu için özet tablo, 6 panelli AGN figürü ve 8 panelli "
              "fizik figürü üretir; olay başına rekonstrüksiyonu <font name='Mono'>_reconstruction.csv</font>'ye yazar. "
              "İkinci bir önek verilirse (<font name='Mono'>analyze.py detail/E3TeV scan/E3TeV</font>) "
              "rekonstrüksiyon ve AGN figürünün 5–6. panelleri bu ikinci, tam istatistikli koşudan; diğer paneller "
              "ayrıntılı kayıtlı ilk koşudan alınır.",
              "<b>compare.py &lt;prefix1&gt; &lt;prefix2&gt;</b>: iki enerjiyi (1 ve 10 TeV) 6 panelde karşılaştırır.",
              "<b>thesis.py</b>: build/data/scan ve build/data/param altındaki tüm koşuları okur ve şunları üretir: "
              "dE/dx'in Groom tablosuyla doğrulanması (oran paneliyle), ışık verimi ve algılama verimi, açısal "
              "çözünürlük (bootstrap güven aralıklı), enerji rekonstrüksiyonu (fiziksel ve ampirik yöntem, "
              "eğitim/test ayrımıyla) ve parametre çalışması (string aralığı, Rayleigh–Mie). Rekonstrüksiyon "
              "sonuçları <font name='Mono'>_reco_detected.csv</font> olarak önbelleğe alınır."]),
          P("8.3 Rekonstrüksiyonun Mantığı", h2),
          P("Her DOM için ilk algılanan fotonun zamanı t<sub>i</sub> ve algılanan foton sayısı q<sub>i</sub> kullanılır. Önce "
            "LineFit hızlı bir ilk yön verir. Ardından her sensör için, aday bir müon izinden beklenen doğrudan "
            "Cherenkov varış zamanı hesaplanır:"),
          eq(r"t_{exp} = t_0 + \frac{1}{c}\left(l - \frac{\rho}{\tan\theta_c}\right) + \frac{n_g}{c}\frac{\rho}{\sin\theta_c}"),
          P("Burada l sensörün iz boyunca izdüşümü, ρ ize dik uzaklığıdır. Ölçülen ve beklenen zamanlar arasındaki "
            "fark (artık) saçılma nedeniyle çoğunlukla pozitiftir; bu yüzden kareler toplamı yerine uç değerlere "
            "dayanıklı logaritmik bir maliyet en küçüklenir. Bulunan müon yönü ters çevrilip RA/Dec'e dönüştürülür."),
          ]

    # ---------------------------------------------------------------- 9
    S += [P("9. SIK SORULAN SORULAR", h1),
          *[x for q, a in [
              ("Neden dünya hacmi hava değil de vakum?",
               "Buzdan çıkan fotonların izlenmesine gerek yoktur. Vakuma RINDEX verilmediği için foton sınırda "
               "soğurulur; bu, hem gerçekçi bir 'kaçış' sınırı hem de hesap tasarrufu sağlar."),
              ("Neden her buz katmanı ayrı bir malzeme?",
               "Geant4'te optik özellikler malzemeye bağlıdır. Derinliğe göre farklı soğurma/saçılma için her katmana "
               "ayrı malzeme gerekir. Kırılma indisleri aynı olduğundan katman sınırlarında yansıma/kırılma olmaz."),
              ("Foton sensöre girince neden yok ediliyor?",
               "Gerçek DOM'da foton fotokatotta soğurulur. Cam içinde izlemeye devam etmek hem gereksiz hem de aynı "
               "fotonun iki kez sayılmasına yol açabilir."),
              ("Neden fotonlar yalnız ilk olayda tek tek yazılıyor?",
               "1 TeV'de bir olay ~10<super>6</super>, 100 TeV'de ~10<super>8</super> foton üretir; hepsini yazmak "
               "gigabaytlarca dosya demektir. Sayılar her olay için events.csv'de vardır."),
              ("Kuantum verimi neden simülasyonda rastgele uygulanıyor?",
               "Gerçek bir fotoçoğaltıcı her fotonu değil, QE olasılığıyla bir kısmını algılar. Hem tüm hit'ler hem "
               "algılananlar kaydedildiği için ikisi de analizde karşılaştırılabilir."),
              ("Program farklı thread sayısıyla aynı sonucu verir mi?",
               "İstatistiksel olarak evet, olay olay hayır: rastgele sayı tohumları olaylara dağıtılır, thread sayısı "
               "değişince hangi olayın hangi tohumu aldığı değişebilir."),
              ("Koordinat dönüşümünde neden yerel yıldız zamanı sıfır?",
               "Basitleştirmedir. Gerçek analizde her olayın zamanı kullanılarak azimut RA'ya çevrilir; Güney "
               "Kutbu'nda Dec dönüşümü (Dec = −yükseklik) zamandan bağımsızdır."),
          ] for x in (P(f"<b>S: {q}</b>", body), P(a, body))],
          ]

    # ---------------------------------------------------------------- Ek
    S += [PageBreak(), P("EK A. C++ KAYNAK KODLARININ TAM LİSTESİ", h1)]
    files = ["sim.cc", "include/Config.hh", "src/Config.cc", "include/DetectorConstruction.hh",
             "src/DetectorConstruction.cc", "include/SensorSD.hh", "src/SensorSD.cc",
             "include/PrimaryGeneratorAction.hh", "src/PrimaryGeneratorAction.cc",
             "include/ActionInitialization.hh", "src/ActionInitialization.cc", "include/RunAction.hh",
             "src/RunAction.cc", "include/EventAction.hh", "src/EventAction.cc", "include/SteppingAction.hh",
             "src/SteppingAction.cc", "include/StackingAction.hh", "src/StackingAction.cc",
             "include/OutputManager.hh", "src/OutputManager.cc", "CMakeLists.txt"]
    for fpath in files:
        lines = src(fpath).splitlines()
        numbered = "\n".join(f"{i:3d}  {l}" for i, l in enumerate(lines, 1))
        S += [CondPageBreak(4*cm), P(f"A.{files.index(fpath)+1} {fpath}", h2), Preformatted(numbered, small_code)]

    doc = CodeDoc(OUT, title=DOC_TITLE, author=br.STUDENT, subject="Teknik belge")
    doc.multiBuild(S)
    print("PDF:", OUT)


if __name__ == "__main__":
    build()

#!/usr/bin/env python3
"""IceCube Geant4 projesi için Türkçe lisans raporu (PDF) üretir."""
import os
import re
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Circle, Rectangle

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.fonts import addMapping
from reportlab.platypus import (BaseDocTemplate, Frame, Image, KeepTogether, NextPageTemplate,
                                PageBreak, PageTemplate, Paragraph, Preformatted, Spacer, Table,
                                TableStyle, CondPageBreak)
from reportlab.platypus.tableofcontents import TableOfContents

PROJ = "/home/yusuf/Desktop/Geant4_dosyaları/Geant4_2"
DATA = f"{PROJ}/build/data"
HERE = os.path.dirname(os.path.abspath(__file__))
EQDIR = f"{HERE}/eq"
# TEZ=1 ortam değişkeniyle aynı içerikten lisans bitirme tezi üretilir: tez kapağı ve ön sayfalar, Abstract,
# şekil/tablo listeleri, ayrıntılı Giriş bölümü (word/giris_taslak.py) ve tek kaynakça. Aksi halde proje raporu.
THESIS = os.environ.get("TEZ") == "1"
OUT = (f"{PROJ}/rapor/03_Tez/Bitirme_Tezi.pdf" if THESIS
       else f"{PROJ}/rapor/01_Proje_Raporu/IceCube_Geant4_Raporu.pdf")
os.makedirs(EQDIR, exist_ok=True)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
sys.path.insert(0, f"{PROJ}/analysis")
import common as cm_  # noqa: E402

# ------------------------------------------------------------------ öğrenci bilgileri
STUDENT = "Yusuf AYDEMİR" if THESIS else "[Ad Soyad]"
STUDENT_NO = "1110510281"
ADVISOR = "[Unvan Ad Soyad]"
DEPARTMENT = "[Bölüm Adı]"
DATE = "Kasım 2026" if THESIS else "Ekim 2026"
LONG_TITLE = ("GEANT4 MONTE CARLO YÖNTEMİYLE BUZDA TeV ENERJİLİ MÜONLARIN CHERENKOV IŞIMASI, IceCube TİPİ "
              "SENSÖRLERLE ALGILANMASI VE AGN KAYNAK YÖNÜNÜN YENİDEN YAPILANDIRILMASI")
HEADER = "Lisans Bitirme Tezi" if THESIS else "Geant4 ile IceCube Müon ve Cherenkov Işığı Simülasyonu"
if THESIS:
    TITLE = HEADER   # Word sürümünün sayfa başlığı (word/dump_blocks.py)

# ------------------------------------------------------------------ yazı tipleri
FD = "/usr/share/fonts/truetype/dejavu"
pdfmetrics.registerFont(TTFont("Serif", f"{FD}/DejaVuSerif.ttf"))
pdfmetrics.registerFont(TTFont("Serif-B", f"{FD}/DejaVuSerif-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Serif-I", f"{FD}/DejaVuSerif-Italic.ttf"))
pdfmetrics.registerFont(TTFont("Serif-BI", f"{FD}/DejaVuSerif-BoldItalic.ttf"))
pdfmetrics.registerFont(TTFont("Mono", f"{FD}/DejaVuSansMono.ttf"))
addMapping("Serif", 0, 0, "Serif"); addMapping("Serif", 1, 0, "Serif-B")
addMapping("Serif", 0, 1, "Serif-I"); addMapping("Serif", 1, 1, "Serif-BI")

NAVY = colors.HexColor("#1b365d")
body = ParagraphStyle("body", fontName="Serif", fontSize=10.5, leading=15.5, alignment=TA_JUSTIFY,
                      spaceAfter=7, firstLineIndent=0)
bullet = ParagraphStyle("bullet", parent=body, leftIndent=16, bulletIndent=5, spaceAfter=3)
h1 = ParagraphStyle("h1", fontName="Serif-B", fontSize=15, leading=19, textColor=NAVY,
                    spaceBefore=6, spaceAfter=10)
h2 = ParagraphStyle("h2", fontName="Serif-B", fontSize=12, leading=16, textColor=NAVY,
                    spaceBefore=10, spaceAfter=5)
caption = ParagraphStyle("cap", fontName="Serif", fontSize=9, leading=12, alignment=TA_JUSTIFY,
                         textColor=colors.HexColor("#333333"), spaceBefore=3, spaceAfter=12)
cell = ParagraphStyle("cell", fontName="Serif", fontSize=8.8, leading=11.5, alignment=TA_LEFT)
cellc = ParagraphStyle("cellc", parent=cell, alignment=TA_CENTER)
cellh = ParagraphStyle("cellh", parent=cell, fontName="Serif-B", textColor=colors.white,
                       alignment=TA_CENTER)
ref = ParagraphStyle("ref", parent=body, fontSize=9.5, leading=13, leftIndent=22,
                     firstLineIndent=-22, alignment=TA_LEFT, spaceAfter=4)
gloss = ParagraphStyle("gloss", parent=body, fontSize=9.8, leading=13.5, leftIndent=14,
                       firstLineIndent=-14, alignment=TA_LEFT, spaceAfter=3)
code = ParagraphStyle("code", fontName="Mono", fontSize=7.8, leading=10, leftIndent=8,
                      backColor=colors.HexColor("#f4f6f8"), borderColor=colors.HexColor("#d0d7de"),
                      borderWidth=0.5, borderPadding=6, spaceBefore=4, spaceAfter=12)

# ------------------------------------------------------------------ sayaçlar ve yardımcılar
_counters = {"fig": 0, "tab": 0, "eq": 0}

# ------------------------------------------------------------------ atıflar (tez modu)
# Rapor metni ve Giriş taslağı kendi kaynak listelerine göre numaralanmıştır. Tezde her [n] atıfı, o anda işlenen
# metnin listesine (CITE["src"]) göre çözülür ve ilk geçiş sırasına göre tek bir kaynakçada yeniden numaralanır.
CITE = {"src": None, "lists": {}, "order": [], "text": {}}
WORDING = [("Bu projede", "Bu tez çalışmasında"),
           ("bir öğrenci projesi kapsamında", "bir lisans bitirme tezi kapsamında")]


def _ref_key(r):
    m = re.search(r"“([^”]+)”", r)
    return (m.group(1) if m else r).lower().strip(" ,.")


def register_refs(name, refs):
    CITE["lists"][name] = [_ref_key(r) for r in refs]
    for r in refs:
        CITE["text"].setdefault(_ref_key(r), r.replace(" et al.", " vd."))


def cite(text):
    if not THESIS:
        return text
    for a, b in WORDING:
        text = text.replace(a, b)
    if CITE["src"] is None:
        return text
    keys = CITE["lists"][CITE["src"]]

    def one(m):
        nums = []
        for part in re.split(r"\s*,\s*", m.group(1)):
            lo, _, hi = part.partition("–")
            for n in range(int(lo), int(hi or lo) + 1):
                if keys[n - 1] not in CITE["order"]:
                    CITE["order"].append(keys[n - 1])
                nums.append(CITE["order"].index(keys[n - 1]) + 1)
        nums, out, i = sorted(set(nums)), [], 0
        while i < len(nums):            # ardışık üç ve daha fazla numara aralık olarak yazılır
            j = i
            while j + 1 < len(nums) and nums[j + 1] == nums[j] + 1:
                j += 1
            out.append(f"{nums[i]}–{nums[j]}" if j - i >= 2 else ", ".join(map(str, nums[i:j + 1])))
            i = j + 1
        return "[" + ", ".join(out) + "]"
    return re.sub(r"\[(\d+(?:\s*[,–]\s*\d+)*)\]", one, text)


def P(text, style=body):
    return Paragraph(cite(text), style)


def bullets(items):
    return [Paragraph(cite(t), bullet, bulletText="•") for t in items]


yorum_style = ParagraphStyle("yorum", fontName="Serif", fontSize=9.6, leading=13.5, alignment=TA_JUSTIFY)


def figure(path, width_cm, text, comment=None):
    """Şekil + alt yazı; comment verilirse altına kısa bir 'Şekil yorumu' kutusu eklenir."""
    _counters["fig"] += 1
    from PIL import Image as PILImage
    w, h = PILImage.open(path).size
    img = Image(path, width=width_cm*cm, height=width_cm*cm*h/w)
    cap = P(f"<b>Şekil {_counters['fig']}.</b> {text}", caption)
    if not comment:
        return KeepTogether([img, cap])
    box = Table([[Paragraph(f"<b>Şekil {_counters['fig']} yorumu:</b> {cite(comment)}", yorum_style)]],
                colWidths=[16.4*cm])
    box.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eef4fb")),
                             ("LINEBEFORE", (0, 0), (0, -1), 2.5, NAVY),
                             ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                             ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 6)]))
    return KeepTogether([img, cap, box, Spacer(1, 10)])


def table(rows, widths, title, header=True, align_center_cols=(), numbered=True):
    if numbered:
        _counters["tab"] += 1
    data = []
    for i, r in enumerate(rows):
        st = cellh if (header and i == 0) else None
        data.append([Paragraph(cite(str(c)), st or (cellc if j in align_center_cols else cell))
                     for j, c in enumerate(r)])
    t = Table(data, colWidths=[w*cm for w in widths], repeatRows=1 if header else 0)
    style = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9aa5b1")),
             ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), NAVY))
        for i in range(1, len(rows)):
            if i % 2 == 0:
                style.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#eef2f7")))
    t.setStyle(TableStyle(style))
    if not numbered:                    # ön sayfalardaki listeler: numarasız, tablo listesine girmez
        return KeepTogether([t, Spacer(1, 10)])
    cap = P(f"<b>Tablo {_counters['tab']}.</b> {title}", caption)
    return KeepTogether([cap, t, Spacer(1, 10)])


def eq(latex, fontsize=15):
    """Matplotlib mathtext ile numaralı denklem."""
    _counters["eq"] += 1
    n = _counters["eq"]
    path = f"{EQDIR}/eq{n}.png"
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, f"${latex}$", fontsize=fontsize)
    fig.savefig(path, dpi=300, bbox_inches="tight", pad_inches=0.04, transparent=True)
    plt.close(fig)
    from PIL import Image as PILImage
    w, h = PILImage.open(path).size
    scale = 0.85*2.54/300  # cm/px (biraz küçült)
    W, H = w*scale, h*scale
    if W > 13.5:
        H *= 13.5/W; W = 13.5
    t = Table([[Image(path, width=W*cm, height=H*cm), P(f"({n})", cellc)]],
              colWidths=[15.0*cm, 1.4*cm])
    t.setStyle(TableStyle([("ALIGN", (0, 0), (0, 0), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    return t


# ------------------------------------------------------------------ belge şablonu
class ReportDoc(BaseDocTemplate):
    def __init__(self, filename, **kw):
        super().__init__(filename, pagesize=A4, leftMargin=2.3*cm, rightMargin=2.3*cm,
                         topMargin=2.2*cm, bottomMargin=2.0*cm, **kw)
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="f")
        self.addPageTemplates([PageTemplate("cover", [frame], onPage=lambda c, d: None),
                               PageTemplate("normal", [frame], onPage=self._decor)])

    def _decor(self, canv, doc):
        canv.saveState()
        canv.setFont("Serif", 8.5)
        canv.setFillColor(colors.HexColor("#555555"))
        canv.drawString(self.leftMargin, A4[1] - 1.4*cm, HEADER)
        canv.drawRightString(A4[0] - self.rightMargin, A4[1] - 1.4*cm, STUDENT)
        canv.setStrokeColor(colors.HexColor("#9aa5b1")); canv.setLineWidth(0.4)
        canv.line(self.leftMargin, A4[1] - 1.55*cm, A4[0] - self.rightMargin, A4[1] - 1.55*cm)
        canv.drawCentredString(A4[0]/2, 1.2*cm, str(doc.page - 1))
        canv.restoreState()

    def afterFlowable(self, f):
        if isinstance(f, Paragraph) and f.style.name in ("h1", "h2"):
            level = 0 if f.style.name == "h1" else 1
            text = f.getPlainText()
            key = f"h{self.seq.nextf('heading')}"
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(text, key, level=level, closed=level > 0)
            self.notify("TOCEntry", (level, text, self.page - 1, key))
        elif isinstance(f, Paragraph) and f.style.name == "cap":     # tezde şekil ve tablo listeleri
            m = re.match(r"(Şekil|Tablo) (\d+)\.\s*(.*)", f.getPlainText())
            if m:
                first = re.split(r"(?<=[^\d\s])\. |: ", m.group(3))[0].rstrip(".")   # kısa liste girişi
                key = f"c{self.seq.nextf('caption')}"
                self.canv.bookmarkPage(key)
                self.notify("TOCFigure" if m.group(1) == "Şekil" else "TOCTable",
                            (0, f"{m.group(1)} {m.group(2)}. {first}", self.page - 1, key))


# ------------------------------------------------------------------ veriler
def load_stats():
    s = {}
    for e in ("1TeV", "10TeV"):
        ev = pd.read_csv(f"{DATA}/{e}_events.csv")
        el = pd.read_csv(f"{DATA}/{e}_muon_energy_loss.csv")
        reco = pd.read_csv(f"{DATA}/{e}_reconstruction.csv")
        g = el.groupby("process")["dE_MeV"].sum()
        src = cm_.combined_source(reco)
        s[e] = dict(
            ev=ev, reco=reco, proc=g/g.sum(), src=src,
            eloss_mean=ev.E_loss_MeV.mean()/1e3, eloss_med=ev.E_loss_MeV.median()/1e3,
            eloss_min=ev.E_loss_MeV.min()/1e3, eloss_max=ev.E_loss_MeV.max()/1e3,
            frac=100*ev.E_loss_MeV.mean()/ev.E0_MeV.iloc[0],
            edep=ev.edep_total_MeV.mean()/1e3,
            ph=ev.n_photons.mean(), ph_med=ev.n_photons.median(), ph_prim=ev.n_photons_primary.mean(),
            prim_frac=100*ev.n_photons_primary.sum()/ev.n_photons.sum(),
            hits=ev.n_hits.mean(), hits_med=ev.n_hits.median(),
            eff=100*ev.n_hits.sum()/ev.n_photons.sum(),
            L=ev.track_len_mm.mean()/1000,
            dedx_mean=el.dE_MeV.sum()/(el.step_mm.sum()/10),
            dedx_med=(ev.E_loss_MeV/(ev.track_len_mm/10)).median(),
            lf=reco.err_linefit_deg.median(), fit=reco.err_fit_deg.median(),
            fit68=reco.err_fit_deg.quantile(0.68), lt1=100*(reco.err_fit_deg < 1).mean(),
            lt5=100*(reco.err_fit_deg < 5).mean(),
            dists={a[0]: cm_.ang_dist(src[0], src[1], a[1], a[2]) for a in cm_.AGN_CATALOG},
        )
    return s


def geometry_figure(path):
    sens = pd.read_csv(f"{DATA}/1TeV_sensors.csv")
    ice = pd.read_csv(f"{DATA}/1TeV_ice_properties.csv")
    at400 = ice[ice.wavelength_nm == 400].set_index("layer")
    ev = pd.read_csv(f"{DATA}/1TeV_events.csv").sort_values("event")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 5.6))

    # Üstten görünüm
    a1.add_patch(Rectangle((-10, -10), 20, 20, fc="#dbeefc", ec="#2171b5", lw=1.5))
    a1.scatter(sens.x_mm/1000, sens.y_mm/1000, s=110, c="orange", ec="k", zorder=3)
    for sid in sens.string_id.unique():
        r = sens[sens.string_id == sid].iloc[0]
        a1.annotate(f"S{sid}", (r.x_mm/1000, r.y_mm/1000), xytext=(7, 7), textcoords="offset points")
    for _, e in ev.head(15).iterrows():
        p0 = np.array([e.x0_mm, e.y0_mm])/1000; d = np.array([e.dir_x, e.dir_y])
        a1.plot(*np.array([p0, p0 + 28*d/np.linalg.norm([e.dir_x, e.dir_y, e.dir_z])]).T,
                color="crimson", lw=0.8, alpha=0.6)
    a1.annotate("", xy=(4, -12.5), xytext=(6, -3.5),
                arrowprops=dict(arrowstyle="->", color="crimson", lw=2))
    a1.text(6.3, -6, "müon\nyönü", color="crimson")
    a1.set_xlim(-15, 15); a1.set_ylim(-15, 15); a1.set_aspect("equal")
    a1.set_xlabel("x [m]"); a1.set_ylabel("y [m]")
    a1.set_title("(a) Üstten görünüm: 3×3 string ve ilk 15 müon izi")

    # Yandan görünüm
    cmap = plt.get_cmap("Blues_r")
    for L, r in at400.iterrows():
        zmin, zmax = r.zmin_mm/1000, r.zmax_mm/1000
        c = cmap(0.25 + 0.6*(r.abs_length_m - 40)/110)
        a2.add_patch(Rectangle((-10, zmin), 20, zmax - zmin, fc=c, ec="#2171b5", lw=0.8))
        a2.text(10.4, (zmin + zmax)/2,
                f"katman {L}\n{r.depth_m:.1f} m\nλ$_{{abs}}$={r.abs_length_m:.0f} m\nλ$_{{R}}$={r.rayleigh_length_m:.0f} m",
                va="center", fontsize=8.5)
    for x in (-6, 0, 6):
        a2.plot([x, x], [-10, 10], color="k", lw=0.8)
    a2.scatter(sens.x_mm/1000, sens.z_mm/1000, s=90, c="orange", ec="k", zorder=3)
    a2.set_xlim(-15, 17); a2.set_ylim(-12, 12)
    a2.set_xlabel("x [m]"); a2.set_ylabel("z [m] (yukarı)")
    a2.set_title("(b) Yandan görünüm: 4 buz katmanı ve DOM'lar (400 nm)")
    a2.set_aspect("equal")
    fig.tight_layout()
    fig.savefig(path, dpi=150); plt.close(fig)


# ------------------------------------------------------------------ içerik
def load_scan():
    """İkinci aşama (enerji taraması + parametre çalışması) özet tabloları (analysis/thesis.py çıktısı)."""
    TH = f"{DATA}/thesis"
    T = pd.read_csv(f"{TH}/thesis_summary.csv").sort_values("E_TeV").reset_index(drop=True)
    R = pd.read_csv(f"{TH}/energy_resolution.csv").sort_values("E_TeV").reset_index(drop=True)
    Pm = pd.read_csv(f"{TH}/parameter_study.csv")
    return T, R, Pm, TH


ALL_E = [0.1, 0.3, 3, 10, 30, 100]   # 1 TeV figürleri ana metinde (Şekil 2–3)


def detail_paths(E):
    """Ayrıntılı (foton/hit/adım kayıtlı) koşu öneki ve tarama koşusunun rekonstrüksiyon tablosu."""
    return f"{DATA}/detail/E{E:g}TeV", f"{DATA}/scan/E{E:g}TeV_reconstruction.csv"


def load_detail_stats():
    groom = cm_.load_groom()
    out = {}
    for E in ALL_E:
        pre, rfile = detail_paths(E)
        if not os.path.exists(f"{pre}_physics.png"):
            continue
        ev = pd.read_csv(f"{pre}_events.csv")
        el = pd.read_csv(f"{pre}_muon_energy_loss.csv")
        reco = pd.read_csv(rfile)
        sc = pd.read_csv(f"{DATA}/scan/E{E:g}TeV_events.csv")
        src = cm_.combined_source(reco)
        big = ev.loc[ev.E_loss_MeV.idxmax()]
        out[E] = dict(
            pre=pre, n=len(ev), n_reco=len(reco),
            dedx=el.dE_MeV.sum()/(el.step_mm.sum()/10), groom=cm_.groom_dedx_ice(E*1e6, table=groom),
            rad=100*sc.E_loss_rad_MeV.sum()/sc.E_loss_MeV.sum(),   # tarama koşusundan (daha çok olay)
            ph_cm=ev.n_photons_primary.sum()/(ev.track_len_mm.sum()/10),
            ph=ev.n_photons.mean(), prim=100*ev.n_photons_primary.sum()/ev.n_photons.sum(),
            hits=ev.n_hits.mean(), eff=100*ev.n_hits.sum()/ev.n_photons.sum(),
            big_loss=big.E_loss_MeV/1e3, big_dep=big.edep_total_MeV/1e3,
            spread=float(ev.n_photons.max()/ev.n_photons.min()),
            fit=reco.err_fit_deg.median(), lf=reco.err_linefit_deg.median(),
            txs=cm_.ang_dist(src[0], src[1], 77.358, 5.693), r90=src[2],
        )
    return out


# Enerjiye özgü kısa gözlemler (genel, veriden hesaplanan yorumun sonuna eklenir).
NOTES_PHYS = {
    0.1: "Bu enerji kritik enerjinin (≈ 1 TeV) çok altındadır ve kayıp büyük ölçüde iyonizasyondur. (h)'nin sağındaki "
         "birkaç olay, tek bir büyük δ-elektronu ya da seyrek bir radyatif kayıpla ortalamanın çok üzerinde ışık "
         "üretmiştir (en büyük kayıp {big_loss} GeV).",
    0.3: "Radyatif kayıplar görülmeye başlar ama iyonizasyon hâlâ baskındır. (h)'deki uzun kuyruk birkaç büyük "
         "radyatif kayıptan gelir (en büyük kayıp {big_loss} GeV).",
    3: "Kritik enerjinin üstünde çift üretimi belirginleşir ve (b)'deki çift üretimi dağılımı 10<super>6</super> "
       "MeV/cm'ye uzanır. (h)'nin sağ altındaki olayda müon {big_loss} GeV kaybetmiş ama buzda yalnızca {big_dep} GeV "
       "bırakmıştır: kaybedilen enerjinin büyük kısmı ışık üretmeden hacimden kaçan ikincil parçacıklara gitmiştir.",
    10: "Radyatif kayıplar artık toplam kaybın büyük bölümünü oluşturur; (h)'de en parlak ve en sönük olay "
        "arasındaki ışık farkı {spread} kata ulaşır.",
    30: "Olaylar arasındaki ışık farkı iki mertebeyi aşar; tek bir büyük kaskad (en büyük kayıp {big_loss} GeV) bir "
        "olayın ışığının neredeyse tamamını belirleyebilir.",
    100: "Aynı enerjideki 4000 olaylık ve ışık üretimi kapalı doğrulama koşusunda ortalama kayıp Groom değerine "
         "yaklaşır (Bölüm 4.9). (b)'de çift üretimi adımları 10<super>6</super> MeV/cm'ye uzanır; en büyük kayıp "
         "{big_loss} GeV'dir.",
}
NOTES_AGN = {
    0.1: "Işığın büyük kısmı birincil müondan geldiği için (1)'de iz ince ve düzgün bir çizgidir.",
    0.3: "Kaskad ışığı birincil müonunkine yaklaşmıştır; (4)'te ize yakın orta stringler yine en çok ışığı alır.",
    3: "Işığın yaklaşık dörtte üçü artık kaskadlardan gelir; buna rağmen yön hatası düşük enerjilerdekiyle aynıdır.",
    10: "Işık 0,1 TeV'e göre birkaç kat artmasına karşın tek olay hatası değişmez, çünkü yön bilgisini taşıyan ilk "
        "fotonlar her enerjide birincil müonun Cherenkov konisinden gelir.",
    30: "Birincil müonun ışıktaki payı yalnızca %{prim} kadardır; buna karşın yön hatası düşük enerjilerdeki düzeyde kalır.",
    100: "(1)'de iz boyunca parlak bir kaskad kümesi görülür ve (4)'te bu kaskada en yakın sensör diğerlerinden kat kat "
         "fazla ışık alır. Yalnızca 20 olay birleştirildiği için hata yarıçapı ({r90}°) düşük enerjilere göre "
         "geniştir.",
}


def appendix_all_energies(f, Etxt):
    D = load_detail_stats()
    rows = [["E<br/>[TeV]", "Olay<br/>ayr./tar.", "⟨dE/dx⟩", "Groom", "Rad.<br/>pay", "Foton<br/>/cm", "DOM'a<br/>ulaşan",
             "Fit<br/>hatası", "TXS<br/>uzaklık"]]
    for E, d in D.items():
        rows.append([Etxt(E), f"{d['n']} / {d['n_reco']}", f(d['dedx'], 2), f(d['groom'], 2), f(d['rad']),
                     f(d['ph_cm']), f(d['eff'], 2), f(d['fit'], 2), f(d['txs'], 2)])
    out = [PageBreak(), P("EK C. TÜM ENERJİLER İÇİN AYRINTILI GRAFİKLER", h1),
           P("Ana metinde 1 TeV için verilen fizik (Şekil 2) ve AGN (Şekil 3) grafikleri bu ekte taramanın diğer "
             "enerjileri için tekrarlanmıştır. Enerji taraması koşuları disk alanından tasarruf için yalnızca olay "
             "özetlerini kaydettiğinden, foton, sensör vuruşu ve müon adımı kayıtları gerektiren grafikler için her "
             "enerjide ayrıntılı kayıtlı kısa ek koşular yapılmıştır. Fizik grafikleri ve AGN grafiklerinin 1–4. "
             "panelleri bu ek koşulardan, AGN grafiklerinin 5–6. panelleri (kaynak eşleşmesi ve gökyüzü haritası) ise "
             "tam tarama istatistiğinden üretilmiştir; her grafiğin başlığında olay sayıları belirtilmiştir. "
             "Grafiklerin panel tanımları Şekil 2 ve Şekil 3'teki "
             "gibidir."),
           table(rows, [1.6, 2.1, 1.8, 1.8, 1.4, 1.5, 1.7, 1.6, 1.8],
                 "Ayrıntılı koşuların özeti: ortalama enerji kaybı ve Groom değeri [MeV/cm], radyatif kayıp payı [%], "
                 "birincil müonun cm başına foton sayısı, DOM'lara ulaşan fotonların oranı [%] (kuantum verimi öncesi; Bölüm "
                 "4.8'deki algılama verimi bunun yaklaşık beşte biridir), Cherenkov fitinin medyan hatası [°] ve "
                 "birleşik kaynağın TXS 0506+056'ya uzaklığı [°]. ⟨dE/dx⟩, foton sayısı ve DOM'a ulaşan oran ayrıntılı koşudan; "
                 "radyatif pay, fit hatası ve TXS uzaklığı tarama koşusundan alınmıştır.",
                 align_center_cols=range(9))]
    for i, (E, d) in enumerate(D.items(), 1):
        v = {k: (f(x, 1) if isinstance(x, float) else x) for k, x in d.items()}
        ratio = d['dedx']/d['groom']
        samp = ("" if abs(ratio - 1) <= 0.15 else
                f" Simülasyon ile tablo arasındaki %{f(100*abs(ratio - 1))} fark, yalnızca {d['n']} olayda seyrek ve büyük "
                f"radyatif kayıpların eksik ya da fazla örneklenmesinden kaynaklanır (bkz. Bölüm 4.9).")
        phys = (f"(a) Ortalama kayıp {f(d['dedx'], 2)} MeV/cm, Groom tablosu {f(d['groom'], 2)} MeV/cm.{samp} Radyatif "
                f"süreçlerin kayıptaki payı %{f(d['rad'])} düzeyindedir. (c) Birincil müon {f(d['ph_cm'])} foton/cm üretir; bu sayı "
                f"Frank-Tamm bağıntısıyla uyumludur ve enerjiden bağımsızdır. (d)–(f) buz özellikleri tüm enerjilerde "
                f"aynıdır. " + NOTES_PHYS.get(E, "").format(**v))
        agn = (f"Olay başına ortalama {f(d['ph']/1e6, 2)} milyon foton üretilir, birincil müonun "
               f"bu ışıktaki payı %{f(d['prim'])} kadardır. DOM'lara olay başına ortalama {f(d['hits'])} foton, yani üretilen fotonların %{f(d['eff'], 2)} kadarı ulaşır. Cherenkov "
               f"fitinin medyan hatası {f(d['fit'], 2)}°, LineFit'inki {f(d['lf'], 1)}°'dir. Birleşik kaynak TXS "
               f"0506+056'ya {f(d['txs'], 2)}° uzaklıktadır (hata yarıçapı {f(d['r90'], 2)}°) ve katalogdaki diğer "
               f"AGN'lerden açıkça ayrışır. " + NOTES_AGN.get(E, "").format(**v))
        out += [PageBreak(), P(f"C.{i} {Etxt(E)} TeV", h2),
                figure(f"{d['pre']}_physics.png", 12.6, f"{Etxt(E)} TeV müonlar için fiziksel yorumlar "
                       f"({d['n']} olaylık ayrıntılı koşu).", comment=phys),
                figure(f"{d['pre']}_agn_reconstruction.png", 13.4, f"{Etxt(E)} TeV için AGN kaynak "
                       f"rekonstrüksiyonu.", comment=agn)]
    return out


REFS_RAPOR = [
    "IceCube Collaboration, M. G. Aartsen et al., “Neutrino emission from the direction of the blazar TXS 0506+056 prior to the IceCube-170922A alert,” <i>Science</i> 361, 147–151 (2018).",
    "IceCube, Fermi-LAT, MAGIC et al., “Multimessenger observations of a flaring blazar coincident with high-energy neutrino IceCube-170922A,” <i>Science</i> 361, eaat1378 (2018).",
    "IceCube Collaboration, R. Abbasi et al., “Evidence for neutrino emission from the nearby active galaxy NGC 1068,” <i>Science</i> 378, 538–543 (2022).",
    "IceCube Collaboration, M. G. Aartsen et al., “The IceCube Neutrino Observatory: instrumentation and online systems,” <i>JINST</i> 12, P03012 (2017).",
    "S. Agostinelli et al., “Geant4 — a simulation toolkit,” <i>Nucl. Instrum. Meth. A</i> 506, 250–303 (2003); J. Allison et al., “Recent developments in Geant4,” <i>Nucl. Instrum. Meth. A</i> 835, 186–225 (2016).",
    "Particle Data Group, S. Navas et al., “Review of Particle Physics – Passage of particles through matter,” <i>Phys. Rev. D</i> 110, 030001 (2024).",
    "D. E. Groom, N. V. Mokhov, S. I. Striganov, “Muon stopping power and range tables 10 MeV–100 TeV,” <i>Atomic Data and Nuclear Data Tables</i> 78, 183–356 (2001).",
    "P. B. Price, L. Bergström, “Optical properties of deep ice at the South Pole: scattering,” <i>Applied Optics</i> 36, 4181–4194 (1997).",
    "M. Ackermann et al. (AMANDA), “Optical properties of deep glacial ice at the South Pole,” <i>J. Geophys. Res.</i> 111, D13203 (2006).",
    "I. M. Frank, I. E. Tamm, “Coherent visible radiation of fast electrons passing through matter,” <i>C. R. Acad. Sci. URSS</i> 14, 109–114 (1937).",
    "R. M. Sternheimer, M. J. Berger, S. M. Seltzer, “Density effect for the ionization loss of charged particles in various substances,” <i>Atomic Data and Nuclear Data Tables</i> 30, 261–271 (1984).",
    "C. M. Urry, P. Padovani, “Unified schemes for radio-loud active galactic nuclei,” <i>Publ. Astron. Soc. Pac.</i> 107, 803–845 (1995).",
    "IceCube Collaboration, M. G. Aartsen et al., “Improvement in fast particle track reconstruction with robust statistics,” <i>Nucl. Instrum. Meth. A</i> 736, 143–149 (2014).",
    "D. Chirkin, W. Rhode, “Propagating leptons through matter with Muon Monte Carlo (MMC),” arXiv:hep-ph/0407075 (2004).",
]
register_refs("rapor", REFS_RAPOR)

# ------------------------------------------------------------------ tez modu: ön sayfalar ve bölümler
CV = ParagraphStyle("cv", fontName="Serif-B", fontSize=14, leading=20, alignment=TA_CENTER)
CVS = ParagraphStyle("cvs", fontName="Serif", fontSize=12, leading=18, alignment=TA_CENTER)
TT = ParagraphStyle("tt", fontName="Serif-B", fontSize=20, leading=28, alignment=TA_CENTER, textColor=NAVY)


def thesis_front():
    """Dış kapak, kabul ve onay, bilimsel etik beyanı ve teşekkür."""
    title_tc = ("Geant4 Monte Carlo Yöntemiyle Buzda TeV Enerjili Müonların Cherenkov Işıması, IceCube Tipi "
                "Sensörlerle Algılanması ve AGN Kaynak Yönünün Yeniden Yapılandırılması")
    return [Spacer(1, 1.5*cm), P("T.C.", CV), P("ERCİYES ÜNİVERSİTESİ", CV), P("FEN FAKÜLTESİ", CV),
            P(DEPARTMENT, CVS), Spacer(1, 2.2*cm), P(LONG_TITLE, TT), Spacer(1, 1.0*cm),
            P("LİSANS BİTİRME TEZİ", CV), Spacer(1, 2.0*cm),
            P(f"<b>Hazırlayan:</b> {STUDENT}", CVS), P(f"<b>Öğrenci No:</b> {STUDENT_NO}", CVS),
            Spacer(1, 0.4*cm), P(f"<b>Danışman:</b> {ADVISOR}", CVS), Spacer(1, 2.0*cm),
            P("KAYSERİ", CV), P(DATE, CVS), NextPageTemplate("normal"), PageBreak(),

            P("KABUL VE ONAY", h1),
            P(f"{STUDENT} tarafından hazırlanan “{title_tc}” başlıklı bu çalışma, jürimiz tarafından Erciyes "
              f"Üniversitesi Fen Fakültesi {DEPARTMENT} Bölümü'nde <b>Lisans Bitirme Tezi</b> olarak kabul "
              f"edilmiştir."),
            Spacer(1, 0.8*cm),
            table([["Görevi", "Unvanı, Adı Soyadı", "İmza"],
                   ["Danışman", ADVISOR, ""], ["Üye", "[Unvan Ad Soyad]", ""], ["Üye", "[Unvan Ad Soyad]", ""]],
                  [3.5, 8.4, 4.5], "", numbered=False),
            Spacer(1, 0.6*cm), P("Onay tarihi: ..... / ..... / 20....."), PageBreak(),

            P("BİLİMSEL ETİĞE UYGUNLUK BEYANI", h1),
            P("Bu tezdeki tüm bilgilerin akademik ve etik kurallara uygun olarak elde edildiğini ve sunulduğunu; "
              "ayrıca bu kuralların gerektirdiği şekilde, bu çalışmada özgün olmayan tüm materyal ve sonuçlara "
              "kaynak gösterdiğimi beyan ederim."),
            P("Bu tezde kullanılan simülasyon ve analiz programlarının yazımında ve metnin düzenlenmesinde yapay "
              "zekâ destekli araçlardan yararlanılmıştır. Programların çalıştırılması, sonuçların kontrolü ve "
              "yorumlanması tarafımdan yapılmış; tezde yer alan tüm sayısal sonuçlar, bu tez kapsamında yapılan "
              "benzetimlerden elde edilmiştir."),
            Spacer(1, 1.2*cm), P(f"{STUDENT}<br/>İmza:", ParagraphStyle("imza", parent=body, alignment=TA_LEFT,
                                                                       leftIndent=10*cm)),
            PageBreak(),

            P("TEŞEKKÜR", h1),
            P(f"Bu çalışmanın her aşamasında bilgi ve deneyimiyle bana yol gösteren, sorularıma sabırla yanıt veren "
              f"danışmanım {ADVISOR}'a teşekkür ederim. Lisans eğitimim boyunca emeği geçen bölümümüzün tüm "
              f"öğretim elemanlarına ve beni her zaman destekleyen aileme teşekkürü bir borç bilirim."),
            Spacer(1, 1.0*cm), P(f"{STUDENT}<br/>{DATE}", ParagraphStyle("imza2", parent=body, alignment=TA_LEFT,
                                                                       leftIndent=10*cm)),
            PageBreak()]


def thesis_abstract(a, b, T, sp):
    """İngilizce özet (Türkçe ÖZET ile aynı içerik; ondalık ayırıcı nokta)."""
    g = lambda x, d=0: f"{x:,.{d}f}"   # noqa: E731
    Eg = lambda E: g(E, 1) if E < 1 else g(E)   # noqa: E731
    return [P("ABSTRACT", h1),
            P(f"In this study, a simplified model of the IceCube Neutrino Observatory at the South Pole was built "
              f"with the Geant4 (version 11.3.1) Monte Carlo simulation toolkit, and the behaviour in ice of TeV "
              f"muons arriving from the direction of an active galactic nucleus (AGN) was investigated. The model "
              f"consists of a four-layer 20 m × 20 m × 20 m ice block with depth-dependent absorption and "
              f"scattering and 36 optical sensors arranged as 3×3 strings × 4 DOMs. The study was carried out in "
              f"two stages: in the first stage, 1 and 10 TeV muons (100 events each) were examined in detail at "
              f"the photon level; in the second stage, with the photomultiplier quantum efficiency included, "
              f"{g(T.N.sum())} muons were simulated at {len(T)} energies between {Eg(T.E_TeV.min())} and "
              f"{Eg(T.E_TeV.max())} TeV, and a parameter study was performed by varying the string spacing and "
              f"the ice scattering model."),
            P(f"1 TeV muons lost on average {g(a['eloss_mean'],1)} GeV ({g(a['frac'],2)}%) along a {g(a['L'],1)} m "
              f"path in ice and produced on average {g(a['ph'])} Cherenkov photons per event, {g(a['hits'])} of "
              f"which reached the sensors (fraction {g(a['eff'],2)}%). The number of photons emitted "
              f"by the primary muon ({g(a['ph_prim'])} photons, ≈326 photons/cm) agrees with the Frank–Tamm "
              f"prediction to better than 1%. At 10 TeV the mean loss rose to {g(b['eloss_mean'],1)} GeV and the "
              f"photon yield to {g(b['ph'])}; this increase was shown to originate from electromagnetic cascades "
              f"initiated by radiative processes, mainly e<super>+</super>e<super>−</super> pair production."),
            P(f"The muon direction was reconstructed from the sensor hit times with LineFit and a Cherenkov "
              f"time-residual fit. The median angular error per event is {g(a['fit'],2)}° at 1 TeV and "
              f"{g(b['fit'],2)}° at 10 TeV. By combining 100 events, the source direction was found "
              f"{g(a['dists']['TXS 0506+056'],2)}° (1 TeV) and {g(b['dists']['TXS 0506+056'],2)}° (10 TeV) away "
              f"from the blazar TXS 0506+056 and was correctly matched to this BL Lac-type blazar within a small AGN "
              f"catalogue."),
            P(f"In the energy scan, the simulated muon energy loss agreed with the PDG/Groom tables within 5% up to "
              f"1 TeV. With quantum efficiency included, the median angular error of the Cherenkov time fit stayed "
              f"between {g(T.fit.min(),1)}° and {g(T.fit.max(),1)}° at all energies. Reducing the string spacing "
              f"from 8 m to 4 m increased the detected light and lowered the angular error from "
              f"{g(sp.fit.iloc[-1],2)}° to {g(sp.fit.iloc[0],2)}°. The calibration-curve method developed to "
              f"estimate the energy from the amount of light substantially reduced the systematic bias; however, "
              f"the 20 m track length was shown to fundamentally limit the energy resolution, and below 1 TeV the "
              f"light is almost insensitive to the muon energy."),
            P("<b>Keywords:</b> Geant4, IceCube, muon energy loss, Bethe–Bloch, Cherenkov radiation, Frank–Tamm, "
              "ice optics, track reconstruction, AGN, blazar."),
            PageBreak()]


def thesis_lists():
    """Şekiller listesi, tablolar listesi, simgeler ve kısaltmalar."""
    lst = ParagraphStyle("lst", fontName="Serif", fontSize=9.6, leading=13, leftIndent=0)
    out = []
    for title, kind in (("ŞEKİLLER LİSTESİ", "TOCFigure"), ("TABLOLAR LİSTESİ", "TOCTable")):
        t = TableOfContents(notifyKind=kind)
        t.levelStyles = [lst]
        t.dotsMinLevel = 0
        out += [P(title, h1), t, PageBreak()]
    sym = [["Simge", "Açıklama", "Birim"],
           ["E", "Müonun kinetik enerjisi", "GeV, TeV"],
           ["dE/dx", "Birim yol başına ortalama enerji kaybı (durdurma gücü)", "MeV/cm"],
           ["a(E), b(E)", "İyonizasyon ve radyatif kayıp katsayıları (−dE/dx = a + bE)", "MeV/cm, cm<super>−1</super>"],
           ["E<sub>c</sub>", "Kritik enerji (iyonizasyon ve radyatif kaybın eşit olduğu enerji)", "TeV"],
           ["β", "Parçacık hızının boşluktaki ışık hızına oranı (v/c)", "–"],
           ["n, n<sub>g</sub>", "Faz ve grup kırılma indisi", "–"],
           ["θ<sub>c</sub>", "Cherenkov açısı, cos θ<sub>c</sub> = 1/(nβ)", "°"],
           ["λ", "Foton dalga boyu", "nm"],
           ["λ<sub>abs</sub>, λ<sub>s</sub>, λ<sub>e</sub>", "Soğurma, saçılma ve etkin saçılma uzunluğu", "m"],
           ["g", "Saçılma açısının ortalama kosinüsü ⟨cos θ⟩ (Henyey-Greenstein)", "–"],
           ["η", "Algılama verimi (algılanan / üretilen foton)", "%"],
           ["σ", "Standart sapma; enerji kestiriminde çözünürlük", "–, dex"],
           ["r<sub>90</sub>", "Birleşik kaynak konumunun %90 hata yarıçapı", "°"],
           ["α (RA), δ (Dec)", "Sağ açıklık ve dik açıklık (ekvatoral koordinatlar)", "°"],
           ["N", "Olay sayısı", "–"]]
    abbr = [["Kısaltma", "Açıklama"],
            ["AGN", "Aktif galaktik çekirdek (Active Galactic Nucleus)"],
            ["BL Lac", "Salma çizgileri zayıf ya da olmayan blazar türü (BL Lacertae nesnesi)"],
            ["CSV", "Virgülle ayrılmış değerler dosya biçimi (Comma-Separated Values)"],
            ["DOM", "Sayısal optik modül (Digital Optical Module)"],
            ["EM", "Elektromanyetik"],
            ["FSRQ", "Düz tayflı radyo kuasarı (Flat-Spectrum Radio Quasar)"],
            ["MC", "Monte Carlo"],
            ["MT", "Çok iş parçacıklı çalışma (multi-threading)"],
            ["PDG", "Parçacık Verileri Grubu (Particle Data Group)"],
            ["PMT", "Fotoçoğaltıcı tüp (photomultiplier tube)"],
            ["QE", "Kuantum verimi (quantum efficiency)"],
            ["SPICE", "Güney Kutbu buz modeli (South Pole ICE)"],
            ["TRUBA", "TÜBİTAK ULAKBİM yüksek başarımlı hesaplama altyapısı"],
            ["eV, TeV, PeV", "Elektronvolt; 1 TeV = 10<super>12</super> eV, 1 PeV = 10<super>15</super> eV"]]
    out += [P("SİMGELER VE KISALTMALAR", h1), P("<b>Simgeler</b>"),
            table(sym, [3.6, 9.8, 3.0], "", numbered=False), P("<b>Kısaltmalar</b>"),
            table(abbr, [3.0, 13.4], "", numbered=False)]
    return out


def thesis_giris():
    """Bölüm 1: ayrıntılı Giriş taslağı (word/giris_taslak.py) kendi atıf listesiyle aktarılır."""
    import json
    import subprocess
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        subprocess.run([sys.executable, f"{HERE}/word/giris_taslak.py", f"{d}/g.json"], check=True)
        blocks = json.load(open(f"{d}/g.json", encoding="utf-8"))["blocks"]
    k = next(i for i, b in enumerate(blocks) if b.get("text", "").startswith("Bu Bölümde Kullanılan"))
    register_refs("giris", [re.sub(r"^\[\d+\]\s*", "", b["text"]) for b in blocks[k + 1:]
                            if b.get("style") == "ref"])
    CITE["src"] = "giris"
    out = []
    for b in blocks[:k]:
        if b["type"] == "bullet":
            out += bullets([b["text"]])
        else:
            out.append(P(b["text"], {"h1": h1, "h2": h2}.get(b["style"], body)))
    CITE["src"] = "rapor"            # Bölüm 2–6 proje raporunun kaynak listesine göre atıf yapar
    return out


def thesis_oneriler():
    return [P("6.2 Öneriler", h2),
            P("Bu çalışmanın sonuçları ve sınırlılıkları (Bölüm 5) göz önüne alınarak ileri çalışmalar için şu "
              "adımlar önerilmektedir:"),
            *bullets([
                "<b>Gerçekçi buz modeli:</b> Temsili katman parametreleri yerine ölçülmüş bir buz modelinin "
                "(ör. SPICE) derinliğe ve dalga boyuna bağlı soğurma ve Mie saçılması değerleriyle kullanılması.",
                "<b>Daha büyük dedektör:</b> Geometrinin büyütülerek müon izinin daha uzun bir bölümünün "
                "gözlenmesi; bu, hem açısal çözünürlüğü hem de stokastik kayıpların ortalamasının alınmasını "
                "iyileştirerek enerji çözünürlüğünü artıracaktır.",
                "<b>Daha yüksek istatistik:</b> Yüksek enerjilerde olay sayısının artırılması; gerekirse "
                "hesaplamaların TRUBA gibi yüksek başarımlı bir altyapıda yürütülmesi.",
                "<b>Gelişmiş rekonstrüksiyon:</b> Kaskad ışığını ve saçılmayı da hesaba katan olabilirlik "
                "tabanlı bir yön ve enerji rekonstrüksiyonu yazılması.",
                "<b>Gerçekçi sinyal ve arka plan:</b> Nötrinonun yüklü akım etkileşmesinin benzetilmesi ve "
                "atmosferik müon ile nötrino arka planı eklenerek kaynak anlamlılığının (p-değeri) "
                "hesaplanması.",
                "<b>Sensör yanıtı:</b> DOM'un açısal kabulü, zaman çözünürlüğü ve karanlık sayım gürültüsünün; "
                "ayrıca IceCube Upgrade kapsamında geliştirilen çok fotoçoğaltıcılı yeni sensörlerin "
                "modellenmesi."])]


def glossary_story():
    """rapor/uretim/sozluk.md: '## başlık' ve '- **Terim:** tanım' satırlarından sözlük eki üretir."""
    import re
    items = []
    for line in open(f"{HERE}/sozluk.md", encoding="utf-8"):
        line = line.strip()
        if line.startswith("## "):
            items.append(P(line[3:], h2))
        elif line.startswith("- **"):
            items.append(P(re.sub(r"^- \*\*(.+?)\*\*", r"<b>\1</b>", line), gloss))
    return items


def build():
    S = load_stats()
    a, b = S["1TeV"], S["10TeV"]
    T, R, Pm, TH = load_scan()
    C = pd.read_csv(f"{TH}/dedx_check.csv").sort_values("E_TeV")
    bias_old = max(R.reg_bias.abs().max(), R.phys_bias.abs().max())
    f = lambda x, d=0: f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    Etxt = lambda E: f(E, 1) if E < 1 else f(E)
    RUNTIME = {}
    tfile = f"{PROJ}/build/logs/times.txt"
    if os.path.exists(tfile):
        for line in open(tfile):
            name, _, sec = line.partition(":")
            if name.startswith("scan_") and sec.strip():
                m = float(sec.split()[0])/60
                RUNTIME[float(name[5:].replace("TeV", ""))] = f"{f(m)} dk" if m < 90 else f"{f(m/60,1)} sa"
    r1 = T[T.E_TeV == 1].iloc[0]
    ratio = T.dedx_tot/T.groom_tot
    good = T[ratio.sub(1).abs() <= 0.05]
    sp = Pm[Pm.ice == "Rayleigh"].drop_duplicates("spacing").sort_values("spacing")
    mie = Pm[Pm.ice != "Rayleigh"].iloc[0]
    ray = sp[sp.spacing == 6].iloc[0]
    Ecal = R[(R.E_TeV >= 1) & (R.E_TeV < T.E_TeV.max())]
    geo_png = f"{HERE}/geometry.png"
    geometry_figure(geo_png)
    f = lambda x, d=0: f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")

    story = []

    # ============================== KAPAK
    cover = ParagraphStyle("cv", fontName="Serif-B", fontSize=14, leading=20, alignment=TA_CENTER)
    coverS = ParagraphStyle("cvs", fontName="Serif", fontSize=12, leading=18, alignment=TA_CENTER)
    title = ParagraphStyle("tt", fontName="Serif-B", fontSize=20, leading=28, alignment=TA_CENTER,
                           textColor=NAVY)
    story += thesis_front() if THESIS else [Spacer(1, 1.5*cm), P("T.C.", cover), P("ERCİYES ÜNİVERSİTESİ", cover),
              P(DEPARTMENT, coverS), Spacer(1, 3*cm),
              P("GEANT4 MONTE CARLO YÖNTEMİYLE BUZDA TeV ENERJİLİ MÜONLARIN CHERENKOV IŞIMASI, "
                "IceCube TİPİ SENSÖRLERLE ALGILANMASI VE AGN KAYNAK YÖNÜNÜN YENİDEN YAPILANDIRILMASI",
                title),
              Spacer(1, 1.2*cm), P("Proje Raporu", coverS), Spacer(1, 3.2*cm),
              P(f"<b>Hazırlayan:</b> {STUDENT}", coverS),
              P(f"<b>Öğrenci No:</b> {STUDENT_NO}", coverS), Spacer(1, 0.4*cm),
              P(f"<b>Danışman:</b> {ADVISOR}", coverS), Spacer(1, 3*cm),
              P("KAYSERİ", cover), P(DATE, coverS),
              NextPageTemplate("normal"), PageBreak()]

    # ============================== ÖZET
    story += [P("ÖZET", h1),
              P(f"Bu çalışmada, Güney Kutbu'ndaki IceCube Nötrino Gözlemevi'nin basitleştirilmiş bir modeli "
                f"Geant4 (sürüm 11.3.1) Monte Carlo benzetim aracı ile kurulmuş ve bir aktif galaktik çekirdek "
                f"(AGN) yönünden gelen TeV enerjili müonların buzdaki davranışı incelenmiştir. Model; derinliğe "
                f"bağlı soğurma ve saçılma içeren dört katmanlı 20 m × 20 m × 20 m bir buz bloğu ile 3×3 string × "
                f"4 DOM düzeninde 36 optik sensörden oluşmaktadır. Çalışma iki aşamada yürütülmüştür: ilk aşamada "
                f"1 ve 10 TeV müonlar (100'er olay) foton düzeyinde ayrıntılı olarak incelenmiş; ikinci aşamada "
                f"fotoçoğaltıcı kuantum verimi eklenerek {Etxt(T.E_TeV.min())}–{Etxt(T.E_TeV.max())} TeV aralığında "
                f"{len(T)} enerjide toplam {f(T.N.sum())} müon benzetilmiş, ayrıca string aralığı ve buz saçılma "
                f"modeli değiştirilerek bir parametre çalışması yapılmıştır."),
              P(f"1 TeV müonlar ortalama {f(a['L'],1)} m'lik buz yolunda {f(a['eloss_mean'],1)} GeV "
                f"(%{f(a['frac'],2)}) enerji kaybetmiş, olay başına ortalama {f(a['ph'])} Cherenkov fotonu "
                f"üretmiş ve bunların {f(a['hits'])} tanesi sensörlere ulaşmıştır (oran %{f(a['eff'],2)}). "
                f"Birincil müonun ürettiği foton sayısı ({f(a['ph_prim'])} foton, ≈326 foton/cm) Frank-Tamm "
                f"bağıntısının öngörüsüyle %1'in altında bir farkla uyumludur. 10 TeV'de ortalama kayıp "
                f"{f(b['eloss_mean'],1)} GeV'e, foton sayısı {f(b['ph'])}'e çıkmış; artışın kaynağının radyatif "
                f"süreçlerin (özellikle e<super>+</super>e<super>−</super> çift üretimi) başlattığı "
                f"elektromanyetik kaskadlar olduğu gösterilmiştir."),
              P(f"Sensör vuruş zamanlarından LineFit ve Cherenkov zaman-artığı fiti ile müon yönü yeniden "
                f"yapılandırılmıştır. Olay başına medyan açısal hata 1 TeV için {f(a['fit'],2)}°, 10 TeV için "
                f"{f(b['fit'],2)}°'dir. 100 olayın birleştirilmesiyle kaynak yönü 1 TeV'de "
                f"TXS 0506+056 blazarına {f(a['dists']['TXS 0506+056'],2)}°, 10 TeV'de "
                f"{f(b['dists']['TXS 0506+056'],2)}° uzaklıkta bulunmuş ve küçük bir AGN kataloğu içinde doğru "
                f"kaynakla (BL Lac türü blazar) eşleştirilmiştir."),
              P(f"Enerji taramasında müon enerji kaybı PDG/Groom tablolarıyla 1 TeV'e kadar %5 içinde uyumlu "
                f"bulunmuştur. Kuantum verimi sonrası Cherenkov zaman fitinin medyan açısal hatası tüm enerjilerde "
                f"{f(T.fit.min(),1)}–{f(T.fit.max(),1)}° aralığında kalmıştır. String aralığı 8 m'den 4 m'ye "
                f"indirildiğinde algılanan ışık artmış ve açısal hata {f(sp.fit.iloc[-1],2)}°'den "
                f"{f(sp.fit.iloc[0],2)}°'ye düşmüştür. Işık miktarından enerji kestirimi için geliştirilen "
                f"kalibrasyon eğrisi yöntemi sistematik sapmayı belirgin biçimde azaltmış; ancak 20 m'lik iz boyunun enerji "
                f"çözünürlüğünü temelde sınırladığı ve 1 TeV altında ışığın enerjiye neredeyse duyarsız olduğu "
                f"gösterilmiştir."),
              P("<b>Anahtar kelimeler:</b> Geant4, IceCube, müon enerji kaybı, Bethe-Bloch, Cherenkov "
                "ışıması, Frank-Tamm, buz optiği, iz rekonstrüksiyonu, AGN, blazar."),
              PageBreak()]

    if THESIS:
        story += thesis_abstract(a, b, T, sp)

    # ============================== İÇİNDEKİLER
    toc = TableOfContents()
    toc.levelStyles = [ParagraphStyle("t0", fontName="Serif-B", fontSize=10.5, leading=16, leftIndent=0),
                       ParagraphStyle("t1", fontName="Serif", fontSize=10, leading=14, leftIndent=18)]
    toc.dotsMinLevel = 0
    story += [P("İÇİNDEKİLER", ParagraphStyle("tch", parent=h1)), toc, PageBreak()]
    if THESIS:
        story += thesis_lists()

    # ============================== 1. GİRİŞ
    story += thesis_giris() if THESIS else [P("1. GİRİŞ VE AMAÇ", h1),
              P("Yüksek enerjili nötrinolar, evrendeki en güçlü parçacık hızlandırıcılarını incelemek için "
                "benzersiz habercilerdir: elektrik yükleri olmadığı için manyetik alanlarda sapmazlar ve "
                "zayıf etkileştikleri için yol boyunca soğurulmazlar. Bu nedenle bir nötrinonun geliş yönü, "
                "doğrudan kaynağını gösterir. Aynı özellik nötrinoların algılanmasını da son derece zorlaştırır; "
                "bu yüzden kilometreküp ölçeğinde dedektörlere ihtiyaç vardır."),
              P("IceCube Nötrino Gözlemevi, Güney Kutbu'nda 1450–2450 m derinlikler arasına 86 string "
                "üzerinde yerleştirilmiş 5160 optik modülden (DOM) oluşan 1 km³ hacimli bir dedektördür [4]. "
                "Bir müon nötrinosu buzda ya da kayada yüklü akım etkileşmesi yaptığında yüksek enerjili bir "
                "müon üretir. Müon buzda ışıktan (c/n) hızlı hareket ettiği için Cherenkov ışığı yayar; bu ışık "
                "DOM'lardaki fotoçoğaltıcı tüplerle ölçülür ve vuruş zamanlarından müonun – dolayısıyla "
                "nötrinonun – geliş yönü bulunur."),
              P("2017 yılında IceCube-170922A olayının yönünün, o sırada parlama evresinde olan TXS 0506+056 "
                "blazarıyla çakışması, bir AGN'nin yüksek enerjili nötrino kaynağı olabileceğine ilişkin ilk "
                "kanıtı sağlamıştır [1, 2]. 2022'de ise Seyfert galaksisi NGC 1068'den nötrino yayımına dair "
                "kanıt raporlanmıştır [3]. Bu sonuçlar, müon izlerinin yön çözünürlüğünü ve dedektör "
                "verimini anlamanın önemini ortaya koymaktadır."),
              P("Bu projenin amaçları şunlardır:"),
              *bullets([
                  "Geant4 ile IceCube'a benzeyen, derinliğe bağlı optik özelliklere sahip bir buz ve sensör "
                  "geometrisi kurmak,",
                  "1 TeV müonun buzdaki enerji kaybını adım adım kaydederek Bethe-Bloch ve radyatif kayıp "
                  "teorisiyle karşılaştırmak,",
                  "Üretilen Cherenkov fotonlarının sayısını, enerji spektrumunu ve yayılma açısını Frank-Tamm "
                  "teorisiyle sınamak,",
                  "36 sensörün foton algılama verimini ve vuruş zamanı dağılımlarını incelemek,",
                  "Sensör verisinden müon yönünü yeniden yapılandırıp kaynağı bir AGN kataloğuyla eşleştirmek,",
                  "Sonuçları 10 TeV müon ile karşılaştırarak enerjiye bağlı değişimleri yorumlamak."]),
              ]

    # ============================== 2. TEORİ
    story += [CondPageBreak(6*cm), P("2. KURAMSAL ARKA PLAN" if THESIS else "2. TEORİK ARKA PLAN", h1),
              P("2.1 Müonun Madde İçinde Enerji Kaybı", h2),
              P("Yüklü ağır bir parçacık madde içinde ilerlerken atomik elektronlarla etkileşerek enerji "
                "kaybeder. Bu iyonizasyon kaybı Bethe-Bloch bağıntısı ile verilir [6]:"),
              eq(r"-\left\langle\frac{dE}{dx}\right\rangle_{ion} = K z^2 \frac{Z}{A}\frac{1}{\beta^2}"
                 r"\left[\frac{1}{2}\ln\frac{2m_ec^2\beta^2\gamma^2T_{max}}{I^2} - \beta^2 - \frac{\delta(\beta\gamma)}{2}\right]"),
              P("Burada K = 0,307 MeV cm²/mol, Z/A buz için 0,555, I = 75 eV ortalama uyarılma enerjisi, "
                "T<sub>max</sub> tek bir çarpışmada aktarılabilecek en büyük enerji ve δ yoğunluk etkisi "
                "düzeltmesidir. δ için su/buz Sternheimer parametreleri kullanılmıştır [11]. İyonizasyon kaybı "
                "βγ ≈ 3 civarında minimum yapar (≈ 2 MeV cm²/g) ve yüksek enerjilerde yalnızca logaritmik "
                "olarak artar."),
              P("TeV enerjilerde müonun enerji kaybına <i>radyatif</i> süreçler eklenir: frenleme ışıması "
                "(bremsstrahlung), e<super>+</super>e<super>−</super> çift üretimi ve fotonükleer etkileşim. "
                "Bu süreçlerin katkısı enerjiyle doğrusal artar; toplam kayıp genellikle"),
              eq(r"-\frac{dE}{dx} = a(E) + b(E)\,E"),
              P("biçiminde yazılır [7, 14]. Buz için a ≈ 2,7 MeV cm²/g ve b ≈ 3,2×10<super>−6</super> g<super>−1</super> cm² "
                "alınırsa, iki katkının eşitlendiği <i>kritik enerji</i> E<sub>c</sub> = a/b ≈ 0,9 TeV bulunur. "
                "Yani 1 TeV, iyonizasyon ile radyatif kaybın aşağı yukarı eşit olduğu geçiş bölgesindedir; "
                "10 TeV'de ise radyatif kayıp baskındır. Radyatif kayıplar seyrek ama büyük (stokastik) olduğu "
                "için enerji kaybı dağılımı uzun bir kuyruğa sahiptir ve ortalama değer medyandan belirgin "
                "biçimde büyüktür."),

              P("2.2 Cherenkov Işıması ve Frank-Tamm Bağıntısı", h2),
              P("Kırılma indisi n olan bir ortamda yüklü bir parçacığın hızı ortamdaki ışık hızını (c/n) "
                "aştığında, ortamın kutuplanmasıyla oluşan dalga cepheleri bir koni üzerinde yapıcı girişim "
                "yapar ve Cherenkov ışığı yayılır. Işığın parçacık yönüyle yaptığı açı"),
              eq(r"\cos\theta_c = \frac{1}{n\beta}, \qquad \beta > \frac{1}{n}"),
              P("ile verilir. Buz için 400 nm'de n = 1,319 olduğundan β ≈ 1 bir müon için θ<sub>c</sub> ≈ 40,7° "
                "elde edilir. Eşik koşulu müon için yaklaşık 56 MeV, elektron için yaklaşık 0,27 MeV kinetik "
                "enerjiye karşılık gelir; bu nedenle müonun ürettiği ikincil elektronlar da Cherenkov ışığı "
                "yayar. Birim yol ve birim foton enerjisi başına üretilen foton sayısı Frank-Tamm bağıntısıyla "
                "verilir [6, 10]:"),
              eq(r"\frac{d^2N}{dx\,dE} = \frac{\alpha}{\hbar c}\sin^2\theta_c "
                 r"\approx 370\left(1-\frac{1}{\beta^2n^2(E)}\right)\ \mathrm{eV^{-1}\,cm^{-1}}"),
              P("Bu bağıntı, n sabit kabul edildiğinde foton sayısının foton <i>enerjisine bağlı olmadığını</i> "
                "(düz spektrum) gösterir; dalga boyu cinsinden ise dN/dλ ∝ 1/λ² olur, yani mavi/morötesi "
                "fotonlar çoğunluktadır. 300–600 nm aralığında integral alındığında buz için yaklaşık "
                "326 foton/cm elde edilir. Cherenkov ışıması müonun toplam enerji kaybına çok küçük bir "
                "katkı yapar (≈ keV/cm)."),

              P("2.3 Buzda Işığın Yayılması", h2),
              P("<b>Dispersiyon:</b> Buzun kırılma indisi dalga boyuna bağlıdır. Çalışmada Price ve Bergström'ün [8] "
                "kullandığı parametrizasyon alınmıştır (λ mikron cinsinden):"),
              eq(r"n(\lambda) = 1.55749 - 1.57988\lambda + 3.99993\lambda^2 - 4.68271\lambda^3 + 2.09354\lambda^4"),
              P("Işık sinyali faz hızıyla değil grup hızıyla ilerler. Grup indisi n<sub>g</sub> = n − λ dn/dλ "
                "ile hesaplanır; 400 nm'de n<sub>g</sub> = 1,356'dır. Dolayısıyla farklı renkteki fotonlar "
                "sensörlere farklı zamanlarda ulaşır; bu, vuruş zamanı dağılımının genişlemesine katkıda bulunur."),
              P("<b>Soğurma:</b> Derin buzda soğurma iki bileşenden oluşur: buzun içindeki toz parçacıklarına bağlı ve "
                "dalga boyuyla yavaşça azalan bir terim ile kızılötesine doğru hızla artan buzun kendi soğurması [9]:"),
              eq(r"\frac{1}{\lambda_{abs}} = \frac{1}{\lambda_{toz}(400)}\left(\frac{\lambda}{400\,\mathrm{nm}}\right)^{-1.08}"
                 r" + A\,e^{-\lambda_0/\lambda}, \quad A = 6954\ \mathrm{m^{-1}},\ \lambda_0 = 6700\ \mathrm{nm}"),
              P("Toz yoğunluğu buzun oluştuğu iklim dönemine bağlı olduğu için soğurma derinlikle değişir; "
                "IceCube'da ≈ 2000 m civarındaki 'toz katmanı' bunun en belirgin örneğidir."),
              P("<b>Saçılma:</b> Bu çalışmada saçılma, dalga boyunun dördüncü kuvvetiyle değişen Rayleigh "
                "saçılması olarak modellenmiştir:"),
              eq(r"\lambda_R(\lambda) = \lambda_R(400)\left(\frac{\lambda}{400\,\mathrm{nm}}\right)^{4}"),
              P("Bu nedenle kısa dalga boylu (mavi) ışık daha çok saçılır. Gerçek buzda baskın saçılma ileri "
                "yönlü Mie saçılmasıdır; bu basitleştirme Bölüm 5'te tartışılmıştır."),

              P("2.4 Aktif Galaktik Çekirdekler ve Blazarlar", h2),
              P("AGN'ler, merkezlerindeki süper kütleli kara deliğe madde aktarımıyla beslenen ve tüm "
                "elektromanyetik tayfta çok parlak olan galaksi çekirdekleridir. Göreli jetlerinden biri "
                "doğrudan Dünya'ya yönelmiş olan AGN'lere <i>blazar</i> denir. Blazarlar iki alt sınıfa ayrılır [12]: "
                "geniş salma çizgileri zayıf veya hiç olmayan <b>BL Lac</b> nesneleri ve güçlü geniş salma "
                "çizgilerine sahip <b>düz tayflı radyo kuasarları (FSRQ)</b>. Jetlerde hızlandırılan "
                "protonların foton veya madde ile etkileşmesi (pγ, pp) yüklü pionlar ve onların bozunmasıyla "
                "nötrinolar üretebilir. Bu nedenle blazarlar en güçlü nötrino kaynağı adaylarındandır."),
              ]

    # ============================== 3. YÖNTEM
    story += [PageBreak(), P("3. YÖNTEM: GEANT4 SİMÜLASYONU", h1),
              P("3.1 Programın Yapısı", h2),
              P("Geant4, parçacıkların madde içinden geçişini Monte Carlo yöntemiyle benzeten C++ tabanlı bir "
                "araç takımıdır [5]. Kullanıcı; geometriyi, fizik listesini ve birincil parçacık üretecini "
                "zorunlu olarak tanımlar, isteğe bağlı 'kullanıcı eylemleri' (user actions) ile de "
                "benzetimin her aşamasına müdahale edebilir. Programımızın sınıfları Tablo 1'de özetlenmiştir. "
                "Program çok iş parçacıklı (multi-threaded) çalışır; her iş parçacığı kendi CSV parça dosyasını "
                "yazar ve koşu sonunda ana iş parçacığı bunları tek dosyada birleştirir."),
              table([["Sınıf / dosya", "Görevi"],
                     ["sim.cc", "Run manager'ı oluşturur; QBBC fizik listesine G4OpticalPhysics ekler; makroyu çalıştırır."],
                     ["DetectorConstruction", "Buz katmanlarını, optik özellik tablolarını ve 36 DOM'u kurar; DOM'ları hassas dedektör yapar."],
                     ["PrimaryGeneratorAction", "AGN'nin (RA, Dec) koordinatından müon yönünü hesaplar, açısal sapma ve iz kayması ekler."],
                     ["SensorSD", "DOM'a dışarıdan giren optik fotonu 'hit' olarak kaydeder ve yok eder."],
                     ["StackingAction", "Üretilen her Cherenkov fotonunu (konum, yön, enerji, zaman) yakalar."],
                     ["SteppingAction", "Birincil müonun buzdaki her adımında enerji kaybını kaydeder."],
                     ["EventAction / RunAction", "Olay sayaçlarını yönetir, CSV dosyalarını açar/kapatır/birleştirir."],
                     ["Config", "/icecube/... makro komutlarıyla değiştirilebilen ayarlar (enerji, kaynak, çıktı adı)."],
                     ["OutputManager", "İş parçacığına özel CSV yazıcı ve olay başı sayaçlar."],
                     ["analysis/*.py", "Python ile analiz, rekonstrüksiyon ve grafikler (pandas, SciPy, matplotlib)."]],
                    [4.4, 12.0], "Simülasyon programını oluşturan sınıflar ve görevleri."),

              P("3.2 Dedektör Geometrisi", h2),
              P("Benzetim hacmi 30 m kenarlı vakum bir dünya kutusudur. Bunun içine 20 m kenarlı bir buz bloğu "
                "yerleştirilmiş ve blok düşey doğrultuda 5'er m kalınlığında dört katmana ayrılmıştır. Her "
                "katman ayrı bir malzemedir (aynı kırılma indisi, farklı soğurma ve saçılma uzunlukları); "
                "böylece derinliğe bağlı optik özellikler modellenmiştir. Kırılma indisleri aynı olduğu için "
                "katman sınırlarında yansıma veya kırılma oluşmaz. Buzdan dışarı çıkan fotonlar vakumda kırılma "
                "indisi tanımlı olmadığından soğurulur, yani 'kaçmış' sayılır."),
              P("Sensörler 6 m aralıklı 3×3 string üzerine, her stringde her katmanın ortasına bir tane olmak üzere "
                "4 DOM şeklinde yerleştirilmiştir (toplam 36 DOM). Her DOM, gerçek IceCube DOM'u ile aynı "
                "boyutta (33 cm çap) Pyrex camdan bir küredir. Cama n = 1,48 kırılma indisi verilerek fotonların "
                "buzdan cama geçmesi (Fresnel yansıma/kırılmasıyla birlikte) sağlanmıştır. Geometri Şekil 1'de, "
                "parametreler Tablo 2 ve 3'te verilmiştir. Geant4'ün çakışma (overlap) kontrolü tüm hacimler "
                "için başarılı olmuştur."),
              figure(geo_png, 16.4, "Dedektör geometrisi. (a) Üstten görünüm: 9 string (S0–S8), buz bloğu ve "
                     "1 TeV koşusunun ilk 15 müon izinin izdüşümü. (b) Yandan görünüm: dört buz katmanı, "
                     "400 nm'deki soğurma (λ<sub>abs</sub>) ve Rayleigh (λ<sub>R</sub>) uzunlukları ile DOM konumları. "
                     "Koyu renk, daha kısa soğurma uzunluğunu (daha tozlu buz) gösterir.",
                     comment=(f"(a)'da tüm izler dedektöre +y kenarından girip −y yönünde ilerler ve merkeze en fazla 3 m uzaklıktan "
                 f"geçer; izlerin paralel olması hepsinin aynı kaynaktan (TXS 0506+056) geldiğini gösterir. (b)'de en koyu "
                 f"katman toz katmanıdır (katman 2), en derindeki katman 0 ise en berrak buzdur. Her stringde her "
                 f"katmanın ortasında bir DOM bulunduğu için her katmanın ışığı ayrı ayrı örneklenir.")),
              table([["Parametre", "Değer"],
                     ["Dünya hacmi", "30 m × 30 m × 30 m, G4_Galactic (vakum)"],
                     ["Buz bloğu", "20 m × 20 m × 20 m, H<sub>2</sub>O, ρ = 0,917 g/cm³"],
                     ["Buz katmanı sayısı / kalınlığı", "4 / 5 m"],
                     ["Nominal derinlik aralığı", "2000 – 2020 m"],
                     ["String düzeni / aralığı", "3 × 3 / 6 m"],
                     ["String başına DOM / düşey aralık", "4 / 5 m"],
                     ["DOM", "Küre, r = 16,51 cm, G4_Pyrex_Glass, n = 1,48"],
                     ["Optik dalga boyu aralığı", "300 – 600 nm (2,07 – 4,13 eV), 61 noktalı tablo"]],
                    [6.5, 9.9], "Geometri parametreleri."),
              table([["Katman", "Derinlik (m)", "z aralığı (m)", "λ<sub>abs</sub>(400 nm) (m)", "λ<sub>R</sub>(400 nm) (m)", "Yorum"],
                     ["3", "2002,5", "+5 … +10", "87", "28", "üst katman"],
                     ["2", "2007,5", "0 … +5", "44", "12", "toz katmanı"],
                     ["1", "2012,5", "−5 … 0", "106", "35", "temiz buz"],
                     ["0", "2017,5", "−10 … −5", "142", "45", "en temiz buz"]],
                    [1.5, 2.2, 2.4, 3.2, 3.0, 4.1],
                    "Buz katmanlarının 400 nm'deki optik parametreleri (soğurma uzunluğu, toz ve buz bileşenlerinin "
                    "toplamıdır).", align_center_cols=(0, 1, 2, 3, 4)),
              P("Katmanların soğurma ve saçılma değerleri, IceCube buzunun genel davranışını (yüz metre "
                "mertebesinde soğurma, onlarca metre saçılma, belirgin bir toz katmanı) yansıtacak biçimde "
                "seçilmiş <i>temsili</i> değerlerdir; ölçülmüş bir buz modelinin birebir aktarımı değildir."),

              P("3.3 Fizik Listesi", h2),
              P("Hadronik ve elektromanyetik süreçler için Geant4'ün hazır <b>QBBC</b> fizik listesi kullanılmıştır. "
                "Bu liste müonlar için iyonizasyon (muIoni), bremsstrahlung (muBrems), çift üretimi "
                "(muPairProd), fotonükleer etkileşim (muonNuclear) ve çoklu saçılmayı içerir. Listeye "
                "<b>G4OpticalPhysics</b> eklenerek Cherenkov ışıması, optik soğurma (OpAbsorption), Rayleigh "
                "saçılması (OpRayleigh) ve ortam sınırı süreçleri (OpBoundary) etkinleştirilmiştir. Buz "
                "sintilasyon yapmadığı için sintilasyon ve dalga boyu kaydırma süreçleri kapatılmıştır. İleri yönlü "
                "Mie saçılması (OpMieHG, g = 0,9) da tanımlanmıştır ve Rayleigh yerine makro komutuyla seçilebilir "
                "(Bölüm 3.8). Cherenkov "
                "süreci için adım başına en fazla 500 foton üretilmesine izin verilmiştir; bu, müon adım boyunu "
                "yaklaşık 1,5 cm ile sınırlar ve fotonların iz boyunca düzgün dağılmasını sağlar."),

              P("3.4 Birincil Parçacık ve Kaynak Yönü", h2),
              P("Her olayda tek bir μ<super>−</super> üretilmiştir. Müonun yönü, seçilen AGN'nin ekvator koordinatlarından "
                "(sağ açıklık α, dik açıklık δ) hesaplanır. Güney Kutbu'nda yerel zenit gök küresinin güney "
                "kutbuna denk geldiği için bir kaynağın ufuk üzerindeki yüksekliği h = −δ'dır. Yerel yıldız "
                "zamanı sıfır kabul edilerek azimut A = α alınmıştır:"),
              eq(r"\hat{s} = (\cos h\cos A,\ \cos h\sin A,\ \sin h),\quad h=-\delta,\ A=\alpha,\quad \hat{d}_\mu = -\hat{s}"),
              P("Kaynak olarak TXS 0506+056 (α = 77,358°, δ = +5,693°) seçilmiştir. δ > 0 olduğu için kaynak "
                "ufkun altındadır ve müon Dünya'nın içinden geçerek aşağıdan yukarı (upgoing) gelir; IceCube'un "
                "kuzey gökyüzünü bu tür olaylarla gözlemesiyle tutarlıdır. Nötrino–müon arasındaki kinematik "
                "açıyı temsil etmek için yöne σ = 0,5°'lik iki boyutlu Gauss sapması eklenmiştir. Ayrıca iz, "
                "dedektör merkezinden yöne dik 3 m yarıçaplı bir disk içinde rastgele kaydırılmıştır. Müon, "
                "buz bloğunun dışında, merkezden 14 m geride başlatılır."),

              P("3.5 Veri Kaydı", h2),
              P("Benzetim sırasında kaydedilen bilgiler ve oluşturulan dosyalar Tablo 4'te verilmiştir. Bir 1 TeV "
                "müon olay başına 10<super>6</super> mertebesinde foton ürettiği için fotonlar tek tek yalnızca "
                "ilk olay için yazılmış, tüm olayların foton sayıları ise olay özet dosyasında tutulmuştur."),
              table([["Dosya", "İçerik (her satır)", "1 TeV satır", "Boyut"],
                     ["cherenkov_photons.csv", "olay, ana iz no, x, y, z, yön (p<sub>x</sub>, p<sub>y</sub>, p<sub>z</sub>), enerji (eV), dalga boyu (nm), zaman (ns)", "1.166.315", "86 MB"],
                     ["muon_energy_loss.csv", "olay, adım, konum, E<sub>önce</sub>, E<sub>sonra</sub>, ΔE, depolanan enerji, adım boyu, süreç", "166.239", "15 MB"],
                     ["sensor_hits.csv", "olay, sensör/string/DOM no, giriş noktası, enerji, dalga boyu, zaman, ana iz no", "671.912", "45 MB"],
                     ["events.csv", "olay başına E<sub>0</sub>, E<sub>çıkış</sub>, kayıp, iz boyu, foton ve hit sayıları, başlangıç noktası, yön", "100", "16 kB"],
                     ["sensors.csv, ice_properties.csv", "sensör konumları; katman ve dalga boyuna göre n, λ<sub>abs</sub>, λ<sub>R</sub>", "36 / 244", "16 kB"]],
                    [4.1, 8.0, 2.2, 2.1], "Simülasyonun ürettiği CSV dosyaları (1 TeV koşusu).",
                    align_center_cols=(2, 3)),

              P("3.6 İz Rekonstrüksiyonu", h2),
              P("Müon yönü, her olayda sensörlerdeki ilk vuruş zamanları t<sub>i</sub>, sensör konumları "
                "<b>r</b><sub>i</sub> ve vuruş sayıları q<sub>i</sub> kullanılarak iki aşamada bulunmuştur. "
                "İlk aşamada IceCube'un hızlı ön tahmin yöntemi olan <b>LineFit</b> [13] uygulanmıştır. Bu yöntem, "
                "ışığın düzlem bir dalga gibi bir hızla ilerlediğini varsayarak <b>r</b>(t) = <b>r</b><sub>0</sub> + <b>v</b>t "
                "doğrusunu en küçük kareler yöntemiyle uydurur:"),
              eq(r"\vec{v} = \frac{\sum_i w_i(\vec{r}_i-\bar{r})(t_i-\bar{t})}{\sum_i w_i (t_i-\bar{t})^2},\qquad w_i=\sqrt{q_i}"),
              P("İkinci aşamada Cherenkov konisinin geometrisi kullanılır. Müon izinden dik uzaklığı ρ, iz "
                "boyunca konumu l olan bir sensöre doğrudan (saçılmamış) bir fotonun beklenen varış zamanı"),
              eq(r"t_{exp} = t_0 + \frac{1}{c}\left(l - \frac{\rho}{\tan\theta_c}\right) + \frac{n_g}{c}\,\frac{\rho}{\sin\theta_c}"),
              P("ile verilir. Beş parametre (yön için θ, φ; ize dik iki kayma; t<sub>0</sub>) Nelder-Mead "
                "yöntemiyle aşağıdaki maliyet fonksiyonunu en küçükleyecek biçimde bulunmuştur. Saçılmış fotonlar "
                "geç geldiği için kare yerine uç değerlere dayanıklı (Cauchy tipi) bir fonksiyon seçilmiştir "
                "(σ = 10 ns):"),
              eq(r"C = \sum_i \sqrt{q_i}\,\ln\left[1+\left(\frac{t_i - t_{exp,i}}{\sigma}\right)^2\right]"),
              P("Bulunan müon yönü −<b>d</b> kaynak yönüne, oradan da Bölüm 3.4'teki dönüşümün tersiyle (α, δ) "
                "koordinatlarına çevrilmiştir. Tüm olayların kaynak yönleri ortalanarak (3 medyandan uzak "
                "aykırı olaylar atılarak) birleşik bir kaynak konumu ve %90 kapsama yarıçapının √N'e "
                "bölünmesiyle yaklaşık bir hata yarıçapı hesaplanmıştır. Bu konum, 7 kaynaklık küçük bir AGN "
                "kataloğuyla karşılaştırılmıştır (Tablo 8)."),

              CondPageBreak(5*cm), P("3.7 Koşu Koşulları (Birinci Aşama)", h2),
              P("Birinci aşamada her enerji için 100 olay benzetilmiştir. Koşular AMD Ryzen 5 5500U (6 çekirdek / 12 iş "
                "parçacığı) işlemcili bir dizüstü bilgisayarda 12 iş parçacığıyla yapılmış; 1 TeV koşusu "
                "2 dk 15 s, 10 TeV koşusu 10 dk 6 s sürmüştür. Analiz Python 3 (pandas, NumPy, SciPy, "
                "matplotlib) ile yapılmıştır. Kullanılan makro komutlarına bir örnek:"),
              Preformatted("/icecube/particle   mu-\n/icecube/energy     1 TeV\n"
                           "/icecube/sourceRA   77.358 deg      # TXS 0506+056\n"
                           "/icecube/sourceDec  5.693 deg\n/icecube/angularSpread 0.5 deg\n"
                           "/icecube/offsetRadius  3 m\n/icecube/prefix     data/1TeV\n"
                           "/icecube/photonSaveEvents 1\n/run/beamOn 100", code),

              CondPageBreak(8*cm), P("3.8 İkinci Aşama: Enerji Taraması ve Parametre Çalışması", h2),
              P("İkinci aşamada programa üç özellik eklenmiştir. (1) <b>Kuantum verimi:</b> DOM'a giren her foton, "
                "dalga boyuna bağlı temsili bir fotoçoğaltıcı verimiyle (en yüksek ≈ %26, 380 nm) rastgele "
                "'algılandı' olarak işaretlenir; böylece DOM'a ulaşan ve algılanan foton sayıları ayrı ayrı "
                "kaydedilir. (2) <b>Sensör özeti:</b> Yüksek enerjide dosya boyutunu sınırlamak için her olayda her "
                "DOM'un algıladığı foton sayısı ve ilk sinyal zamanı tek satırda saklanır. (3) <b>Ayarlanabilir "
                "geometri ve buz:</b> String aralığı (/icecube/stringSpacing) ve saçılma modeli (/process/inactivate "
                "OpMieHG veya OpRayleigh) makrodan seçilir. Mie modelinde etkin saçılma uzunluğu Rayleigh "
                "modelindekine eşit tutulmuş, dalga boyu bağımlılığı λ<super>0,9</super> alınmıştır."),
              P("<b>Fizik tablolarının enerji sınırı.</b> Geant4'ün elektromanyetik süreç tabloları varsayılan "
                "olarak yalnızca 100 TeV'e kadar hesaplanır. İlk 100 TeV koşusunda müon tam bu sınırda başladığı için "
                "radyatif kayıplar belirgin biçimde eksik çıkmış (Groom değerinin ≈ %23'ü), ışık miktarı 30 TeV'in "
                "bile altında kalmıştır. Bu nedenle tablolar G4EmParameters::SetMaxEnergy ile 10 PeV'e genişletilmiş "
                "ve 100 TeV koşusu yeniden yapılmıştır; 100 TeV altındaki tablo değerleri bu değişiklikten "
                "etkilenmez. Ayrıca enerji kaybını büyük istatistikle doğrulamak için Cherenkov ışıması kapatılarak "
                "30 ve 100 TeV'de 4000'er olaylık ek koşular yapılmıştır."),
              table([["Enerji (TeV)", "Olay sayısı", "Koşu süresi"]] +
                    [[Etxt(r.E_TeV), f(r.N), RUNTIME.get(r.E_TeV, "–")] for _, r in T.iterrows()],
                    [4.0, 4.0, 4.0], "Enerji taraması koşuları (12 iş parçacığı). Yüksek enerjide kaskadların "
                    "ürettiği çok sayıda optik fotonun izlenmesi süreyi hızla artırdığı için olay sayısı azaltılmıştır.",
                    align_center_cols=(0, 1, 2)),
              P("Parametre çalışmasında 1 TeV'de 300'er olay ile string aralığı 4, 6 ve 8 m; 6 m aralıkta buz "
                "modeli Rayleigh ve Mie olarak değiştirilmiştir. Tüm yön sonuçları algılanan fotonlarla (kuantum "
                "verimi sonrası) elde edilmiş; medyan hataların belirsizliği 2000 tekrarlı bootstrap ile %68 güven "
                "aralığı olarak verilmiştir."),
              P("<b>Enerji rekonstrüksiyonu.</b> Müon enerjisi, olayda algılanan ışık miktarından kestirilmiştir. "
                "Tek bir büyük kaskadın etkisini azaltmak için her olayda en parlak %20 DOM atılarak <i>kesilmiş "
                "ışık</i> hesaplanmıştır (IceCube'un 'truncated energy' yaklaşımı). Olaylar eğitim (çift numaralı) "
                "ve test (tek numaralı) olarak ikiye ayrılmış; eğitim olaylarında her enerjideki kesilmiş ışığın "
                "medyanı bir kalibrasyon eğrisi oluşturmuş, test olaylarının enerjisi bu eğrinin tersinden "
                "bulunmuştur. Sonuç, basit bir log–log regresyonu ve ortalama Groom eğrisinin tersine çevrilmesiyle "
                "karşılaştırılmıştır. Başarım, log<sub>10</sub>(E<sub>reko</sub>/E<sub>gerçek</sub>) dağılımının "
                "medyanı (sapma) ve %16–%84 yarı genişliği (σ, çözünürlük) ile ölçülmüştür."),
              ]

    # ============================== 4. BULGULAR
    pa, pb = a["proc"], b["proc"]
    pr = lambda p, k: f"%{f(100*p.get(k, 0), 1)}"
    story += [PageBreak(), P("4. BULGULAR", h1),
              P("4.1 Genel Sonuçlar", h2),
              P("Bulgular iki aşamada sunulmaktadır. Bölüm 4.1–4.7, birinci aşamadaki 1 ve 10 TeV koşularının "
                "foton düzeyindeki ayrıntılı analizidir; bu koşularda kuantum verimi uygulanmadığı için 'hit' "
                "sayıları DOM yüzeyine ulaşan fotonlardır. Bölüm 4.8–4.12 ikinci aşamanın (enerji taraması ve "
                "parametre çalışması, kuantum verimi dahil) sonuçlarını verir. Birinci aşamanın özet sonuçları "
                "Tablo 6'dadır."),
              table([["Büyüklük", "1 TeV", "10 TeV"],
                     ["Olay sayısı", "100", "100"],
                     ["Buzdaki ortalama iz uzunluğu", f"{f(a['L'],2)} m", f"{f(b['L'],2)} m"],
                     ["Enerji kaybı: ortalama", f"{f(a['eloss_mean'],2)} GeV (%{f(a['frac'],2)})", f"{f(b['eloss_mean'],2)} GeV (%{f(b['frac'],2)})"],
                     ["Enerji kaybı: medyan", f"{f(a['eloss_med'],2)} GeV", f"{f(b['eloss_med'],2)} GeV"],
                     ["Enerji kaybı: en küçük – en büyük", f"{f(a['eloss_min'],1)} – {f(a['eloss_max'],1)} GeV", f"{f(b['eloss_min'],1)} – {f(b['eloss_max'],1)} GeV"],
                     ["Ortalama ⟨dE/dx⟩ (simülasyon)", f"{f(a['dedx_mean'],2)} MeV/cm", f"{f(b['dedx_mean'],2)} MeV/cm"],
                     ["Cherenkov foton / olay (ortalama)", f(a['ph']), f(b['ph'])],
                     ["  – birincil müondan", f"{f(a['ph_prim'])} (%{f(a['prim_frac'],1)})", f"{f(b['ph_prim'])} (%{f(b['prim_frac'],1)})"],
                     ["Sensör hit / olay (ortalama / medyan)", f"{f(a['hits'])} / {f(a['hits_med'])}", f"{f(b['hits'])} / {f(b['hits_med'])}"],
                     ["Algılama verimi η = N<sub>hit</sub>/N<sub>γ</sub>", f"%{f(a['eff'],3)}", f"%{f(b['eff'],3)}"],
                     ["Medyan açısal hata (LineFit / Cherenkov fit)", f"{f(a['lf'],1)}° / {f(a['fit'],2)}°", f"{f(b['lf'],1)}° / {f(b['fit'],2)}°"],
                     ["Birleşik kaynak (α, δ)", f"({f(a['src'][0],2)}°, {f(a['src'][1],2)}°) ± {f(a['src'][2],2)}°", f"({f(b['src'][0],2)}°, {f(b['src'][1],2)}°) ± {f(b['src'][2],2)}°"],
                     ["TXS 0506+056'ya uzaklık", f"{f(a['dists']['TXS 0506+056'],2)}°", f"{f(b['dists']['TXS 0506+056'],2)}°"]],
                    [7.2, 4.6, 4.6], "1 TeV ve 10 TeV koşularının özet sonuçları.", align_center_cols=(1, 2)),

              P("4.2 Enerji Kaybı Analizi", h2),
              P(f"1 TeV müon, ≈ 20,6 m'lik buz yolunda ortalama {f(a['eloss_mean'],2)} GeV, yani başlangıç "
                f"enerjisinin yalnızca %{f(a['frac'],2)}'ini kaybetmiştir; müon dedektörü neredeyse enerjisini "
                f"değiştirmeden geçer. Olaylar arası dağılım çok asimetriktir: medyan kayıp {f(a['eloss_med'],2)} GeV "
                f"iken en büyük kayıp {f(a['eloss_max'],1)} GeV'tir. Medyan değer yalnızca iyonizasyondan beklenen "
                f"kayba (≈ 2,7 MeV/cm × 2059 cm ≈ 5,5 GeV) çok yakındır; ortalamayı yukarı çeken, az sayıdaki "
                f"olayda görülen büyük radyatif kayıplardır."),
              P(f"Kayıpların süreçlere göre dağılımı Tablo 7'de verilmiştir. Geant4'te bir adımı Cherenkov süreci "
                f"sonlandırdığında bile o adım boyunca sürekli iyonizasyon kaybı uygulanır; bu nedenle "
                f"'Cerenkov' ve 'muIoni' satırlarının toplamı iyonizasyon kaybını temsil eder. 1 TeV'de "
                f"iyonizasyon ve çift üretimi hemen hemen eşit paya sahiptir; bu, 1 TeV'in kritik enerjiye yakın "
                f"olmasıyla uyumludur. 10 TeV'de ise kaybın %{f(100*(pb.get('muPairProd',0)+pb.get('muBrems',0)+pb.get('muonNuclear',0)),0)}'i "
                f"radyatif süreçlerden gelmektedir."),
              table([["Adımı sonlandıran süreç", "1 TeV payı", "10 TeV payı", "Fiziksel anlamı"],
                     ["muIoni + Cerenkov", pr(pa, 'muIoni') + " + " + pr(pa, 'Cerenkov'), pr(pb, 'muIoni') + " + " + pr(pb, 'Cerenkov'), "Sürekli iyonizasyon ve δ-elektron üretimi"],
                     ["muPairProd", pr(pa, 'muPairProd'), pr(pb, 'muPairProd'), "e<super>+</super>e<super>−</super> çift üretimi"],
                     ["muBrems", pr(pa, 'muBrems'), pr(pb, 'muBrems'), "Frenleme ışıması"],
                     ["muonNuclear", pr(pa, 'muonNuclear'), pr(pb, 'muonNuclear'), "Fotonükleer etkileşim"]],
                    [4.0, 3.3, 3.3, 5.8], "Birincil müonun enerji kaybının süreçlere göre dağılımı.",
                    align_center_cols=(1, 2)),
              P(f"Şekil 2(a)'da teorik Bethe-Bloch + radyatif kayıp eğrisi ile simülasyondan bulunan ortalama "
                f"⟨dE/dx⟩ = {f(a['dedx_mean'],2)} MeV/cm karşılaştırılmıştır. Teori 1 TeV için ≈ 5,6 MeV/cm "
                f"öngörmektedir. Simülasyon değerinin daha düşük olmasının nedeni, radyatif kayıpların büyük "
                f"kısmının nadir fakat çok büyük olaylardan gelmesi ve 20 m'lik yolda 100 olayla bu kuyruğun "
                f"yeterince örneklenmemesidir. Şekil 2(b)'deki adım başına dE/dx dağılımı, iyonizasyonun "
                f"≈ 2 MeV/cm civarında dar bir tepe, çift üretiminin ise 10<super>5</super> MeV/cm'ye kadar uzanan "
                f"geniş bir kuyruk oluşturduğunu açıkça göstermektedir."),

              CondPageBreak(9*cm), P("4.3 Cherenkov Foton Analizi", h2),
              P(f"1 TeV'de olay başına ortalama {f(a['ph'])} Cherenkov fotonu üretilmiştir. Bunların "
                f"{f(a['ph_prim'])} tanesi (%{f(a['prim_frac'],1)}) doğrudan birincil müondan, geri kalanı müonun "
                f"ürettiği ikincil elektron ve pozitronlardan (δ-elektronları ve kaskadlar) gelmektedir. Birincil "
                f"müonun foton sayısı olaydan olaya neredeyse hiç değişmez (yaklaşık 670.900), çünkü Cherenkov "
                f"verimi β ≈ 1 için sabittir ve iz uzunlukları benzerdir. Bu, metre başına ≈ 32.600, santimetre "
                f"başına ≈ 326 foton demektir."),
              P("Şekil 2(c)'de birincil müon fotonlarının dN/dx dE spektrumu Frank-Tamm öngörüsü "
                "370(1 − 1/n²) ile karşılaştırılmıştır. Simülasyon ile teori tüm enerji aralığında uyumludur; "
                "spektrum enerjiye göre yaklaşık düzdür ve yalnızca n'nin enerjiyle hafifçe artmasından dolayı "
                "yüksek enerjilere doğru küçük bir eğim gösterir. Fotonların müon yönüyle yaptığı açının dağılımı "
                "(Şekil 2(e)) 40,2°–41,4° aralığında, yani 300–600 nm için cos θ<sub>c</sub> = 1/n bağıntısının "
                "öngördüğü aralıkta toplanmıştır. Bu iki sonuç, Cherenkov üretiminin ve buzun dispersiyonunun "
                "simülasyonda doğru tanımlandığını göstermektedir."),
              P("Şekil 3'ün 1. panelinde ilk olaydaki fotonların üretim noktaları görülmektedir. Fotonlar müon "
                "izi boyunca dar bir çizgi üzerinde üretilmiştir; izin bir noktasında görülen saçılmış küme, "
                "bir elektromanyetik kaskadın oluşturduğu ek ışığa karşılık gelir."),
              figure(f"{DATA}/1TeV_physics.png", 11.0,
                     "1 TeV koşusunun fiziksel yorum grafikleri: (a) teorik Bethe-Bloch ve radyatif kayıp eğrisi ile "
                     "simülasyon ortalaması; (b) süreçlere göre adım başına enerji kaybı; (c) Frank-Tamm "
                     "karşılaştırması; (d) faz ve grup kırılma indisi ile Cherenkov açısı; (e) ölçülen foton–müon "
                     "açısı; (f) katmanlara göre Rayleigh saçılma uzunluğu; (g) derinliğe bağlı soğurma ve "
                     "saçılma uzunlukları ile DOM başına hit sayısı; (h) olay başına foton ve hit sayısının "
                     "enerji kaybıyla ilişkisi.",
                     comment=(f"(a) 1 TeV simülasyon noktası ({f(a['dedx_mean'],2)} MeV/cm) toplam kayıp eğrisinin biraz altındadır; bu enerji "
                 f"iyonizasyon ve radyatif eğrilerin kesiştiği kritik enerji bölgesidir. (b) İyonizasyon adımları ≈ 2 MeV/cm'de "
                 f"dar bir tepe yapar, çift üretimi ise 10<super>5</super> MeV/cm'ye uzanan geniş bir kuyruk oluşturur. (c) Simülasyon "
                 f"basamakları Frank-Tamm eğrisinin üzerindedir ve enerjiyle yaklaşık düzdür. (d) Kırılma indisi mavide "
                 f"büyüktür; Cherenkov açısı 300 nm'de 41,4°'den 600 nm'de 40,2°'ye iner. (e) Ölçülen foton açıları beklenen "
                 f"40,2–41,4° bandının içindedir. (f) Saçılma uzunluğu dalga boyuyla hızla artar; en kısa değer toz katmanındadır. "
                 f"(g) En çok hit, müon izinin geçtiği orta derinlikteki DOM'larda görülür. (h) Foton ve hit sayıları buzda "
                 f"kaybedilen enerjiyle birlikte artar.")),

              CondPageBreak(5*cm), P("4.4 Buz Optiği: Dispersiyon, Saçılma ve Soğurma", h2),
              P("Şekil 2(d), faz indisinin 300 nm'de 1,334'ten 600 nm'de 1,310'a düştüğünü göstermektedir "
                "(analiz planında kullanılan n ≈ 1,325 değeri bu aralığın ortasındadır). Grup indisi faz "
                "indisinden yaklaşık 0,02–0,07 büyüktür. Bu yüzden 20 m yol alan mavi ve kırmızı fotonlar "
                "arasında birkaç nanosaniyelik varış farkı oluşur."),
              P("Rayleigh saçılma uzunluğu λ<super>4</super> ile arttığı için 300 nm'de 4–14 m iken 600 nm'de "
                "60–230 m'ye çıkar (Şekil 2(f)). Algılanan fotonların enerji spektrumunun (Şekil 3, panel 2) "
                "üretilen spektruma göre mavi tarafa kaymış olması ilk bakışta saçılmayla çelişiyormuş gibi "
                "görünebilir. Ancak burada belirleyici etken soğurmadır: buzun kendi soğurması nedeniyle 550 nm'de "
                "fotonların soğurma uzunluğu 20–25 m'ye, 600 nm'de ise ≈ 10 m'ye düşer ve bu fotonlar sensörlere ulaşamadan "
                "kaybolur. Saçılma ise fotonları yok etmez, yalnızca geciktirir ve yönlerini değiştirir."),
              P("Derinliğe bağlı soğurmanın etkisi DOM başına hit sayılarında görülmektedir (Şekil 2(g)): "
                "katman 1 ve 2'deki DOM'lar, müon izleri bu katmanlardan geçtiği için en çok hit almıştır. Toz "
                "katmanı olan katman 2'deki DOM'lar, ize benzer uzaklıkta olmalarına rağmen katman 1'e göre "
                "biraz daha az ışık toplamıştır. Bu katmandaki kısa saçılma uzunluğu ayrıca vuruş zamanı "
                "dağılımını genişletmektedir."),

              P("4.5 Sensör Deteksiyon Analizi", h2),
              P(f"36 sensör 1 TeV'de olay başına ortalama {f(a['hits'])} foton algılamıştır. Bu, üretilen fotonların "
                f"%{f(a['eff'],2)}'ine karşılık gelir. Verimin düşük olmasının başlıca nedeni geometriktir: "
                f"36 DOM'un toplam kesit alanı yalnızca ≈ 3,1 m²'dir ve fotonların büyük bölümü buz bloğundan "
                f"dışarı kaçar ya da soğurulur. Her olayda 36 sensörün tamamı en az bir foton almıştır; bu da "
                f"rekonstrüksiyon için yeterli bilgi sağlamaktadır. Sensörlere göre dağılım (Şekil 3, panel 4) "
                f"müon izine en yakın merkez stringlerde (S3–S5) belirgin bir artış gösterir. Bu çalışmada "
                f"fotoçoğaltıcının kuantum verimi uygulanmamıştır; yani sayılan 'hit'ler DOM yüzeyine ulaşan "
                f"fotonlardır. Gerçek bir DOM için (%25 dolayında tepe kuantum verimi) algılanan sayı yaklaşık "
                f"dörtte bire inecektir."),
              P("Vuruş zamanlarının her olaydaki ilk vuruşa göre dağılımı (Şekil 3, panel 3) birkaç on "
                f"nanosaniyede tepe yapan ve üstel olarak azalan bir kuyruk gösterir. Medyan gecikme ≈ 43 ns, "
                f"%90'lık değer ≈ 85 ns'dir. Bu kuyruk saçılmış fotonlardan kaynaklanır ve basit doğrusal "
                f"yöntemlerin (LineFit) başarımını sınırlayan temel etkendir."),

              CondPageBreak(24*cm), P("4.6 AGN Kaynak Rekonstrüksiyonu", h2),
              figure(f"{DATA}/1TeV_agn_reconstruction.png", 14.0,
                     "1 TeV için altı panelli AGN analizi: (1) ilk olayın foton üretim noktaları ve string "
                     "konumları; (2) üretilen ve algılanan fotonların enerji spektrumu; (3) DOM katmanlarına göre "
                     "vuruş zamanı dağılımı; (4) sensör başına ortalama hit; (5) rekonstrükte kaynağın katalogdaki "
                     "AGN'lere açısal uzaklığı (mavi: BL Lac, kırmızı: FSRQ, yeşil: Seyfert); (6) olay başına "
                     "rekonstrükte kaynak yönleri, birleşik kaynak (+) ve hata çemberi.",
                     comment=(f"(1) Fotonlar müon izi boyunca ince bir çizgi halinde üretilir; izin alt ucundaki dağınık küme bir "
                 f"elektromanyetik kaskaddır. (2) Algılanan fotonların spektrumu mavi tarafa kaymıştır, çünkü kırmızı fotonlar "
                 f"buzda daha çabuk soğurulur. (3) Sinyaller birkaç on ns içinde tepe yapar ve saçılma nedeniyle yüzlerce ns'ye "
                 f"uzanan bir kuyruk gösterir; ize uzak en üst ve en alt katmanlar (3 ve 0) daha geç sinyal alır. (4) En çok "
                 f"hit, ize en yakın orta stringlerde toplanır. (5) TXS 0506+056 çubuğu en kısadır "
                 f"({f(a['dists']['TXS 0506+056'],2)}°); diğer AGN'ler 30°'den daha uzaktadır. (6) Tek olaylar ±6°'lik bir "
                 f"alana dağılır, ancak birleşik kaynak (+) gerçek kaynağa (yıldız) çok yakındır.")),
              P(f"LineFit yöntemi olay başına {f(a['lf'],1)}° medyan hata vermiştir. Bu yöntem saçılmayı ve "
                f"Cherenkov konisinin geometrisini hesaba katmadığı için kaba bir ön tahmindir. Cherenkov "
                f"zaman-artığı fiti hatayı {f(a['fit'],2)}°'ye düşürmüştür (olayların %{f(a['lt5'],0)}'i 5°'nin, "
                f"%{f(a['lt1'],0)}'i 1°'nin altında). Tek bir olayın yönü bu nedenle bir kaynağı tek başına "
                f"belirlemek için yeterli değildir. Ancak aynı kaynaktan gelen 100 olay birleştirildiğinde "
                f"istatistiksel hata √N ile azalır ve kaynak konumu ({f(a['src'][0],2)}°, {f(a['src'][1],2)}°) ± "
                f"{f(a['src'][2],2)}° olarak bulunur."),
              table([["AGN", "Sınıf", "α (°)", "δ (°)", "1 TeV uzaklık (°)", "10 TeV uzaklık (°)"]] +
                    [[n, c, f(ra, 2), f(dec, 2), f(a['dists'][n], 2), f(b['dists'][n], 2)]
                     for n, ra, dec, c in sorted(cm_.AGN_CATALOG, key=lambda x: a['dists'][x[0]])],
                    [3.2, 3.2, 1.9, 1.7, 3.1, 3.3],
                    "Kullanılan AGN kataloğu ve birleşik rekonstrükte kaynağa açısal uzaklıklar.",
                    align_center_cols=(2, 3, 4, 5)),
              P(f"Katalogdaki yedi AGN içinde birleşik kaynağa en yakın olan TXS 0506+056'dır "
                f"({f(a['dists']['TXS 0506+056'],2)}°); ikinci en yakın kaynak olan NGC 1068 ise ≈ 37° uzaktadır. "
                f"Dolayısıyla eşleşme belirsizlik içermez ve kaynak, BL Lac türü bir blazar olarak doğru şekilde "
                f"teşhis edilmiştir. Bulunan konum gerçek konumdan yaklaşık 0,7° sapmaktadır; bu sapma hata "
                f"yarıçapıyla ({f(a['src'][2],2)}°) aynı mertebededir. Dec yönündeki küçük sistematik kayma "
                f"(≈ −0,7°), seyrek string düzeninin (yalnızca 3 sütun) düşey yönde daha zayıf bir kaldıraç "
                f"sağlamasıyla ilişkili olabilir."),

              CondPageBreak(24*cm), P("4.7 1 TeV ve 10 TeV'in Karşılaştırılması", h2),
              figure(f"{DATA}/comparison.png", 14.0,
                     "1 TeV ve 10 TeV müonların karşılaştırılması: (1) enerji kaybı dağılımı; (2) teorik dE/dx "
                     "eğrisi ile simülasyon ortalama ve medyanları; (3) birincil ve toplam Cherenkov foton sayısı; "
                     "(4) olay başına sensör hit sayısı ve verim; (5) açısal hata dağılımı (düz: Cherenkov fiti, "
                     "kesikli: LineFit); (6) birleşik hata yarıçapı ve en yakın AGN'ye uzaklık.",
                     comment=(f"(1) 10 TeV'de kayıp dağılımı sağa kaymış ve çok daha uzun bir kuyruk kazanmıştır. (2) Her iki enerjide de "
                 f"medyan ortalamanın belirgin altındadır ve bu fark 10 TeV'de büyür. (3) Birincil müon ışığı iki enerjide "
                 f"aynıdır; toplam ışığı artıran kaskadlardır. (4) 10 TeV'de olay başına hit sayısı yaklaşık "
                 f"{f(b['hits']/a['hits'],1)} kat fazladır. (5) Cherenkov fitinin hataları iki enerjide de ≈ 4° civarında, "
                 f"LineFit'inkiler ≈ 15–25° civarında toplanır. (6) Her iki enerjide de en yakın AGN TXS 0506+056'dır ve "
                 f"uzaklık hata yarıçapı mertebesindedir.")),
              *bullets([
                  f"<b>Enerji kaybı:</b> Enerji 10 kat artırıldığında ortalama kayıp {f(a['eloss_mean'],1)} GeV'ten "
                  f"{f(b['eloss_mean'],1)} GeV'e (≈ 5 kat) çıkmıştır. Kesirsel kayıp ise %{f(a['frac'],2)}'den "
                  f"%{f(b['frac'],2)}'ye inmiştir, çünkü sabit iyonizasyon kısmı (≈ 5,5 GeV) toplam enerjiye göre "
                  f"küçülmektedir. 10 TeV'de radyatif payın büyümesi a + bE modelinin beklentisiyle uyumludur.",
                  f"<b>Foton üretimi:</b> Birincil müonun ürettiği foton sayısı iki enerjide de aynıdır "
                  f"(≈ 670.800). Bu, Frank-Tamm bağıntısının β ≈ 1 için enerjiden bağımsız olmasının doğrudan "
                  f"sonucudur. Toplam foton sayısının 4,5 kat artması tamamen radyatif kayıpların başlattığı "
                  f"kaskadlardan kaynaklanır; 10 TeV'de fotonların yalnızca %{f(b['prim_frac'],1)}'i birincil "
                  f"müondan gelir. Şekil 2(h)'de görüldüğü gibi toplam foton sayısı, buzda bırakılan enerjiyle "
                  f"doğru orantılıdır. IceCube'un müon enerjisini ışık miktarından kestirmesinin temeli budur.",
                  f"<b>Sensör hit oranı:</b> Ortalama hit sayısı {f(a['hits'])}'den {f(b['hits'])}'e çıkmıştır. "
                  f"Verim ise %{f(a['eff'],2)}'den %{f(b['eff'],2)}'ye hafifçe düşmüştür. Kaskadlar iz boyunca "
                  f"rastgele noktalarda oluştuğundan ve bazıları sensörlerden uzak olduğundan ışıklarının daha "
                  f"küçük bir kesri toplanır.",
                  f"<b>AGN teşhis güvenilirliği:</b> 10 TeV'de medyan açısal hata {f(b['fit'],2)}° ile 1 TeV'den "
                  f"({f(a['fit'],2)}°) biraz daha kötüdür ve birleşik kaynak TXS 0506+056'ya "
                  f"{f(b['dists']['TXS 0506+056'],2)}° uzaklıktadır. Bunun nedeni, kaskadlardan gelen yoğun ve "
                  f"yaklaşık küresel ışığın Cherenkov konisinin zaman yapısını bozmasıdır. Basit fit modelimiz "
                  f"yalnızca izden gelen doğrudan ışığı varsaydığından bu ışığı modelleyemez. Her iki enerjide de "
                  f"doğru AGN açık farkla seçilmiştir; dolayısıyla teşhis güvenilirdir, ancak daha yüksek "
                  f"enerjilerde kaskad ışığını da modelleyen bir olabilirlik (likelihood) yöntemi gerekir."]),
              ]

    # ============================== 4.8–4.12 İKİNCİ AŞAMA
    story += [PageBreak(), P("4.8 Enerji Taraması: Işık Üretimi ve Algılanması", h2),
              P(f"İkinci aşamada {len(T)} enerjide toplam {f(T.N.sum())} müon benzetilmiştir. Olay başına "
                f"ortalama değerler Tablo 9'da, enerjiye bağlılıkları Şekil 5'te verilmiştir."),
              table([["Enerji (TeV)", "Olay", "Üretilen foton", "DOM'a ulaşan", "Algılanan", "η<sub>det</sub>",
                      "⟨dE/dx⟩ (MeV/cm)", "Groom (MeV/cm)", "Yön hatası"]] +
                    [[Etxt(r.E_TeV), f(r.N), f(r.ph), f(r.hits), f(r.det), f"%{f(100*r.eff_det,3)}",
                      f"{f(r.dedx_tot,2)} ± {f(r.dedx_tot_err,2)}", f(r.groom_tot, 2), f"{f(r.fit,2)}°"]
                     for _, r in T.iterrows()],
                    [1.4, 1.0, 2.2, 1.8, 1.7, 1.7, 2.8, 1.9, 1.9],
                    "Enerji taraması sonuçları (olay başına ortalama; ⟨dE/dx⟩ ortalama ± standart hata; yön hatası "
                    "Cherenkov fitinin medyanı).", align_center_cols=tuple(range(9))),
              figure(f"{TH}/fig_light_yield.png", 15.0,
                     "Enerji taraması: (a) olay başına üretilen Cherenkov fotonu (toplam ve birincil müon); "
                     "(b) DOM'a ulaşan ve kuantum verimi sonrası algılanan foton; (c) algılama verimleri; "
                     "(d) buzda bırakılan enerji başına foton sayısı.",
                     comment=(f"(a) Birincil müonun ışığı tüm enerjilerde ≈ {f(T.ph_prim.mean()/1e3)} bin fotonda sabit kalırken toplam ışık "
                 f"{Etxt(T.E_TeV.iloc[0])} TeV'den {Etxt(T.E_TeV.iloc[-1])} TeV'e ≈ {f(T.ph.iloc[-1]/T.ph.iloc[0])} kat artar; "
                 f"artışın tamamı kaskadlardandır. (b) Algılanan foton sayısı DOM'a ulaşanların yaklaşık beşte biridir "
                 f"(kuantum verimi). (c) Algılama verimi enerjiden büyük ölçüde bağımsızdır "
                 f"(%{f(100*T.eff_det.min(),2)}–%{f(100*T.eff_det.max(),2)}). (d) Bırakılan enerji başına foton sayısı "
                 f"{f(T.ph_per_GeV.min()/1e3)}–{f(T.ph_per_GeV.max()/1e3)} bin foton/GeV aralığında, yani "
                 f"%{f(100*(T.ph_per_GeV.max()/T.ph_per_GeV.min()-1))} içinde sabittir: ışık miktarı iyi bir kalorimetrik "
                 f"(enerji) ölçüsüdür.")),
              P(f"Birincil müonun ürettiği foton sayısı tüm enerjilerde yaklaşık sabittir; toplam ışıktaki artış "
                f"radyatif kayıpların başlattığı kaskadlardan gelir. Algılanan foton sayısı {Etxt(T.E_TeV.iloc[0])} "
                f"TeV'de {f(T.det.iloc[0])}'den {Etxt(T.E_TeV.iloc[-1])} TeV'de {f(T.det.iloc[-1])}'e çıkmıştır. "
                f"Üretilen fotonların algılanma oranı %{f(100*T.eff_det.min(),3)}–%{f(100*T.eff_det.max(),3)} "
                f"aralığındadır; kuantum verimi DOM'a ulaşan fotonların yaklaşık beşte birini sinyale çevirir."),

              CondPageBreak(12*cm), P("4.9 Enerji Kaybının Literatürle Doğrulanması", h2),
              figure(f"{TH}/fig_dedx_validation.png", 12.5,
                     "Simülasyondaki ortalama ve medyan dE/dx'in PDG/Groom su tablosuyla (buz yoğunluğuna "
                     "ölçeklenmiş) karşılaştırılması. Alt panel: simülasyon / Groom oranı.",
                     comment=(f"Siyah noktalar (ortalama) 1 TeV'e kadar Groom eğrisinin üzerindedir; daha yüksek enerjide büyük hata "
                 f"çubuklarıyla eğrinin etrafında dağılır ve yalnızca 20 olaylık 100 TeV noktası belirgin altında kalır. Yeşil "
                 f"elmaslar (4000 olay) ise 30 ve 100 TeV'de eğriye oturur. Mavi kareler (iyonizasyon) tüm enerjilerde "
                 f"{f(T.dedx_ion.min(),1)}–{f(T.dedx_ion.max(),1)} MeV/cm civarında hemen hemen yatay kalır; toplam kayıptaki "
                 f"artış radyatif kayıplardan (kırmızı) gelir. Medyanlar (×) ortalamanın altındadır.")),
              P(f"Simülasyondaki ortalama enerji kaybı {', '.join(Etxt(E) for E in good.E_TeV)} TeV'de Groom "
                f"tablosuyla %5 içinde uyumludur (1 TeV'de {f(r1.dedx_tot,2)} ± {f(r1.dedx_tot_err,2)} MeV/cm, "
                f"Groom {f(r1.groom_tot,2)} MeV/cm). Daha yüksek enerjilerde simülasyon / Groom oranı "
                f"{', '.join(Etxt(E) + ' TeV: ' + f(x, 2) for E, x in zip(T.E_TeV, ratio) if abs(x - 1) > 0.05)} "
                f"olarak dalgalanır ve istatistiksel belirsizlik büyür. Bunun nedeni, radyatif kaybın seyrek fakat "
                f"çok büyük olaylarla taşınmasıdır: 20 m'lik izde ve sınırlı olay sayısında birkaç büyük olayın "
                f"varlığı ya da yokluğu ortalamayı belirgin biçimde değiştirir. Tipik olayı temsil eden medyan "
                f"değerler ise ortalamanın sistematik olarak altındadır."),
              P(f"Bu açıklamayı sınamak için Cherenkov ışıması kapatılarak 4000'er olaylık doğrulama koşuları "
                f"yapılmıştır (Şekil 6, yeşil noktalar). Bu koşularda ortalama kayıp Groom değerine oranla "
                f"{', '.join(Etxt(r.E_TeV) + ' TeV: ' + f(r.ratio, 2) + ' ± ' + f(r.dedx_err/r.groom, 2) for _, r in C.iterrows())} "
                f"bulunmuş, yani literatürle istatistiksel belirsizlik içinde uyumludur. Aynı verilerden rastgele "
                f"20 olaylık alt örnekler çekildiğinde ortalamanın Groom'a oranı tipik olarak "
                f"{f(C.sub20_med.iloc[-1],2)}, %68 aralığı ise {f(C.sub20_lo.iloc[-1],2)}–{f(C.sub20_hi.iloc[-1],2)} "
                f"çıkmaktadır. Dolayısıyla tarama koşularında yüksek enerjide görülen sapmalar simülasyon fiziğindeki "
                f"bir hatadan değil, sınırlı olay sayısıyla nadir büyük kayıpların eksik örneklenmesinden kaynaklanır."),

              CondPageBreak(12*cm), P("4.10 Açısal Çözünürlüğün Enerjiye Bağlılığı", h2),
              figure(f"{TH}/fig_angular_resolution.png", 15.6,
                     "(a) LineFit ve Cherenkov zaman fitinin medyan açısal hatası (hata çubukları: bootstrap %68 "
                     "güven aralığı). (b) Cherenkov fiti açısal hata dağılımları.",
                     comment=(f"(a) Cherenkov fiti tüm enerjilerde {f(T.fit.min(),1)}–{f(T.fit.max(),1)}° aralığında hemen hemen yatay "
                 f"seyreder; LineFit ise {f(T.lf.max(),0)}°'den {f(T.lf.min(),0)}°'ye hafifçe iyileşir ama Cherenkov fitinden "
                 f"4–5 kat kötü kalır. (b) Hata dağılımlarının biçimi enerjiyle pek değişmez; olayların çoğu 2–8° arasındadır "
                 f"ve 1°'nin altına düşen olayların oranı yalnızca %{f(100*T.frac_lt1.min())}–%{f(100*T.frac_lt1.max())} "
                 f"düzeyindedir.")),
              P(f"Kuantum verimi uygulanmış verilerle Cherenkov fiti {f(T.fit.min(),2)}–{f(T.fit.max(),2)}°, "
                f"LineFit ise {f(T.lf.min(),1)}–{f(T.lf.max(),1)}° medyan hata vermiştir. Çözünürlük enerjiyle "
                f"belirgin biçimde iyileşmemektedir: düşük enerjide ışık azdır, yüksek enerjide ise kaskadların "
                f"yaklaşık küresel ışığı, fitin varsaydığı Cherenkov konisi zaman yapısını bozar. Birleşik kaynak "
                f"tüm enerjilerde TXS 0506+056'ya {f(T.src_dist_TXS.min(),2)}–{f(T.src_dist_TXS.max(),2)}° "
                f"uzaklıkta bulunmuştur."),

              CondPageBreak(12*cm), P("4.11 Enerji Rekonstrüksiyonu", h2),
              figure(f"{TH}/fig_energy_reconstruction.png", 16.2,
                     "(a) Kalibrasyon: kesilmiş algılanan ışığın enerjiye bağlılığı (medyan ve %16–%84 bandı). "
                     "(b) Test olaylarında rekonstrükte ve gerçek enerji. (c) Üç yöntemin sapması (nokta) ve "
                     "çözünürlüğü (hata çubuğu).",
                     comment=(f"(a) Kalibrasyon eğrisi 1 TeV'e kadar neredeyse yataydır (ışık enerjiye duyarsız), sonra dikleşir; bant "
                 f"yüksek enerjide çok genişler, yani aynı enerjideki olayların ışığı birkaç kat farklı olabilir. (b) Noktalar "
                 f"köşegen etrafında geniş bir alana dağılır; en düşük ve en yüksek enerjideki yığılmalar, kestirimin "
                 f"kalibrasyon aralığının uçlarına sıkışmasıdır. (c) Turuncu ve yeşil yöntemler düşük enerjide sıfırın "
                 f"üstünde, yüksek enerjide altındadır (sistematik sapma); mavi yöntem sıfıra yakın kalır ama hata çubukları "
                 f"geniştir.")),
              table([["Enerji (TeV)", "Test olayı", "Regresyon: sapma / σ", "Groom tersi: sapma / σ",
                      "Kalibrasyon: sapma / σ"]] +
                    [[Etxt(r.E_TeV), f(r.n), f"{f(r.reg_bias,2)} / {f(r.reg_sigma,2)}",
                      f"{f(r.phys_bias,2)} / {f(r.phys_sigma,2)}", f"{f(r.cal_bias,2)} / {f(r.cal_sigma,2)}"]
                     for _, r in R.iterrows()],
                    [2.2, 2.0, 4.0, 4.0, 4.2],
                    "Enerji rekonstrüksiyonu (log<sub>10</sub> birimi; sapma: medyan, σ: %16–%84 yarı genişlik).",
                    align_center_cols=tuple(range(5))),
              P(f"Basit regresyon ve ortalama Groom eğrisinin tersi belirgin sistematik sapma gösterir: düşük "
                f"enerjileri fazla, yüksek enerjileri eksik kestirir. Regresyonun küçük görünen σ değeri "
                f"yanıltıcıdır; yöntem tüm tahminleri dağılımın ortasına çektiği için dar görünür. Kalibrasyon "
                f"eğrisi yöntemi sapmayı belirgin biçimde azaltır (|sapma| ≤ {f(R.cal_bias.abs().max(),2)}; diğer "
                f"yöntemlerde en fazla {f(bias_old,2)}). Kalan sapma test olayı sayısının az olduğu yüksek enerjilerde "
                f"görülür. Ancak çözünürlük "
                f"1 TeV ve üzerinde {f(Ecal.cal_sigma.min(),2)}–{f(Ecal.cal_sigma.max(),2)} dex'tir; yani enerji "
                f"ancak birkaç kat içinde kestirilebilmektedir. En düşük ve en yüksek enerjide σ'nın küçük "
                f"görünmesi, kestirimin kalibrasyon aralığının dışına çıkamamasından kaynaklanan yapay bir etkidir."),
              P(f"Bunun iki fiziksel nedeni vardır. Birincisi, kalibrasyon eğrisinin eğimi 1 TeV'in altında "
                f"yalnızca {f(R.slope_to_next.iloc[0],2)}–{f(R.slope_to_next.iloc[1],2)} kadardır: bu bölgede kayıp "
                f"iyonizasyon tarafından belirlendiği için ışık enerjiye neredeyse duyarsızdır. İkincisi, kritik "
                f"enerjinin üstünde ışığı belirleyen radyatif kayıplar stokastiktir ve 20 m'lik izde yalnızca "
                f"birkaç büyük kayıp gözlenir; bu dalgalanmanın ortalaması alınamaz. IceCube'un kilometrelik "
                f"izlerle çok daha iyi enerji çözünürlüğüne ulaşmasının nedeni budur."),

              CondPageBreak(12*cm), P("4.12 Parametre Çalışması: String Aralığı ve Buz Modeli", h2),
              figure(f"{TH}/fig_parameter_study.png", 15.0,
                     "1 TeV parametre çalışması: (a) string aralığı – açısal hata; (b) string aralığı – algılanan "
                     "ışık; (c) Rayleigh ve Mie buzunda ilk fotonun gecikmesi; (d) buz modeline göre açısal hata "
                     "ve algılanan ışık.",
                     comment=(f"(a) Cherenkov fitinin hatası aralık büyüdükçe artar ve en iyi değer 4 m'dedir; LineFit ise tersine "
                 f"iyileşir. (b) Algılanan ışık 4 m'de belirgin yüksektir; 6 ve 8 m'de hemen hemen aynıdır. (c) Mie buzunda "
                 f"(kırmızı) ilk fotonların gecikme kuyruğu Rayleigh buzuna (mavi) göre daha kısadır. (d) Mie buzunda "
                 f"algılanan ışık ≈ %{f(100*(1 - mie.det/ray.det))} azalırken açısal hata benzer kalır.")),
              table([["Ayar (1 TeV, 300 olay)", "Medyan açısal hata (%68 GA)", "LineFit", "Algılanan foton / olay"]] +
                    [[f"String aralığı {f(r.spacing)} m", f"{f(r.fit,2)}° ({f(r.fit_lo,2)}–{f(r.fit_hi,2)})",
                      f"{f(r.lf,1)}°", f(r.det)] for _, r in sp.iterrows()] +
                    [["Mie buz (6 m)", f"{f(mie.fit,2)}° ({f(mie.fit_lo,2)}–{f(mie.fit_hi,2)})", f"{f(mie.lf,1)}°",
                      f(mie.det)]],
                    [5.0, 4.8, 2.4, 4.2], "Parametre çalışması sonuçları.", align_center_cols=(1, 2, 3)),
              P(f"String aralığı 8 m'den 4 m'ye indirildiğinde Cherenkov fitinin medyan hatası "
                f"{f(sp.fit.iloc[-1],2)}°'den {f(sp.fit.iloc[0],2)}°'ye düşmüş ve 4 m ile 8 m'nin güven aralıkları "
                f"örtüşmemiştir; bu sonuç, sensör yoğunluğu arttıkça yön hatasının azaldığı beklentisini destekler. "
                f"4 m'de algılanan ışık da belirgin biçimde artmıştır ({f(sp.det.iloc[0])} foton). LineFit ise ters "
                f"eğilim göstermiştir ({f(sp.lf.iloc[0],1)}° → {f(sp.lf.iloc[-1],1)}°): sık dizilimde ize yakın çok "
                f"sayıda DOM'un neredeyse eş zamanlı sinyali, düz dalga varsayımına dayanan LineFit'i yanıltmaktadır. "
                f"Mie buzunda algılanan ışık %{f(100*(1 - mie.det/ray.det))} azalmış, açısal hata ise güven "
                f"aralıkları içinde Rayleigh ile benzer kalmıştır; Mie saçılması ileri yönlü olduğundan ilk "
                f"fotonların gecikme dağılımının kuyruğu kısalmıştır."),
              ]

    # ============================== 5. TARTIŞMA
    story += [CondPageBreak(5*cm), P("5. TARTIŞMA VE SINIRLILIKLAR", h1),
              P("Elde edilen sonuçlar temel fiziksel beklentilerle (Frank-Tamm foton sayısı, Cherenkov açısı, "
                "iyonizasyon kaybının büyüklüğü, radyatif kaybın enerjiyle artışı) nicel olarak uyumludur. "
                "Bununla birlikte, modelin bir öğrenci projesi kapsamında yapılan bilinçli basitleştirmeleri "
                "vardır ve sonuçlar yorumlanırken dikkate alınmalıdır:"),
              *bullets([
                  "<b>Dedektör boyutu:</b> 20 m'lik buz bloğu ve 36 DOM, IceCube'un 1 km³'lük hacminin ve 5160 "
                  "DOM'unun çok küçük bir parçasıdır. Gerçek IceCube'da müon izi yüzlerce metre boyunca "
                  "izlenebildiği için açısal çözünürlük TeV enerjilerde 1°'nin altındadır.",
                  "<b>Buz modeli:</b> Katmanların optik parametreleri temsilidir. Gerçek buzda baskın saçılma ileri "
                  "yönlü Mie saçılmasıdır; bu model ikinci aşamada denenmiş ve algılanan ışığı ile zaman dağılımını "
                  "belirgin biçimde değiştirdiği görülmüştür (Bölüm 4.12). Ölçülmüş bir buz modeli (ör. SPICE) "
                  "kullanılmamıştır.",
                  "<b>Sensör yanıtı:</b> Kuantum verimi yalnızca ikinci aşamada ve temsili bir eğriyle "
                  "uygulanmıştır; DOM'un açısal kabulü, fotoçoğaltıcının zaman çözünürlüğü ve karanlık sayım "
                  "gürültüsü modellenmemiştir.",
                  "<b>Enerji ölçümü:</b> 20 m'lik iz boyu, stokastik radyatif kayıpların ortalamasının alınmasına "
                  "yetmediği için enerji çözünürlüğünü temelde sınırlar; 1 TeV altında ise ışık enerjiye neredeyse "
                  "duyarsızdır (Bölüm 4.11).",
                  "<b>Koordinat dönüşümü:</b> Yerel yıldız zamanı sıfır alınmış ve Dünya'nın dönüşü ihmal "
                  "edilmiştir. Gerçek analizde her olayın zaman damgası ile yerel koordinatlar ekvator "
                  "koordinatlarına çevrilir.",
                  "<b>AGN teşhisi:</b> Simülasyonda kaynağın yönü baştan verilmektedir; yapılan iş, bu yönün "
                  "dedektör verisinden ne doğrulukla geri bulunabildiğinin bir <i>yöntem testidir</i>. Bir "
                  "kaynağın BL Lac veya FSRQ olduğu müon verisinden çıkarılamaz; sınıf bilgisi katalogla "
                  "eşleştirme sonucunda elde edilir. Ayrıca gerçek gözlemde atmosferik müon ve nötrino arka "
                  "planı baskındır ve kaynak sinyali istatistiksel olarak ayrıştırılmalıdır.",
                  "<b>Nötrino etkileşmesi:</b> Nötrinonun müona dönüştüğü yüklü akım etkileşmesi "
                  "benzetilmemiş, etkisi 0,5°'lik açısal sapma ile temsil edilmiştir. Gerçekte bu açı "
                  "kabaca 0,7°·(E<sub>ν</sub>/TeV)<super>−0,7</super> ile ölçeklenir.",
                  f"<b>İstatistik:</b> Yüksek enerjide olay sayısı hesaplama süresi nedeniyle azaltılmıştır "
                  f"({Etxt(T.E_TeV.iloc[-1])} TeV'de {f(T.N.iloc[-1])} olay); ortalama enerji kaybı gibi uzun "
                  f"kuyruklu büyüklükler bu nedenle belirgin istatistiksel dalgalanma gösterir (Bölüm 4.9)."]),
              *([] if THESIS else [   # tezde öneriler Bölüm 6.2'de
              P("Çalışmanın geliştirilmesi için şu adımlar önerilmektedir: ölçülmüş bir buz modelinin (ör. SPICE) "
                "kullanılması, dedektör boyutunun ve yüksek enerjide olay sayısının artırılması (gerekirse TRUBA "
                "gibi bir hesaplama altyapısında), kaskad ışığını da içeren olabilirlik tabanlı bir yön ve enerji "
                "rekonstrüksiyonu yazılması ve atmosferik arka plan eklenerek bir kaynak anlamlılık (p-değeri) "
                "analizi yapılması.")]),
              ]

    # ============================== 6. SONUÇ
    story += [P("6. SONUÇ VE ÖNERİLER" if THESIS else "6. SONUÇ", h1),
              *([P("6.1 Sonuçlar", h2)] if THESIS else []),
              P("Bu projede Geant4 kullanılarak IceCube benzeri, derinliğe bağlı optik özelliklere sahip bir buz "
                "dedektörü modellenmiş ve AGN yönünden gelen TeV müonların ürettiği Cherenkov ışığı uçtan uca "
                "benzetilmiştir. Başlıca sonuçlar şunlardır:"),
              *bullets([
                  f"1 TeV müon ≈ 20,6 m buzda ortalama {f(a['eloss_mean'],1)} GeV (medyan {f(a['eloss_med'],1)} GeV) "
                  f"kaybetmiştir. Medyan kayıp Bethe-Bloch iyonizasyonuyla, ortalama ile medyan arasındaki fark ise "
                  f"stokastik radyatif kayıplarla açıklanmaktadır.",
                  f"Birincil müon ≈ 326 foton/cm üretmiştir; bu değer, foton enerji spektrumu ve ≈ 40,7°'lik "
                  f"Cherenkov açısı Frank-Tamm teorisiyle uyumludur.",
                  f"Üretilen fotonların ≈ %{f(a['eff'],2)} kadarı 36 sensöre ulaşmıştır. Sensörlere ulaşan ışık, kızıl "
                  f"fotonların soğurulması nedeniyle maviye kaymıştır ve tozlu katman ışık miktarını ve zaman "
                  f"dağılımını etkilemektedir.",
                  f"Cherenkov zaman fiti olay başına ≈ {f(a['fit'],1)}° çözünürlük sağlamış, 100 olay "
                  f"birleştirilerek kaynak TXS 0506+056'ya {f(a['dists']['TXS 0506+056'],2)}° uzaklıkta bulunmuş ve "
                  f"BL Lac türü blazar olarak doğru şekilde eşleştirilmiştir.",
                  "10 TeV'de radyatif kayıplar baskın hale gelmiş, kaskadlar nedeniyle toplam ışık 4,5 kat "
                  "artmıştır. Buna karşın birincil müon ışığı değişmemiş ve basit fit modelinin açısal "
                  "çözünürlüğü hafifçe kötüleşmiştir.",
                  f"{Etxt(T.E_TeV.iloc[0])}–{Etxt(T.E_TeV.iloc[-1])} TeV taramasında enerji kaybı 1 TeV'e kadar "
                  f"Groom tablolarıyla %5 içinde doğrulanmış; kuantum verimi sonrası açısal hata "
                  f"{f(T.fit.min(),1)}–{f(T.fit.max(),1)}° aralığında kalmıştır.",
                  f"String aralığının 8 m'den 4 m'ye inmesi açısal hatayı {f(sp.fit.iloc[-1],2)}°'den "
                  f"{f(sp.fit.iloc[0],2)}°'ye düşürmüş ve algılanan ışığı artırmıştır; Mie buzunda algılanan ışık "
                  f"azalmış, açısal hata benzer kalmıştır.",
                  f"Kalibrasyon eğrisine dayanan enerji kestirimi sistematik sapmayı belirgin biçimde azaltmış, ancak 1 TeV ve "
                  f"üzerinde çözünürlük {f(Ecal.cal_sigma.min(),1)}–{f(Ecal.cal_sigma.max(),1)} dex ile sınırlı "
                  f"kalmıştır; bunun nedeni kısa iz boyu ve 1 TeV altındaki ışık duyarsızlığıdır."]),
              P("Sonuç olarak, kurulan simülasyon zinciri (Geant4 → CSV → Python analizi), nötrino teleskoplarında "
                "kullanılan temel fiziksel süreçleri ve yöntemleri anlamak için çalışan ve genişletilebilir bir "
                "altyapı sunmaktadır."),
              *(thesis_oneriler() if THESIS else []),
              ]

    # ============================== KAYNAKLAR
    if THESIS:                          # tek kaynakça: metinde ilk geçiş sırasıyla
        CITE["src"] = None
        refs = [CITE["text"][k] for k in CITE["order"]]
    else:
        refs = REFS_RAPOR
    story += [PageBreak(), P("KAYNAKLAR", h1)] + [P(f"[{i}] {r}", ref) for i, r in enumerate(refs, 1)]

    # ============================== EKLER
    story += [PageBreak(), P("EK A. PROGRAMIN ÇALIŞTIRILMASI", h1),
              P("Proje dizin yapısı ve programın derlenip çalıştırılması aşağıda özetlenmiştir."),
              Preformatted(
                  "Geant4_2/\n"
                  "├── CMakeLists.txt\n├── sim.cc\n"
                  "├── include/  src/        (Config, DetectorConstruction, SensorSD, PrimaryGenerator,\n"
                  "│                          Run/Event/Stepping/StackingAction, OutputManager)\n"
                  "├── run1TeV.mac  run10TeV.mac  test.mac  vis.mac\n"
                  "├── macros/   make_macros.sh, scan_*TeV.mac, param_*.mac, detail_*TeV.mac\n"
                  "├── run_thesis.sh         (ikinci aşama koşularını sırayla çalıştırır)\n"
                  "├── analysis/  common.py  analyze.py  compare.py  thesis.py\n"
                  "└── build/data/           (CSV çıktıları ve grafikler)\n\n"
                  "# Derleme\ncd build && cmake .. && make -j\n\n"
                  "# Simülasyon (2. argüman: iş parçacığı sayısı)\n"
                  "./sim run1TeV.mac 12\n./sim run10TeV.mac 12\n./sim            # görsel arayüz (vis.mac)\n\n"
                  "# Analiz\ncd ..\npython3 analysis/analyze.py build/data/1TeV\n"
                  "python3 analysis/analyze.py build/data/10TeV\n"
                  "python3 analysis/compare.py build/data/1TeV build/data/10TeV\n\n"
                  "# İkinci aşama (enerji taraması + parametre çalışması)\n"
                  "bash run_thesis.sh 12\npython3 analysis/thesis.py\n\n"
                  "# Ek C: her enerji için ayrıntılı koşu + tarama rekonstrüksiyonu\n"
                  "python3 analysis/analyze.py build/data/detail/E3TeV build/data/scan/E3TeV", code),
              P("EK B. ÖNEMLİ KOD PARÇALARI", h1),
              P("<b>B.1 Cherenkov fotonlarının yakalanması (StackingAction.cc).</b> Yeni oluşturulan her iz yığına "
                "konmadan önce bu fonksiyondan geçer. Cherenkov süreciyle oluşan optik fotonlar kaydedilir:"),
              Preformatted(
                  "G4ClassificationOfNewTrack StackingAction::ClassifyNewTrack(const G4Track* track)\n{\n"
                  "  if (track->GetDefinition() == G4OpticalPhoton::Definition()) {\n"
                  "    const G4VProcess* creator = track->GetCreatorProcess();\n"
                  "    if (creator && creator->GetProcessName() == \"Cerenkov\") {\n"
                  "      OutputManager::Instance()->AddPhoton(track->GetParentID(), track->GetPosition(),\n"
                  "                                           track->GetMomentumDirection(),\n"
                  "                                           track->GetTotalEnergy(), track->GetGlobalTime());\n"
                  "    }\n  }\n  return fUrgent;\n}", code),
              P("<b>B.2 Sensör vuruşu (SensorSD.cc).</b> DOM'a sınırdan giren foton kaydedilir, kuantum verimine "
                "göre 'algılandı' olarak işaretlenir ve yok edilir:"),
              Preformatted(
                  "G4bool SensorSD::ProcessHits(G4Step* step, G4TouchableHistory*)\n{\n"
                  "  G4Track* track = step->GetTrack();\n"
                  "  if (track->GetDefinition() != G4OpticalPhoton::Definition()) return false;\n"
                  "  track->SetTrackStatus(fStopAndKill);\n"
                  "  G4StepPoint* pre = step->GetPreStepPoint();\n"
                  "  if (pre->GetStepStatus() != fGeomBoundary) return false;\n"
                  "  G4double lambda = 1239.84193 / (pre->GetTotalEnergy()/eV);\n"
                  "  G4bool detected = G4UniformRand() < QuantumEfficiency(lambda);\n"
                  "  G4int sensorID = pre->GetTouchableHandle()->GetCopyNumber();\n"
                  "  OutputManager::Instance()->AddHit(sensorID, pre->GetPosition(), pre->GetTotalEnergy(),\n"
                  "                                    pre->GetGlobalTime(), track->GetParentID(), detected);\n"
                  "  return true;\n}", code),
              CondPageBreak(9*cm), P("<b>B.3 Buzun optik özellikleri (DetectorConstruction.cc).</b> Her katman için kırılma indisi, "
                "soğurma ve Rayleigh tabloları malzemeye eklenir:"),
              Preformatted(
                  "auto* mpt = new G4MaterialPropertiesTable();\n"
                  "mpt->AddProperty(\"RINDEX\",    energies, rindex);  // Dispersiyon -> Cherenkov\n"
                  "mpt->AddProperty(\"ABSLENGTH\", energies, absLen);  // Soğurma\n"
                  "mpt->AddProperty(\"RAYLEIGH\",  energies, rayLen);  // Rayleigh saçılması\n"
                  "ice->SetMaterialPropertiesTable(mpt);", code),
              ]
    story += appendix_all_energies(f, Etxt)
    story += [PageBreak(), P("EK D. TERİMLER SÖZLÜĞÜ", h1),
              P("Raporda geçen temel kavramların kısa tanımları konulara göre aşağıda toplanmıştır.")]
    story += glossary_story()
    if THESIS:
        story += [PageBreak(), P("ÖZGEÇMİŞ", h1),
                  P("[Doğum yeri ve yılı, mezun olunan lise, üniversite eğitimi, ilgi alanları ve varsa katılınan "
                    "proje, kongre ve yayınları içeren kısa bir özgeçmiş buraya yazılacaktır.]")]
        if isinstance(PageBreak, type):  # PDF: her ana bölüm yeni sayfada başlar (Word'de başlık stili yapar)
            fixed = []
            for x in story:
                if (isinstance(x, Paragraph) and x.style.name == "h1" and fixed
                        and not isinstance(fixed[-1], PageBreak)):
                    while isinstance(fixed[-1], CondPageBreak):
                        fixed.pop()
                    fixed.append(PageBreak())
                fixed.append(x)
            story = fixed

    doc = ReportDoc(OUT, title="Geant4 ile IceCube Müon ve Cherenkov Işığı Simülasyonu",
                    author=STUDENT, subject="Lisans Bitirme Tezi" if THESIS else "Proje Raporu")
    doc.multiBuild(story)
    print("PDF:", OUT)


if __name__ == "__main__":
    build()

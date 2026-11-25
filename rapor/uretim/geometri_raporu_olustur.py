#!/usr/bin/env python3
"""Dedektör geometrisinin sade ve anlaşılır raporu (PDF). Word sürümü: word/dump_blocks.py + build_docx.js"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rapor_olustur as br  # noqa: E402
import kod_raporu_olustur as kr  # noqa: E402
from cikti_raporu_olustur import (OutDoc, callout, see, means, kpi_cards, f,  # noqa: E402
                                  BLUE, ORANGE, RED)
from rapor_olustur import P, bullets, figure, table, h1, h2  # noqa: E402
from reportlab.lib.enums import TA_CENTER  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.lib.units import cm  # noqa: E402
from reportlab.platypus import NextPageTemplate, PageBreak, Spacer, CondPageBreak  # noqa: E402

PROJ = br.PROJ
HERE = os.path.dirname(os.path.abspath(__file__))
FIG = f"{HERE}/geofig"
os.makedirs(FIG, exist_ok=True)
OUT = f"{PROJ}/rapor/02_Dedektor_Raporlari/Dedektor_Geometrisi_Raporu.pdf"
TITLE = "Dedektör Geometrisi Raporu"
import cikti_raporu_olustur as _co  # noqa: E402
_co.TITLE = TITLE  # sayfa üst bilgisindeki başlık
ICE = f"{PROJ}/build/data/scan/E1TeV_ice_properties.csv"
EVENTS = f"{PROJ}/build/data/scan/E1TeV_events.csv"
LAYER_COLORS = ["#08306b", "#2171b5", "#9e9ac8", "#6baed6"]


# ------------------------------------------------------------------ yeni figürler
def fig_layers(path):
    at = pd.read_csv(ICE)
    at = at[at.wavelength_nm == 400].sort_values("depth_m")
    fig, ax = plt.subplots(figsize=(9, 4.6))
    y = np.arange(len(at))
    ax.barh(y + 0.2, at.abs_length_m, 0.38, color=BLUE, label="soğurma uzunluğu")
    ax.barh(y - 0.2, at.rayleigh_length_m, 0.38, color=ORANGE, label="saçılma uzunluğu (Rayleigh)")
    for yi, (a, r) in enumerate(zip(at.abs_length_m, at.rayleigh_length_m)):
        ax.text(a + 2, yi + 0.2, f"{a:.0f} m", va="center", fontsize=9)
        ax.text(r + 2, yi - 0.2, f"{r:.0f} m", va="center", fontsize=9)
    ax.set_yticks(y)
    ax.set_yticklabels([f"katman {int(L)}\n{d:.1f} m" for L, d in zip(at.layer, at.depth_m)])
    ax.invert_yaxis()
    dust = list(at.layer).index(2)
    ax.axhspan(dust - 0.5, dust + 0.5, color="#f3e9c6", zorder=0)
    ax.text(150, dust, "toz katmanı", va="center", ha="right", fontsize=10, color="#8a6d1d")
    ax.set_xlabel("400 nm (mavi) ışık için uzunluk [m]  –  uzun = berrak buz")
    ax.set_title("Buz katmanlarının berraklığı (üstte en sığ)")
    ax.legend(loc="lower right"); ax.set_xlim(0, 165)
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


def fig_dom(path):
    fig, ax = plt.subplots(figsize=(8.5, 5))
    ax.set_xlim(-2.6, 2.6); ax.set_ylim(-1.6, 1.6); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(Rectangle((-2.6, -1.6), 5.2, 3.2, fc="#e6f1fb", ec="none"))
    ax.text(-2.45, 1.4, "buz  (n ≈ 1,32)", fontsize=11, color="#1b4f8a")
    ax.add_patch(Circle((0, 0), 1.0, fc="#fde9b8", ec="#b07d12", lw=2))
    ax.add_patch(Circle((0, 0), 0.92, fc="#fff6dd", ec="none"))
    ax.text(0, 0.25, "DOM", ha="center", fontsize=14, fontweight="bold")
    ax.text(0, -0.05, "cam küre, r = 16,5 cm\nn = 1,48", ha="center", va="top", fontsize=9.5)
    # gelen foton
    ang = np.radians(140)
    p_in = np.array([np.cos(ang), np.sin(ang)])
    start = p_in*2.4 + np.array([0.3, 0.25])
    ax.add_patch(FancyArrowPatch(start, p_in*1.0, arrowstyle="-|>", mutation_scale=18, color=BLUE, lw=2))
    ax.text(*(start + np.array([0.05, 0.12])), "Cherenkov fotonu", color=BLUE, fontsize=10)
    ax.plot(*p_in, "o", color=RED, ms=9)
    ax.annotate("① sınırdan giriş:\n   'hit' olarak kaydedilir\n   (zaman, enerji, DOM no)",
                xy=p_in, xytext=(-2.5, -0.65), fontsize=9.5, arrowprops=dict(arrowstyle="->", color=RED))
    ax.annotate("② kuantum verimi (~%25):\n   foton gerçekten\n   algılandı mı?",
                xy=(0.55, -0.35), xytext=(1.15, -1.3), fontsize=9.5, arrowprops=dict(arrowstyle="->"))
    ax.annotate("③ foton içeride\n   yok edilir", xy=(0.4, 0.45), xytext=(1.2, 0.95), fontsize=9.5,
                arrowprops=dict(arrowstyle="->"))
    ax.set_title("Bir DOM bir fotonu nasıl sayar?", fontsize=12)
    fig.tight_layout(); fig.savefig(path, dpi=150); plt.close(fig)


def fig_tracks(path):
    ev = pd.read_csv(EVENTS).sort_values("event").head(20)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(12, 5.4))
    for ax, (i, j, xl, yl, title) in zip((a1, a2), [(0, 1, "x [m]", "y [m]", "(a) Üstten görünüm"),
                                                    (0, 2, "x [m]", "z [m] (yukarı)", "(b) Yandan görünüm")]):
        ax.add_patch(Rectangle((-15, -15), 30, 30, fc="#f4f4f4", ec="#999999", ls="--"))
        ax.add_patch(Rectangle((-10, -10), 20, 20, fc="#dbeefc", ec="#2171b5", lw=1.5))
        for k in range(1, 4) if j == 2 else []:
            ax.axhline(-10 + 5*k, xmin=1/6, xmax=5/6, color="#2171b5", lw=0.6)
        for s in range(9):
            x, y = ((s//3) - 1)*6, ((s % 3) - 1)*6
            if j == 1:
                ax.plot(x, y, "o", color="orange", mec="k", ms=10, zorder=4)
            elif s in (0, 3, 6):  # yandan görünümde x'e göre üst üste binen stringler
                ax.plot([x, x], [-10, 10], "k", lw=0.8)
                for L in range(4):
                    ax.plot(x, -7.5 + 5*L, "o", color="orange", mec="k", ms=9, zorder=4)
        for _, e in ev.iterrows():
            p0 = np.array([e.x0_mm, e.y0_mm, e.z0_mm])/1000
            d = np.array([e.dir_x, e.dir_y, e.dir_z])
            seg = np.array([p0, p0 + 28*d])
            ax.plot(seg[:, i], seg[:, j], color=RED, lw=0.9, alpha=0.6)
            ax.plot(p0[i], p0[j], ".", color=RED, ms=5)
        ax.set_xlim(-16, 16); ax.set_ylim(-16, 16); ax.set_aspect("equal")
        ax.set_xlabel(xl); ax.set_ylabel(yl); ax.set_title(title)
    a1.text(-14.5, 14, "dünya hacmi (vakum)", fontsize=8.5, color="#666666")
    a1.annotate("müonlar\nbu yöne gider", xy=(-4.5, -13), xytext=(3.5, -13.6), fontsize=9, color=RED,
                arrowprops=dict(arrowstyle="->", color=RED))
    a2.text(-14.5, 13.8, "müon hafifçe yukarı doğru gider", fontsize=8.5, color=RED)
    fig.suptitle("1 TeV koşusunun ilk 20 müon izi (noktalar: başlangıç noktaları)", fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.95]); fig.savefig(path, dpi=150); plt.close(fig)


# ------------------------------------------------------------------ içerik
def build():
    figs = {k: f"{FIG}/{k}.png" for k in ("3d", "hier", "num", "layers", "optics", "dom", "tracks")}
    kr.fig_3d(figs["3d"]); kr.fig_hierarchy(figs["hier"]); kr.fig_numbering(figs["num"])
    kr.fig_optics(figs["optics"]); fig_layers(figs["layers"]); fig_dom(figs["dom"]); fig_tracks(figs["tracks"])

    st = []
    title = ParagraphStyle("tt", fontName="Serif-B", fontSize=24, leading=32, alignment=TA_CENTER,
                           textColor=br.NAVY)
    cs = ParagraphStyle("cs", fontName="Serif", fontSize=12.5, leading=19, alignment=TA_CENTER)
    st += [Spacer(1, 5*cm), P(TITLE.upper(), title), Spacer(1, 0.6*cm),
           P("IceCube tipi Geant4 simülasyonunda kullanılan buz dedektörünün yapısı", cs),
           Spacer(1, 6*cm), P(f"<b>Hazırlayan:</b> {br.STUDENT} ({br.STUDENT_NO})", cs),
           P(f"<b>Danışman:</b> {br.ADVISOR}", cs), Spacer(1, 3*cm), P("Erciyes Üniversitesi – " + br.DATE, cs),
           NextPageTemplate("normal"), PageBreak()]

    # ---------------------------------------------------------- bir bakışta
    st += [P("BİR BAKIŞTA", h1),
           P("Simülasyonda kullanılan dedektör, Güney Kutbu'ndaki IceCube Nötrino Gözlemevi'nin küçültülmüş bir "
             "modelidir: derin buzun içine dikey kablolar (string) üzerinde dizilmiş ışık sensörlerinden (DOM) "
             "oluşur. Aşağıdaki kartlar dedektörün temel ölçülerini özetler."),
           kpi_cards([("20 m", "buz bloğunun kenarı<br/>(20 × 20 × 20 m küp)"),
                      ("4", "derinliğe göre farklı<br/>buz katmanı (5'er m)"),
                      ("9", "dikey string<br/>(3 × 3 düzen)"),
                      ("36", "optik sensör (DOM)<br/>(string başına 4)"),
                      ("6 m / 5 m", "stringler arası /<br/>DOM'lar arası mesafe"),
                      ("33 cm", "DOM çapı<br/>(gerçek IceCube DOM'u ile aynı)")]),
           Spacer(1, 10),
           P("<b>Beş temel nokta</b>", h2),
           *bullets([
               "Dedektör üç iç içe parçadan oluşur: vakum <b>dünya</b> kutusu → 4 <b>buz katmanı</b> → 36 <b>DOM</b>.",
               "Her DOM'un 0–35 arası bir kimlik numarası vardır: <b>ID = 4 × string + DOM</b>.",
               "Buz katmanları aynı kırılma indisine ama farklı berraklığa sahiptir; üstten ikinci katman tozludur.",
               "DOM, içine giren her fotonu kaydeder ve fotoçoğaltıcının kuantum verimiyle 'algılandı' olarak işaretler.",
               "String aralığı ve buz modeli (Rayleigh / Mie) koda dokunmadan makro dosyasından değiştirilebilir."]),
           ]

    # ---------------------------------------------------------- 1 genel
    st += [PageBreak(), P("1. GENEL GÖRÜNÜM", h1),
           figure(figs["3d"], 13.5, "Dedektörün üç boyutlu görünümü: dört buz katmanı, 9 string (S0–S8), "
                  "36 DOM (turuncu) ve TXS 0506+056 yönünden gelen örnek bir müon izi (kırmızı)."),
           see("20 m'lik bir buz küpü dört yatay katmana bölünmüştür. Küpün içinde 3 × 3 düzende 9 dikey string "
               "vardır; her stringde her katmanın ortasında bir DOM bulunur. Koordinat sisteminin merkezi küpün "
               "merkezidir ve <b>z ekseni yukarıyı</b> gösterir (z arttıkça derinlik azalır)."),
           means("Gerçek IceCube'da da DOM'lar dikey kablolar üzerinde, düzenli bir ızgara halinde buza "
                 "gömülüdür. Bu model aynı düzeni çok daha küçük ölçekte kurar; böylece aynı fizik (Cherenkov ışığı, "
                 "buzda soğurma ve saçılma, sensör tepkisi) bir dizüstü bilgisayarda simüle edilebilir."),
           ]

    # ---------------------------------------------------------- 2 hacimler
    st += [PageBreak(), P("2. PARÇALAR VE BOYUTLARI", h1),
           figure(figs["hier"], 15.5, "Hacim hiyerarşisi: dünya hacmi dört buz katmanını, her buz katmanı "
                  "dokuz DOM'u içerir."),
           table([["Parça", "Şekil", "Boyut", "Malzeme"],
                  ["Dünya hacmi", "kutu", "30 × 30 × 30 m", "vakum (G4_Galactic)"],
                  ["Buz katmanı (×4)", "kutu", "20 × 20 × 5 m", "buz, yoğunluk 0,917 g/cm³"],
                  ["DOM (×36)", "küre", "yarıçap 16,51 cm", "Pyrex cam, kırılma indisi 1,48"]],
                 [4.0, 2.2, 4.4, 5.8], "Dedektör parçaları.", align_center_cols=(1, 2)),
           see("Geant4'te her parça bir 'anne' hacmin içine yerleştirilir. Buz katmanları dünya hacminin, DOM'lar "
               "ise bulundukları buz katmanının içindedir. Bilgisayar, parçaların birbirinin içine taşmadığını "
               "(çakışma kontrolü) her koşunun başında doğrular."),
           means("<b>Dünya neden vakum?</b> Buzdan çıkan ışığın takibine gerek yoktur; vakumun kırılma indisi "
                 "tanımlanmadığı için ışık buzun sınırında yok olur ve 'dedektörden kaçmış' sayılır. <b>Katmanlar "
                 "neden ayrı?</b> Geant4'te optik özellikler malzemeye bağlıdır; derinliğe göre farklı berraklık için "
                 "her katman ayrı bir buz malzemesidir."),
           ]

    # ---------------------------------------------------------- 3 yerleşim
    rows = [["String", "x (m)", "y (m)", "DOM kimlikleri (alttan üste)"]]
    for s in range(9):
        rows.append([f"S{s}", f(((s//3) - 1)*6), f(((s % 3) - 1)*6), f"{4*s}, {4*s+1}, {4*s+2}, {4*s+3}"])
    st += [PageBreak(), P("3. SENSÖRLERİN YERLEŞİMİ VE NUMARALARI", h1),
           figure(figs["num"], 16.0, "Sensör numaralandırması. (a) Üstten: string numaraları. (b) Yandan "
                  "(y = 0 kesiti): DOM kimlikleri ve katmanlar."),
           P("Her DOM'un kimliği, bulunduğu string (s) ve string üzerindeki sırası (DOM 0 = en derin) ile "
             "hesaplanır: <b>ID = 4 × s + DOM</b>. String numarası da ızgaradaki konumdan gelir: s = 3 × i<sub>x</sub> + "
             "i<sub>y</sub> (i<sub>x</sub>, i<sub>y</sub> = 0, 1, 2)."),
           table(rows, [2.2, 2.4, 2.4, 9.4], "String konumları ve üzerlerindeki DOM'lar (aralık 6 m).",
                 align_center_cols=(0, 1, 2, 3)),
           see("Stringler x ve y yönünde −6, 0 ve +6 m'dedir. Her stringde DOM'lar z = −7,5 / −2,5 / +2,5 / "
               "+7,5 m yüksekliklerinde, yani her buz katmanının tam ortasındadır."),
           means("Bir foton bir DOM'a girdiğinde Geant4 o DOM'un kimliğini verir. Kimlikten DOM'un konumu ve "
                 "derinliği hemen bulunabilir; analizdeki ısı haritaları ve yön hesabı bu numaralandırmaya dayanır."),
           ]

    # ---------------------------------------------------------- 4 katmanlar
    st += [PageBreak(), P("4. BUZ KATMANLARI VE DERİNLİK", h1),
           figure(figs["layers"], 14.0, "Her buz katmanında 400 nm (mavi) ışık için soğurma ve saçılma uzunlukları. "
                  "Uzunluk ne kadar büyükse buz o kadar berraktır."),
           table([["Katman", "Derinlik", "z aralığı", "Soğurma (400 nm)", "Saçılma (400 nm)", "Not"],
                  ["3", "2002,5 m", "+5 … +10 m", "87 m", "28 m", "en sığ"],
                  ["2", "2007,5 m", "0 … +5 m", "44 m", "12 m", "toz katmanı"],
                  ["1", "2012,5 m", "−5 … 0 m", "106 m", "35 m", "berrak"],
                  ["0", "2017,5 m", "−10 … −5 m", "142 m", "45 m", "en berrak, en derin"]],
                 [1.6, 2.2, 2.6, 3.0, 3.0, 4.0], "Buz katmanlarının optik değerleri.",
                 align_center_cols=(0, 1, 2, 3, 4)),
           see("En derindeki katman en berrak buzdur: mavi ışık soğurulmadan ~140 m yol alabilir. Üstten ikinci "
               "katman (katman 2) tozludur; ışık yalnızca ~44 m'de soğurulur ve ~12 m'de bir saçılır."),
           means("Antarktika buzundaki toz miktarı, buzun oluştuğu dönemin iklimine bağlıdır; bu yüzden berraklık "
                 "derinlikle değişir. Gerçek IceCube'da da yaklaşık 2000 m derinlikte belirgin bir toz katmanı vardır. "
                 "Değerler bu davranışı yansıtacak şekilde seçilmiş temsili değerlerdir."),
           ]

    # ---------------------------------------------------------- 5 optik
    st += [PageBreak(), P("5. BUZUN IŞIĞA ETKİSİ", h1),
           figure(figs["optics"], 15.5, "Simülasyonda tanımlı optik özellikler: (a) kırılma indisi, (b) soğurma "
                  "uzunluğu, (c) Rayleigh (düz) ve Mie (kesikli) saçılma uzunlukları, (d) DOM kuantum verimi."),
           table([["Özellik", "Ne işe yarar?"],
                  ["Kırılma indisi n(λ)", "Cherenkov ışığının açısını (~41°) ve miktarını belirler; renge göre biraz değişir (dispersiyon)."],
                  ["Soğurma uzunluğu", "Işığın ortalama ne kadar yol alıp yok olduğu; kırmızı ışık çok daha çabuk soğurulur."],
                  ["Rayleigh saçılması", "Işığın her yöne saçılması; mavi ışık daha çok saçılır (∝ λ<super>−4</super>)."],
                  ["Mie saçılması", "İleri yönlü saçılma; gerçek buza daha yakındır. Makrodan Rayleigh yerine seçilebilir."],
                  ["Kuantum verimi", "DOM'a giren fotonun algılanma olasılığı; ~380 nm'de en yüksek (~%26)."]],
                 [4.2, 12.2], "Optik özellikler ve görevleri."),
           see("Kırılma indisi 300–600 nm arasında 1,33'ten 1,31'e iner. Soğurma uzunluğu 500 nm'den sonra hızla "
               "kısalır. Saçılma kısa dalga boylarında (mavi-mor) daha sıktır."),
           means("Cherenkov ışığı çoğunlukla mavi-mordur; DOM'un da en duyarlı olduğu bölge burasıdır. Kırmızı ışık "
                 "uzağa gidemediği için sensörlere ulaşan ışık 'maviye kaymış' olur."),
           ]

    # ---------------------------------------------------------- 6 DOM
    st += [PageBreak(), P("6. OPTİK SENSÖR (DOM)", h1),
           figure(figs["dom"], 13.0, "Bir DOM'un bir fotonu sayma adımları."),
           see("DOM, 33 cm çapında bir cam küredir. Cama kırılma indisi verildiği için foton buzdan cama geçebilir; "
               "bu sırada gerçek hayattaki gibi kırılabilir ya da yansıyabilir. Foton cama girdiği anda kaydedilir "
               "(DOM kimliği, zaman, enerji), ardından kuantum verimine göre 'algılandı' ya da 'algılanmadı' olarak "
               "işaretlenir ve yok edilir."),
           means("Gerçek bir DOM'da foton fotoçoğaltıcı tüpün katoduna çarpar ve yalnızca yaklaşık dörtte bir "
                 "olasılıkla elektrik sinyaline dönüşür. Simülasyon hem DOM'a ulaşan tüm fotonları hem de "
                 "algılananları ayrı ayrı sakladığı için iki durum karşılaştırılabilir. DOM'un içinde (camda) oluşan "
                 "ışık sayılmaz; yalnızca dışarıdan gelen ışık kaydedilir."),
           ]

    # ---------------------------------------------------------- 7 müon
    st += [PageBreak(), P("7. MÜONLAR DEDEKTÖRE NEREDEN GİRER?", h1),
           figure(figs["tracks"], 16.2, "1 TeV koşusundaki ilk 20 müonun izi. Gri kesikli çerçeve dünya hacmidir."),
           see("Müonlar dedektörün 14 m dışından başlar ve TXS 0506+056 blazarından uzaklaşan yönde, hemen hemen "
               "yatay ve hafifçe yukarı doğru ilerler. Her müon, dedektör merkezinden en fazla 3 m kayacak şekilde "
               "rastgele seçilmiş bir yoldan geçer; böylece her olay farklı DOM'ları farklı uzaklıklardan aydınlatır. "
               "Buzdaki yol uzunluğu ~20,6 m'dir."),
           means("Kaynak (Dec = +5,7°) Güney Kutbu'nda ufkun hemen altındadır; bu yüzden müon Dünya'nın içinden "
                 "geçip aşağıdan yukarı gelir. IceCube kuzey gökyüzünü bu tür 'yukarı yönlü' müonlarla gözler, çünkü "
                 "Dünya atmosferden gelen müonlar için kalkan görevi görür. Yöne eklenen 0,5°'lik rastgele sapma, "
                 "nötrino ile müon arasındaki küçük açıyı temsil eder."),
           ]

    # ---------------------------------------------------------- 8 ayarlar
    st += [PageBreak(), P("8. DEĞİŞTİRİLEBİLİR AYARLAR", h1),
           P("Geometrinin ve kaynağın bazı özellikleri koda dokunmadan, makro dosyasındaki komutlarla değiştirilebilir:"),
           table([["Makro komutu", "Varsayılan", "Neyi değiştirir?"],
                  ["/icecube/stringSpacing 6 m", "6 m", "Stringler arası mesafe (/run/initialize'dan önce yazılmalı)"],
                  ["/process/inactivate OpMieHG", "–", "Buz modeli: yalnız Rayleigh saçılması (varsayılan)"],
                  ["/process/inactivate OpRayleigh", "–", "Buz modeli: yalnız Mie saçılması (gerçeğe yakın)"],
                  ["/icecube/sourceRA, sourceDec", "77,358°, 5,693°", "Müonların geldiği kaynak (TXS 0506+056)"],
                  ["/icecube/offsetRadius", "3 m", "İzin dedektör merkezinden ne kadar kayabileceği"],
                  ["/icecube/angularSpread", "0,5°", "Müon yönündeki rastgele sapma"]],
                 [5.6, 3.0, 7.8], "Geometri ve kaynakla ilgili makro komutları."),
           see("Tez çalışmasında string aralığı 4, 6 ve 8 m olarak denenmiş; buz modeli Rayleigh ve Mie olarak "
               "değiştirilmiştir. Buz katman sayısı, blok boyutu ve DOM boyutu ise kodda sabittir."),
           means("Ayarların makrodan değiştirilebilmesi, aynı programla farklı dedektör tasarımlarının "
                 "karşılaştırılmasını sağlar. Bir tasarımın ne kadar ışık topladığı ve müon yönünü ne kadar iyi "
                 "bulduğu, Dedektör Çıktı Raporu'nda incelenmiştir."),
           ]

    # ---------------------------------------------------------- 9 IceCube
    st += [PageBreak(), P("9. GERÇEK ICECUBE İLE KARŞILAŞTIRMA", h1),
           table([["Özellik", "Bu simülasyon", "IceCube"],
                  ["Hacim", "8.000 m³ (20 m küp)", "~1 km³ (10<super>9</super> m³)"],
                  ["String sayısı", "9", "86"],
                  ["DOM sayısı", "36", "5.160"],
                  ["String başına DOM", "4", "60"],
                  ["Stringler arası mesafe", "6 m", "~125 m (DeepCore'da daha sık)"],
                  ["DOM'lar arası düşey mesafe", "5 m", "~17 m"],
                  ["Derinlik", "2000–2020 m", "1450–2450 m"],
                  ["DOM boyutu", "33 cm cam küre", "33 cm cam küre"]],
                 [5.2, 5.4, 5.8], "Simülasyondaki dedektör ile IceCube'un karşılaştırılması.",
                 align_center_cols=(1, 2)),
           see("Bu model IceCube'dan yaklaşık 125.000 kat küçük bir hacmi kaplar ve 143 kat daha az sensöre sahiptir. "
               "Buna karşılık sensörler çok daha sık yerleştirilmiştir; DOM boyutu ve derinlik ise gerçeğe uygundur."),
           means("Sık yerleşim, küçük hacimde bile her olayda tüm DOM'ların ışık görmesini sağlar. Ancak müon izi "
                 "yalnızca ~20 m boyunca izlenebildiği için yön ve enerji ölçümü gerçek IceCube kadar hassas olamaz. "
                 "Bu model, IceCube'un çalışma prensibini anlamak ve tasarım değişikliklerinin etkisini görmek için "
                 "uygun bir 'laboratuvar' ölçeğindedir."),
           ]

    # ---------------------------------------------------------- sözlük
    st += [PageBreak(), P("TERİMLER SÖZLÜĞÜ", h1),
           table([["Terim", "Anlamı"],
                  ["DOM", "Digital Optical Module: içinde fotoçoğaltıcı tüp bulunan cam küre; ışık sensörü."],
                  ["String", "Üzerine DOM'ların dizildiği dikey kablo."],
                  ["Dünya hacmi", "Simülasyonun tamamını içine alan en dış kutu."],
                  ["Kırılma indisi", "Işığın ortamdaki yavaşlama oranı; buz için ~1,32."],
                  ["Soğurma uzunluğu", "Işığın yok olmadan ortalama alabildiği yol."],
                  ["Saçılma uzunluğu", "Işığın yönü değişmeden ortalama alabildiği yol."],
                  ["Rayleigh / Mie saçılması", "Işığın küçük parçacıklarla yön değiştirmesi; Mie ileri yönlüdür."],
                  ["Kuantum verimi", "Bir fotonun sensörde sinyale dönüşme olasılığı."],
                  ["Toz katmanı", "Buzun daha çok toz içeren, ışığı daha çok soğuran ve saçan bölümü."],
                  ["Makro komutu", "Programı yeniden derlemeden ayar değiştiren metin komutu (/icecube/...)."],
                  ["TXS 0506+056", "2017'de bir IceCube nötrinosuyla ilişkilendirilen BL Lac türü blazar."]],
                 [4.4, 12.0], "Raporda geçen terimler."),
           ]

    doc = OutDoc(OUT, title=TITLE, author=br.STUDENT, subject="Dedektör geometrisi")
    doc.multiBuild(st)
    print("PDF:", OUT)


if __name__ == "__main__":
    build()

#!/usr/bin/env python3
"""Her enerji için ayrı PDF: fizik (8 panel) ve AGN (6 panel) grafikleri panel panel, adım adım açıklanır.
Ayrıca enerjiler arası karşılaştırma grafikleri için bir genel PDF üretilir.

Çıktı:     rapor/06_Enerji_Grafikleri/
Önkoşul:   python3 analysis/analyze.py build/data/detail/E<E>TeV build/data/scan/E<E>TeV   (her enerji için;
           panel PNG'lerini <önek>_panels/ altına yazar) ve python3 analysis/thesis.py
Kullanım:  python3 enerji_grafikleri_olustur.py [enerji ...]     (enerji verilmezse hepsi)
"""
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rapor_olustur as br  # noqa: E402  (yazı tipleri, stiller, yardımcılar)
from rapor_olustur import P, bullets, table, h1, h2, body, NAVY  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.enums import TA_CENTER  # noqa: E402
from reportlab.lib.pagesizes import A4  # noqa: E402
from reportlab.lib.styles import ParagraphStyle  # noqa: E402
from reportlab.lib.units import cm  # noqa: E402
from reportlab.platypus import CondPageBreak, Image, KeepTogether, NextPageTemplate, PageBreak, Spacer  # noqa: E402

cm_ = br.cm_
DATA = br.DATA
OUTDIR = f"{br.PROJ}/rapor/06_Enerji_Grafikleri"
ENERGIES = [0.1, 0.3, 1, 3, 10, 30, 100]
TXS = (77.358, 5.693)

title_st = ParagraphStyle("tt", fontName="Serif-B", fontSize=21, leading=29, alignment=TA_CENTER, textColor=NAVY)
sub_st = ParagraphStyle("cs", fontName="Serif", fontSize=12, leading=18, alignment=TA_CENTER)
step_st = ParagraphStyle("adim", parent=body, leftIndent=12, spaceAfter=5)


def f(x, d=0):
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def Et(E):
    return f(E, 1) if E < 1 else f(E)


class PanelDoc(br.ReportDoc):
    def __init__(self, filename, header, **kw):
        self.header = header
        super().__init__(filename, **kw)

    def _decor(self, canv, doc):
        canv.saveState()
        canv.setFont("Serif", 8.5)
        canv.setFillColor(colors.HexColor("#555555"))
        canv.drawString(self.leftMargin, A4[1] - 1.4*cm, self.header)
        canv.drawRightString(A4[0] - self.rightMargin, A4[1] - 1.4*cm, "Yusuf AYDEMİR")
        canv.setStrokeColor(colors.HexColor("#9aa5b1")); canv.setLineWidth(0.4)
        canv.line(self.leftMargin, A4[1] - 1.55*cm, A4[0] - self.rightMargin, A4[1] - 1.55*cm)
        canv.drawCentredString(A4[0]/2, 1.2*cm, str(doc.page - 1))
        canv.restoreState()


def img(path, width_cm, max_h_cm=12.5):
    from PIL import Image as PILImage
    w, h = PILImage.open(path).size
    W, H = width_cm, width_cm*h/w
    if H > max_h_cm:
        W, H = W*max_h_cm/H, max_h_cm
    return Image(path, width=W*cm, height=H*cm)


def panel(title, path, steps, width=13.5):
    """Panel başlığı + görüntü + numaralı adımlar (Ne gösteriyor / Nasıl okunur / Bu enerjide / Anlamı)."""
    head = [CondPageBreak(9*cm), P(title, h2), img(path, width), Spacer(1, 4)]
    return [KeepTogether(head)] + [P(f"<b>Adım {i}. {q}</b> {t}", step_st) for i, (q, t) in enumerate(steps, 1)]


def cover(title, subtitle):
    return [Spacer(1, 4.5*cm), P(title, title_st), Spacer(1, 0.6*cm), P(subtitle, sub_st), Spacer(1, 6*cm),
            P("<b>Hazırlayan:</b> Yusuf AYDEMİR (1110510281)", sub_st),
            P(f"<b>Danışman:</b> {br.ADVISOR}", sub_st), Spacer(1, 3*cm),
            P("Erciyes Üniversitesi – Kasım 2026", sub_st), NextPageTemplate("normal"), PageBreak()]


# ======================================================================= veriler
def stats(E):
    pre, scan = f"{DATA}/detail/E{E:g}TeV", f"{DATA}/scan/E{E:g}TeV"
    ev = pd.read_csv(f"{pre}_events.csv")
    el = pd.read_csv(f"{pre}_muon_energy_loss.csv")
    ph = pd.read_csv(f"{pre}_cherenkov_photons.csv",
                     usecols=["event", "parent_id", "px", "py", "pz", "wavelength_nm"])
    hits = pd.read_csv(f"{pre}_sensor_hits.csv",
                       usecols=["event", "sensor_id", "dom_id", "wavelength_nm", "time_ns", "detected"])
    sens = pd.read_csv(f"{pre}_sensors.csv")
    ice = pd.read_csv(f"{pre}_ice_properties.csv")
    reco = pd.read_csv(f"{scan}_reconstruction.csv")
    sc = pd.read_csv(f"{scan}_events.csv")
    groom = cm_.load_groom()
    s = dict(E=E, pre=pre, N=len(ev), Nreco=len(reco), L=ev.track_len_mm.mean()/1000)

    # (a), (b) enerji kaybı
    s["dedx"] = el.dE_MeV.sum()/(el.step_mm.sum()/10)
    s["groom"] = cm_.groom_dedx_ice(E*1e6, table=groom)
    s["groom_ion"] = cm_.groom_dedx_ice(E*1e6, "ion", table=groom)
    s["groom_rad"] = cm_.groom_dedx_ice(E*1e6, "rad", table=groom)
    s["ratio"] = s["dedx"]/s["groom"]
    s["loss_mean"], s["loss_med"] = ev.E_loss_MeV.mean()/1e3, ev.E_loss_MeV.median()/1e3
    s["loss_max"] = ev.E_loss_MeV.max()/1e3
    s["rad_share"] = 100*sc.E_loss_rad_MeV.sum()/sc.E_loss_MeV.sum()
    s["steps_ev"] = len(el)/len(ev)
    s["pair_ev"] = (el.process == "muPairProd").sum()/len(ev)
    s["brems_ev"] = (el.process == "muBrems").sum()/len(ev)
    s["nuc_ev"] = (el.process == "muonNuclear").sum()/len(ev)
    sd = el.dE_MeV/(el.step_mm/10).clip(lower=1e-6)
    s["step_max"] = sd.max()
    s["step_ion_med"] = sd[el.process.isin(["muIoni", "Cerenkov"])].median()

    # (c), (e), AGN 1: kaydedilen tek olayın fotonları
    e0 = ph.event.iloc[0]
    p0 = ph[ph.event == e0]
    prim = p0[p0.parent_id == 1]
    ev0 = ev.set_index("event").loc[e0]
    s["e0"], s["ph_e0"], s["prim_e0"] = int(e0), len(p0), 100*len(prim)/len(p0)
    s["loss_e0"] = ev0.E_loss_MeV/1e3
    s["ph_cm"] = len(prim)/(ev0.track_len_mm/10)
    mu = np.array([ev0.dir_x, ev0.dir_y, ev0.dir_z])
    ang = np.degrees(np.arccos(np.clip(prim[["px", "py", "pz"]].to_numpy() @ mu, -1, 1)))
    s["ang_mean"], s["ang_lo"], s["ang_hi"] = ang.mean(), np.percentile(ang, 2), np.percentile(ang, 98)

    # (d), (f), (g): optik
    lam = np.array([300., 400., 600.])
    n = cm_.n_phase(lam)
    s["n300"], s["n400"], s["n600"] = n
    s["ng400"] = cm_.n_group(np.array([400.]))[0]
    s["th300"], s["th600"] = np.degrees(np.arccos(1/n[0])), np.degrees(np.arccos(1/n[2]))
    i4 = ice[ice.wavelength_nm == 400].set_index("layer").sort_index()
    s["layers"] = i4
    s["ray300"] = ice[ice.wavelength_nm == 300].set_index("layer").rayleigh_length_m
    s["ray600"] = ice[ice.wavelength_nm == 600].set_index("layer").rayleigh_length_m
    per_layer = hits.groupby("dom_id").size()/len(ev)/9
    s["hits_layer"] = per_layer.reindex(range(4), fill_value=0)

    # (h) ışık – enerji kaybı
    s["ph_mean"], s["hits_mean"] = ev.n_photons.mean(), ev.n_hits.mean()
    s["det_mean"] = ev.n_detected.mean()
    s["prim_all"] = 100*ev.n_photons_primary.sum()/ev.n_photons.sum()
    s["ph_per_GeV"] = ev.n_photons.sum()/(ev.edep_total_MeV.sum()/1e3)
    s["light_spread"] = ev.n_photons.max()/ev.n_photons.min()
    ok = ev.E_loss_MeV > 0
    s["corr"] = np.corrcoef(np.log(ev.E_loss_MeV[ok]), np.log(ev.n_photons[ok]))[0, 1]
    s["eff_hit"] = 100*ev.n_hits.sum()/ev.n_photons.sum()
    s["eff_det"] = 100*ev.n_detected.sum()/ev.n_photons.sum()

    # AGN 2: spektrum
    s["lam_prod"] = ph.wavelength_nm.mean()
    s["lam_hit"] = hits.wavelength_nm.mean()
    s["lam_det"] = hits.loc[hits.detected == 1, "wavelength_nm"].mean()
    s["qe_frac"] = 100*hits.detected.mean()

    # AGN 3: zaman
    t_rel = hits.time_ns - hits.groupby("event").time_ns.transform("min")
    s["t_med"], s["late50"] = t_rel.median(), 100*(t_rel > 50).mean()
    s["t_layer"] = t_rel.groupby(hits.dom_id).median().reindex(range(4))

    # AGN 4: sensörler
    per_s = hits.groupby("sensor_id").size()/len(ev)
    top = per_s.sort_values(ascending=False)
    s["top_id"], s["top_val"] = int(top.index[0]), top.iloc[0]
    s["top_str"], s["top_dom"] = s["top_id"]//4, s["top_id"] % 4
    s["top4"] = 100*top.iloc[:4].sum()/top.sum()
    s["n_active"] = int((per_s > 0.01*top.iloc[0]).sum())

    # AGN 5–6: rekonstrüksiyon
    src = cm_.combined_source(reco)
    s["ra"], s["dec"], s["r90"], s["nused"] = src
    d = sorted((cm_.ang_dist(src[0], src[1], a[1], a[2]), a[0], a[3]) for a in cm_.AGN_CATALOG)
    s["agn_sorted"] = d
    s["txs"] = cm_.ang_dist(src[0], src[1], *TXS)
    s["fit"], s["lf"] = reco.err_fit_deg.median(), reco.err_linefit_deg.median()
    s["lt5"], s["lt1"] = 100*(reco.err_fit_deg < 5).mean(), 100*(reco.err_fit_deg < 1).mean()
    s["fit68"] = reco.err_fit_deg.quantile(0.68)
    return s


# ======================================================================= enerji PDF'i
def regime(E):
    if E < 0.5:
        return ("kritik enerjinin (≈ 1 TeV) belirgin biçimde altındadır; bu bölgede müon enerjisini neredeyse "
                "tamamen iyonizasyonla, yani atomik elektronlarla çarpışarak kaybeder")
    if E <= 2:
        return ("kritik enerji (≈ 1 TeV) civarındadır; iyonizasyon ve radyatif kayıplar burada yaklaşık eşit "
                "büyüklüktedir")
    return ("kritik enerjinin (≈ 1 TeV) üstündedir; bu bölgede radyatif kayıplar (çift üretimi, frenleme ışıması, "
            "fotonükleer etkileşme) baskındır ve toplam kayıp enerjiyle neredeyse doğru orantılı artar")


def energy_story(s):
    E, N = s["E"], s["N"]
    L4 = s["layers"]
    dust = int(L4.abs_length_m.idxmin())
    hl = s["hits_layer"]
    second = s["agn_sorted"][1]
    samp = ("" if abs(s["ratio"] - 1) <= 0.15 else
            f" Simülasyon ile tablo arasındaki fark (oran {f(s['ratio'], 2)}) beklenen bir istatistik etkisidir: "
            f"ortalamayı seyrek ama çok büyük radyatif kayıplar belirler ve yalnızca {N} olayda bu kayıplar eksik "
            f"ya da fazla örneklenebilir. Aynı ölçüm çok daha fazla olayla yapıldığında ortalama tabloya yaklaşır.")
    story = cover(f"{Et(E)} TeV MÜON", "Fizik ve AGN grafiklerinin panel panel, adım adım açıklaması")

    # ------------------------------------------------------------- giriş
    story += [P("BU BELGE NE ANLATIYOR?", h1),
              P(f"Bu belgede, buzdaki IceCube tipi dedektör modelimizde <b>{Et(E)} TeV</b> enerjili müonlar için "
                f"üretilen iki grafik (8 panelli fizik grafiği ve 6 panelli AGN grafiği) panel panel incelenmektedir. "
                f"Her panel dört adımda açıklanır: (1) panelin ne gösterdiği, (2) nasıl okunacağı, (3) bu enerjide ne "
                f"görüldüğü (bu koşunun kendi sayılarıyla) ve (4) fiziksel anlamı."),
              P(f"Müonlar, TXS 0506+056 blazarının gök konumundan (RA = 77,36°, Dec = +5,69°) hesaplanan yönde, "
                f"0,5° açısal yayılımla gönderilmiştir. Dedektör 20 m × 20 m × 20 m'lik, dört katmanlı bir buz bloğu "
                f"ve 3 × 3 string üzerindeki 36 optik sensörden (DOM) oluşur. Grafikler iki koşudan gelir:"),
              *bullets([
                  f"<b>Ayrıntılı koşu ({N} olay):</b> tek tek foton, sensör vuruşu ve müon adımı kaydedilmiştir. Fizik "
                  f"grafiğinin tamamı ve AGN grafiğinin 1–4. panelleri bu koşudandır.",
                  f"<b>Enerji taraması koşusu ({s['Nreco']} olay):</b> yalnızca olay ve sensör özetleri kaydedilmiştir. "
                  f"AGN grafiğinin 5–6. panelleri (kaynak eşleşmesi, gökyüzü haritası) bu daha büyük örnekten "
                  f"hesaplanmıştır."]),
              table([["Büyüklük", "Değer"],
                     ["Müon enerjisi", f"{Et(E)} TeV"],
                     ["Buzdaki ortalama iz uzunluğu", f"{f(s['L'], 1)} m"],
                     ["Ortalama / medyan enerji kaybı", f"{f(s['loss_mean'], 1)} GeV / {f(s['loss_med'], 1)} GeV"],
                     ["Ortalama dE/dx (simülasyon / Groom)", f"{f(s['dedx'], 2)} / {f(s['groom'], 2)} MeV/cm"],
                     ["Radyatif kayıp payı", f"%{f(s['rad_share'])}"],
                     ["Olay başına üretilen Cherenkov fotonu", f(s["ph_mean"])],
                     ["Birincil müonun ışıktaki payı", f"%{f(s['prim_all'])}"],
                     ["Olay başına DOM'a ulaşan / algılanan foton", f"{f(s['hits_mean'])} / {f(s['det_mean'])}"],
                     ["Cherenkov fitinin medyan açısal hatası", f"{f(s['fit'], 2)}°"],
                     ["Birleşik kaynağın TXS 0506+056'ya uzaklığı", f"{f(s['txs'], 2)}° (hata yarıçapı {f(s['r90'], 2)}°)"]],
                    [9.0, 7.4], f"{Et(E)} TeV koşusunun özet sayıları.")]

    # ------------------------------------------------------------- fizik grafiği
    ppath = f"{s['pre']}_panels/physics"
    story += [PageBreak(), P("1. FİZİK GRAFİĞİ (8 PANEL)", h1),
              P("Aşağıda grafiğin tamamı, ardından her paneli tek tek büyütülmüş olarak verilmiştir."),
              img(f"{s['pre']}_physics.png", 13.0, max_h_cm=19.0)]

    story += panel("(a) Bethe-Bloch eğrisi: enerji kaybı – müon enerjisi", f"{ppath}/1.png", [
        ("Ne gösteriyor?", "Bir müonun buzda birim yol başına kaybettiği ortalama enerjiyi (dE/dx) müon enerjisinin "
         "fonksiyonu olarak gösteren kuramsal eğrileri ve bu koşunun simülasyondaki ortalama değerini."),
        ("Nasıl okunur?", "İki eksen de logaritmiktir: yatay eksen 10 MeV'den 100 TeV'e müon enerjisi (GeV), dikey "
         "eksen MeV/cm cinsinden kayıptır. Mavi çizgi iyonizasyon (Bethe-Bloch), turuncu çizgi radyatif kayıp (b·E), "
         "siyah çizgi ikisinin toplamıdır. Mavi ile turuncunun kesiştiği nokta kritik enerjidir (≈ 1 TeV). Kırmızı "
         "nokta bu koşunun simülasyon ortalamasıdır; siyah eğriye ne kadar yakınsa simülasyon kurama o kadar uyar."),
        ("Bu enerjide ne görüyoruz?", f"Kırmızı nokta {Et(E)} TeV'de {f(s['dedx'], 2)} MeV/cm değerindedir. Groom/PDG "
         f"tablosunun toplam değeri {f(s['groom'], 2)} MeV/cm, bunun iyonizasyon kısmı {f(s['groom_ion'], 2)}, "
         f"radyatif kısmı {f(s['groom_rad'], 2)} MeV/cm'dir.{samp}"),
        ("Ne anlama geliyor?", f"Bu enerji {regime(E)}. Müonun buzda bıraktığı enerji Cherenkov ışığına dönüştüğü "
         f"için, bu panel aynı zamanda ışık miktarının neden düşük enerjide hemen hemen sabit, yüksek enerjide ise "
         f"hızla artan bir büyüklük olduğunu açıklar.")])

    story += panel("(b) Adım başına enerji kaybı (sürece göre)", f"{ppath}/2.png", [
        ("Ne gösteriyor?", "Geant4'ün müonu izlerken attığı her adımda kaybedilen enerjinin, adım boyuna bölünmüş "
         "hâlinin (adım dE/dx) dağılımını; her renk adımı sonlandıran fiziksel süreçtir."),
        ("Nasıl okunur?", "İki eksen de logaritmiktir. 1–3 MeV/cm civarındaki dar tepe, her adımda uygulanan sürekli "
         "iyonizasyon kaybıdır (Cerenkov ve muIoni etiketli adımlar). muIoni dağılımının sağa uzanan kuyruğu, tek "
         "çarpışmada yüksek enerjili δ-elektronu sökülen adımlardır. Sağda, 10–10<super>6</super> MeV/cm aralığındaki "
         "muPairProd (e<super>+</super>e<super>−</super> çift üretimi), muBrems (frenleme ışıması) ve muonNuclear "
         "(fotonükleer) adımları seyrek ama çok büyük 'felaket' kayıplardır. Not: etiket, adımı bitiren süreçtir; "
         "örneğin 'Cerenkov' adımlarındaki kayıp aslında iyonizasyondur."),
        ("Bu enerjide ne görüyoruz?", f"Müon olay başına ortalama {f(s['steps_ev'])} adım atmıştır. Sürekli kayıp "
         f"tepesinin medyanı {f(s['step_ion_med'], 2)} MeV/cm'dir. Olay başına ortalama {f(s['pair_ev'], 1)} çift "
         f"üretimi, {f(s['brems_ev'], 2)} frenleme ışıması ve {f(s['nuc_ev'], 2)} fotonükleer adımı vardır. En büyük "
         f"tek adım kaybı {f(s['step_max'])} MeV/cm'dir."),
        ("Ne anlama geliyor?", "Enerji kaybı iki farklı karakterdedir: her adımda küçük ve düzenli (iyonizasyon) ile "
         "seyrek ve dev (radyatif). Ortalamayı seyrek büyük kayıplar belirlediği için aynı enerjideki iki müonun "
         "bıraktığı enerji, dolayısıyla ürettiği ışık, çok farklı olabilir. Buna stokastik kayıp denir.")])

    story += panel("(c) Frank-Tamm karşılaştırması", f"{ppath}/3.png", [
        ("Ne gösteriyor?", "Yalnızca birincil müonun ürettiği Cherenkov fotonlarının, birim iz uzunluğu ve birim foton "
         "enerjisi başına sayısını (mavi) Frank-Tamm bağıntısının öngörüsüyle (siyah kesikli) karşılaştırır."),
        ("Nasıl okunur?", "Yatay eksen foton enerjisidir (2,07 eV ≈ 600 nm, 4,13 eV ≈ 300 nm). Dikey eksen "
         "dN/(dx·dE), yani cm ve eV başına foton sayısıdır. İki eğrinin üst üste binmesi, Geant4'ün Cherenkov ışığını "
         "kuramla aynı miktarda ürettiğini gösterir. Başlıktaki sayı 300–600 nm arasındaki toplam foton/cm değeridir."),
        ("Bu enerjide ne görüyoruz?", f"Kaydedilen olayda (olay {s['e0']}) birincil müon {f(s['ph_cm'])} foton/cm "
         f"üretmiştir; kuramsal değer ≈ 326 foton/cm'dir. Eğri foton enerjisiyle hafifçe yükselir, çünkü kırılma "
         f"indisi mavide daha büyüktür ve (1 − 1/n²) çarpanı artar."),
        ("Ne anlama geliyor?", "Birincil müon her enerjide ışık hızına çok yakın gittiği için (β ≈ 1) birim yolda aynı "
         "sayıda foton üretir; bu sayı enerjiden bağımsızdır. Dolayısıyla toplam ışığın enerjiyle artması birincil "
         "müondan değil, onun başlattığı ikincil parçacıklardan (δ-elektronları ve kaskadlar) gelir.")])

    story += panel("(d) Dispersiyon: kırılma indisi ve Cherenkov açısı", f"{ppath}/4.png", [
        ("Ne gösteriyor?", "Buzun faz kırılma indisi n (mavi), grup kırılma indisi n<sub>g</sub> (turuncu) ve bunlardan "
         "hesaplanan Cherenkov açısının (kırmızı kesikli, sağ eksen) dalga boyuna bağlılığını."),
        ("Nasıl okunur?", "Sol eksen kırılma indisi, sağ eksen derece cinsinden Cherenkov açısıdır. Gri noktalı çizgi "
         "sık kullanılan sabit n = 1,325 değeridir. Eğrilerin sola doğru (maviye doğru) yükselmesi dispersiyondur."),
        ("Bu enerjide ne görüyoruz?", f"n, 300 nm'de {f(s['n300'], 3)}, 400 nm'de {f(s['n400'], 3)}, 600 nm'de "
         f"{f(s['n600'], 3)} değerindedir; 400 nm'de grup indisi {f(s['ng400'], 3)} olur. Cherenkov açısı 300 nm'de "
         f"{f(s['th300'], 1)}°, 600 nm'de {f(s['th600'], 1)}°'dir. Bu panel buzun özelliğidir ve enerjiden bağımsızdır; "
         f"tüm enerjilerde aynıdır."),
        ("Ne anlama geliyor?", "Işık sinyali buzda faz hızıyla değil grup hızıyla (c/n<sub>g</sub>) ilerler; bu yüzden "
         "yön rekonstrüksiyonunda beklenen varış zamanı grup indisiyle hesaplanır. Mavi ışığın daha yavaş gitmesi, "
         "uzak sensörlerde sinyalin zamanca hafifçe yayılmasına da katkı yapar.")])

    story += panel("(e) Cherenkov konisi açısı", f"{ppath}/5.png", [
        ("Ne gösteriyor?", "Birincil müonun ürettiği her fotonun yönü ile müonun yönü arasındaki açının dağılımını."),
        ("Nasıl okunur?", "Yatay eksen foton–müon açısı (derece), dikey eksen foton sayısıdır. Pembe bant, 300–600 nm "
         "için kuramın öngördüğü açı aralığıdır (cos θ<sub>c</sub> = 1/(nβ)). Histogramın bandın içinde kalması "
         "beklenir; sol kenardaki yığılma kırmızı, sağ kenar mavi fotonlara karşılık gelir."),
        ("Bu enerjide ne görüyoruz?", f"Fotonların açısı ortalama {f(s['ang_mean'], 2)}°'dir ve %96'sı "
         f"{f(s['ang_lo'], 2)}–{f(s['ang_hi'], 2)}° arasındadır; yani dağılım beklenen bandın içindedir. Sol tarafta "
         f"daha çok foton olması, Cherenkov spektrumunun foton enerjisinde düz olması ve buz indisinin dalga boyuyla "
         f"değişmesinin sonucudur."),
        ("Ne anlama geliyor?", "Işık, müon izi etrafında yaklaşık 41°'lik keskin bir koni boyunca yayılır. Yön "
         "rekonstrüksiyonundaki Cherenkov zaman fiti tam olarak bu geometriyi kullanır: koninin her sensöre ne zaman "
         "ulaşacağı müonun yönüne bağlıdır.")])

    story += panel("(f) Rayleigh saçılma uzunluğu", f"{ppath}/6.png", [
        ("Ne gösteriyor?", "Her buz katmanında ışığın saçılmadan önce ortalama alabildiği yolun (Rayleigh saçılma "
         "uzunluğu) dalga boyuna bağlılığını."),
        ("Nasıl okunur?", "Dikey eksen logaritmiktir. Her renk bir katmandır; parantezde katmanın derinliği yazar. "
         "Eğri ne kadar aşağıdaysa o katmanda ışık o kadar sık saçılır."),
        ("Bu enerjide ne görüyoruz?",
         "400 nm'de saçılma uzunlukları katman 0'dan 3'e sırasıyla " +
         ", ".join(f"{f(v)} m" for v in L4.rayleigh_length_m) +
         f"'dir. En kısa uzunluk katman {dust}'dedir (toz katmanı). Uzunluk 300 nm'den 600 nm'ye yaklaşık "
         f"{f(s['ray600'].iloc[0]/s['ray300'].iloc[0])} kat artar. Bu panel enerjiden bağımsızdır."),
        ("Ne anlama geliyor?", "Rayleigh saçılması λ<super>−4</super> ile değiştiği için mavi ışık kırmızıdan çok daha "
         "sık saçılır. Saçılan foton sensöre daha uzun bir yoldan ve geç ulaşır; bu geç fotonlar yön "
         "rekonstrüksiyonunun en büyük hata kaynağıdır.")])

    story += panel("(g) Derinliğe bağlı soğurma ve sensör vuruşları", f"{ppath}/7.png", [
        ("Ne gösteriyor?", "400 nm'de soğurma uzunluğunun (mavi) ve Rayleigh saçılma uzunluğunun (turuncu) derinliğe "
         "göre değişimini; aynı grafikte, kırmızı çizgi ve üst eksenle, her katmandaki DOM başına ortalama vuruş "
         "sayısını."),
        ("Nasıl okunur?", "Dikey eksen derinliktir ve aşağı doğru artar (en altta en derin katman). Alt eksen uzunluğu "
         "(m), kırmızı üst eksen ise olay başına bir DOM'a düşen ortalama foton sayısını verir. Mavi ve turuncu "
         "eğrinin sola kaydığı derinlik ışığı en çok soğuran ve saçan katmandır."),
        ("Bu enerjide ne görüyoruz?",
         "Katman 3'ten 0'a (sığdan derine) DOM başına ortalama vuruş: " +
         ", ".join(f"{f(hl[i])}" for i in (3, 2, 1, 0)) +
         f". Soğurma uzunluğu en kısa olan katman {dust} (toz katmanı, "
         f"{f(L4.abs_length_m[dust])} m), en uzun olan katman {int(L4.abs_length_m.idxmax())} "
         f"({f(L4.abs_length_m.max())} m). Müon hafifçe yukarı yönlü ve neredeyse yatay geldiği için iz çoğunlukla "
         f"orta katmanlardan geçer; bu yüzden orta katmanlardaki DOM'lar en çok ışığı alır, en üst ve en alt "
         f"katmanlar ize uzak kaldığından çok daha az ışık görür."),
        ("Ne anlama geliyor?", "Bir sensörün aldığı ışık miktarını iki şey belirler: ize uzaklığı ve aradaki buzun "
         "berraklığı. Toz katmanı ışığı daha çok soğurup saçtığı için, iz o katmandan geçse bile sinyal hem "
         "zayıflar hem de zamanca bozulur.")])

    story += panel("(h) Işık miktarı – enerji kaybı ilişkisi", f"{ppath}/8.png", [
        ("Ne gösteriyor?", "Her olay için üretilen toplam Cherenkov foton sayısını (mavi) ve DOM'lara ulaşan foton "
         "sayısını (turuncu), müonun o olayda buzda kaybettiği enerjiye karşı."),
        ("Nasıl okunur?", "İki eksen de logaritmiktir; her nokta bir olaydır. Noktaların düz bir çizgi boyunca "
         "dizilmesi ışığın kayıpla orantılı olduğunu gösterir. Turuncu noktalar mavilerden yaklaşık iki mertebe "
         "aşağıdadır; bu, üretilen ışığın küçük bir kısmının sensörlere ulaştığını gösterir."),
        ("Bu enerjide ne görüyoruz?", f"Olay başına ortalama {f(s['ph_mean'])} foton üretilmiş, {f(s['hits_mean'])} "
         f"tanesi DOM'lara ulaşmış (%{f(s['eff_hit'], 2)}), kuantum verimi sonrası {f(s['det_mean'])} tanesi "
         f"algılanmıştır (%{f(s['eff_det'], 3)}). Buzda bırakılan her GeV için yaklaşık {f(s['ph_per_GeV']/1e3)} bin "
         f"foton üretilmiştir. En parlak ve en sönük olay arasında {f(s['light_spread'])} kat fark vardır; logaritmik "
         f"ışık ile kayıp arasındaki korelasyon katsayısı {f(s['corr'], 2)}'dir."),
        ("Ne anlama geliyor?", "Işık miktarı buzda bırakılan enerjinin iyi bir ölçüsüdür (kalorimetre gibi). Ancak "
         "müon enerjisinin değil, o olaydaki kaybın ölçüsüdür: kayıp stokastik olduğu için aynı enerjideki müonların "
         "ışığı çok farklı olabilir. Işıktan müon enerjisini kestirmeyi zorlaştıran temel neden budur.")])

    # ------------------------------------------------------------- AGN grafiği
    apath = f"{s['pre']}_panels/agn"
    story += [PageBreak(), P("2. AGN KAYNAK REKONSTRÜKSİYONU GRAFİĞİ (6 PANEL)", h1),
              P("Bu grafik, ışığın nasıl üretildiğinden (1–4) müonun yönünün ve kaynağın nasıl bulunduğuna (5–6) kadar "
                "bütün zinciri gösterir."),
              img(f"{s['pre']}_agn_reconstruction.png", 13.0, max_h_cm=17.5)]

    story += panel("Panel 1. Foton dağılımı (üstten görünüm)", f"{apath}/1.png", [
        ("Ne gösteriyor?", "Kaydedilen tek bir olayda üretilen bütün Cherenkov fotonlarının doğduğu noktaları, "
         "dedektöre yukarıdan bakarak (x–y düzlemi)."),
        ("Nasıl okunur?", "Renk, o küçük karede doğan foton sayısıdır ve logaritmiktir (sarı = çok, mor = az). Turuncu "
         "halkalar 9 stringin konumudur; her stringde farklı derinliklerde 4 DOM vardır. Müon +y kenarından girip −y "
         "yönünde ilerler."),
        ("Bu enerjide ne görüyoruz?", f"Olay {s['e0']}'da {f(s['ph_e0'])} foton üretilmiş, bunların %{f(s['prim_e0'])} "
         f"kadarı birincil müondandır; müon bu olayda {f(s['loss_e0'], 1)} GeV kaybetmiştir. İnce düz çizgi birincil "
         f"müonun izi, iz üzerindeki geniş ve parlak lekeler ise kaskadların (elektron–pozitron–foton çığları) "
         f"ışığıdır."),
        ("Ne anlama geliyor?", "Işığın büyük kısmı müon izi boyunca üretilir; bu yüzden ize yakın sensörler çok, uzak "
         "olanlar az ışık alır. Kaskad ışığı tek bir noktada yoğunlaştığı için hem toplam ışığı artırır hem de "
         "zaman örüntüsünü bozarak yön hesabını zorlaştırabilir.")])

    story += panel("Panel 2. Foton enerji spektrumu", f"{apath}/2.png", [
        ("Ne gösteriyor?", "Üretilen fotonların (mavi), DOM'lara ulaşan fotonların (turuncu) ve kuantum verimi "
         "uygulandıktan sonra algılanan fotonların (yeşil kesikli) enerji dağılımlarını."),
        ("Nasıl okunur?", "Alt eksen foton enerjisi (eV), üst eksen aynı değerin dalga boyu karşılığıdır (nm). "
         "Eğriler normalize edilmiştir, yani yalnızca biçimleri karşılaştırılır. Bir eğrinin sağa kayması, o "
         "fotonların daha mavi olduğunu gösterir."),
        ("Bu enerjide ne görüyoruz?", f"Ortalama dalga boyu üretilen fotonlarda {f(s['lam_prod'])} nm, DOM'a ulaşanlarda "
         f"{f(s['lam_hit'])} nm, algılananlarda {f(s['lam_det'])} nm'dir. DOM'a ulaşan fotonların %{f(s['qe_frac'])} "
         f"kadarı algılanmıştır. Üretilen spektrum enerjide neredeyse düzdür; ulaşan ve algılanan spektrumlar maviye "
         f"kaymıştır."),
        ("Ne anlama geliyor?", "Kırmızı fotonlar buzun kendisi tarafından hızla soğurulur, bu yüzden sensöre ulaşan "
         "ışık maviye kayar. Fotoçoğaltıcının kuantum verimi ≈ 380 nm'de en yüksek olduğu için algılanan ışık daha da "
         "maviye kayar. Bu nedenle IceCube asıl olarak mavi-mor ışığı görür.")])

    story += panel("Panel 3. Vuruş zamanı dağılımı (katmanlara göre)", f"{apath}/3.png", [
        ("Ne gösteriyor?", "Her olayda ilk vuruşa göre ölçülen zaman farkının (t − t<sub>ilk</sub>) dağılımını, DOM'un "
         "bulunduğu katmana göre ayrı renklerle."),
        ("Nasıl okunur?", "Dikey eksen logaritmiktir. Sol baştaki keskin tepe saçılmadan doğrudan gelen fotonlardır; "
         "sağa doğru uzanan düz (logaritmik eksende doğrusal) kuyruk, saçılarak gecikmiş fotonlardır. Bir katmanın "
         "eğrisinin sağa kayması, o katmana ışığın daha geç ulaştığını gösterir."),
        ("Bu enerjide ne görüyoruz?",
         f"Vuruşların medyan gecikmesi {f(s['t_med'], 1)} ns'dir ve %{f(s['late50'])} kadarı ilk vuruştan 50 ns'den "
         f"daha geç gelmiştir. Katman 0–3 için medyan gecikmeler sırasıyla " +
         ", ".join(f"{f(v, 1)}" for v in s["t_layer"]) +
         " ns'dir. " + ("İze uzak en alt ve en üst katmanlar ışığı orta katmanlardan daha geç alır."
                        if min(s["t_layer"][0], s["t_layer"][3]) > max(s["t_layer"][1], s["t_layer"][2])
                        else "Katmanlar arasındaki fark, izin bu olaylarda hangi derinlikten geçtiğine bağlıdır.")),
        ("Ne anlama geliyor?", "Yön rekonstrüksiyonu için asıl değerli olan, her DOM'a ilk ulaşan doğrudan fotonların "
         "zamanıdır. Saçılma kuyruğu bu zamanları bozar; bu yüzden rekonstrüksiyonda geç fotonlara karşı dayanıklı "
         "bir maliyet fonksiyonu kullanılmıştır.")])

    story += panel("Panel 4. Sensörlere göre ışık", f"{apath}/4.png", [
        ("Ne gösteriyor?", "36 sensörün her birine olay başına ortalama kaç foton ulaştığını; başlıkta, üretilen "
         "fotonların toplamda ne kadarının sensörlere ulaştığı yazar."),
        ("Nasıl okunur?", "Yatay eksen sensör numarasıdır: ID = 4 × string + DOM. Gri dikey çizgiler stringleri ayırır "
         "(her blokta 4 DOM). Çubuk renkleri katmanları gösterir. Uzun çubuklar ize yakın sensörlerdir."),
        ("Bu enerjide ne görüyoruz?", f"En çok ışığı sensör {s['top_id']} (string {s['top_str']}, DOM {s['top_dom']}) "
         f"almıştır: olay başına {f(s['top_val'])} foton. En parlak 4 sensör toplam ışığın %{f(s['top4'])} kadarını "
         f"toplar. Üretilen fotonların %{f(s['eff_hit'], 2)} kadarı sensörlere ulaşmıştır."),
        ("Ne anlama geliyor?", "Işık birkaç sensörde yoğunlaşır; bu sensörler müon izinin hangi stringlere yakın "
         "geçtiğini gösterir. Rekonstrüksiyon, hangi sensörün ne zaman ve ne kadar ışık aldığından yararlanarak izin "
         "yönünü bulur.")])

    story += panel("Panel 5. AGN kataloğuyla eşleştirme", f"{apath}/5.png", [
        ("Ne gösteriyor?", "Tüm olayların yönleri birleştirilerek bulunan kaynak konumunun, katalogdaki 7 AGN'nin her "
         "birine açısal uzaklığını."),
        ("Nasıl okunur?", "Yatay eksen logaritmiktir (derece). Çubuk renkleri AGN sınıfıdır: mavi BL Lac, kırmızı FSRQ "
         "(ikisi de blazar), yeşil Seyfert. Siyah kesikli çizgi birleşik kaynağın hata yarıçapıdır. Çubuğu bu "
         "çizgiye yakın ya da onun solunda kalan AGN, kaynakla eşleşen adaydır; sağ alttaki kutu sonucu yazar."),
        ("Bu enerjide ne görüyoruz?", f"Birleşik kaynak TXS 0506+056'ya {f(s['txs'], 2)}° uzaklıktadır; hata yarıçapı "
         f"{f(s['r90'], 2)}°'dir. En yakın ikinci aday {second[1]} olup {f(second[0], 1)}° uzaktadır. " +
         (f"TXS 0506+056'ya uzaklık hata yarıçapıyla aynı mertebededir; ikinci aday ise hata yarıçapının "
          f"yaklaşık {f(second[0]/s['r90'])} katı kadar uzaktadır. Yani eşleşme açıktır." if s["txs"] < 3*s["r90"] else
          "TXS 0506+056'ya uzaklık hata yarıçapının birkaç katıdır; eşleşme yalnızca katalogdaki en yakın aday "
          "olmasına dayanır.")),
        ("Ne anlama geliyor?", "Tek bir olayın yön hatası birkaç derece olsa da çok sayıda olay birleştirildiğinde "
         "kaynak yönü çok daha iyi belirlenir ve bilinen bir gök cismiyle eşleştirilebilir. Bir kaynağın blazar "
         "olduğu müon verisinden değil, bu katalog eşleşmesinden anlaşılır.")])

    story += panel("Panel 6. Gökyüzü haritası ve konum belirleme", f"{apath}/6.png", [
        ("Ne gösteriyor?", "TXS 0506+056 çevresindeki ±6°'lik gökyüzü bölgesinde, her olay için yeniden yapılandırılan "
         "kaynak yönlerini (mavi noktalar), bunların birleşimini (+) ve hata çemberini (kesikli)."),
        ("Nasıl okunur?", "Yatay eksen sağ açıklık (RA), dikey eksen dik açıklıktır (Dec), ikisi de derece. Yıldız "
         "gerçek kaynaktır. Noktaların saçılımı tek olay hatasını, + işaretinin yıldıza uzaklığı birleşik sonucun "
         "doğruluğunu gösterir. Başlıkta tek olay hatasının medyanı yazar."),
        ("Bu enerjide ne görüyoruz?", f"Tek olayların medyan açısal hatası {f(s['fit'], 2)}°'dir (LineFit ile "
         f"{f(s['lf'], 1)}°). Olayların %{f(s['lt5'])} kadarının hatası 5°'nin, %{f(s['lt1'])} kadarınınki 1°'nin "
         f"altındadır. Aykırı olaylar atıldıktan sonra {s['nused']} olay birleştirilmiş ve kaynak (RA = "
         f"{f(s['ra'], 2)}°, Dec = {f(s['dec'], 2)}°) olarak bulunmuştur."),
        ("Ne anlama geliyor?", "Her olay gerçek yönün etrafına birkaç derecelik bir alana dağılır; ancak hatalar "
         "rastgele olduğu için birleşik konum, olay sayısının karekökü oranında daha kesin hâle gelir. Bu, gerçek "
         "nötrino teleskoplarında kaynak arama yönteminin temel fikridir.")])

    # ------------------------------------------------------------- özet
    story += [PageBreak(), P("3. BU ENERJİNİN ÖZETİ", h1),
              *bullets([
                  f"<b>Enerji kaybı:</b> {Et(E)} TeV müon {f(s['L'], 1)} m buzda ortalama {f(s['loss_mean'], 1)} GeV "
                  f"kaybetmiştir; radyatif payı %{f(s['rad_share'])}. Bu enerji {regime(E)}.",
                  f"<b>Işık üretimi:</b> Birincil müon {f(s['ph_cm'])} foton/cm üretmiş (Frank-Tamm ≈ 326); olay "
                  f"başına toplam {f(s['ph_mean'])} fotonun %{f(s['prim_all'])} kadarı birincil müondandır.",
                  f"<b>Algılama:</b> Fotonların %{f(s['eff_hit'], 2)} kadarı DOM'lara ulaşmış, "
                  f"%{f(s['eff_det'], 3)} kadarı algılanmıştır; algılanan ışık maviye kaymıştır.",
                  f"<b>Zaman:</b> Medyan gecikme {f(s['t_med'], 1)} ns; vuruşların %{f(s['late50'])} kadarı 50 ns'den "
                  f"geçtir (saçılma).",
                  f"<b>Yön:</b> Tek olay hatası (medyan) {f(s['fit'], 2)}°; {s['nused']} olay birleştirilince kaynak "
                  f"TXS 0506+056'ya {f(s['txs'], 2)}° uzaklıkta bulunmuş ve doğru eşleşmiştir."])]
    return story


# ======================================================================= karşılaştırma PDF'i
def overview_story():
    TH = f"{DATA}/thesis"
    T = pd.read_csv(f"{TH}/thesis_summary.csv").sort_values("E_TeV").reset_index(drop=True)
    R = pd.read_csv(f"{TH}/energy_resolution.csv").sort_values("E_TeV").reset_index(drop=True)
    Pm = pd.read_csv(f"{TH}/parameter_study.csv")
    C = pd.read_csv(f"{TH}/dedx_check.csv").sort_values("E_TeV")
    sp = Pm[Pm.ice == "Rayleigh"].drop_duplicates("spacing").sort_values("spacing")
    mie, ray = Pm[Pm.ice != "Rayleigh"].iloc[0], sp[sp.spacing == 6].iloc[0]
    hi = R[(R.E_TeV >= 1) & (R.E_TeV < R.E_TeV.max())]   # 100 TeV'de test kümesi çok küçük
    story = cover("ENERJİLER ARASI KARŞILAŞTIRMA", "Tüm enerjileri bir arada gösteren grafiklerin adım adım açıklaması")
    story += [P("BU BELGE NE ANLATIYOR?", h1),
              P("Enerjiye özel belgelerde (0,1–100 TeV) her enerji tek başına incelenmiştir. Bu belgedeki grafikler ise "
                "yedi enerjiyi aynı eksende karşılaştırır ve tezin ana sonuçlarını taşır. Her grafik dört adımda "
                "açıklanmıştır. Sayılar enerji taraması koşularından (" +
                ", ".join(f"{Et(e)} TeV: {n}" for e, n in zip(T.E_TeV, T.N)) + " olay) alınmıştır.")]

    def whole(title, path, steps, w=15.5, mh=12.5):
        return [CondPageBreak(10*cm), P(title, h2), img(path, w, mh), Spacer(1, 4)] + \
               [P(f"<b>Adım {i}. {q}</b> {t}", step_st) for i, (q, t) in enumerate(steps, 1)]

    story += [PageBreak(), P("1. IŞIK ÜRETİMİ VE ALGILANMASI", h1)]
    story += whole("Enerji taraması: ışık verimi (4 panel)", f"{TH}/fig_light_yield.png", [
        ("Ne gösteriyor?", "(a) olay başına üretilen toplam foton ve bunun birincil müondan gelen kısmı, (b) DOM'lara "
         "ulaşan ve kuantum verimi sonrası algılanan foton sayısı, (c) bu iki verim oranı, (d) buzda bırakılan GeV "
         "başına üretilen foton sayısı; hepsi müon enerjisine karşı."),
        ("Nasıl okunur?", "Yatay eksen her panelde müon enerjisidir (logaritmik). Hata çubukları ortalamanın standart "
         "hatasıdır. (a)'da iki eğri arasındaki açıklık, ışığın ne kadarının ikincil parçacıklardan geldiğini gösterir."),
        ("Ne görüyoruz?", f"Birincil müonun ışığı tüm enerjilerde ≈ {f(T.ph_prim.mean()/1e3)} bin fotonda sabittir; "
         f"toplam ışık {Et(T.E_TeV.iloc[0])} TeV'den {Et(T.E_TeV.iloc[-1])} TeV'e ≈ "
         f"{f(T.ph.iloc[-1]/T.ph.iloc[0])} kat artar. Algılama verimi %{f(100*T.eff_det.min(), 2)}–"
         f"%{f(100*T.eff_det.max(), 2)} aralığındadır. Bırakılan enerji başına ışık "
         f"{f(T.ph_per_GeV.min()/1e3)}–{f(T.ph_per_GeV.max()/1e3)} bin foton/GeV'tir; yani %"
         f"{f(100*(T.ph_per_GeV.max()/T.ph_per_GeV.min() - 1))} içinde sabittir."),
        ("Ne anlama geliyor?", "Işık artışının tamamı kaskadlardan gelir ve ışık miktarı buzda bırakılan enerjinin "
         "neredeyse sabit oranlı bir ölçüsüdür. Algılama verimi enerjiden bağımsız olduğu için dedektörün davranışı "
         "basit bir ölçeklemeyle tanımlanabilir.")])

    story += [PageBreak(), P("2. ENERJİ KAYBININ DOĞRULANMASI", h1)]
    story += whole("Simülasyon ile Groom/PDG tablosunun karşılaştırması", f"{TH}/fig_dedx_validation.png", [
        ("Ne gösteriyor?", "Üst panelde, her enerjide simülasyondaki ortalama toplam, iyonizasyon ve radyatif dE/dx "
         "değerleri ile Groom/PDG tablosunun eğrileri; alt panelde simülasyonun tabloya oranı."),
        ("Nasıl okunur?", "Siyah, mavi ve kırmızı çizgiler tablodan (toplam, iyonizasyon, radyatif), aynı renkli "
         "işaretler simülasyondandır. × işaretleri medyan, yeşil elmaslar ışık üretimi kapalı 4000 olaylık doğrulama "
         "koşularıdır. Dikey noktalı çizgi kritik enerjidir. Alt panelde 1 çizgisi tam uyumu gösterir."),
        ("Ne görüyoruz?", f"1 TeV'e kadar toplam kayıp tabloyla birkaç yüzde içinde uyumludur. 10–100 TeV'de ortalamalar "
         f"büyük hata çubuklarıyla dağılır; 20 olaylık 100 TeV noktasında oran yalnızca "
         f"{f(T.dedx_tot.iloc[-1]/T.groom_tot.iloc[-1], 2)} kadardır. Buna karşın 4000 olaylık doğrulama koşularında oran " +
         " ve ".join(f"{Et(e)} TeV'de {f(r, 2)}" for e, r in zip(C.E_TeV, C.ratio)) +
         " olur. Medyanlar ortalamaların altındadır."),
        ("Ne anlama geliyor?", "Simülasyonun enerji kaybı fiziği doğrudur. Yüksek enerjideki sapmalar fiziksel bir hata "
         "değil, seyrek ve dev radyatif kayıpların az sayıda olayda yeterince örneklenememesinden kaynaklanan "
         "istatistik etkisidir.")], w=12.5, mh=13.5)

    story += [PageBreak(), P("3. AÇISAL ÇÖZÜNÜRLÜK", h1)]
    story += whole("Yön hatasının enerjiye bağlılığı (2 panel)", f"{TH}/fig_angular_resolution.png", [
        ("Ne gösteriyor?", "(a) LineFit ve Cherenkov zaman fitinin medyan açısal hatasını enerjiye karşı, (b) her "
         "enerjide Cherenkov fiti hatalarının dağılımını."),
        ("Nasıl okunur?", "(a)'da hata çubukları bootstrap ile hesaplanan %68 güven aralığıdır; düşük değer daha iyi "
         "yön ölçümü demektir. (b)'de her eğri bir enerjidir; dağılımın sola yığılması küçük hatalar demektir."),
        ("Ne görüyoruz?", f"Cherenkov fitinin medyan hatası tüm enerjilerde {f(T.fit.min(), 1)}–{f(T.fit.max(), 1)}° "
         f"aralığında hemen hemen yataydır; LineFit {f(T.lf.max(), 0)}°'den {f(T.lf.min(), 0)}°'ye iyileşir ama 4–5 kat "
         f"kötü kalır. Hatası 1°'nin altında kalan olayların oranı %{f(100*T.frac_lt1.min())}–"
         f"%{f(100*T.frac_lt1.max())} düzeyindedir."),
        ("Ne anlama geliyor?", "Bu küçük dedektörde yön doğruluğunu enerji değil, iz uzunluğu (≈ 20 m) ve buzdaki saçılma "
         "sınırlar. Kaskad ışığı artsa da yön bilgisini taşıyan ilk fotonlar birincil müonun konisinden gelir.")])

    story += [PageBreak(), P("4. ENERJİ REKONSTRÜKSİYONU", h1)]
    story += whole("Işık miktarından müon enerjisinin kestirimi (3 panel)", f"{TH}/fig_energy_reconstruction.png", [
        ("Ne gösteriyor?", "(a) eğitim olaylarında kesilmiş ışığın (en parlak %20 DOM atılarak) enerjiye bağlılığı, yani "
         "kalibrasyon eğrisi; (b) test olaylarında kestirilen ve gerçek enerji; (c) üç yöntemin sapması ve "
         "çözünürlüğü."),
        ("Nasıl okunur?", "(a)'da mavi bant olaydan olaya %16–%84 aralığıdır; gri bölge ışığın enerjiye duyarsız olduğu "
         "aralıktır. (b)'de noktalar köşegene ne kadar yakınsa kestirim o kadar iyidir. (c)'de sıfır çizgisi sapmasız "
         "kestirimdir; hata çubukları çözünürlüktür (dex: 1 dex = 10 kat)."),
        ("Ne görüyoruz?", f"Kalibrasyon eğrisi 1 TeV'e kadar neredeyse yataydır (eğim {f(R.slope_to_next.iloc[0], 2)}–"
         f"{f(R.slope_to_next.iloc[1], 2)}), sonra dikleşir. Kalibrasyon yönteminin sapması 1 TeV ve üstünde en fazla "
         f"{f(hi.cal_bias.abs().max(), 2)} dex, çözünürlüğü {f(hi.cal_sigma.min(), 2)}–{f(hi.cal_sigma.max(), 2)} "
         f"dex'tir (1–30 TeV; 100 TeV'de test kümesi yalnızca {int(R.n.iloc[-1])} olaydır). Diğer iki yöntem düşük enerjide fazla, yüksek enerjide az kestirir."),
        ("Ne anlama geliyor?", "Kalibrasyon yaklaşımı sistematik sapmayı büyük ölçüde giderir; ancak çözünürlük kötüdür, "
         "çünkü 20 m'lik iz, stokastik kayıpların ortalamasını almaya yetmez ve 1 TeV altında ışık enerjiyi "
         "neredeyse hiç taşımaz.")])

    story += [PageBreak(), P("5. PARAMETRE ÇALIŞMASI", h1)]
    story += whole("String aralığı ve buz modeli (4 panel, 1 TeV)", f"{TH}/fig_parameter_study.png", [
        ("Ne gösteriyor?", "(a) string aralığına göre açısal hata, (b) string aralığına göre algılanan ışık, (c) Rayleigh "
         "ve Mie buzunda ilk fotonların gecikme dağılımı, (d) iki buz modelinde açısal hata ve algılanan ışık."),
        ("Nasıl okunur?", "(a)–(b)'de yatay eksen string aralığıdır (4, 6, 8 m). (c)'de kuyruğu uzun olan dağılım daha "
         "çok geciken ışık demektir. Hata çubukları %68 güven aralığıdır."),
        ("Ne görüyoruz?", f"Cherenkov fitinin hatası 4, 6 ve 8 m için {f(sp.fit.iloc[0], 2)}°, {f(sp.fit.iloc[1], 2)}° ve "
         f"{f(sp.fit.iloc[2], 2)}°'dir; LineFit ise tersine 4 m'de en kötüdür ({f(sp.lf.iloc[0], 1)}°). Olay başına "
         f"algılanan ışık 4 m'de {f(sp.det.iloc[0])}, 6 m'de {f(sp.det.iloc[1])}, 8 m'de {f(sp.det.iloc[2])} "
         f"fotondur. Mie buzunda algılanan ışık ≈ %{f(100*(1 - mie.det/ray.det))} azalır, açısal hata "
         f"{f(mie.fit, 2)}° ile benzer kalır; ilk fotonların gecikme kuyruğu Mie'de daha kısadır."),
        ("Ne anlama geliyor?", "Sensörleri sıklaştırmak hem ışığı hem yön doğruluğunu artırır; bu, IceCube Upgrade'in "
         "fikridir. İleri yönlü Mie saçılması ışığın yönünü az değiştirdiği için zaman bilgisini daha az bozar.")])

    story += [PageBreak(), P("6. 1 TeV VE 10 TeV KARŞILAŞTIRMASI", h1)]
    story += whole("İlk aşama: 1 TeV ile 10 TeV (6 panel)", f"{DATA}/comparison.png", [
        ("Ne gösteriyor?", "(1) enerji kaybı dağılımları, (2) kuramsal dE/dx eğrisi üzerinde ortalama ve medyanlar, "
         "(3) birincil ve toplam foton sayısı, (4) olay başına sensör vuruşu, (5) açısal hata dağılımları, (6) hata "
         "yarıçapı ve en yakın AGN'ye uzaklık."),
        ("Nasıl okunur?", "Her panelde iki enerji farklı renktir. (5)'te düz çizgiler Cherenkov fiti, kesikli çizgiler "
         "LineFit'tir."),
        ("Ne görüyoruz?", "10 TeV'de kayıp dağılımı sağa kayar ve kuyruğu uzar; medyan ortalamanın belirgin altında "
         "kalır. Birincil müon ışığı iki enerjide aynıdır, toplam ışığı artıran kaskadlardır. Cherenkov fitinin "
         "hataları iki enerjide de ≈ 4° civarında, LineFit'inkiler 15–25° civarındadır. İki enerjide de en yakın AGN "
         "TXS 0506+056'dır."),
        ("Ne anlama geliyor?", "On kat enerji, on kat ışık anlamına gelmez; ışık kayıpla, kayıp ise stokastik süreçlerle "
         "belirlenir. Yön doğruluğu ise enerjiden çok geometriye bağlıdır.")])
    return story


# ======================================================================= ana program
def main():
    os.makedirs(OUTDIR, exist_ok=True)
    todo = [float(a) for a in sys.argv[1:]] or ENERGIES
    for E in todo:
        if not os.path.isdir(f"{DATA}/detail/E{E:g}TeV_panels"):
            print(f"{Et(E)} TeV: panel PNG'leri yok, atlanıyor (önce analyze.py çalıştırılmalı)")
            continue
        br._counters.update(fig=0, tab=0, eq=0)
        s = stats(E)
        name = f"{OUTDIR}/{ENERGIES.index(E) + 1:02d}_{Et(E).replace(',', '.')}TeV_Grafikleri.pdf"
        doc = PanelDoc(name, f"{Et(E)} TeV müon – grafiklerin açıklaması",
                       title=f"{Et(E)} TeV müon grafikleri", author="Yusuf AYDEMİR")
        doc.multiBuild(energy_story(s))
        print("PDF:", name)
    if not sys.argv[1:]:
        br._counters.update(fig=0, tab=0, eq=0)
        name = f"{OUTDIR}/00_Enerjiler_Arasi_Karsilastirma.pdf"
        PanelDoc(name, "Enerjiler arası karşılaştırma – grafiklerin açıklaması",
                 title="Enerjiler arası karşılaştırma", author="Yusuf AYDEMİR").multiBuild(overview_story())
        print("PDF:", name)


if __name__ == "__main__":
    main()

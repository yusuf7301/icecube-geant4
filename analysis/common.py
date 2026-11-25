"""Ortak yardımcılar: CSV okuma, buz optiği, müon izi rekonstrüksiyonu, AGN kataloğu."""
import os

import numpy as np
import pandas as pd
from scipy.optimize import minimize

C_VAC = 0.299792458  # m/ns
HC = 1239.84193      # eV*nm

# Küçük bir nötrino-aday AGN kataloğu (J2000, derece)
AGN_CATALOG = [
    # isim,            RA,       Dec,     sınıf
    ("TXS 0506+056",   77.358,   5.693,   "BL Lac (blazar)"),
    ("PKS 1424+240",  216.752,  23.800,   "BL Lac (blazar)"),
    ("Mrk 421",       166.114,  38.209,   "BL Lac (blazar)"),
    ("PKS 1502+106",  226.104,  10.494,   "FSRQ (blazar)"),
    ("3C 279",        194.047,  -5.789,   "FSRQ (blazar)"),
    ("3C 454.3",      343.491,  16.148,   "FSRQ (blazar)"),
    ("NGC 1068",       40.670,  -0.013,   "Seyfert 2"),
]
CLASS_COLORS = {"BL Lac (blazar)": "#1f77b4", "FSRQ (blazar)": "#d62728", "Seyfert 2": "#2ca02c"}


# ---------------------------------------------------------------- veri okuma
def load(prefix):
    """Bir koşunun tüm CSV dosyalarını sözlük olarak döndürür (eksik olanlar None)."""
    names = ["events", "sensors", "ice_properties", "muon_energy_loss",
             "sensor_hits", "cherenkov_photons", "sensor_summary"]
    data = {}
    for n in names:
        path = f"{prefix}_{n}.csv"
        data[n] = pd.read_csv(path) if os.path.exists(path) else None
    if data["events"] is None:
        raise FileNotFoundError(f"{prefix}_events.csv bulunamadı")
    data["events"] = data["events"].sort_values("event").reset_index(drop=True)
    return data


# ---------------------------------------------------------------- buz optiği
def n_phase(lam_nm):
    """Price & Bergström faz kırılma indisi (C++ tarafıyla aynı formül)."""
    l = np.asarray(lam_nm) / 1000.0
    return 1.55749 - 1.57988*l + 3.99993*l**2 - 4.68271*l**3 + 2.09354*l**4


def n_group(lam_nm):
    """Grup indisi n_g = n - lambda * dn/dlambda (ışık sinyalinin gerçek hızı c/n_g)."""
    lam = np.asarray(lam_nm, dtype=float)
    dn = (n_phase(lam + 0.5) - n_phase(lam - 0.5)) / 1.0
    return n_phase(lam) - lam*dn


N_REF = float(n_phase(400.0))
NG_REF = float(n_group(400.0))
THETA_C = np.arccos(1.0/N_REF)


# ---------------------------------------------------------------- koordinatlar
def source_dir_from_radec(ra_deg, dec_deg):
    """C++ PrimaryGeneratorAction ile aynı: yükseklik = -Dec, azimut = RA. Kaynağa bakan birim vektör."""
    alt, az = np.radians(-np.asarray(dec_deg)), np.radians(np.asarray(ra_deg))
    return np.stack([np.cos(alt)*np.cos(az), np.cos(alt)*np.sin(az), np.sin(alt)], axis=-1)


def radec_from_muon_dir(d):
    """Müon yönü -> kaynağın (RA, Dec) koordinatı (derece)."""
    s = -np.asarray(d, dtype=float)
    s = s / np.linalg.norm(s, axis=-1, keepdims=True)
    alt = np.degrees(np.arcsin(np.clip(s[..., 2], -1, 1)))
    ra = np.degrees(np.arctan2(s[..., 1], s[..., 0])) % 360.0
    return ra, -alt


def ang_dist(ra1, dec1, ra2, dec2):
    """İki gök noktası arasındaki açı (derece)."""
    ra1, dec1, ra2, dec2 = map(np.radians, (ra1, dec1, ra2, dec2))
    c = np.sin(dec1)*np.sin(dec2) + np.cos(dec1)*np.cos(dec2)*np.cos(ra1 - ra2)
    return np.degrees(np.arccos(np.clip(c, -1, 1)))


def angle_between(a, b):
    a = a / np.linalg.norm(a, axis=-1, keepdims=True)
    b = b / np.linalg.norm(b, axis=-1, keepdims=True)
    return np.degrees(np.arccos(np.clip(np.sum(a*b, axis=-1), -1, 1)))


# ---------------------------------------------------------------- rekonstrüksiyon
def line_fit(pos, t, w):
    """IceCube LineFit: r(t) = r0 + v t doğrusunu hit'lere en küçük kareler ile uydurur."""
    tm = np.average(t, weights=w)
    rm = np.average(pos, axis=0, weights=w)
    dt = t - tm
    v = np.sum((w*dt)[:, None]*(pos - rm), axis=0) / np.sum(w*dt*dt)
    return v / np.linalg.norm(v), rm, tm


def _perp_basis(d):
    a = np.array([1.0, 0, 0]) if abs(d[0]) < 0.9 else np.array([0, 1.0, 0])
    u = np.cross(d, a); u /= np.linalg.norm(u)
    return u, np.cross(d, u)


def expected_time(pos, d, r0, t0):
    """Doğrudan Cherenkov fotonunun sensöre varış zamanı (Cherenkov konisi geometrisi)."""
    w = pos - r0
    l = w @ d
    rho = np.linalg.norm(w - np.outer(l, d), axis=1)
    return t0 + (l - rho/np.tan(THETA_C))/C_VAC + rho/np.sin(THETA_C)*NG_REF/C_VAC


def reconstruct_event(hits_ev, sensors):
    """Bir olayın sensör hit'lerinden müon yönünü bulur. Dönüş: (linefit_dir, fit_dir, n_sensor)."""
    g = hits_ev.groupby("sensor_id")["time_ns"].agg(["min", "count"])
    return reconstruct_from_sensors(g.index, g["min"].to_numpy(), g["count"].to_numpy(), sensors)


def reconstruct_from_sensors(sensor_ids, t, q, sensors):
    """Sensör başına ilk vuruş zamanı t ve vuruş sayısı q'dan müon yönü."""
    if len(t) < 3:
        return None, None, len(t)
    sp = sensors.set_index("sensor_id").loc[sensor_ids, ["x_mm", "y_mm", "z_mm"]].to_numpy()/1000.0
    t = np.asarray(t, dtype=float)
    q = np.asarray(q, dtype=float)
    w = np.sqrt(q)

    d_lf, r_lf, t_lf = line_fit(sp, t, w)

    # Cherenkov-zaman fit'i: yön (theta, phi), ize dik kayma (a, b), t0
    def unpack(p):
        th, ph, a, b, t0 = p
        d = np.array([np.sin(th)*np.cos(ph), np.sin(th)*np.sin(ph), np.cos(th)])
        u, v = _perp_basis(d)
        return d, r_lf + a*u + b*v, t0

    def cost(p):
        d, r0, t0 = unpack(p)
        res = t - expected_time(sp, d, r0, t0)
        return np.sum(w*np.log1p((res/10.0)**2))  # Saçılma gecikmelerine dayanıklı (Cauchy)

    best = None
    for seed in (d_lf, ):
        th0, ph0 = np.arccos(np.clip(seed[2], -1, 1)), np.arctan2(seed[1], seed[0])
        for dth in (0.0, 0.2, -0.2):
            p0 = [th0 + dth, ph0, 0.0, 0.0, t_lf]
            r = minimize(cost, p0, method="Nelder-Mead",
                         options={"maxiter": 4000, "xatol": 1e-4, "fatol": 1e-4})
            if best is None or r.fun < best.fun:
                best = r
    return d_lf, unpack(best.x)[0], len(t)


def reconstruct_all(data, mode="auto"):
    """Her olay için rekonstrüksiyon tablosu.

    mode: "hits"     -> tek tek sensör fotonları (sensor_hits.csv)
          "all"      -> sensör özeti, DOM'a ulaşan tüm fotonlar
          "detected" -> sensör özeti, yalnız kuantum verimini geçen fotonlar (gerçekçi)
          "auto"     -> varsa hits, yoksa detected
    """
    ev, hits, sensors, summ = data["events"], data["sensor_hits"], data["sensors"], data["sensor_summary"]
    if mode == "auto":
        mode = "hits" if hits is not None and len(hits) else "detected"
    if mode == "hits":
        groups = dict(tuple(hits.groupby("event")))
    else:
        s = summ.copy()
        if mode == "detected":
            s = s[s["n_detected"] > 0].assign(t=s["t_first_det_ns"], q=s["n_detected"])
        else:
            s = s.assign(t=s["t_first_ns"], q=s["n_hits"])
        groups = dict(tuple(s.groupby("event")))
    rows = []
    for _, e in ev.iterrows():
        true_d = e[["dir_x", "dir_y", "dir_z"]].to_numpy(float)
        h = groups.get(int(e["event"]))
        if h is None:
            d_lf, d_fit, nsens = None, None, 0
        elif mode == "hits":
            d_lf, d_fit, nsens = reconstruct_event(h, sensors)
        else:
            d_lf, d_fit, nsens = reconstruct_from_sensors(h["sensor_id"].to_numpy(), h["t"], h["q"], sensors)
        row = {"event": int(e["event"]), "n_sensors": nsens, "n_hits": int(e["n_hits"])}
        row["ra_true"], row["dec_true"] = radec_from_muon_dir(true_d)
        if d_fit is not None:
            row["err_linefit_deg"] = float(angle_between(d_lf, true_d))
            row["err_fit_deg"] = float(angle_between(d_fit, true_d))
            row["ra_reco"], row["dec_reco"] = (float(x) for x in radec_from_muon_dir(d_fit))
            row.update(dx=d_fit[0], dy=d_fit[1], dz=d_fit[2])
        rows.append(row)
    return pd.DataFrame(rows)


def combined_source(reco):
    """Tüm olayların kaynak yönlerinin ortalaması ve ~%90 hata yarıçapı (derece)."""
    ok = reco.dropna(subset=["ra_reco"])
    if ok.empty:
        return None
    s = source_dir_from_radec(ok["ra_reco"], ok["dec_reco"])
    m = s.mean(axis=0); m /= np.linalg.norm(m)
    ra, dec = radec_from_muon_dir(-m)
    spread = angle_between(s, np.broadcast_to(m, s.shape))
    # Aykırı olayları (>3 medyan) at, tekrar ortala
    keep = spread < max(3*np.median(spread), 1.0)
    m = s[keep].mean(axis=0); m /= np.linalg.norm(m)
    ra, dec = radec_from_muon_dir(-m)
    spread = angle_between(s[keep], np.broadcast_to(m, s[keep].shape))
    r90 = np.percentile(spread, 90) / np.sqrt(keep.sum())
    return float(ra), float(dec), float(r90), int(keep.sum())


# ---------------------------------------------------------------- muon dE/dx teorisi
def muon_dedx_ice(E_MeV, rho=0.917):
    """Müonun buzdaki ortalama enerji kaybı (MeV/cm): Bethe-Bloch (yoğunluk etkili) + radyatif b*E."""
    M, me, K, ZA, I = 105.658, 0.510999, 0.307075, 0.5551, 75e-6
    E = np.asarray(E_MeV, dtype=float)
    gam = (E + M)/M
    bg2 = gam**2 - 1
    b2 = bg2/gam**2
    Tmax = 2*me*bg2/(1 + 2*gam*me/M + (me/M)**2)
    x = np.log10(np.sqrt(bg2))
    Cb, x0, x1, a, k = 3.5017, 0.2400, 2.8004, 0.09116, 3.4773  # Sternheimer, su
    delta = np.where(x >= x1, 2*np.log(10)*x - Cb,
                     np.where(x >= x0, 2*np.log(10)*x - Cb + a*np.clip(x1 - x, 0, None)**k, 0.0))
    ion = K*ZA/b2*(0.5*np.log(2*me*bg2*Tmax/I**2) - b2 - delta/2)  # MeV cm2/g
    rad = 3.2e-6*E                                                  # brems + çift + fotonükleer
    return ion*rho, rad*rho


# ---------------------------------------------------------------- literatür ve istatistik
GROOM_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ref", "muE_water_liquid.txt")
RHO_ICE = 0.917  # g/cm3


def load_groom(path=GROOM_FILE):
    """PDG/Groom müon tablosu (su). Birimler: T [MeV], kayıplar [MeV cm2/g]."""
    rows = []
    with open(path) as f:
        for line in f:
            tok = line.split()
            try:
                vals = [float(x) for x in tok[:8]]
            except ValueError:
                continue
            if len(vals) == 8 and vals[0] >= 10.0:
                rows.append(vals)
    cols = ["T_MeV", "p_MeV", "ion", "brems", "pair", "photonuc", "rad", "total"]
    df = pd.DataFrame(rows, columns=cols).drop_duplicates("T_MeV").sort_values("T_MeV")
    return df.reset_index(drop=True)


def groom_dedx_ice(E_MeV, column="total", table=None):
    """Groom tablosundan buz için dE/dx [MeV/cm] (log-log interpolasyon)."""
    t = load_groom() if table is None else table
    return np.exp(np.interp(np.log(E_MeV), np.log(t["T_MeV"]), np.log(t[column]))) * RHO_ICE


def mean_sem(x):
    x = np.asarray(x, dtype=float)
    return x.mean(), x.std(ddof=1)/np.sqrt(len(x))


def median_ci(x, n_boot=2000, cl=0.68, seed=1):
    """Medyan ve bootstrap güven aralığı (alt, üst)."""
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    rng = np.random.default_rng(seed)
    meds = np.median(rng.choice(x, size=(n_boot, len(x)), replace=True), axis=1)
    a = (1 - cl)/2
    return np.median(x), np.quantile(meds, a), np.quantile(meds, 1 - a)


def expected_time_true(sensors_xyz_m, vertex_m, d):
    """Gerçek müon izi için doğrudan Cherenkov fotonunun varış zamanı (müon t=0'da tepe noktasında)."""
    return expected_time(sensors_xyz_m, d, vertex_m, 0.0)

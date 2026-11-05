# LTRAC, MONASH UNIVERSITY
# Screech tone identification for an underexpanded supersonic jet
# Shreeji Kumawat
#
# Microphone data acquired in LabVIEW (NI DAQ, 204.8 kHz). Each run is one nozzle
# pressure ratio (NPR). Script does Welch PSD, picks the screech fundamental and
# harmonics, and compares the screech frequency with Tam's (1986) empirical model.
#
# input files in ./data :  .lvm (LabVIEW text export), .csv (time, volts) or .npz
# run:  python screech_psd.py

import os
import glob
import re
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import welch, find_peaks, spectrogram

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

# --- setup ---
D = 0.010              # nozzle exit diameter [m], converging nozzle
GAMMA = 1.4
R_AIR = 287.0
T0 = 293.0             # stagnation temperature [K]
P_REF = 20e-6          # Pa
MIC_SENS = 3.16e-3     # V/Pa, 1/4" mic (use value from calibration sheet)
NPERSEG = 2 ** 14      # Welch segment -> 12.5 Hz resolution at 204.8 kHz
F_MIN = 2000           # ignore anything below this when picking screech


def load_run(path):
    ext = os.path.splitext(path)[1].lower()
    placeholder = False
    if ext == ".npz":
        d = np.load(path)
        v, fs, npr = d["volts"].astype(float), float(d["fs"]), float(d["NPR"])
        sens = float(d["sensitivity_V_per_Pa"]) if "sensitivity_V_per_Pa" in d else MIC_SENS
        placeholder = bool(d["placeholder"]) if "placeholder" in d else False
    else:
        # LabVIEW .lvm / csv : skip header lines, first col time, second col volts
        raw = np.genfromtxt(path, delimiter="," if ext == ".csv" else "\t", comments="#",
                            skip_header=0, invalid_raise=False)
        raw = raw[~np.isnan(raw).any(axis=1)]
        t, v = raw[:, 0], raw[:, 1]
        fs = 1.0 / np.median(np.diff(t))
        npr = float(re.findall(r"NPR([\d.]+)", os.path.basename(path))[0].rstrip("."))
        sens = MIC_SENS
    return v / sens, fs, npr, placeholder


def jet_conditions(NPR):
    Mj = np.sqrt(2 / (GAMMA - 1) * (NPR ** ((GAMMA - 1) / GAMMA) - 1))       # fully expanded Mach
    Tj = T0 / (1 + (GAMMA - 1) / 2 * Mj ** 2)
    Uj = Mj * np.sqrt(GAMMA * R_AIR * Tj)
    # fully expanded jet diameter (Tam & Tanna)
    Dj = D * ((1 + (GAMMA - 1) / 2 * Mj ** 2) / (1 + (GAMMA - 1) / 2)) ** ((GAMMA + 1) / (4 * (GAMMA - 1))) / np.sqrt(Mj)
    return Mj, Uj, Dj


def tam_screech(NPR):
    Mj, Uj, Dj = jet_conditions(NPR)
    St = 0.67 / np.sqrt(Mj ** 2 - 1) / (1 + 0.7 * Mj / np.sqrt(1 + (GAMMA - 1) / 2 * Mj ** 2))
    return St * Uj / Dj


def analyse(p, fs):
    f, Pxx = welch(p, fs=fs, window="hann", nperseg=NPERSEG, noverlap=NPERSEG // 2, detrend="constant")
    spl = 10 * np.log10(Pxx / P_REF ** 2)                 # dB/Hz
    oaspl = 10 * np.log10(np.var(p) / P_REF ** 2)
    m = f > F_MIN
    # screech = most prominent narrow peak (prominence vs local broadband)
    pk, prop = find_peaks(spl[m], prominence=10)
    if len(pk) == 0:
        return f, spl, oaspl, np.nan, np.nan, np.nan, []
    i = pk[np.argmax(prop["prominences"])]
    fsc = f[m][i]
    # refine with parabolic interpolation
    j = np.where(m)[0][i]
    a, b, c = spl[j - 1], spl[j], spl[j + 1]
    fsc = fsc + 0.5 * (a - c) / (a - 2 * b + c) * (f[1] - f[0])
    level = spl[j]
    prom = prop["prominences"].max()
    harm = []
    for k in (2, 3):
        win = (f > k * fsc * 0.97) & (f < k * fsc * 1.03)
        if win.any():
            harm.append((k, f[win][np.argmax(spl[win])], spl[win].max()))
    return f, spl, oaspl, fsc, level, prom, harm


def main():
    files = sorted(glob.glob(os.path.join(DATA, "*NPR*.*")), key=lambda s: float(re.findall(r"NPR([\d.]+\d)", s)[0]))
    results = []
    any_placeholder = False
    fig, ax = plt.subplots(figsize=(10, 6))
    for k, path in enumerate(files):
        p, fs, npr, ph = load_run(path)
        any_placeholder |= ph
        f, spl, oaspl, fsc, lvl, prom, harm = analyse(p, fs)
        Mj, Uj, Dj = jet_conditions(npr)
        results.append(dict(NPR=npr, Mj=Mj, Uj=Uj, fs=fsc, f_tam=tam_screech(npr), St=fsc * Dj / Uj,
                            level=lvl, prom=prom, oaspl=oaspl, harm=harm, f=f, spl=spl, p=p, fsr=fs))
        off = 20 * k
        ax.semilogx(f, spl + off, lw=0.8, label=f"NPR {npr:.1f} (+{off} dB)")
        ax.plot(fsc, lvl + off, "kv", ms=6)
    ax.set_xlim(1e3, 1e5)
    ax.set_xlabel("Frequency [Hz]"); ax.set_ylabel("PSD [dB/Hz re 20 uPa], offset")
    ax.set_title("Welch PSD of near-field microphone - screech fundamental marked")
    ax.grid(alpha=0.3, which="both"); ax.legend(fontsize=8)
    if any_placeholder:
        ax.text(0.5, 0.5, "PLACEHOLDER DATA", transform=ax.transAxes, fontsize=30, color="grey",
                alpha=0.18, ha="center", va="center", rotation=25)
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "psd_all_NPR.png"), dpi=150); plt.close(fig)

    # screech frequency vs NPR, Tam model
    NPRf = np.linspace(2.2, 4.6, 100)
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.5))
    axs[0].plot(NPRf, tam_screech(NPRf) / 1e3, "k--", label="Tam (1986) empirical")
    axs[0].plot([r["NPR"] for r in results], [r["fs"] / 1e3 for r in results], "o", ms=8, label="Measured fundamental")
    axs[0].set_xlabel("NPR"); axs[0].set_ylabel("Screech frequency [kHz]"); axs[0].legend(); axs[0].grid(alpha=0.3)
    axs[0].set_title("Screech frequency vs NPR")
    axs[1].plot([r["Mj"] for r in results], [r["St"] for r in results], "s", ms=8, color="C1")
    Mjf = jet_conditions(NPRf)[0]
    St_tam = 0.67 / np.sqrt(Mjf ** 2 - 1) / (1 + 0.7 * Mjf / np.sqrt(1 + (GAMMA - 1) / 2 * Mjf ** 2))
    axs[1].plot(Mjf, St_tam, "k--")
    axs[1].set_xlabel("Fully expanded Mach number M$_j$"); axs[1].set_ylabel("St = f D$_j$ / U$_j$")
    axs[1].set_title("Screech Strouhal number"); axs[1].grid(alpha=0.3)
    if any_placeholder:
        for a in axs:
            a.text(0.5, 0.5, "PLACEHOLDER DATA", transform=a.transAxes, fontsize=24, color="grey",
                   alpha=0.18, ha="center", va="center", rotation=25)
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "screech_vs_NPR.png"), dpi=150); plt.close(fig)

    # spectrogram of the strongest case to show tone is steady
    best = max(results, key=lambda r: r["prom"])
    fsr = best["fsr"]
    ff, tt, Sxx = spectrogram(best["p"], fs=fsr, nperseg=4096, noverlap=2048)
    fig, ax = plt.subplots(figsize=(9, 4))
    pc = ax.pcolormesh(tt * 1e3, ff / 1e3, 10 * np.log10(Sxx / P_REF ** 2 + 1e-12), shading="auto", vmin=0)
    ax.set_ylim(0, 50); ax.set_xlabel("Time [ms]"); ax.set_ylabel("Frequency [kHz]")
    ax.set_title(f"Spectrogram NPR {best['NPR']:.1f} - screech fundamental + harmonics")
    fig.colorbar(pc, label="dB/Hz")
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "spectrogram.png"), dpi=150); plt.close(fig)

    lines = ["SUPERSONIC JET SCREECH - RESULTS SUMMARY", "=" * 44]
    if any_placeholder:
        lines.append("!! generated from PLACEHOLDER data - rerun after replacing data/ !!")
    lines.append(f"Nozzle D = {D*1e3:.0f} mm, T0 = {T0:.0f} K, Welch nperseg = {NPERSEG}, Hann, 50% overlap")
    lines.append("")
    lines.append(f"{'NPR':>5s}{'Mj':>7s}{'Uj m/s':>9s}{'f_s Hz':>10s}{'Tam Hz':>10s}{'err%':>7s}{'St':>7s}{'peak dB':>9s}{'prom dB':>9s}{'OASPL':>8s}")
    for r in results:
        lines.append(f"{r['NPR']:5.1f}{r['Mj']:7.3f}{r['Uj']:9.1f}{r['fs']:10.0f}{r['f_tam']:10.0f}"
                     f"{(r['fs']/r['f_tam']-1)*100:7.1f}{r['St']:7.3f}{r['level']:9.1f}{r['prom']:9.1f}{r['oaspl']:8.1f}")
        for k, fh, lh in r["harm"]:
            lines.append(f"{'':12s}harmonic {k}: {fh:8.0f} Hz ({fh/r['fs']:.2f} f_s), {lh:.1f} dB/Hz")
    txt = "\n".join(lines)
    print(txt)
    open(os.path.join(HERE, "results_summary.txt"), "w").write(txt + "\n")


if __name__ == "__main__":
    main()

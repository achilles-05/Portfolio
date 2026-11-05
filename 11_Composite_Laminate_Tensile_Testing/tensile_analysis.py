# MAHINDRA UNIVERSITY - MATERIALS SCIENCE LAB
# Tensile testing of hand laid, vacuum bagged CFRP and GFRP laminate coupons
# Shreeji Kumawat
#
# UTM export (time, crosshead extension, load) for each coupon is in data/utm/.
# Strain is from crosshead, corrected for machine compliance and toe region
# (no extensometer was available), so modulus here is the corrected apparent modulus.
# Coupons roughly follow ASTM D3039: 250 x 25 mm, 150 mm between grips, 2 mm/min.
#
# run:  python tensile_analysis.py

import os
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

MACHINE_COMPLIANCE = 0.015   # mm/kN, from steel bar calibration test on the same UTM
CHORD = (0.25, 0.50)          # modulus taken between 25% and 50% of UTS (linear part)

COLORS = {"CFRP": "C0", "GFRP": "C2"}


def read(path):
    with open(path) as f:
        ph = f.readline().startswith("# PLACEHOLDER")
    df = pd.read_csv(path, comment="#")
    df.attrs["placeholder"] = ph
    return df


def stamp(ax):
    ax.text(0.5, 0.5, "PLACEHOLDER DATA", transform=ax.transAxes, fontsize=26, color="grey",
            alpha=0.18, ha="center", va="center", rotation=25)


def reduce_coupon(raw, w, t, L0):
    A = w * t
    load = raw.load_kN.values
    ext = raw.extension_mm.values - MACHINE_COMPLIANCE * load
    sig = load * 1e3 / A                       # MPa
    i_max = np.argmax(sig)
    uts = sig[i_max]
    # chord modulus on raw extension, then use it to remove toe region
    lo, hi = CHORD[0] * uts, CHORD[1] * uts
    m = (sig[:i_max] >= lo) & (sig[:i_max] <= hi)
    k, c = np.polyfit(ext[:i_max][m], sig[:i_max][m], 1)
    toe = -c / k                                # extension where linear part hits zero stress
    eps = (ext - toe) / L0
    E = k * L0 / 1e3                            # GPa
    eps_f = eps[i_max]
    return eps, sig, uts, E, eps_f, i_max


def fibre_volume_fraction(row):
    Wf = row.dry_fabric_g / row.cured_panel_g
    vf = (Wf / row.fibre_density) / (Wf / row.fibre_density + (1 - Wf) / row.resin_density)
    return Wf, vf


def weibull(x):
    x = np.sort(x)
    n = len(x)
    F = (np.arange(1, n + 1) - 0.3) / (n + 0.4)        # median rank
    m, b = np.polyfit(np.log(x), np.log(-np.log(1 - F)), 1)
    return m, np.exp(-b / m)


def main():
    spec = read(os.path.join(DATA, "specimens.csv"))
    panels = read(os.path.join(DATA, "panel_weights.csv"))
    placeholder = spec.attrs["placeholder"]

    rows = []
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.5), sharey=False)
    for _, s in spec.iterrows():
        raw = read(os.path.join(DATA, "utm", f"{s.specimen}.csv"))
        placeholder |= raw.attrs["placeholder"]
        eps, sig, uts, E, eps_f, i_max = reduce_coupon(raw, s.width_mm, s.thickness_mm, s.gauge_mm)
        rows.append(dict(specimen=s.specimen, material=s.material, UTS=uts, E=E, eps_f=eps_f * 100,
                         Fmax=raw.load_kN.max(), mode=s.failure_mode))
        ax = axs[0 if s.material == "CFRP" else 1]
        keep = (eps >= 0) & (np.arange(len(eps)) <= i_max + 1)     # drop toe region and post-failure tail
        ax.plot(np.r_[0, eps[keep]] * 100, np.r_[0, sig[keep]], color=COLORS[s.material], alpha=0.8, lw=1.2)
        ax.text(eps[i_max] * 100, sig[i_max] + 6, s.specimen, fontsize=7, ha="center")
    for ax, mat in zip(axs, ["CFRP", "GFRP"]):
        ax.set_title(f"{mat} coupons - stress vs strain")
        ax.set_xlabel("Strain [%] (compliance + toe corrected)"); ax.set_ylabel("Stress [MPa]")
        ax.grid(alpha=0.3); ax.set_xlim(left=0); ax.set_ylim(bottom=0)
        if placeholder:
            stamp(ax)
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "stress_strain.png"), dpi=150); plt.close(fig)

    res = pd.DataFrame(rows)
    summ = res.groupby("material").agg(UTS=("UTS", "mean"), UTS_sd=("UTS", "std"),
                                       E=("E", "mean"), E_sd=("E", "std"),
                                       eps=("eps_f", "mean"), eps_sd=("eps_f", "std"))

    # comparison bar chart
    fig, axs = plt.subplots(1, 3, figsize=(12, 4))
    for ax, (key, sd, lab) in zip(axs, [("UTS", "UTS_sd", "UTS [MPa]"), ("E", "E_sd", "Modulus [GPa]"),
                                        ("eps", "eps_sd", "Failure strain [%]")]):
        ax.bar(summ.index, summ[key], yerr=summ[sd], capsize=6, color=[COLORS[m] for m in summ.index])
        for x, m in enumerate(summ.index):
            pts = res[res.material == m][{"UTS": "UTS", "E": "E", "eps": "eps_f"}[key]]
            ax.plot(np.full(len(pts), x) + np.linspace(-0.12, 0.12, len(pts)), pts, "k.", ms=5)
        ax.set_ylabel(lab); ax.grid(alpha=0.3, axis="y")
        if placeholder:
            stamp(ax)
    fig.suptitle("CFRP vs GFRP - mean +/- 1 SD, n = 5 each")
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "property_comparison.png"), dpi=150); plt.close(fig)

    # specific properties vs density (rule of mixtures density)
    lines = ["COMPOSITE LAMINATE TENSILE TESTS - RESULTS SUMMARY", "=" * 50]
    if placeholder:
        lines.append("!! generated from PLACEHOLDER data - rerun after replacing data/ !!")
    lines.append(f"Machine compliance correction {MACHINE_COMPLIANCE} mm/kN, chord modulus {CHORD[0]*100:.0f}-{CHORD[1]*100:.0f}% UTS")
    lines.append("")
    lines.append("Fibre content (burn-off free, from fabric / cured panel weights):")
    dens = {}
    for _, p in panels.iterrows():
        Wf, vf = fibre_volume_fraction(p)
        rho = vf * p.fibre_density + (1 - vf) * p.resin_density
        dens[p.material] = rho
        lines.append(f"  {p.material}: Wf = {Wf*100:.1f}%, Vf = {vf*100:.1f}%, laminate density {rho:.2f} g/cc")
    lines.append("")
    lines.append(f"{'coupon':8s}{'mat':6s}{'Fmax kN':>9s}{'UTS MPa':>9s}{'E GPa':>8s}{'eps_f %':>9s}  mode")
    for _, r in res.iterrows():
        lines.append(f"{r.specimen:8s}{r.material:6s}{r.Fmax:9.2f}{r.UTS:9.1f}{r.E:8.1f}{r.eps_f:9.2f}  {r['mode']}")
    lines.append("")
    for m, r in summ.iterrows():
        wm, s0 = weibull(res[res.material == m].UTS.values)
        lines.append(f"{m}: UTS {r.UTS:.0f} +/- {r.UTS_sd:.0f} MPa (CV {r.UTS_sd/r.UTS*100:.1f}%), "
                     f"E {r.E:.1f} +/- {r.E_sd:.1f} GPa, eps_f {r.eps:.2f} +/- {r.eps_sd:.2f} %")
        lines.append(f"      specific strength {r.UTS/dens[m]:.0f} MPa/(g/cc), specific modulus {r.E/dens[m]:.1f} GPa/(g/cc), "
                     f"Weibull m = {wm:.1f}, sigma0 = {s0:.0f} MPa")
    lines.append("")
    lines.append("Failure codes (ASTM D3039): LGM = lateral gauge middle, LAT = lateral at grip/tab, XGM = explosive gauge middle")
    txt = "\n".join(lines)
    print(txt)
    open(os.path.join(HERE, "results_summary.txt"), "w").write(txt + "\n")


if __name__ == "__main__":
    main()

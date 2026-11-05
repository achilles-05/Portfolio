# MAHINDRA UNIVERSITY - SMART INDIA HACKATHON SIH2026 (AEROSPACE)
# Cold-gas thruster static test stand - data reduction and comparison with theory
# Shreeji Kumawat
#
# Reads the stand data in ./data and compares measured thrust and mass flow against
# 1D isentropic / choked-flow theory for the converging (C) and converging-diverging (CD)
# 3D printed nozzles. Working gas is dry air from the regulator.
#
# run:  python thrust_analysis.py

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")

# gas + ambient
GAMMA = 1.4
R_AIR = 287.0        # J/kg K
T0 = 293.0           # K, lab temperature (bottle gas assumed at room temp)
PA = 101325.0        # Pa

# nozzle geometry (nominal CAD values, mm)
NOZZLES = {
    "C":  {"d_throat": 3.0, "d_exit": 3.0, "label": "Converging"},
    "CD": {"d_throat": 3.0, "d_exit": 4.0, "label": "Converging-Diverging"},
}

NOMINAL_P = 7.0      # barg, the operating point we quote in the report


def read_csv(name):
    path = os.path.join(DATA, name)
    with open(path) as f:
        first = f.readline()
    df = pd.read_csv(path, comment="#")
    df.attrs["placeholder"] = first.startswith("# PLACEHOLDER")
    return df


def stamp(ax, df):
    if df.attrs.get("placeholder"):
        ax.text(0.5, 0.5, "PLACEHOLDER DATA", transform=ax.transAxes, fontsize=26,
                color="grey", alpha=0.18, ha="center", va="center", rotation=25)


# ---------------- theory ----------------

def choked_mdot(P0, A_t):
    # mass flow through a choked throat [kg/s]
    return A_t * P0 / np.sqrt(T0) * np.sqrt(GAMMA / R_AIR) * \
        (2 / (GAMMA + 1)) ** ((GAMMA + 1) / (2 * (GAMMA - 1)))


def area_ratio(M):
    return (1 / M) * ((2 / (GAMMA + 1)) * (1 + (GAMMA - 1) / 2 * M**2)) ** ((GAMMA + 1) / (2 * (GAMMA - 1)))


def exit_mach_supersonic(AR):
    # newton iteration on the area-mach relation, supersonic branch
    if AR <= 1.0:
        return 1.0
    M = 2.0
    for _ in range(50):
        h = 1e-6
        f = area_ratio(M) - AR
        df = (area_ratio(M + h) - area_ratio(M - h)) / (2 * h)
        M = M - f / df
    return M


def ideal_thrust(P0_gauge_bar, d_t_mm, d_e_mm):
    """ideal 1D thrust [N] and mass flow [kg/s] for a given chamber pressure (barg)"""
    P0 = P0_gauge_bar * 1e5 + PA
    A_t = np.pi * (d_t_mm * 1e-3) ** 2 / 4
    A_e = np.pi * (d_e_mm * 1e-3) ** 2 / 4
    m = choked_mdot(P0, A_t)
    Me = exit_mach_supersonic(A_e / A_t)
    Te = T0 / (1 + (GAMMA - 1) / 2 * Me**2)
    Pe = P0 * (1 + (GAMMA - 1) / 2 * Me**2) ** (-GAMMA / (GAMMA - 1))
    Ve = Me * np.sqrt(GAMMA * R_AIR * Te)
    F = m * Ve + (Pe - PA) * A_e
    return F, m, Me, Pe


ideal_thrust_v = np.vectorize(ideal_thrust)


# ---------------- analysis ----------------

def loadcell_calibration():
    cal = read_csv("loadcell_calibration.csv")
    k, c = np.polyfit(cal.mass_g, cal.raw_counts, 1)
    fit = k * cal.mass_g + c
    r2 = 1 - np.sum((cal.raw_counts - fit) ** 2) / np.sum((cal.raw_counts - cal.raw_counts.mean()) ** 2)
    N_per_count = 9.81e-3 / k

    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(cal.mass_g, cal.raw_counts, "o", label="dead weights")
    ax.plot(cal.mass_g, fit, "-", label=f"fit  R$^2$ = {r2:.5f}")
    ax.set_xlabel("Applied mass [g]")
    ax.set_ylabel("HX711 raw counts")
    ax.set_title("Load cell calibration")
    ax.grid(alpha=0.3); ax.legend()
    stamp(ax, cal)
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "loadcell_calibration.png"), dpi=150)
    plt.close(fig)
    return r2, N_per_count


def sweep():
    df = read_csv("thrust_sweep.csv")
    g = df.groupby(["nozzle", "P_set_barg"]).agg(
        P_ch=("P_chamber_barg", "mean"),
        F=("thrust_N", "mean"), F_sd=("thrust_N", "std"),
        m=("mdot_gs", "mean"), m_sd=("mdot_gs", "std")).reset_index()

    rows = []
    fig, axs = plt.subplots(1, 2, figsize=(12, 4.5))
    for c, (name, geo) in enumerate(NOZZLES.items()):
        s = g[g.nozzle == name]
        col = "C0" if c == 0 else "C3"
        Pfine = np.linspace(1.5, 8.5, 100)
        Fth, mth, _, _ = ideal_thrust_v(Pfine, geo["d_throat"], geo["d_exit"])
        axs[0].plot(Pfine, Fth, "--", color=col, label=f"{name} theory (P$_{{set}}$)")
        axs[0].errorbar(s.P_set_barg, s.F, yerr=s.F_sd, fmt="o", color=col, capsize=3, label=f"{name} measured")
        axs[1].plot(Pfine, mth * 1e3, "--", color=col, label=f"{name} choked-flow theory")
        axs[1].errorbar(s.P_set_barg, s.m, yerr=s.m_sd, fmt="s", color=col, capsize=3, label=f"{name} measured")

        F_set, m_set, Me, Pe = ideal_thrust_v(s.P_set_barg.values, geo["d_throat"], geo["d_exit"])
        F_ch, m_ch, _, _ = ideal_thrust_v(s.P_ch.values, geo["d_throat"], geo["d_exit"])
        for i, (_, r) in enumerate(s.iterrows()):
            rows.append(dict(nozzle=name, P_set=r.P_set_barg, P_ch=r.P_ch,
                             F_meas=r.F, F_th_set=F_set[i], F_th_ch=F_ch[i],
                             m_meas=r.m, m_th_set=m_set[i] * 1e3, m_th_ch=m_ch[i] * 1e3,
                             Me=Me[i], Pe_bar=Pe[i] / 1e5))
    for ax in axs:
        ax.set_xlabel("Regulator set pressure [barg]"); ax.grid(alpha=0.3); ax.legend(fontsize=8)
        stamp(ax, df)
    axs[0].set_ylabel("Thrust [N]"); axs[0].set_title("Thrust vs supply pressure")
    axs[1].set_ylabel("Mass flow [g/s]"); axs[1].set_title("Mass flow vs supply pressure")
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "thrust_massflow_vs_pressure.png"), dpi=150)
    plt.close(fig)
    return pd.DataFrame(rows), df


def shortfall_breakdown(res, df):
    # split the deficit at the nominal point into: regulator droop / throat (Cd) / remaining nozzle losses
    out = {}
    fig, ax = plt.subplots(figsize=(7, 4.5))
    x = np.arange(len(NOZZLES)); w = 0.2
    for j, name in enumerate(NOZZLES):
        r = res[(res.nozzle == name) & (res.P_set == NOMINAL_P)].iloc[0]
        total = 1 - r.F_meas / r.F_th_set
        droop = 1 - r.F_th_ch / r.F_th_set
        Cd = r.m_meas / r.m_th_ch                       # discharge coefficient from measured flow
        throat = (1 - droop) * (1 - Cd)
        rest = total - droop - throat
        Cf_meas = r.F_meas / ((r.P_ch * 1e5 + PA) * np.pi * (NOZZLES[name]["d_throat"] * 1e-3) ** 2 / 4)
        out[name] = dict(total=total, droop=droop, throat=throat, rest=rest, Cd=Cd,
                         Cf=Cf_meas, P_ch=r.P_ch, F_meas=r.F_meas, F_th=r.F_th_set, Me=r.Me)
        vals = [droop, throat, rest]
        bottom = 0
        for k, (v, lab) in enumerate(zip(vals, ["Regulator droop", "Throat roughness / undersize (C$_d$)", "Other nozzle losses"])):
            ax.bar(j, v * 100, 0.5, bottom=bottom, color=f"C{k}", label=lab if j == 0 else None)
            bottom += v * 100
        ax.text(j, bottom + 0.3, f"{total*100:.1f}%", ha="center", fontweight="bold")
    ax.set_xticks(x); ax.set_xticklabels([NOZZLES[n]["label"] for n in NOZZLES])
    ax.set_ylabel("Thrust shortfall vs ideal [%]")
    ax.set_title(f"Thrust shortfall breakdown at {NOMINAL_P:.0f} barg")
    ax.legend(); ax.grid(alpha=0.3, axis="y")
    stamp(ax, df)
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "shortfall_breakdown.png"), dpi=150)
    plt.close(fig)
    return out


def firing_trace():
    tr = read_csv("firing_CD_7barg.csv")
    fig, ax1 = plt.subplots(figsize=(8, 4))
    ax1.plot(tr.time_s, tr.thrust_N, color="C0", label="Thrust")
    ax1.set_xlabel("Time [s]"); ax1.set_ylabel("Thrust [N]", color="C0")
    ax2 = ax1.twinx()
    ax2.plot(tr.time_s, tr.P_chamber_barg, color="C3", alpha=0.7, label="Chamber pressure")
    ax2.axhline(NOMINAL_P, color="C3", ls=":", lw=1)
    ax2.set_ylabel("Chamber pressure [barg]", color="C3")
    ax1.set_title("CD nozzle firing at 7 barg set - regulator droop visible after valve opens")
    ax1.grid(alpha=0.3)
    stamp(ax1, tr)
    fig.tight_layout(); fig.savefig(os.path.join(HERE, "firing_trace_CD.png"), dpi=150)
    plt.close(fig)
    steady = tr[(tr.time_s > 3) & (tr.time_s < 5.8)]
    return steady.thrust_N.mean(), steady.thrust_N.std(), steady.P_chamber_barg.mean()


def main():
    r2, Npc = loadcell_calibration()
    res, raw = sweep()
    br = shortfall_breakdown(res, raw)
    F_ss, F_sd, P_ss = firing_trace()
    insp = read_csv("throat_inspection.csv")

    lines = []
    lines.append("COLD-GAS THRUSTER STATIC TEST - RESULTS SUMMARY")
    lines.append("=" * 52)
    if raw.attrs.get("placeholder"):
        lines.append("!! generated from PLACEHOLDER data - rerun after replacing data/ !!")
    lines.append(f"Load cell calibration: R^2 = {r2:.5f}, sensitivity = {Npc*1e6:.2f} uN/count")
    lines.append("")
    lines.append("Throat inspection:")
    for _, r in insp.iterrows():
        lines.append(f"  {r.nozzle:3s} nominal {r.nominal_throat_mm:.2f} mm, measured {r.measured_throat_mm:.2f} mm, Ra {r.Ra_um:.1f} um")
    lines.append("")
    lines.append("Sweep (mean of 3 runs):")
    lines.append(f"  {'noz':4s}{'Pset':>6s}{'Pch':>7s}{'F_meas':>9s}{'F_ideal':>9s}{'dF%':>7s}{'m_meas':>9s}{'m_ideal':>9s}")
    for _, r in res.iterrows():
        lines.append(f"  {r.nozzle:4s}{r.P_set:6.1f}{r.P_ch:7.2f}{r.F_meas:9.3f}{r.F_th_set:9.3f}"
                     f"{(1-r.F_meas/r.F_th_set)*100:7.1f}{r.m_meas:9.2f}{r.m_th_set:9.2f}")
    lines.append("")
    lines.append(f"Shortfall at {NOMINAL_P:.0f} barg set pressure:")
    for n, b in br.items():
        lines.append(f"  {NOZZLES[n]['label']}: F = {b['F_meas']:.2f} N vs {b['F_th']:.2f} N ideal -> {b['total']*100:.1f}% short")
        lines.append(f"     regulator droop   {b['droop']*100:5.1f}%  (chamber only reached {b['P_ch']:.2f} barg)")
        lines.append(f"     throat Cd = {b['Cd']:.3f} {b['throat']*100:5.1f}%")
        lines.append(f"     other losses      {b['rest']*100:5.1f}%")
        lines.append(f"     measured Cf = {b['Cf']:.3f}, design exit Mach = {b['Me']:.2f}")
    lines.append("")
    lines.append(f"Firing trace (CD, 7 barg): steady thrust {F_ss:.2f} +/- {F_sd:.2f} N at {P_ss:.2f} barg chamber")
    txt = "\n".join(lines)
    print(txt)
    with open(os.path.join(HERE, "results_summary.txt"), "w") as f:
        f.write(txt + "\n")


if __name__ == "__main__":
    main()

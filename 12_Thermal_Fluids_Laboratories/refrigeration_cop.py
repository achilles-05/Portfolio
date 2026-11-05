# Vapour compression refrigeration test rig (R134a) - Thermal Lab
# Shreeji Kumawat
# Actual COP from cooling of the evaporator water tank and compressor power,
# theoretical COP from the measured cycle state points using CoolProp, and Carnot COP.

import numpy as np
import matplotlib.pyplot as plt
from CoolProp.CoolProp import PropsSI
from labutils import read, stamp, save, write_summary, CP_W

FLUID = "R134a"
M_TANK = 40.0          # kg water in evaporator tank
PATM = 1.013e5

df = read("vcr_test.csv")
Pe = df.P_evap_barg * 1e5 + PATM
Pc = df.P_cond_barg * 1e5 + PATM
h1 = np.array([PropsSI("H", "P", p, "T", t + 273.15, FLUID) for p, t in zip(Pe, df.T1_comp_in_C)])
s1 = np.array([PropsSI("S", "P", p, "T", t + 273.15, FLUID) for p, t in zip(Pe, df.T1_comp_in_C)])
h2 = np.array([PropsSI("H", "P", p, "T", t + 273.15, FLUID) for p, t in zip(Pc, df.T2_comp_out_C)])
h2s = np.array([PropsSI("H", "P", p, "S", s, FLUID) for p, s in zip(Pc, s1)])
h3 = np.array([PropsSI("H", "P", p, "T", t + 273.15, FLUID) for p, t in zip(Pc, df.T3_cond_out_C)])
h4 = h3
Tev = np.array([PropsSI("T", "P", p, "Q", 1, FLUID) for p in Pe])
Tcd = np.array([PropsSI("T", "P", p, "Q", 0, FLUID) for p in Pc])

COP_cycle = (h1 - h4) / (h2 - h1)
COP_isen = (h1 - h4) / (h2s - h1)
COP_carnot = Tev / (Tcd - Tev)
eta_s = (h2s - h1) / (h2 - h1)

t = df.time_min.values * 60
dTdt = -np.gradient(df.T_evap_water_C.values, t)
Q_e = M_TANK * CP_W * dTdt
COP_act = Q_e / df.P_comp_W
m_ref = Q_e / (h1 - h4)

fig, axs = plt.subplots(1, 2, figsize=(12, 4.5))
axs[0].plot(df.time_min, COP_carnot, "k^-", label="Carnot")
axs[0].plot(df.time_min, COP_isen, "o-", label="Ideal cycle (isentropic)")
axs[0].plot(df.time_min, COP_cycle, "s-", label="Cycle from measured states")
axs[0].plot(df.time_min, COP_act, "D-", label="Actual (tank cooling / electrical)")
axs[0].set_xlabel("Time [min]"); axs[0].set_ylabel("COP"); axs[0].set_title("COP during pull-down"); axs[0].legend(fontsize=8)
axs[0].grid(alpha=0.3); stamp(axs[0], df)

# p-h diagram with the 60 min cycle
hl = []; hv = []; ps = np.linspace(1.0e5, 3.5e6, 120)
for p in ps:
    hl.append(PropsSI("H", "P", p, "Q", 0, FLUID)); hv.append(PropsSI("H", "P", p, "Q", 1, FLUID))
ax = axs[1]
ax.plot(np.array(hl) / 1e3, ps / 1e5, "k-", lw=1); ax.plot(np.array(hv) / 1e3, ps / 1e5, "k-", lw=1)
for i, c in [(0, "C0"), (len(df) - 1, "C3")]:
    H = np.array([h1[i], h2[i], h3[i], h4[i], h1[i]]) / 1e3
    P = np.array([Pe[i], Pc[i], Pc[i], Pe[i], Pe[i]]) / 1e5
    ax.plot(H, P, "o-", color=c, label=f"t = {df.time_min[i]} min")
ax.set_yscale("log"); ax.set_xlabel("Enthalpy [kJ/kg]"); ax.set_ylabel("Pressure [bar abs]")
ax.set_title("R134a cycle on p-h diagram"); ax.legend(); ax.grid(alpha=0.3, which="both"); stamp(ax, df)
save(fig, "refrigeration_cop.png")

lines = ["VAPOUR COMPRESSION REFRIGERATION (R134a)", "=" * 40,
         f"{'t min':>6s}{'T_ev C':>8s}{'T_cd C':>8s}{'RE kJ/kg':>9s}{'Q_e W':>8s}{'m g/s':>7s}{'COP_act':>8s}{'COP_cyc':>8s}{'COP_C':>7s}{'eta_s':>7s}"]
for i in range(len(df)):
    lines.append(f"{df.time_min[i]:6d}{Tev[i]-273.15:8.1f}{Tcd[i]-273.15:8.1f}{(h1[i]-h4[i])/1e3:9.1f}{Q_e[i]:8.0f}"
                 f"{m_ref[i]*1e3:7.2f}{COP_act[i]:8.2f}{COP_cycle[i]:8.2f}{COP_carnot[i]:7.2f}{eta_s[i]:7.2f}")
lines.append(f"\nmean actual COP {COP_act.mean():.2f}, cycle COP {COP_cycle.mean():.2f}, Carnot {COP_carnot.mean():.2f}, "
             f"relative efficiency {np.mean(COP_act/COP_carnot)*100:.0f}% of Carnot")
write_summary("refrigeration_cop.txt", lines, df)

# Concentric tube heat exchanger - parallel and counter flow - Heat Transfer Lab
# Shreeji Kumawat
# Hot water in inner tube, cold water in annulus. LMTD, overall U, effectiveness and NTU.

import numpy as np
import matplotlib.pyplot as plt
from labutils import read, stamp, save, write_summary, CP_W

D_I = 0.0127        # m, inner tube OD
L = 1.5             # m
A = np.pi * D_I * L

df = read("heat_exchanger.csv")
mh = df.hot_Lpm / 60 * 0.998
mc = df.cold_Lpm / 60 * 0.998
Qh = mh * CP_W * (df.T_hot_in - df.T_hot_out)
Qc = mc * CP_W * (df.T_cold_out - df.T_cold_in)
par = df.flow == "parallel"
dT1 = np.where(par, df.T_hot_in - df.T_cold_in, df.T_hot_in - df.T_cold_out)
dT2 = np.where(par, df.T_hot_out - df.T_cold_out, df.T_hot_out - df.T_cold_in)
LMTD = (dT1 - dT2) / np.log(dT1 / dT2)
Qm = (Qh + Qc) / 2
U = Qm / (A * LMTD)
Cmin = np.minimum(mh, mc) * CP_W
eff = Qh / (Cmin * (df.T_hot_in - df.T_cold_in))
NTU = U * A / Cmin

fig, axs = plt.subplots(1, 2, figsize=(12, 4.5))
lab = [f"{h:.0f}/{c:.0f}" for h, c in zip(df.hot_Lpm, df.cold_Lpm)]
x = np.arange(par.sum())
for k, (mode, m) in enumerate([("parallel", par), ("counter", ~par)]):
    axs[0].bar(x + (k - 0.5) * 0.38, eff[m] * 100, 0.38, label=mode)
    axs[1].bar(x + (k - 0.5) * 0.38, U[m], 0.38, label=mode)
for a, yl, t in [(axs[0], "Effectiveness [%]", "Effectiveness"), (axs[1], "U [W/m$^2$K]", "Overall heat transfer coefficient")]:
    a.set_xticks(x); a.set_xticklabels(np.array(lab)[par.values]); a.set_xlabel("Hot / cold flow [L/min]")
    a.set_ylabel(yl); a.set_title(t); a.legend(); a.grid(alpha=0.3, axis="y"); stamp(a, df)
save(fig, "heat_exchanger.png")

# temperature profile sketch for one case of each
fig, ax = plt.subplots(figsize=(7, 4))
for mode, ls in [("parallel", "-"), ("counter", "--")]:
    r = df[(df.flow == mode) & (df.hot_Lpm == 3) & (df.cold_Lpm == 3)].iloc[0]
    ax.plot([0, L], [r.T_hot_in, r.T_hot_out], "r" + ls, label=f"hot, {mode}")
    if mode == "parallel":
        ax.plot([0, L], [r.T_cold_in, r.T_cold_out], "b" + ls, label=f"cold, {mode}")
    else:
        ax.plot([0, L], [r.T_cold_out, r.T_cold_in], "b" + ls, label=f"cold, {mode}")
ax.set_xlabel("Position along exchanger [m]"); ax.set_ylabel("Temperature [°C]")
ax.set_title("Inlet / outlet temperatures, 3 L/min each side"); ax.legend(); ax.grid(alpha=0.3); stamp(ax, df)
save(fig, "hx_temperature_profile.png")

lines = ["CONCENTRIC TUBE HEAT EXCHANGER", "=" * 30,
         f"{'mode':9s}{'h/c Lpm':>8s}{'Qh W':>8s}{'Qc W':>8s}{'loss%':>7s}{'LMTD':>7s}{'U':>7s}{'eff%':>7s}{'NTU':>6s}"]
for i in range(len(df)):
    lines.append(f"{df.flow[i]:9s}{lab[i]:>8s}{Qh[i]:8.0f}{Qc[i]:8.0f}{(1-Qc[i]/Qh[i])*100:7.1f}{LMTD[i]:7.2f}{U[i]:7.0f}{eff[i]*100:7.1f}{NTU[i]:6.2f}")
lines.append(f"\nmean effectiveness: parallel {eff[par].mean()*100:.1f}%, counter {eff[~par].mean()*100:.1f}%")
write_summary("heat_exchanger.txt", lines, df)

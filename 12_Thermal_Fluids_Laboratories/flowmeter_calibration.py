# Venturimeter and orificemeter calibration - Fluid Mechanics Lab
# Shreeji Kumawat
# Actual flow from collecting tank, theoretical flow from Bernoulli with mercury manometer
# differential. Gives Cd for both meters and the Q = K h^n calibration fit.

import numpy as np
import matplotlib.pyplot as plt
from labutils import read, stamp, save, write_summary, RHO_W, RHO_HG, G

GEOM = {"venturi": (25.0, 12.5), "orifice": (25.0, 14.0)}   # inlet, throat/orifice dia [mm]

df = read("flowmeter_test.csv")
lines = ["FLOWMETER CALIBRATION", "=" * 30]
fig, axs = plt.subplots(1, 2, figsize=(12, 4.5))
for k, (name, (d1, d2)) in enumerate(GEOM.items()):
    s = df[df.meter == name]
    A1, A2 = np.pi * (d1 / 1e3) ** 2 / 4, np.pi * (d2 / 1e3) ** 2 / 4
    Q_act = s.volume_L / s.time_s / 1000                                   # m3/s
    h_w = s.manometer_mmHg / 1000 * (RHO_HG / RHO_W - 1)                   # m of water
    Q_th = A2 * np.sqrt(2 * G * h_w / (1 - (A2 / A1) ** 2))
    Cd = Q_act / Q_th
    n, logK = np.polyfit(np.log(h_w), np.log(Q_act * 60000), 1)
    axs[0].plot(h_w * 100, Q_act * 60000, "o", color=f"C{k}", label=f"{name} measured")
    hf = np.linspace(h_w.min(), h_w.max(), 50)
    axs[0].plot(hf * 100, np.exp(logK) * hf ** n, "-", color=f"C{k}", label=f"Q = {np.exp(logK):.1f} h$^{{{n:.2f}}}$")
    axs[1].plot(Q_act * 60000, Cd, "s-", color=f"C{k}", label=f"{name}, mean C$_d$ = {Cd.mean():.3f}")
    lines.append(f"{name}: d1 = {d1} mm, d2 = {d2} mm, beta = {d2/d1:.2f}")
    for qa, qt, cd in zip(Q_act, Q_th, Cd):
        lines.append(f"   Q_act {qa*60000:6.2f} L/min  Q_th {qt*60000:6.2f} L/min  Cd {cd:.3f}")
    lines.append(f"   mean Cd = {Cd.mean():.3f} +/- {Cd.std():.3f},  calibration Q[L/min] = {np.exp(logK):.2f} h[m]^{n:.3f}")
axs[0].set_xlabel("Head difference [cm of water]"); axs[0].set_ylabel("Q actual [L/min]"); axs[0].set_title("Calibration curves")
axs[1].set_xlabel("Q actual [L/min]"); axs[1].set_ylabel("C$_d$"); axs[1].set_ylim(0.5, 1.05); axs[1].set_title("Coefficient of discharge")
for a in axs:
    a.grid(alpha=0.3); a.legend(); stamp(a, df)
save(fig, "flowmeter_calibration.png")
write_summary("flowmeter_calibration.txt", lines, df)

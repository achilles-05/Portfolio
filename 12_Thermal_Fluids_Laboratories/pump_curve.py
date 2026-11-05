# Centrifugal pump performance test - Fluid Mechanics Lab, Mahindra University
# Shreeji Kumawat
# Flow from collecting tank (volume / time), head from suction and delivery gauges,
# input power from energy meter. Fits H-Q curve and finds best efficiency point.

import numpy as np
import matplotlib.pyplot as plt
from labutils import read, stamp, save, write_summary, RHO_W, G

DZ = 0.30   # m, delivery gauge above suction gauge

df = read("pump_test.csv")
Q = np.where(df.time_s > 0, df.volume_L / df.time_s.replace(0, np.nan), 0) * 60   # L/min
Q = np.nan_to_num(Q)
H = (df.P_delivery_bar - df.P_suction_bar) * 1e5 / (RHO_W * G) + DZ
P_hyd = RHO_W * G * (Q / 60000) * H
eta = P_hyd / df.P_input_W * 100

a, b = np.polyfit(Q ** 2, H, 1)                # H = b + a Q^2
c = np.polyfit(Q, eta, 2)
Qf = np.linspace(0, Q.max() * 1.05, 200)
eta_f = np.polyval(c, Qf)
i = np.argmax(eta_f)

fig, ax1 = plt.subplots(figsize=(8, 5))
ax1.plot(Q, H, "o", color="C0", label="Head (measured)")
ax1.plot(Qf, b + a * Qf ** 2, "-", color="C0", label=f"H = {b:.1f} - {-a:.4f} Q$^2$")
ax1.set_xlabel("Flow rate Q [L/min]"); ax1.set_ylabel("Head H [m]", color="C0")
ax2 = ax1.twinx()
ax2.plot(Q, eta, "s", color="C3", label="Overall efficiency")
ax2.plot(Qf, eta_f, "--", color="C3")
ax2.plot(Qf[i], eta_f[i], "k*", ms=14, label=f"BEP {Qf[i]:.0f} L/min, {eta_f[i]:.0f}%")
ax2.set_ylabel("Overall efficiency [%]", color="C3"); ax2.set_ylim(0, 60)
h1, l1 = ax1.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
ax1.legend(h1 + h2, l1 + l2, loc="lower center")
ax1.set_title("Centrifugal pump characteristic at 2900 rpm"); ax1.grid(alpha=0.3)
stamp(ax1, df); save(fig, "pump_curve.png")

lines = ["CENTRIFUGAL PUMP TEST", "=" * 30,
         f"{'Q L/min':>8s}{'H m':>8s}{'P_hyd W':>9s}{'P_in W':>8s}{'eta %':>7s}"]
for q, h, ph, pi, e in zip(Q, H, P_hyd, df.P_input_W, eta):
    lines.append(f"{q:8.1f}{h:8.2f}{ph:9.1f}{pi:8.1f}{e:7.1f}")
lines += ["", f"Shut-off head {b:.1f} m, curve fit H = {b:.2f} - {-a:.5f} Q^2",
          f"Best efficiency point: Q = {Qf[i]:.1f} L/min, H = {b + a*Qf[i]**2:.1f} m, overall eta = {eta_f[i]:.1f}%"]
write_summary("pump_curve.txt", lines, df)

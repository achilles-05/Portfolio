# Friction factor in smooth pipes - Fluid Mechanics Lab
# Shreeji Kumawat
# Head loss over 1 m test length from water manometer, flow from collecting tank.
# Compares measured Darcy f with 64/Re (laminar), Blasius and Colebrook.

import numpy as np
import matplotlib.pyplot as plt
from labutils import read, stamp, save, write_summary, G

NU = 1.0e-6        # m2/s at ~20 C
EPS = 1.5e-6       # m, drawn copper roughness


def colebrook(Re, d):
    f = 0.02
    for _ in range(50):
        f = (-2 * np.log10(EPS / d / 3.7 + 2.51 / (Re * np.sqrt(f)))) ** -2
    return f


df = read("pipe_friction.csv")
Q = df.volume_L / df.time_s / 1000
d = df.d_mm / 1000
v = Q / (np.pi * d ** 2 / 4)
Re = v * d / NU
hf = df.head_loss_mmH2O / 1000
f = hf * d / df.L_m * 2 * G / v ** 2

fig, ax = plt.subplots(figsize=(8, 5))
for k, dd in enumerate(sorted(df.d_mm.unique())):
    m = df.d_mm == dd
    ax.loglog(Re[m], f[m], "o", color=f"C{k}", label=f"measured, d = {dd:.0f} mm")
Rl = np.logspace(2.5, np.log10(2300), 50); Rt = np.logspace(np.log10(3000), 5, 80)
ax.loglog(Rl, 64 / Rl, "k-", label="64/Re")
ax.loglog(Rt, 0.316 * Rt ** -0.25, "k--", label="Blasius")
ax.loglog(Rt, [colebrook(r, 0.008) for r in Rt], "k:", label="Colebrook")
ax.axvspan(2300, 4000, color="grey", alpha=0.15, label="transition")
ax.set_xlabel("Reynolds number"); ax.set_ylabel("Darcy friction factor f")
ax.set_title("Pipe friction - measured vs Moody correlations")
ax.grid(alpha=0.3, which="both"); ax.legend(); stamp(ax, df)
save(fig, "pipe_friction.png")

lines = ["PIPE FRICTION", "=" * 30, f"{'d mm':>5s}{'v m/s':>8s}{'Re':>9s}{'hf mm':>8s}{'f':>8s}{'f_ref':>8s}{'err%':>7s}"]
errs = []
for dd, vv, rr, h, ff in zip(df.d_mm, v, Re, df.head_loss_mmH2O, f):
    fr = 64 / rr if rr < 2300 else colebrook(rr, dd / 1000)
    errs.append(abs(ff / fr - 1) * 100)
    lines.append(f"{dd:5.0f}{vv:8.3f}{rr:9.0f}{h:8.1f}{ff:8.4f}{fr:8.4f}{(ff/fr-1)*100:7.1f}")
lines.append(f"\nmean abs deviation from 64/Re or Colebrook: {np.mean(errs):.1f}%")
write_summary("pipe_friction.txt", lines, df)

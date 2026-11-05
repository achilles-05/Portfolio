# Schematic of the test stand plumbing + instrumentation and the two nozzle profiles
# Shreeji Kumawat - SIH2026

import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))


def box(ax, x, y, w, h, text, fc="#e8eef7"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", fc=fc, ec="k", lw=1.2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=9)


def arrow(ax, x1, y1, x2, y2, ls="-"):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=12, lw=1.4, ls=ls))


fig, ax = plt.subplots(figsize=(12, 5))
ax.set_xlim(0, 12); ax.set_ylim(0, 5); ax.axis("off")

box(ax, 0.2, 2.0, 1.4, 1.0, "Air cylinder\n(200 bar)")
box(ax, 2.1, 2.0, 1.4, 1.0, "Pressure\nregulator\n0-10 barg")
box(ax, 4.0, 2.0, 1.4, 1.0, "Thermal mass\nflow meter")
box(ax, 5.9, 2.0, 1.4, 1.0, "Solenoid\nvalve")
box(ax, 7.8, 1.6, 2.2, 1.8, "Plenum + nozzle\non flexure arm\n(machined Al frame)", fc="#f7ece8")
box(ax, 10.4, 2.0, 1.4, 1.0, "Exhaust\n(ambient)", fc="#f2f2f2")
for x1, x2 in [(1.6, 2.1), (3.5, 4.0), (5.4, 5.9), (7.3, 7.8), (10.0, 10.4)]:
    arrow(ax, x1, 2.5, x2, 2.5)

box(ax, 7.9, 0.2, 2.0, 0.8, "S-type load cell\n+ HX711 (80 Hz)", fc="#eef7e8")
box(ax, 7.9, 4.0, 2.0, 0.8, "Chamber pressure\ntransducer 0-10 bar", fc="#eef7e8")
box(ax, 4.0, 4.0, 2.4, 0.8, "Arduino Mega + LabVIEW/\nPython serial logger", fc="#fff7d6")
arrow(ax, 8.9, 1.0, 8.9, 1.6, ls="--")
arrow(ax, 8.9, 3.4, 8.9, 4.0, ls="--")
arrow(ax, 7.9, 4.4, 6.4, 4.4, ls="--")
ax.plot([7.9, 7.55, 7.55], [0.6, 0.6, 4.15], "k--", lw=1.4); arrow(ax, 7.55, 4.15, 6.4, 4.15, ls="--")
arrow(ax, 4.7, 3.0, 4.7, 4.0, ls="--")
ax.set_title("Cold-gas thruster static test stand - plumbing and instrumentation", fontsize=12)
fig.tight_layout(); fig.savefig(os.path.join(HERE, "stand_schematic.png"), dpi=150)
plt.close(fig)

# nozzle profiles (as printed)
fig, ax = plt.subplots(1, 2, figsize=(11, 3.5))
for a, (name, rt, re) in zip(ax, [("Converging (C)", 1.5, 1.5), ("Converging-Diverging (CD)", 1.5, 2.0)]):
    rin = 6.0
    xc = np.linspace(0, 10, 100)
    rc = rt + (rin - rt) * (1 + np.cos(np.pi * xc / 10)) / 2
    if re > rt:
        L_div = (re - rt) / np.tan(np.radians(15))
        xd = np.linspace(10, 10 + L_div, 30); rd = rt + (xd - 10) * np.tan(np.radians(15))
    else:
        xd = np.linspace(10, 11.5, 5); rd = np.full_like(xd, rt)
    x = np.r_[xc, xd]; r = np.r_[rc, rd]
    a.fill_between(x, r, rin + 2, color="#bbbbbb"); a.fill_between(x, -r, -rin - 2, color="#bbbbbb")
    a.plot(x, r, "k"); a.plot(x, -r, "k"); a.axhline(0, color="k", ls="-.", lw=0.6)
    a.set_aspect("equal"); a.set_title(f"{name}: d* = {2*rt:.1f} mm, d$_e$ = {2*re:.1f} mm", fontsize=10)
    a.set_xlabel("x [mm]"); a.set_ylabel("r [mm]")
fig.tight_layout(); fig.savefig(os.path.join(HERE, "nozzle_profiles.png"), dpi=150)
plt.close(fig)
print("saved stand_schematic.png, nozzle_profiles.png")

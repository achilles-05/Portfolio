# Vacuum bag stack used for the CFRP / GFRP panels + coupon drawing
# Shreeji Kumawat

import os
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))

layers = [  # name, thickness (drawing units), colour
    ("Aluminium tool plate + release wax", 0.6, "#9e9e9e"),
    ("Laminate (4 ply CF / 6 ply GF woven, epoxy)", 0.8, "#333333"),
    ("Peel ply", 0.25, "#e6d3a3"),
    ("Perforated release film", 0.2, "#7fb3d5"),
    ("Breather / bleeder cloth", 0.5, "#f2f2f2"),
    ("Vacuum bag film", 0.15, "#c39bd3"),
]
fig, ax = plt.subplots(1, 2, figsize=(12, 4.2), gridspec_kw={"width_ratios": [1.4, 1]})
a = ax[0]
y = 0
for name, h, c in layers:
    a.add_patch(Rectangle((0, y), 10, h, fc=c, ec="k"))
    a.annotate(name, (10, y + h / 2), xytext=(10.6, y + h / 2), va="center", fontsize=9,
               arrowprops=dict(arrowstyle="-", lw=0.8))
    y += h
a.add_patch(Rectangle((-0.6, 0.6), 0.5, y - 0.6, fc="#f5b041", ec="k"))
a.text(-0.35, y + 0.15, "sealant\ntape", ha="center", fontsize=8)
a.annotate("to vacuum pump\n(-0.9 bar)", (5, y), xytext=(5, y + 0.9), ha="center", fontsize=9,
           arrowprops=dict(arrowstyle="<-", lw=1.2))
a.set_xlim(-1.2, 17); a.set_ylim(-0.3, y + 1.6); a.axis("off")
a.set_title("Hand lay-up + vacuum bag stack (cured 24 h RT + 4 h at 60 °C)")

b = ax[1]
b.add_patch(Rectangle((0, 0), 250, 25, fc="#555555", ec="k"))
for x in (0, 200):
    b.add_patch(Rectangle((x, 0), 50, 25, fc="#d4ac0d", ec="k", alpha=0.85))
b.annotate("", (50, -8), (200, -8), arrowprops=dict(arrowstyle="<->"))
b.text(125, -16, "150 mm between tabs (gauge)", ha="center", fontsize=9)
b.annotate("", (0, 35), (250, 35), arrowprops=dict(arrowstyle="<->"))
b.text(125, 39, "250 mm", ha="center", fontsize=9)
b.text(25, 12.5, "GFRP\ntab", ha="center", va="center", fontsize=8)
b.text(225, 12.5, "GFRP\ntab", ha="center", va="center", fontsize=8)
b.text(260, 12.5, "25 mm", va="center", fontsize=9)
b.set_xlim(-10, 290); b.set_ylim(-25, 50); b.set_aspect("equal"); b.axis("off")
b.set_title("Tensile coupon (ASTM D3039 style)")
fig.tight_layout(); fig.savefig(os.path.join(HERE, "layup_and_coupon.png"), dpi=150)
print("saved layup_and_coupon.png")

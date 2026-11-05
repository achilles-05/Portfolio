# small helpers shared by the lab scripts - Shreeji Kumawat
import os
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
RHO_W = 998.0      # kg/m3
G = 9.81
CP_W = 4180.0      # J/kg K
RHO_HG = 13600.0


def read(name):
    path = os.path.join(DATA, name)
    with open(path) as f:
        ph = f.readline().startswith("# PLACEHOLDER")
    df = pd.read_csv(path, comment="#")
    df.attrs["placeholder"] = ph
    return df


def stamp(ax, df):
    if df.attrs.get("placeholder"):
        ax.text(0.5, 0.5, "PLACEHOLDER DATA", transform=ax.transAxes, fontsize=24, color="grey",
                alpha=0.18, ha="center", va="center", rotation=25)


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(HERE, name), dpi=150)


def write_summary(name, lines, df):
    if df.attrs.get("placeholder"):
        lines.insert(2, "!! generated from PLACEHOLDER data - rerun after replacing data/ !!")
    txt = "\n".join(lines)
    print(txt + "\n")
    with open(os.path.join(HERE, "results", name), "w") as f:
        f.write(txt + "\n")

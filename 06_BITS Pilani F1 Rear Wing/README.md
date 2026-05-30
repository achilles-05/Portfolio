# F1 Rear Wing Design & CFD Validation

**`ANSYS Fluent` `XFOIL` `Aerodynamics` `CFD` `Airfoil Design` `SolidWorks`**

> 🎯 **Top 10 National Finalist — BITS Pilani APOGEE Airfoil Design Challenge 2026**

## Overview

Full aerodynamic design and CFD validation of a multi-element F1 rear wing optimised
for maximum downforce under strict regulatory constraints. Designed for high-downforce
circuits (Monaco, Hungary) targeting extreme cornering grip with minimum straight-line
drag penalty.

**Result: Cl = 3.8 — validated through full CFD analysis**

📁 [CAD Model 1](https://drive.google.com/file/d/1FCQnnI8KvCDwlGRdg6gfvAf2hpk9IwHA/view?usp=drive_link) · [CAD Model 2](https://drive.google.com/file/d/1q4ZtAoCKOVfjZ03RhYeyedJSQVujAi7J/view?usp=drive_link)


## Design Methodology

### 1 · Custom Airfoil Generation

Both airfoils were designed from scratch using XFOIL, inspired by but heavily modified
from established profiles:

**Main Element** — derived from Eppler-423 (high-lift, low-Re baseline):
- Maximum camber shifted significantly aft (trailing 50% of chord) — "aft-loading"
  forces pressure recovery backward, maintaining boundary layer attachment at extreme
  AoA
- Custom sine-wave thickness distribution applied iteratively — final thickness 16.05%
  of 220 mm chord, satisfying the 15–20% structural rule without choking spanwise flow
- Deployed at **15.5° AoA** — deliberately below the 18° limit to guarantee flow
  attachment in turbulent dirty air and yaw conditions

**Flap** — derived from MSDH (Motor Sport High Downforce):
- Aggressive natural camber scaling applied to aft 30% of flap — simulates a
  Kármán–Trefftz trailing edge (virtual Gurney flap effect)
- Enforces massive Kutta condition angle, ejecting flow violently upward for peak
  suction beneath the rear axis
- Trailing edge spline mathematically smoothed to prevent self-intersection and
  drag-inducing separation
- Thickness held strictly at **12.87%**, complying with the 10–14% rule
- Deployed at **27° relative AoA**


### 2 · Dimensional & AoA Strategy

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Main chord | 220 mm (max) | Maximises low-pressure zone area |
| Flap chord | 120 mm (max) | Maximises suction peak |
| Total span | 1,050 mm (max) | Higher aspect ratio → reduced induced drag |
| Main AoA | 15.5° | Robust attachment, feeds flap cleanly |
| Flap AoA | 27° relative | Maximum suction, aggressive ejector effect |


### 3 · Slot Gap Kinematics

Flap leading edge positioned with **4 mm horizontal overlap** and **8 mm vertical slot
gap** — functioning as a high-pressure nozzle. Injects a high-velocity jet tangentially
into the flap boundary layer from the pressure side, permanently locking flow to the
flap surface and preventing separation at the extreme 27° deployment.


### 4 · Endplate Design & Vortex Management

Three slanted stretched-cylinder slots introduced into the upper-rear quadrant of the
endplate, adjacent to the flap's high-pressure leading zone. Instead of shedding one
massive drag-inducing wingtip vortex, the slots dissolve it into several smaller controlled
threads — recovering straight-line speed while sacrificing zero cornering downforce.


## Key Results

| Metric | Value |
|--------|-------|
| Lift Coefficient (Cl) | **3.8** |
| Validation | Full CFD analysis (ANSYS Fluent) |
| Competition Result | **Top 10 National Finalist, BITS Pilani APOGEE 2026** |


## Tools & Concepts

`XFOIL` `ANSYS Fluent` `SolidWorks` `Multi-Element Aerodynamics`
`Boundary Layer Control` `Slot Gap Flow Control` `Vortex Management`
`Kármán–Trefftz Trailing Edge` `Induced Drag Reduction` `Kutta Condition`
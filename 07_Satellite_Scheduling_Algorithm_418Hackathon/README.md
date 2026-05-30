# 07 · Satellite Imaging Scheduler — LEO Optimisation

**`Python` `Astrodynamics` `TSP Optimisation` `Scheduling Algorithms` `Orbital Mechanics`**

---

## Overview

Satellite imaging scheduling algorithm developed for LEO constellation management
during the **418 Hackathon** (Track: Lost-In-Space) as part of team **Binary Brains**.

**Objective:** Maximise imaging coverage of a ground Area of Interest (AOI) under strict
physical constraints — off-nadir view limits, smear rate limits, slew stabilisation
requirements — with minimal attitude control effort.

**Final Score: 1.2756**

---

## Key Technical Contributions

### Bug Discovery — First Team to Identify Case 3 Failure

Within 4 hours, identified and formally reported a fundamental simulator bug in Case 3:
the evaluator was enforcing the 60° limit on **zenith angle** rather than **off-nadir angle**.
At ~500 km altitude with ~1,009 km cross-track offset, Earth curvature causes the zenith
to systematically exceed 65°, making all Case 3 configurations mathematically
unscorable. Confirmed by locally enforcing the correct formula — Case 3 worked perfectly.

### Algorithm Pipeline

```
AOI Grid (Serpentine) → Feasibility Filter (Off-Nadir ≤ 59.2°)
→ 2-Opt TSP (Min Slew Path) → SLERP + Hold Pad (0.3s Stabilisation)
→ Safe Imaging (Valid Frames)
```

### Constraint Handling

- **Smear Limit (<0.05°/s):** Enforced strict 0.3s static Hold-Pad stabilisation before
  every frame, guaranteeing 0.00°/s body rate — avoiding the greedy nadir-tracking trap
- **Off-Nadir Limit (≤60°):** Mathematically locked footprint boundary to 59.2° tracking
  angle to prevent physics-controller overshoot from breaching the hard limit
- **Case 3 Partial Coverage:** Eastern 45% of AOI physically unreachable under
  constraints — dynamically adapted to a tighter 5×4 grid covering the reachable
  Western 55%

---

## Results

| Metric | Case 1 | Case 2 | Case 3 |
|--------|--------|--------|--------|
| S_orbit | 1.2354 | 1.2568 | 1.3172 |
| Coverage | 0.9997 | 0.9937 | 1.0000 |
| Effort | 0.6104 | 0.7065 | 0.8890 |
| Time | 0.8316 | 0.8810 | 0.9496 |
| Smear | 1.0000 | 1.0000 | 1.0000 |
| Frames | 35/35 | 28/28 | 13/13 |

**Final Score: 1.2756**

---

## Limitations & Future Work

**Current bottleneck:** 2-Opt TSP solver speed limits attitude sampling beyond 5 Hz
and constrains grid resolution expansion within the 120-second timeout.

**Planned improvement:** Replace greedy local TSP with an offline Mixed-Integer Linear
Program (MILP) for globally optimal minimum-slew path calculation.

---

## Tools & Concepts

`Python` `2-Opt TSP` `SLERP Interpolation` `Astrodynamics` `Orbital Mechanics`
`Off-Nadir Constraint Modelling` `LEO Satellite Scheduling` `Attitude Control`
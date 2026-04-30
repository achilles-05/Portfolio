# MAHINDRA UNIVERSITY
#TEAM : BINARY BRAINS
#Pothuraju Satya Keerthi and Shreeji Kumawat


import math
from datetime import datetime, timedelta, timezone
from typing import List

import numpy as np
from sgp4.api import Satrec, jday

WGS84_A  = 6378137.0
WGS84_F  = 1.0 / 298.257223563
WGS84_E2 = WGS84_F * (2.0 - WGS84_F)

def _parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)

def _gmst(dt: datetime) -> float:
    jd, fr = jday(dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second + dt.microsecond * 1e-6)
    T = ((jd - 2451545.0) + fr) / 36525.0
    g = (67310.54841 + (876600.0 * 3600.0 + 8640184.812866) * T + 0.093104 * T * T - 6.2e-6 * T * T * T) % 86400.0
    if g < 0: g += 86400.0
    return math.radians(g / 240.0)

def _llh_to_ecef(lat_deg: float, lon_deg: float, alt_m: float = 0.0) -> np.ndarray:
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    sl, cl = math.sin(lat), math.cos(lat)
    N = WGS84_A / math.sqrt(1.0 - WGS84_E2 * sl * sl)
    return np.array([(N + alt_m) * cl * math.cos(lon), (N + alt_m) * cl * math.sin(lon), (N * (1.0 - WGS84_E2) + alt_m) * sl])

def _ecef_to_eci(r_ecef: np.ndarray, gmst: float) -> np.ndarray:
    c, s = math.cos(gmst), math.sin(gmst)
    return np.array([c * r_ecef[0] - s * r_ecef[1], s * r_ecef[0] + c * r_ecef[1], r_ecef[2]])

def _mat_to_quat_xyzw(m: np.ndarray) -> List[float]:
    tr = m[0, 0] + m[1, 1] + m[2, 2]
    if tr > 0: S = math.sqrt(tr + 1.0) * 2; qw = 0.25 * S; qx = (m[2, 1] - m[1, 2]) / S; qy = (m[0, 2] - m[2, 0]) / S; qz = (m[1, 0] - m[0, 1]) / S
    elif (m[0, 0] > m[1, 1]) and (m[0, 0] > m[2, 2]): S = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2; qw = (m[2, 1] - m[1, 2]) / S; qx = 0.25 * S; qy = (m[0, 1] + m[1, 0]) / S; qz = (m[0, 2] + m[2, 0]) / S
    elif m[1, 1] > m[2, 2]: S = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2; qw = (m[0, 2] - m[2, 0]) / S; qx = (m[0, 1] + m[1, 0]) / S; qy = 0.25 * S; qz = (m[1, 2] + m[2, 1]) / S
    else: S = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2; qw = (m[1, 0] - m[0, 1]) / S; qx = (m[0, 2] + m[2, 0]) / S; qy = (m[1, 2] + m[2, 1]) / S; qz = 0.25 * S
    q = np.array([qx, qy, qz, qw])
    return (q / np.linalg.norm(q)).tolist()

def _stare_quat_BN(r_sat: np.ndarray, r_tgt: np.ndarray, v_sat: np.ndarray) -> List[float]:
    z = r_tgt - r_sat; nz = np.linalg.norm(z)
    z = z / nz if nz > 1e-12 else np.array([0.0, 0.0, 1.0])
    vn = np.linalg.norm(v_sat)
    vh = v_sat / vn if vn > 1e-12 else np.array([1.0, 0.0, 0.0])
    x = vh - np.dot(vh, z) * z; nx = np.linalg.norm(x)
    if nx < 1e-6: arb = np.array([1.0, 0.0, 0.0]); x = arb - np.dot(arb, z) * z; nx = np.linalg.norm(x)
    x /= nx; y = np.cross(z, x)
    return _mat_to_quat_xyzw(np.column_stack([x, y, z]))

def _sat_state(sat: Satrec, when: datetime):
    jd, fr = jday(when.year, when.month, when.day, when.hour, when.minute, when.second + when.microsecond * 1e-6)
    err, r_km, v_kmps = sat.sgp4(jd, fr)
    if err != 0: return None, None
    return (np.asarray(r_km, float) * 1000.0, np.asarray(v_kmps, float) * 1000.0)

def _off_nadir(r_sat: np.ndarray, r_tgt_eci: np.ndarray) -> float:
    los = r_tgt_eci - r_sat; nl = np.linalg.norm(los)
    if nl < 1e-12: return 0.0
    los /= nl; nadir = -r_sat / np.linalg.norm(r_sat)
    return math.degrees(math.acos(max(-1.0, min(1.0, float(np.dot(los, nadir))))))

def plan_imaging(tle_line1, tle_line2, aoi_polygon_llh, pass_start_utc, pass_end_utc, sc_params):
    INTEG = float(sc_params["integration_s"])
    OFF_NADIR_MAX = float(sc_params["off_nadir_max_deg"])
    HOLD_PAD = 0.3
    SLEW_TIME = 0.8
    MIN_GAP = INTEG + 2.0 * HOLD_PAD + SLEW_TIME

    SCAN_THRESH = OFF_NADIR_MAX - 0.3
    COMMIT_THRESH = OFF_NADIR_MAX - 0.8

    t0 = _parse_iso(pass_start_utc)
    t1 = _parse_iso(pass_end_utc)
    T = (t1 - t0).total_seconds()
    sat = Satrec.twoline2rv(tle_line1, tle_line2)

    lats_poly = [p[0] for p in aoi_polygon_llh]
    lons_poly = [p[1] for p in aoi_polygon_llh]
    min_lat, max_lat = min(lats_poly), max(lats_poly)
    min_lon, max_lon = min(lons_poly), max(lons_poly)
    ctr_lat = (min_lat + max_lat) / 2.0; ctr_lon = (min_lon + max_lon) / 2.0

    ctr_ecef = _llh_to_ecef(ctr_lat, ctr_lon)
    min_ctr_off = 90.0
    for dt_s in range(0, int(T) + 1, 5):
        when = t0 + timedelta(seconds=dt_s)
        r_eci, _ = _sat_state(sat, when)
        if r_eci is None: continue
        off = _off_nadir(r_eci, _ecef_to_eci(ctr_ecef, _gmst(when)))
        if off < min_ctr_off: min_ctr_off = off

    t_mid = t0 + timedelta(seconds=T/2)
    r_mid, _ = _sat_state(sat, t_mid)
    r_mid2, _ = _sat_state(sat, t_mid + timedelta(seconds=1))
    flying_south = r_mid2[2] < r_mid[2]

    grid_points = []
    if min_ctr_off > 50.0:
        GRID_ROWS, GRID_COLS = 5, 4  
        lon_east_safe = min_lon + 0.95 * (max_lon - min_lon)
        if flying_south:
            lats_arr = np.linspace(max_lat, min_lat, GRID_ROWS)
        else:
            lats_arr = np.linspace(min_lat, max_lat, GRID_ROWS)
        lons_arr = np.linspace(min_lon, lon_east_safe, GRID_COLS)
    elif min_ctr_off > 15.0:
        GRID_ROWS, GRID_COLS = 6, 5  
        if flying_south:
            lats_arr = np.linspace(max_lat, min_lat, GRID_ROWS)
        else:
            lats_arr = np.linspace(min_lat, max_lat, GRID_ROWS)
        lons_arr = np.linspace(min_lon, max_lon, GRID_COLS)
    else:
        GRID_ROWS, GRID_COLS = 6, 6  
        if flying_south:
            lats_arr = np.linspace(max_lat, min_lat, GRID_ROWS)
        else:
            lats_arr = np.linspace(min_lat, max_lat, GRID_ROWS)
        lons_arr = np.linspace(min_lon, max_lon, GRID_COLS)

    for i, lat in enumerate(lats_arr):
        row_lons = lons_arr if i % 2 == 0 else lons_arr[::-1]
        for lon in row_lons:
            grid_points.append({"lat": lat, "lon": lon, "r_ecef": _llh_to_ecef(lat, lon)})

    reachable = []
    for pt in grid_points:
        best_off = 90.0; win_s = None; win_e = None
        for dt_half in range(0, int(T * 2.0) + 1):
            dt_s = dt_half / 2.0
            when = t0 + timedelta(seconds=dt_s)
            r_eci, _ = _sat_state(sat, when)
            if r_eci is None: continue
            off = _off_nadir(r_eci, _ecef_to_eci(pt["r_ecef"], _gmst(when)))
            if off < best_off: best_off = off
            if off < SCAN_THRESH:
                if win_s is None: win_s = float(dt_s)
                win_e = float(dt_s)

        if win_s is not None and best_off < COMMIT_THRESH:
            pt["win_s"] = win_s; pt["win_e"] = win_e; pt["min_off"] = best_off
            reachable.append(pt)

    if not reachable:
        return {"objective": "fallback", "attitude": [{"t": 0.0, "q_BN": [0,0,0,1]}, {"t": T, "q_BN": [0,0,0,1]}], "shutter": []}

  
    for pt in reachable:
        opt_t = (pt["win_s"] + pt["win_e"]) / 2.0
        when = t0 + timedelta(seconds=opt_t)
        r_eci, v_eci = _sat_state(sat, when)
        pt["opt_t"] = opt_t
        if r_eci is not None:
            pt["q_opt"] = _stare_quat_BN(r_eci, _ecef_to_eci(pt["r_ecef"], _gmst(when)), v_eci)
        else:
            pt["q_opt"] = [0, 0, 0, 1]

    reachable.sort(key=lambda p: p["win_s"])
    
   
    N_pts = len(reachable)
    if N_pts > 0:
        q_arr = np.array([pt["q_opt"] for pt in reachable])
        dist_matrix = 1.0 - np.abs(q_arr @ q_arr.T)
        
        unvisited = set(range(1, N_pts))
        tour = [0]
        while unvisited:
            last = tour[-1]
            next_idx = min(unvisited, key=lambda j: dist_matrix[last, j])
            tour.append(next_idx)
            unvisited.remove(next_idx)

      
        improved = True
        while improved:
            improved = False
            for i in range(1, N_pts - 1):
                for k in range(i + 1, N_pts):
                    cur_cost = dist_matrix[tour[i-1], tour[i]]
                    if k + 1 < N_pts:
                        cur_cost += dist_matrix[tour[k], tour[k+1]]
                        new_cost = dist_matrix[tour[i-1], tour[k]] + dist_matrix[tour[i], tour[k+1]]
                    else:
                        new_cost = dist_matrix[tour[i-1], tour[k]]
                    
                    if new_cost < cur_cost - 1e-9:
                        tour[i:k+1] = reversed(tour[i:k+1])
                        improved = True
                        break
                if improved:
                    break
                    
        tsp_schedule = [reachable[i] for i in tour]
    else:
        tsp_schedule = []

    final_schedule = []
    if len(tsp_schedule) > 0:
        t_first = min(p["win_s"] for p in reachable)
        t_last  = max(p["win_e"] for p in reachable) - INTEG
        n_pts = len(reachable)
        if n_pts > 1:
            stretch_times = np.linspace(t_first, t_last, n_pts)
        else:
            stretch_times = [t_first]
            
        last_end = -999.0
        for i, pt in enumerate(tsp_schedule):
            t_cand = max(stretch_times[i], last_end + MIN_GAP)
            t_cand = max(t_cand, pt["win_s"] + 0.3)
            
            if t_cand > pt["win_e"] - 0.3:
                continue
            if t_cand + INTEG > T - 0.5:
                continue
                
            final_schedule.append((t_cand, pt))
            last_end = t_cand
            
    final_schedule.sort(key=lambda x: x[0])

    override_pts = []
    shutter_times = []
    
   
    scheduled_frames = []
    for ts, pt in final_schedule:
        when = t0 + timedelta(seconds=ts)
        r_eci, v_eci = _sat_state(sat, when)
        if r_eci is not None:
            pt["q_sched"] = _stare_quat_BN(r_eci, _ecef_to_eci(pt["r_ecef"], _gmst(when)), v_eci)
            scheduled_frames.append((ts, pt))
            
    def _slerp(q1, q2, t):
        """Spherical linear interpolation, t in [0,1]."""
        q1, q2 = np.array(q1), np.array(q2)
        dot = np.clip(np.dot(q1, q2), -1.0, 1.0)
        if dot < 0:
            q2 = -q2; dot = -dot
        if dot > 0.9995:
            res = q1 + t*(q2-q1)
            return (res / np.linalg.norm(res)).tolist()
        theta_0 = math.acos(dot)
        theta = theta_0 * t
        sin_t  = math.sin(theta)
        sin_t0 = math.sin(theta_0)
        s1 = math.cos(theta) - dot * sin_t / sin_t0
        s2 = sin_t / sin_t0
        return (s1*q1 + s2*q2).tolist()

    for i in range(len(scheduled_frames)):
        ts, pt = scheduled_frames[i]
        q = pt["q_sched"]
        
        th_s = max(0.0, ts - HOLD_PAD)
        th_e = min(T, ts + INTEG + HOLD_PAD)

        override_pts.append((th_s, q))
        override_pts.append((ts, q))
        override_pts.append((ts + INTEG, q))
        override_pts.append((th_e, q))
        shutter_times.append(ts)
        
        if i + 1 < len(scheduled_frames):
            next_ts, next_pt = scheduled_frames[i+1]
            q_next = next_pt["q_sched"]
            
            slew_start = th_e
            slew_end = next_ts - HOLD_PAD
            
            if slew_end > slew_start + 0.1:
                
                N_slerps = 6
                dt_step = (slew_end - slew_start) / (N_slerps + 1)
                for step in range(1, N_slerps + 1):
                    t_mid = slew_start + step * dt_step
                    u = step / (N_slerps + 1.0)
                    q_mid = _slerp(q, q_next, u)
                    override_pts.append((float(t_mid), q_mid))

    cleaned = []
    for t, q in sorted(override_pts, key=lambda x: x[0]):
        if cleaned and t - cleaned[-1][0] < 0.025: continue
        cleaned.append((t, q))

    if cleaned[0][0] > 1e-9:
        if cleaned[0][0] < 0.025:
            cleaned[0] = (0.0, cleaned[0][1])
        else:
            when0 = t0
            r_eci0, v_eci0 = _sat_state(sat, when0)
            q0 = _stare_quat_BN(r_eci0, _ecef_to_eci(final_schedule[0][1]["r_ecef"], _gmst(when0)), v_eci0)
            cleaned.insert(0, (0.0, q0))
        
    if cleaned[-1][0] < T - 1e-9:
        if T - cleaned[-1][0] < 0.025:
            cleaned[-1] = (T, cleaned[-1][1])
        else:
            whenT = t0 + timedelta(seconds=T)
            r_eciT, v_eciT = _sat_state(sat, whenT)
            qT = _stare_quat_BN(r_eciT, _ecef_to_eci(final_schedule[-1][1]["r_ecef"], _gmst(whenT)), v_eciT)
            cleaned.append((T, qT))

    
    final_attitudes = []
    for i, (t, q) in enumerate(cleaned):
        if i == 0:
            final_attitudes.append((t, list(q)))
            continue
        
        t_prev, q_prev = final_attitudes[-1]
        dt = t - t_prev
        if dt > 0.8:
            n_extra = int(math.ceil(dt / 0.8)) - 1
            for step in range(1, n_extra + 1):
                u = step / float(n_extra + 1)
                q_mid = _slerp(q_prev, q, u)
                t_mid = t_prev + step * (dt / float(n_extra + 1))
                final_attitudes.append((t_mid, q_mid))
        final_attitudes.append((t, list(q)))

    return {
        "objective": "Maximum T_cand stretch for ultra-low dH optimal performance array",
        "attitude": [{"t": round(t, 4), "q_BN": q} for t, q in final_attitudes],
        "shutter": [{"t_start": round(ts, 4), "duration": INTEG} for ts in shutter_times]
    }
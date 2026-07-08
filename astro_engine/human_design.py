"""Human Design bodygraph calculator using Swiss Ephemeris (tropical)."""
import swisseph as swe
from datetime import datetime
import pytz

# ── Gate wheel ──────────────────────────────────────────────────────────────
# 64 I Ching hexagrams in order around the HD wheel, starting at 0° Aquarius
# (= 300° tropical longitude), going in the direction of increasing longitude.
GATE_SEQ = [
    41, 19, 13, 49, 30, 55, 37, 63, 22, 36, 25, 17, 21, 51, 42,  3,
    27, 24,  2, 23,  8, 20, 16, 35, 45, 12, 15, 52, 39, 53, 62, 56,
    31, 33,  7,  4, 29, 59, 40, 64, 47,  6, 46, 18, 48, 57, 32, 50,
    28, 44,  1, 43, 14, 34,  9,  5, 26, 11, 10, 58, 38, 54, 61, 60,
]
GATE_WIDTH = 360 / 64       # 5.625°
LINE_WIDTH = GATE_WIDTH / 6  # 0.9375°

# ── Gate → Center ────────────────────────────────────────────────────────────
GATE_CENTER = {
    # HEAD
    64: 'HEAD', 61: 'HEAD', 63: 'HEAD',
    # AJNA
    47: 'AJNA', 24: 'AJNA',  4: 'AJNA', 17: 'AJNA', 43: 'AJNA', 11: 'AJNA',
    # THROAT
    62: 'THROAT', 23: 'THROAT', 56: 'THROAT', 35: 'THROAT', 12: 'THROAT',
    45: 'THROAT', 33: 'THROAT',  8: 'THROAT', 31: 'THROAT', 20: 'THROAT', 16: 'THROAT',
    # G / IDENTITY
    13: 'G',  7: 'G',  1: 'G', 10: 'G', 25: 'G', 46: 'G', 15: 'G',  2: 'G',
    # HEART / EGO
    21: 'HEART', 51: 'HEART', 26: 'HEART', 40: 'HEART',
    # SOLAR PLEXUS / EMOTIONAL
    36: 'SP', 22: 'SP', 49: 'SP', 55: 'SP', 30: 'SP', 37: 'SP',  6: 'SP',
    # SACRAL
    34: 'SACRAL',  5: 'SACRAL', 14: 'SACRAL', 29: 'SACRAL',  9: 'SACRAL',
     3: 'SACRAL', 42: 'SACRAL', 27: 'SACRAL', 59: 'SACRAL',
    # SPLEEN
    48: 'SPLEEN', 57: 'SPLEEN', 44: 'SPLEEN', 32: 'SPLEEN',
    28: 'SPLEEN', 18: 'SPLEEN', 50: 'SPLEEN',
    # ROOT
    53: 'ROOT', 60: 'ROOT', 52: 'ROOT', 19: 'ROOT', 39: 'ROOT',
    41: 'ROOT', 38: 'ROOT', 54: 'ROOT', 58: 'ROOT',
}

# ── 36 Channels (sorted gate pairs) ─────────────────────────────────────────
CHANNELS = {
    (1, 8),   (2, 14),  (3, 60),  (4, 63),  (5, 15),
    (6, 59),  (7, 31),  (9, 52),  (10, 20), (10, 34),
    (10, 57), (11, 56), (12, 22), (13, 33), (16, 48),
    (17, 62), (18, 58), (19, 49), (20, 34), (20, 57),
    (21, 45), (23, 43), (24, 61), (25, 51), (26, 44),
    (27, 50), (28, 38), (29, 46), (30, 41), (32, 54),
    (34, 57), (35, 36), (37, 40), (39, 55), (42, 53),
    (47, 64),
}

# ── Swiss Ephemeris planet IDs ────────────────────────────────────────────────
SE_PLANETS = [
    (swe.SUN,     'Sun'),
    (swe.MOON,    'Moon'),
    (swe.MERCURY, 'Mercury'),
    (swe.VENUS,   'Venus'),
    (swe.MARS,    'Mars'),
    (swe.JUPITER, 'Jupiter'),
    (swe.SATURN,  'Saturn'),
    (swe.URANUS,  'Uranus'),
    (swe.NEPTUNE, 'Neptune'),
    (swe.PLUTO,   'Pluto'),
    (swe.TRUE_NODE, 'North Node'),
]


def _longitude_to_gate_line(lon: float):
    """Convert a tropical longitude (0–360) to (gate, line)."""
    shifted = (lon - 300) % 360
    idx = int(shifted / GATE_WIDTH)
    gate = GATE_SEQ[idx]
    line = int((shifted % GATE_WIDTH) / LINE_WIDTH) + 1
    return gate, line


def _earth_longitude(sun_lon: float) -> float:
    """Earth is always exactly opposite the Sun."""
    return (sun_lon + 180) % 360


def _calc_jd(dt_utc: datetime) -> float:
    return swe.julday(dt_utc.year, dt_utc.month, dt_utc.day,
                      dt_utc.hour + dt_utc.minute / 60 + dt_utc.second / 3600)


def _planet_longitudes(jd: float) -> dict:
    """Return {planet_name: tropical_longitude} for all HD planets."""
    result = {}
    for pid, name in SE_PLANETS:
        lon, *_ = swe.calc_ut(jd, pid, swe.FLG_SWIEPH | swe.FLG_SPEED)
        result[name] = lon[0]
    # Earth = opposite Sun
    result['Earth'] = _earth_longitude(result['Sun'])
    # South Node = opposite North Node
    result['South Node'] = (result['North Node'] + 180) % 360
    return result


def _get_design_jd(birth_jd: float) -> float:
    """Return JD when Sun was ~88.736° before birth Sun position."""
    sun_birth, *_ = swe.calc_ut(birth_jd, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SPEED)
    target = (sun_birth[0] - 88.736) % 360

    # Binary search: Sun moves ~1°/day, so ≈ 89 days before birth
    lo = birth_jd - 95
    hi = birth_jd - 83

    for _ in range(30):
        mid = (lo + hi) / 2
        sun_mid, *_ = swe.calc_ut(mid, swe.SUN, swe.FLG_SWIEPH | swe.FLG_SPEED)
        diff = (sun_mid[0] - target + 360) % 360
        if diff < 0.001:
            return mid
        if diff > 180:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def _defined_centers(activated: set) -> set:
    """Return set of center names that are defined (complete channel present)."""
    defined = set()
    for (g1, g2) in CHANNELS:
        if g1 in activated and g2 in activated:
            defined.add(GATE_CENTER[g1])
            defined.add(GATE_CENTER[g2])
    return defined


def _motor_to_throat(defined: set, activated: set) -> bool:
    """True if any Motor center is connected to Throat through defined channels."""
    motors = {'HEART', 'SP', 'SACRAL', 'ROOT'}
    if 'THROAT' not in defined:
        return False

    # Build adjacency among defined centers via activated channels
    adj = {c: set() for c in defined}
    for (g1, g2) in CHANNELS:
        if g1 in activated and g2 in activated:
            c1, c2 = GATE_CENTER[g1], GATE_CENTER[g2]
            if c1 in defined and c2 in defined:
                adj[c1].add(c2)
                adj[c2].add(c1)

    # BFS from each motor
    for motor in motors & defined:
        visited, queue = {motor}, [motor]
        while queue:
            cur = queue.pop(0)
            if cur == 'THROAT':
                return True
            for nb in adj.get(cur, set()) - visited:
                visited.add(nb)
                queue.append(nb)
    return False


def _hd_type(defined: set, activated: set) -> tuple[str, str]:
    """Return (hd_type, strategy)."""
    if not defined:
        return 'Reflector', 'Wait a lunar cycle'

    sacral = 'SACRAL' in defined
    mtt = _motor_to_throat(defined, activated)

    if sacral and mtt:
        return 'Manifesting Generator', 'Respond then inform'
    elif sacral:
        return 'Generator', 'Wait to respond'
    elif mtt:
        return 'Manifestor', 'Inform before acting'
    else:
        return 'Projector', 'Wait for invitation'


def _authority(defined: set, sacral: bool) -> str:
    if 'SP' in defined:
        return 'Emotional — wait through your wave'
    if sacral:
        return 'Sacral — trust your gut response'
    if 'SPLEEN' in defined:
        return 'Splenic — trust your instinct in the moment'
    if 'HEART' in defined and 'G' not in defined:
        return 'Ego-Manifested — commit from your will'
    if 'G' in defined and 'THROAT' not in defined:
        return 'Self-Projected — speak to hear your truth'
    if 'AJNA' in defined or 'HEAD' in defined:
        return 'Mental — seek trusted others to reflect'
    return 'No Inner Authority — use environment'


def calculate(dob: str, tob: str, lat: float, lon: float, tz_str: str) -> dict:
    """
    Full HD chart calculation.
    dob: 'YYYY-MM-DD', tob: 'HH:MM', lat/lon: float, tz_str: 'Asia/Kolkata'
    Returns dict with type, strategy, authority, profile, gates, defined_centers.
    """
    swe.set_ephe_path('/usr/share/ephe')

    # Local birth time → UTC
    tz = pytz.timezone(tz_str)
    dt_local = datetime.strptime(f"{dob} {tob}", "%Y-%m-%d %H:%M")
    dt_utc = tz.localize(dt_local).astimezone(pytz.utc).replace(tzinfo=None)

    birth_jd = _calc_jd(dt_utc)
    design_jd = _get_design_jd(birth_jd)

    # Planetary positions (tropical)
    p_lons = _planet_longitudes(birth_jd)   # Personality (black / conscious)
    d_lons = _planet_longitudes(design_jd)  # Design (red / unconscious)

    # Convert to gates
    p_gates = {}
    for name, lon in p_lons.items():
        g, l = _longitude_to_gate_line(lon)
        p_gates[name] = (g, l)

    d_gates = {}
    for name, lon in d_lons.items():
        g, l = _longitude_to_gate_line(lon)
        d_gates[name] = (g, l)

    # Activated gates (set of gate numbers only)
    activated = set(g for g, _ in p_gates.values()) | set(g for g, _ in d_gates.values())

    defined = _defined_centers(activated)
    hd_type, strategy = _hd_type(defined, activated)
    authority = _authority(defined, 'SACRAL' in defined)

    # Profile = Personality Sun line / Design Sun line
    p_sun_line = p_gates['Sun'][1]
    d_sun_line = d_gates['Sun'][1]
    profile = f"{p_sun_line}/{d_sun_line}"

    # Incarnation cross = 4 gates (P-Sun, P-Earth, D-Sun, D-Earth)
    cross_gates = (
        p_gates['Sun'][0], p_gates['Earth'][0],
        d_gates['Sun'][0], d_gates['Earth'][0],
    )

    return {
        'type': hd_type,
        'strategy': strategy,
        'authority': authority,
        'profile': profile,
        'cross_gates': cross_gates,
        'defined_centers': sorted(defined),
        'p_gates': p_gates,
        'd_gates': d_gates,
        'activated_gates': sorted(activated),
    }

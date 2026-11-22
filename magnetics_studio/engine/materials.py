import bisect
import math

MU0 = 4 * math.pi * 1e-7


def validate_material(m):
    if not isinstance(m.get('id'), str) or not m['id']:
        raise ValueError('Every material requires a nonempty string id')
    mu = m.get('mu_r', 1)
    if isinstance(mu,bool) or not isinstance(mu,(float,int)) or not math.isfinite(mu) or mu < 1 or mu > 1e6:
        raise ValueError('Relative permeability must be between 1 and 1e6')
    bh = m.get('bh', [])
    if bh:
        if len(bh) < 2 or len(bh) > 2000 or list(bh[0]) != [0, 0]:
            raise ValueError('B-H data must start at [0 T, 0 A/m] and contain 2–2000 rows')
        for a, b in zip(bh, bh[1:]):
            if len(a) != 2 or len(b) != 2 or not all(isinstance(v,(float,int)) and not isinstance(v,bool) and math.isfinite(v) for v in a + b):
                raise ValueError('Invalid B-H row; use [B in T, H in A/m]')
            if not (b[0] > a[0] and b[1] > a[1]):
                raise ValueError('B and H must both increase strictly')
            if (b[1]-a[1])/(b[0]-a[0]) > 1.000001/MU0:
                raise ValueError('B-H differential permeability must be at least mu0')


def h_and_energy(material, b):
    """Reversible single-valued H(B) and integral H dB. No hysteresis.

    Beyond the final tabulated point, use vacuum differential permeability.
    """
    curve = material.get('bh')
    if not curve:
        nu = 1 / (MU0 * material.get('mu_r', 1.))
        return nu * b, .5 * nu * b * b
    energy = 0.
    for (b0, h0), (b1, h1) in zip(curve, curve[1:]):
        end = min(b, b1)
        slope = (h1 - h0) / (b1 - b0)
        delta = end - b0
        if delta >= 0:
            energy += h0 * delta + .5 * slope * delta * delta
        if b <= b1:
            return h0 + slope * delta, energy
    b0, h0 = curve[-1]
    delta = b - b0
    return h0 + delta / MU0, energy + h0 * delta + .5 * delta * delta / MU0


def reluctivity(material, b):
    if b < 1e-15:
        curve = material.get('bh')
        return curve[1][1] / curve[1][0] if curve else 1/(MU0*material.get('mu_r', 1.))
    return h_and_energy(material, b)[0] / b

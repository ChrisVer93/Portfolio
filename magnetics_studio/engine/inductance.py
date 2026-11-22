"""Sweep postprocessing: explicit static chord, interval slope and AC series equivalent."""
from .connections import series_key  #: Use the same canonical section membership as static matrix extraction.
import math  #: Convert frequency to angular frequency and reject nonfinite study inputs.


def sweep_sections(project, winding_id):  #: Resolve one existing electrical winding without merging a circuit container.
    selected = next((w for w in project['windings'] if w['id'] == winding_id), None)  #: Preserve the user's selected physical/electrical source identity.
    if selected is None:  #: A stale source identifier cannot define a measurement port.
        raise ValueError('Choose a winding to sweep')  #: Retain the existing actionable validation message.
    return [i for i, w in enumerate(project['windings']) if series_key(w) == series_key(selected)]  #: Sweep exactly the selected canonical electrical port, including migrated split-primary sections.


def sweep_currents(values):  #: Validate the complete bounded study before any field solve starts.
    if not isinstance(values, list) or not 2 <= len(values) <= 12:  #: Keep the existing complete-solve capacity limit.
        raise ValueError('Use 2–12 sweep currents')  #: Explain the accepted study size.
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) for v in values):  #: A boolean, NaN or infinity is not a physical current.
        raise ValueError('Sweep currents must be finite numbers')  #: Reject malformed later points before computing earlier ones.
    if len(set(values)) != len(values):  #: Repeated currents cannot define a unique flux/current interval.
        raise ValueError('Sweep currents must be distinct')  #: Avoid division by zero or fabricated differential values.
    return values  #: Preserve the user's input order in the numerical table.


def static_inductance(study, indices, zero_linkage):  #: Add explicitly defined inductance data without changing solved fields.
    for row in study['rows']:  #: Use actual accepted field linkages at every requested current.
        row['selected_linkage_Wb_turn'] = sum(row['linkages_Wb_turn'][i] for i in indices)  #: Sum flux linkages of the same-current series sections exactly once.
        row['chord_inductance_H'] = (row['selected_linkage_Wb_turn'] - zero_linkage) / row['current_A'] if row['current_A'] else None  #: Subtract fixed-other-winding bias flux; leave the zero-current quotient undefined.
    ordered = sorted(study['rows'], key=lambda r: r['current_A'])  #: Form physical current intervals independently of input order.
    study['inductance_intervals'] = [dict(current_low_A=a['current_A'], current_high_A=b['current_A'], current_mid_A=(a['current_A']+b['current_A'])/2, slope_inductance_H=(b['selected_linkage_Wb_turn']-a['selected_linkage_Wb_turn'])/(b['current_A']-a['current_A'])) for a, b in zip(ordered, ordered[1:])]  #: Record the actual finite-interval flux slope, not an uncomputed small-signal tangent.
    study['zero_current_linkage_Wb_turn'] = zero_linkage  #: Keep the baseline used for every chord value reproducible.
    study['selected_section_indices'] = indices  #: Identify which solved source linkages form the measured electrical port.
    study['inductance_note'] = 'Chord L = [lambda(I) - lambda(0)]/I with all other winding currents fixed; undefined at I=0. Interval slope = delta lambda/delta I at the interval midpoint; it is not a qualified small-signal tangent or a leakage/magnetising equivalent-circuit extraction. Refine current spacing and the mesh independently.'  #: Keep bias, zero-current, nonlinear and transformer interpretation limits with exported results.
    return study  #: Preserve all earlier energy, peak-field and full-linkage sweep outputs.


def ac_series_equivalent(port, frequency):  #: Derive a clearly labelled series equivalent from the existing operating-point port ratio.
    result = dict(port)  #: Preserve the original actual complex current, voltage, impedance and identity.
    z = result.get('impedance_ohm')  #: A zero-current source has no defined V/I ratio.
    result['series_resistance_ohm'] = z[0] if z is not None else None  #: Retain the signed real component without claiming an isolated self resistance.
    result['series_equivalent_inductance_H'] = z[1] / (2*math.pi*frequency) if z is not None else None  #: Convert signed reactance using Ls=Im(V/I)/omega, never abs(Z)/omega.
    return result  #: Keep undefined passive-port ratios null rather than plotting invented zero inductance.

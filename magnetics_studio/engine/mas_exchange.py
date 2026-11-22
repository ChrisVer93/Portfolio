"""P002A: checked MAS coil/signal projections with a lossless Studio recipe.

This is a versioned exchange envelope, not a complete MAS component or CAD.
No native OpenMagnetics package or schema validator is needed at runtime.
"""
import copy  #: Detach returned recipes and projections from caller-owned dictionaries.
import hashlib  #: Identify the exact finite source recipe for stale-packet detection.
import json  #: Canonicalise JSON without accepting NaN or infinity.
import math  #: Evaluate the declared peak cosine and SI wire cross-sections.
from .builder import build, conductor  #: Reuse real dimensional builders and wire-fit validation.
from .workflow import expand, upgrade  #: Preserve the original electrical hierarchy and layer order.
from .project import number  #: Reuse bounded finite scalar validation.

FORMAT = 'magnetics-studio.mas-exchange/1'  #: Keep our envelope distinct from the upstream MAS root format.
MAS_COMMIT = '8fb50c0d2eabd9d2fcb0e2894d2c0f0653dba35f'  #: Pin the actual schema snapshot used by the new QA tests.
PEAS_COMMIT = 'cf0481b9a60928d7504bea7139ecfa074f36c6a3'  #: Pin the external signal-descriptor schema dependency separately.
SIDES = ('primary', 'secondary', 'tertiary', 'quaternary', 'quinary', 'senary', 'septenary', 'octonary', 'nonary', 'denary', 'undenary', 'duodenary')  #: Use the pinned MAS electrical-isolation labels without guessing them from display names.


def canonical(value):  #: Produce stable bytes for comparisons and a content hash.
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')  #: Reject nonfinite JSON and include every retained source field.


def wire_projection(winding, packing):  #: Map supported builder conductor dimensions into MAS SI wire data.
    width, height, area = conductor(winding)  #: Check the original round/litz/rectangular/foil geometry and copper area.
    insulation = number(winding.get('turn_insulation_mm', packing.get('turn_insulation_mm', .1)), 'Wire insulation', 0, 10000)  #: Retain the builder's per-side insulation allowance.
    kind = winding.get('conductor', 'round')  #: Use the builder default rather than inferring a wire type from its name.
    wire = {'type': kind, 'conductingArea': {'nominal': area * 1e-6}}  #: Convert square millimetres to square metres exactly once.
    if kind in ('round', 'litz'):  #: Both kinds have a circular outer envelope in the builder.
        wire['outerDiameter'] = {'nominal': (width + 2 * insulation) * 1e-3}  #: Include both sides of the same insulation allowance used by packing.
        if kind == 'round':  #: A solid round conductor has one conducting diameter.
            wire['conductingDiameter'] = {'nominal': width * 1e-3}  #: Convert the bare conductor diameter to metres.
        else:  #: A litz bundle contains many strands but is still one electrical wire per turn.
            wire['numberConductors'] = winding.get('strands', 1)  #: Match the builder's default strand count without confusing strands with parallel electrical windings.
            wire['strand'] = {'type': 'round', 'conductingDiameter': {'nominal': winding.get('strand_diameter_mm', .1) * 1e-3}}  #: Match the builder's bare strand default without inventing strand insulation or twist pitch.
    else:  #: Rectangular and foil conductors use separate radial and axial dimensions.
        for key, value in [('Width', width), ('Height', height)]:  #: Keep the two axes distinct through SI conversion.
            wire['conducting' + key] = {'nominal': value * 1e-3}  #: Map bare conductor width or height in metres.
            wire['outer' + key] = {'nominal': (value + 2 * insulation) * 1e-3}  #: Map the corresponding insulated envelope dimension.
    return wire  #: Conductivity/material metadata remains in the retained recipe, not an invented MAS material.


def voltage_signal(signal, period):  #: Validate an explicitly supplied one-period voltage waveform.
    if not isinstance(signal, dict) or set(signal) != {'time', 'data'}:  #: Avoid silently dropping extra waveform semantics.
        raise ValueError('Voltage waveform requires only time and data arrays')  #: Name the accepted caller-supplied representation.
    times, values = signal['time'], signal['data']  #: Read seconds and volts independently.
    if not isinstance(times, list) or not isinstance(values, list) or not 2 <= len(times) <= 4097 or len(times) != len(values):  #: Bound allocation and enforce paired samples.
        raise ValueError('Voltage waveform requires 2-4097 paired samples')  #: Reject malformed or oversized waveforms before export.
    for t, value in zip(times, values):  #: Check all supplied data rather than only extrema.
        number(t, 'Waveform time (s)', 0, period)  #: Require sample times inside the declared period.
        number(value, 'Voltage (V)', -1e9, 1e9)  #: Reject booleans, infinities and nonnumeric voltage values.
    if times[0] != 0 or not math.isclose(times[-1], period, rel_tol=1e-12, abs_tol=0) or any(b <= a for a, b in zip(times, times[1:])):  #: Require one complete strictly ordered period.
        raise ValueError('Voltage times must increase from zero to one period')  #: Do not resample or reorder a caller's waveform silently.
    return {'waveform': copy.deepcopy(signal)}  #: Keep the supplied sample values exactly; no voltage or load is solved here.


def export_exchange(specification, options):  #: Produce checked native MAS subdocuments and an explicit Studio continuation recipe.
    if not isinstance(options, dict) or set(options) - {'bobbin_reference', 'isolation_sides', 'frequency_Hz', 'voltage_waveforms', 'include_geometry', 'bobbin_dimensions_m', 'limb_bobbin_dimensions_m', 'native_single_turn_orientation', 'native_bobbin_assembly'}:  #: Keep interpretation-affecting options closed and versioned.
        raise ValueError('Unsupported MAS exchange options')  #: Reject typos rather than ignoring requested behaviour.
    if type(options.get('include_geometry', False)) is not bool:
        raise ValueError('include_geometry must be boolean')
    if 'bobbin_dimensions_m' in options and not options.get('include_geometry'):
        raise ValueError('bobbin_dimensions_m requires include_geometry')
    if 'limb_bobbin_dimensions_m' in options:
        if not options.get('include_geometry') or 'bobbin_dimensions_m' in options:
            raise ValueError('Local bobbin views require include_geometry without bobbin_dimensions_m')
    if 'native_single_turn_orientation' in options:
        if type(options['native_single_turn_orientation']) is not bool or 'limb_bobbin_dimensions_m' not in options:
            raise ValueError('native_single_turn_orientation requires a boolean and local bobbin views')
    if 'native_bobbin_assembly' in options:
        if type(options['native_bobbin_assembly']) is not bool or options.get('native_single_turn_orientation') is not True:
            raise ValueError('native_bobbin_assembly requires a boolean and native_single_turn_orientation')
    build(specification)  #: Validate actual geometry, materials, packing and selected dimensional capability first.
    normal, saved, lookup = expand(upgrade(specification))  #: Resolve all logical windings and ordered physical sections using the shared workflow.
    canonical(saved)  #: Check all retained recipe metadata for finite JSON before returning anything.
    ids = [cid + '__' + wid for cid, wid in lookup]  #: Use stable electrical IDs, never container or winding display names.
    if len(set(ids)) != len(ids):  #: Detect delimiter collisions that would alias otherwise independent winding identities.
        raise ValueError('Composite winding IDs collide')  #: Require unambiguous identities instead of merging sources.
    sides = options.get('isolation_sides')  #: Require an explicit electrical-isolation assignment supplied by the caller.
    if not isinstance(sides, dict) or set(sides) != set(ids) or any(side not in SIDES for side in sides.values()):  #: A label must exist for every winding, with no missing or foreign keys.
        raise ValueError('Assign a supported isolation side explicitly to every winding ID')  #: Do not infer shared ground from repeated names or phase containers.
    bobbin = options.get('bobbin_reference')  #: Keep the external bobbin reference a caller declaration, not a database lookup claim.
    if not isinstance(bobbin, str) or not 1 <= len(bobbin.strip()) <= 200:  #: Require a bounded nonempty MAS bobbin name.
        raise ValueError('Supply an explicit bobbin_reference')  #: Never fabricate a geometrically matched catalogue bobbin.
    functional, currents, links = [], [], []  #: Separate MAS functional data from Studio layer and source bookkeeping.
    frequency = None  #: An instantaneous current value does not define an AC frequency or waveform.
    if saved.get('excitation_mode', 'instantaneous') == 'sinusoidal_snapshot':  #: Only the explicitly declared cosine recipe defines periodic current.
        frequency = number(options.get('frequency_Hz'), 'Explicit frequency (Hz)', 1, 1e9)  #: Never infer an operating point from a nameplate range.
    elif 'frequency_Hz' in options or 'voltage_waveforms' in options:  #: Prevent turning an instantaneous snapshot into an invented time problem.
        raise ValueError('Periodic signals require sinusoidal_snapshot excitation')  #: Ask the caller to declare the source semantics in the recipe first.
    for key, (_, winding) in lookup.items():  #: Preserve stable insertion order for all independent electrical windings.
        name = key[0] + '__' + key[1]  #: Use the same name in MAS functional data, excitations and layer links.
        functional.append({'name': name, 'numberTurns': winding['turns'], 'numberParallels': 1, 'isolationSide': sides[name], 'wire': wire_projection(winding, saved['packing'])})  #: Map one electrical winding without flattening its physical sections or litz strands.
        if frequency is not None:  #: Export samples only when a periodic physical source was explicitly supplied.
            amplitude, phase = winding.get('current_A', 0), math.radians(winding.get('phase_deg', 0))  #: Builder current_A is signed peak amplitude, not RMS, in this mode.
            times = [k / (64 * frequency) for k in range(65)]  #: Include both endpoints of one period with 64 equal intervals.
            data = [amplitude * math.cos(2 * math.pi * frequency * t + phase) for t in times]  #: Preserve current sign and phase without including the viewing snapshot angle twice.
            currents.append({'name': name, 'frequency_Hz': frequency, 'current': {'waveform': {'time': times, 'data': data}}})  #: Only the current signal descriptor is a native MAS/PEAS subdocument.
    for section in normal['sections']:  #: Walk actual expanded physical sections in the user's selected interleaving order.
        links.append({'layer_id': section['layer_id'], 'winding': section['series_group'], 'limb': section['limb'], 'turns': section['turns'], 'fraction_of_winding_turns': section['turns'] / lookup[(section['logical_circuit_id'], section['electrical_winding_id'])][1]['turns']})  #: Retain section identity and turn conservation without claiming MAS geometric layers exist.
    operating = None  #: Current-only data does not satisfy the pinned full operating-point excitation schema.
    if 'voltage_waveforms' in options:  #: Complete the native operating point only with explicit caller-supplied winding voltages.
        voltages = options['voltage_waveforms']  #: Read an independent voltage signal for each actual winding.
        if not isinstance(voltages, dict) or set(voltages) != set(ids):  #: Prevent an excitation index shift or a fictitious zero-voltage winding.
            raise ValueError('Supply voltage waveforms for every winding ID')  #: Missing voltages remain missing instead of being invented.
        excitations = [{'name': item['name'], 'frequency': frequency, 'current': item['current'], 'voltage': voltage_signal(voltages[item['name']], 1 / frequency)} for item in currents]  #: Map the schema-required current and voltage pair without solving a network.
        operating = {'conditions': {'ambientTemperature': saved['material'].get('temperature_C', 25)}, 'excitationsPerWinding': excitations}  #: Retain declared temperature and winding order in a real MAS operating-point subdocument.
    packet = {'format': FORMAT, 'schema_basis': {'MAS': MAS_COMMIT, 'PEAS': PEAS_COMMIT}, 'source_sha256': hashlib.sha256(canonical(saved)).hexdigest(), 'source_specification': saved, 'options': copy.deepcopy(options), 'mas_coil': {'bobbin': bobbin, 'functionalDescription': functional}, 'current_signals': currents, 'mas_operating_point': operating, 'layer_links': links, 'scope': 'MAS coil and optional operating-point subdocuments; not a complete MAS root', 'limitations': ['Core/material/gap and insulation data remain lossless Studio recipe fields; no native MAS core/geometry mapping yet', 'Layer links preserve order/turns/limbs; they are not MAS geometric layers or winding/bobbin CAD', 'Caller bobbin/isolation declarations are not catalogue resolution or insulation certification', '64-interval cosine samples approximate a waveform; no harmonic current, voltage, loss or network is solved', 'No compatibility claim for consuming these current schema snapshots in the older pinned PyOpenMagnetics 1.7.35', 'No changed PDE, native nonlinear/AC, finite copper, matched CAD or external Maxwell validation']}  #: Keep unsupported integration claims out of the exported data itself.
    if options.get('include_geometry', False):
        from .mas_coil_geometry import coil_geometry  #: Load geometry lazily because turn planning shares canonical JSON.
        arrays, mapping = coil_geometry(saved, functional)
        packet['mas_coil'].update(arrays)
        packet['coil_geometry'] = mapping
        packet['limitations'][:2] = [
            'Core/material/gap and insulation data remain lossless Studio recipe fields in this packet',
            'Geometric sections, rows and turns describe the right-hand cut through rounded closed paths. Complete bobbin and native winding-window association remain pending.',
        ]
        if 'bobbin_dimensions_m' in options:
            from .mas_bobbin_window import bind_bobbin_window
            bind_bobbin_window(saved, packet, options['bobbin_dimensions_m'])
        if 'limb_bobbin_dimensions_m' in options:
            from .mas_limb_bobbins import bind_limb_bobbins
            bind_limb_bobbins(saved, packet, options['limb_bobbin_dimensions_m'])
    return packet


def restore_exchange(packet, mode=None):  #: Rebuild a checked Studio project without ignoring edited native projections.
    if not isinstance(packet, dict) or packet.get('format') != FORMAT:  #: Refuse arbitrary MAS files or unknown versions as if they were lossless Studio packets.
        raise ValueError('Use a Studio MAS exchange packet with format ' + FORMAT)  #: Distinguish this supported roundtrip from a future general MAS importer.
    expected = export_exchange(packet['source_specification'], packet['options'])  #: Revalidate geometry and regenerate every derived native projection from the retained source.
    if canonical(packet) != canonical(expected):  #: Detect changed currents, wire dimensions, layer order, metadata or stale hashes, including extra keys.
        raise ValueError('Exchange data changed or is stale; edit the source recipe and export again')  #: Never silently ignore edits made only to the MAS projection.
    source = copy.deepcopy(expected['source_specification'])  #: Keep the saved packet immutable during an explicit dimensional conversion.
    if mode is not None:  #: A caller may deliberately rebuild the same workflow through the other dimensional adapter.
        if mode not in ('2d', '3d'):  #: Keep the mode vocabulary consistent with the existing builder.
            raise ValueError('Choose 2d or 3d for exchange restore')  #: Reject ambiguous dimensional requests.
        source['mode'] = mode  #: Change only the explicitly requested dimension; normal builder capability checks still apply.
    return build(source)  #: Invoke the actual builder and its material/source/packing guards, not a stored geometry screenshot.

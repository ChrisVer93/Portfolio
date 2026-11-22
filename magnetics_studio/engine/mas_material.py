"""P002C2A: editable MAS material points with explicit solver-law semantics."""
import copy  #: Detach imported material edits from the caller's packet and retained design.
import hashlib  #: Tie immutable field association and retained source data to their exact bytes.
from .builder import build  #: Apply accepted edits through the real shared dimensional builders.
from .mas_exchange import canonical, MAS_COMMIT  #: Reuse finite deterministic JSON and the pinned licensed MAS snapshot.
from .materials import validate_material  #: Enforce the actual reversible B-H and permeability constraints used by the solver.
from .project import number  #: Reject booleans, nonfinite quantities and unsupported numeric ranges.

FORMAT = 'magnetics-studio.mas-material-points/1'  #: Do not advertise these partial point records as a complete MAS material or root.
EDITABLE = ('law', 'mas_permeability_point', 'mas_bh_points')  #: Close the supported edits so source/geometry/electrical metadata cannot change silently.


def decode_points(law, permeability, points):  #: Decode exactly the supported SI point semantics before constructing a model.
    if law not in ('linear', 'bh'): raise ValueError('Material law must be linear or bh')  #: Never infer hysteresis or complex permeability from a curve's name.
    if not isinstance(permeability, dict) or set(permeability) != {'value', 'temperature'}: raise ValueError('Supply one nominal relative-permeability value and temperature only')  #: Refuse frequency/bias/tolerance modifiers that this constant-law solver cannot apply.
    mu = number(permeability['value'], 'Relative permeability', 1, 1e6)  #: Keep the same real dimensionless permeability limits as the field material.
    temperature = number(permeability['temperature'], 'Material temperature (C)', -273.15, 2000)  #: Treat Celsius as a label rather than an automatic material scaling law.
    if not isinstance(points, list) or len(points) > 2000: raise ValueError('Use at most 2000 reversible B-H points')  #: Bound imported allocation and retain empty dormant curves explicitly.
    curve = []  #: Collect solver [B in T, H in A/m] rows without interpolation or unit guessing.
    for point in points:  #: Check every supplied native point, including a curve stored under a linear law.
        if not isinstance(point, dict) or set(point) != {'magneticFluxDensity', 'magneticField', 'temperature'}: raise ValueError('B-H points require only magneticFluxDensity, magneticField and temperature')  #: Refuse extra coercivity, branch or unit fields rather than silently dropping them.
        b = number(point['magneticFluxDensity'], 'B (T)', 0, 1e9); h = number(point['magneticField'], 'H (A/m)', 0, 1e15)  #: Read finite nonnegative SI values without swapping H/B columns.
        t = number(point['temperature'], 'B-H temperature (C)', -273.15, 2000)  #: Require a physical finite label on every native point.
        if t != temperature: raise ValueError('All points must share the declared material temperature; no temperature interpolation')  #: Do not collapse multiple measured temperature curves into one constitutive law.
        curve.append([b, h])  #: Preserve the actual point ordering and values exactly.
    validate_material({'id':'core', 'mu_r':mu, 'bh':curve})  #: Enforce origin, monotonicity, row count and differential-permeability rules even for stored curves.
    if law == 'bh' and not curve: raise ValueError('Reversible B-H law requires a curve')  #: Never silently fall back to linear permeability for a requested nonlinear law.
    return mu, temperature, curve  #: Return only data demonstrated representable by the existing material implementation.


def export_material(specification):  #: Bind actual native material points to the real generated core regions.
    built = build(specification); source = built['project']['builder']; material = source['material']  #: Validate the full geometry, electrical hierarchy and dimensional material applicability first.
    temperature = material.get('temperature_C', 25)  #: Retain the source label without inventing frequency or measurement conditions.
    permeability = {'value':material.get('mu_r', 2200), 'temperature':temperature}  #: Export a native permeabilityPoint, not a claim of measured initial/incremental permeability.
    points = [{'magneticFluxDensity':b, 'magneticField':h, 'temperature':temperature} for b,h in material.get('bh', [])]  #: Convert only the existing SI column representation to native bhCyclePoint objects; no full hysteresis cycle is implied.
    law = material.get('law', 'linear'); decode_points(law, permeability, points)  #: Validate stored curves and labels before returning an editable packet.
    return {'format':FORMAT, 'schema_basis':MAS_COMMIT, 'source_specification':copy.deepcopy(source), 'source_sha256':hashlib.sha256(canonical(source)).hexdigest(), 'law':law, 'mas_permeability_point':permeability, 'mas_bh_points':points, 'field_binding':{'material_id':'core', 'region_ids':[r['id'] for r in built['project']['regions'] if r['material']=='core'], 'source_material_sha256':hashlib.sha256(canonical(material)).hexdigest()}, 'semantics':{'permeability':'Real constant solver relative permeability; no initial/amplitude/incremental measurement classification', 'curve':'Single-valued reversible first-quadrant H(B), not a hysteresis cycle', 'temperature':'Uniform Celsius label; no interpolation or thermal solve', 'catalogue':'No catalogue resolution; original name/conductivity/density/digitiser metadata retained'}, 'limitations':['Native permeabilityPoint and bhCyclePoint subdocuments only; full MAS material requires unavailable saturation/loss/manufacturer data', 'Stored B-H data under linear law is not active nonlinear physics; applying bh to 3D is rejected', 'Conductivity metadata does not activate eddy currents; no core-loss or thermal law is inferred', 'No changed PDE/mesh kernel, nonlinear 3D, finite copper, commercial validation or complete P002 mapping']}  #: Disclose association, immutable design provenance and the exact limits inside the exchange itself.


def apply_material(packet, mode=None):  #: Apply deliberately edited native points without losing the retained winding design.
    if not isinstance(packet, dict) or packet.get('format') != FORMAT: raise ValueError('Use a Studio material points packet with format ' + FORMAT)  #: Refuse arbitrary MAS catalogue files without a checked continuation recipe.
    original = export_material(packet['source_specification'])  #: Rebuild source material/geometry and regenerate every immutable association.
    if canonical({k:v for k,v in packet.items() if k not in EDITABLE}) != canonical({k:v for k,v in original.items() if k not in EDITABLE}): raise ValueError('Material exchange metadata changed or is stale')  #: Detect changed geometry, winding IDs, source hashes, bindings and extra unsupported fields.
    mu, temperature, curve = decode_points(packet['law'], packet['mas_permeability_point'], packet['mas_bh_points'])  #: Decode only the explicit native edits, not stale material values from the source recipe.
    source = copy.deepcopy(original['source_specification'])  #: Keep original circuits, layer order, wire dimensions, gaps and digitiser provenance detached and unchanged.
    source['material'].update(law=packet['law'], mu_r=mu, temperature_C=temperature, bh=curve)  #: Replace only the declared scalar law, uniform temperature label and exact SI points.
    if canonical({k:packet[k] for k in EDITABLE}) != canonical({k:original[k] for k in EDITABLE}):  #: An unchanged roundtrip retains exact metadata; actual edits need their own explicit attribution.
        source['material']['material_point_exchange'] = {'source_sha256':original['source_sha256'], 'edited_points_sha256':hashlib.sha256(canonical({k:packet[k] for k in EDITABLE})).hexdigest(), 'provenance':'Explicit user point edits; retained digitiser/catalogue metadata describes the input design, not independent verification of edited values'}  #: Prevent retained image/manufacturer provenance being mistaken for evidence of newly edited constitutive values.
    if mode is not None:  #: Require an explicit dimension change rather than inferring it from a curve.
        if mode not in ('2d','3d'): raise ValueError('Choose 2d or 3d for material apply')  #: Keep dimensional adapter vocabulary closed.
        source['mode'] = mode  #: Existing builder restrictions will reject nonlinear 3D rather than linearising silently.
    return build(source)  #: Return a newly validated preview; no current workspace job or field is modified here.

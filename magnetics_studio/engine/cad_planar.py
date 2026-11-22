"""P002B2: convex planar material partitions for checked prismatic CAD only."""
import math  #: Use stable finite area sums and explicit geometric resolution checks.
from .connections import series_key  #: Keep electrical identity separate from display labels and containers.


def polygon_area(poly):  #: Compute signed square metres without large-origin cancellation.
    x, y = poly[0]  #: Translate coordinates to the first vertex before taking cross products.
    return .5 * math.fsum((a[0] - x) * (b[1] - y) - (b[0] - x) * (a[1] - y) for a, b in zip(poly, poly[1:] + poly[:1]))  #: Counterclockwise convex input has positive area.


def tidy(poly, epsilon):  #: Remove numerically repeated and straight-through vertices from a clipped boundary.
    result = []  #: Retain the input order rather than rebuilding a convex hull that could hide bad geometry.
    for point in poly:  #: Inspect every generated intersection and original vertex.
        if not result or math.dist(point, result[-1]) > epsilon: result.append(tuple(point))  #: Collapse only consecutive points within the declared linear tolerance.
    if len(result) > 1 and math.dist(result[0], result[-1]) <= epsilon: result.pop()  #: Keep a polygon open in the data representation; native export closes it explicitly.
    changed = True  #: Straight vertices may become redundant after removing a neighbour.
    while changed and len(result) >= 3:  #: Bound simplification by removing at least one point on each repeated pass.
        changed = False  #: Stop once one full boundary traversal makes no change.
        for i, b in enumerate(result):  #: Test each vertex against its preceding and following edge endpoints.
            a, c = result[i - 1], result[(i + 1) % len(result)]  #: Use cyclic neighbours without duplicating the closing point.
            cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])  #: Measure twice the local signed triangle area in square metres.
            if abs(cross) <= epsilon * math.dist(a, c):  #: Treat only a perpendicular deviation inside the explicit linear tolerance as collinear.
                result.pop(i); changed = True; break  #: Remove one redundant vertex, then reassess the resulting boundary.
    return result if len(result) >= 3 and polygon_area(result) > epsilon * epsilon else []  #: Discard only degenerate pieces at the declared numerical tolerance.


def subtract_convex(poly, mask, epsilon):  #: Return disjoint convex pieces of a convex polygon outside a convex mask.
    if any(max(p[k] for p in poly) <= min(p[k] for p in mask) or min(p[k] for p in poly) >= max(p[k] for p in mask) for k in (0, 1)): return [poly]  #: Skip disjoint or boundary-touching bounding intervals before edge clipping.
    inner, pieces = poly, []  #: Peel exterior half-planes while retaining the intersection for the next mask edge.
    for a, b in zip(mask, mask[1:] + mask[:1]):  #: A validated counterclockwise mask has its interior to the left of every edge.
        left, right = [], []  #: Split the surviving convex intersection on this one directed line.
        dx, dy = b[0] - a[0], b[1] - a[1]  #: Keep edge orientation and physical length explicit.
        tolerance = epsilon * math.hypot(dx, dy)  #: Convert the linear tolerance in metres to cross-product units of square metres.
        def side(p):  #: Evaluate the oriented distance numerator against the current mask edge.
            value = dx * (p[1] - a[1]) - dy * (p[0] - a[0])  #: Positive values identify the mask's interior half-plane.
            return 0.0 if abs(value) <= tolerance else value  #: Classify almost-coincident boundaries consistently within the declared tolerance.
        for p, q in zip(inner, inner[1:] + inner[:1]):  #: Traverse each directed boundary edge of the still-convex inner polygon.
            u, v = side(p), side(q)  #: Classify both edge endpoints using the same line and tolerance.
            if u >= 0: left.append(p)  #: Keep interior and boundary vertices on the intersection side.
            if u <= 0: right.append(p)  #: Keep exterior and boundary vertices in the peeled piece.
            if u * v < 0:  #: Only genuinely crossing edges need an interpolated intersection.
                t = u / (u - v)  #: Solve the linear signed-distance zero along the segment.
                point = (p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1]))  #: Interpolate the physical boundary point in metres.
                left.append(point); right.append(point)  #: Share the same point to avoid a numerical gap between the two pieces.
        outside = tidy(right, epsilon)  #: Remove zero-area or repeated-vertex clipping artifacts.
        if outside: pieces.append(outside)  #: Every peeled region lies outside this edge and inside all previously processed mask edges.
        inner = tidy(left, epsilon)  #: Continue clipping only the intersection; emitted exterior pieces never overlap in positive area.
        if not inner: break  #: There is no remaining mask intersection to remove or split.
    return pieces  #: Omit the final mask intersection while retaining all exterior pieces.


def planar_bodies(project):  #: Partition supported 2D polygons independently of the field mesher's implementation.
    domain, regions = project['domain'], project['regions']  #: Receive the already detached and validated project from geometry_plan.
    epsilon = max(domain['width'], domain['height']) * 1e-12  #: Declare a scale-relative linear clipping tolerance, not a field-error estimate.
    if len(regions) > 128 or sum(len(r.get('polygon', [])) or 4 for r in regions) > 8192: raise ValueError('Planar CAD supports 128 regions and 8192 input vertices')  #: Bound native job size and preflight partition work explicitly.
    parts = []  #: Retain original material ownership through priority subtraction.
    for index, region in enumerate(regions):  #: Apply every later region, including explicit air, as an overwrite mask.
        poly = tidy(region.get('polygon') or [(region['x0'], region['y0']), (region['x1'], region['y0']), (region['x1'], region['y1']), (region['x0'], region['y1'])], epsilon)  #: Use actual polygon vertices or the exact rectangular boundary, never a polygon's bounding box.
        if not poly: raise ValueError('Planar CAD region is below its geometric resolution')  #: Do not silently drop a degenerate original material/source region.
        parts = [(owner, piece) for owner, old in parts for piece in subtract_convex(old, poly, epsilon)]  #: Preserve disjoint original ownership after the new overwrite.
        if region['material'] != 'air': parts.append((index, poly))  #: An explicit air mask removes material but is not exported as an opaque component.
        if len(parts) > 1000: raise ValueError('Planar CAD partition exceeds 1000 prisms; simplify overlapping regions')  #: Refuse an oversized partition before importing native CAD.
    bodies = []  #: Export one labelled compound per surviving original region.
    for index, region in enumerate(regions):  #: Preserve input order and region identity across all partition fragments.
        polygons = [poly for owner, poly in parts if owner == index]  #: Collect only the surviving positive-area material.
        if not polygons: continue  #: Fully overwritten regions contribute no material or source support.
        if any(math.dist(a, b) < 1e-9 for poly in polygons for a, b in zip(poly, poly[1:] + poly[:1])): raise ValueError('Planar CAD partition edge below 1 nm; simplify near-coincident boundaries')  #: Fail explicitly rather than asking the native kernel to heal unresolved slivers silently.
        cross_section = math.fsum(polygon_area(poly) for poly in polygons)  #: Sum independent analytical polygon areas in square metres.
        perimeter = math.fsum(math.dist(a, b) for poly in polygons for a, b in zip(poly, poly[1:] + poly[:1]))  #: Include all fragment faces because the STEP compound does not fuse adjacent pieces.
        extent = {a + e: (min if e == '0' else max)(v[k] for poly in polygons for v in poly) for k, a in enumerate('xy') for e in ('0', '1')}  #: Derive all XY bounds from the surviving vertices, not the original enclosing box.
        extent.update(z0=0, z1=domain['depth'])  #: A planar problem is extruded along its invariant Z direction by the declared model depth.
        bodies.append({'id': 'region_' + str(index), 'kind': 'field_region', 'source_id': region['id'], 'material': region['material'], 'prisms_m': [{'polygon': poly, 'z0': 0, 'z1': domain['depth']} for poly in polygons], 'expected_bounds_m': extent, 'expected_cross_section_m2': cross_section, 'expected_volume_m3': cross_section * domain['depth'], 'expected_area_m2': 2 * cross_section + perimeter * domain['depth']})  #: Retain exact prismatic geometry and independently computed SI measures for native reimport checks.
    windings = {w['id']: w for w in project['windings']}  #: Resolve stable source IDs without using names to connect electrical windings.
    for body in bodies:  #: Attach source data only to regions that actually survive priority assignment.
        region = regions[int(body['id'].split('_')[1])]  #: Use the fixed generated original-region index, not user text as an executable path.
        if not region.get('winding'): continue  #: Non-source magnetic and insulating regions have no impressed winding density.
        winding = windings[region['winding']]  #: Resolve the validated source definition.
        peers = [b for b in bodies if regions[int(b['id'].split('_')[1])].get('winding') == region['winding'] and regions[int(b['id'].split('_')[1])].get('polarity') == region['polarity']]  #: Match the unchanged planar solver's per-polarity area normalization for implicit turns.
        support = body['expected_cross_section_m2'] if 'turns' in region else math.fsum(b['expected_cross_section_m2'] for b in peers)  #: Explicit section turns normalize locally; implicit winding turns normalize over same-polarity regions.
        body['planar_source'] = {'winding_id': winding['id'], 'series_group': series_key(winding), 'polarity': region['polarity'], 'turns_numerator': region.get('turns', winding['turns']), 'current_A': winding['current'], 'normalisation_area_m2': support, 'unit_Jz_A_per_m2_per_A': region['polarity'] * region.get('turns', winding['turns']) / support, 'model': 'prescribed uniform axial current density; no eddy-current or end-turn solve'}  #: Preserve signed ampere-turn density without treating conductor-shaped solids as solved AC copper or closed 3D turns.
    return bodies, {'linear_clipping_tolerance_m': epsilon, 'minimum_export_edge_m': 1e-9, 'representation': 'straight-edged 2D field polygons extruded along Z; circles and toroids remain faceted'}  #: Make geometric tolerance and dimensional assumptions visible in every downloadable manifest.

"""Canonical same-current series identities; named containers stay independent."""

def series_key(winding):  #: Use stable source identity rather than display-name equality.
    return winding.get('series_group') or winding.get('circuit') or winding['id']  #: Preserve explicit series metadata and legacy circuit semantics; isolate unnamed independent ports.


def series_name(winding):  #: Label a measured electrical port without requiring builder-only metadata.
    if winding.get('logical_circuit_name') and winding.get('electrical_winding_name'):  #: New builder sources have both human-readable hierarchy levels.
        return winding['logical_circuit_name']+' / '+winding['electrical_winding_name']  #: Preserve circuit-container and independent winding names in results.
    return winding.get('series_group') or winding.get('circuit') or winding['name']  #: Imported series groups can be named directly without inventing builder fields.


def check_series_currents(project, currents):  #: Check the actual static or complex RMS source currents before field assembly.
    seen = {}  #: Retain the first actual current for each canonical series port.
    for winding, current in zip(project['windings'], currents):  #: Match values to the unchanged source order.
        key = series_key(winding)  #: Keep container membership out of the electrical connection definition.
        if key in seen and abs(current-seen[key]) > 1e-12*max(1, abs(current), abs(seen[key])):  #: A same-current series port cannot be driven by conflicting section currents.
            raise ValueError('Series sections require the same current phasor: '+key)  #: Reject inconsistent input instead of averaging, changing polarity or silently dropping a section.
        seen[key] = current  #: Preserve the supplied real/complex value for the next section comparison.


def normalise_series(project):  #: Migrate the old top-level map on the validator's detached project copy.
    windings = {w['id']: w for w in project['windings']}  #: Resolve physical section IDs, never similar display labels.
    groups = project.get('series_groups', {})  #: Omission means the project already uses current per-section fields.
    if not isinstance(groups, dict):  #: Legacy grouping must be a named mapping rather than a list or scalar.
        raise ValueError('series_groups must map group names to winding IDs')  #: Explain the accepted legacy import shape.
    assigned = set()  #: A physical section may belong to at most one electrical series port.
    for group, members in groups.items():  #: Retain each explicitly declared old series identity.
        if not isinstance(group, str) or not group or len(group) > 160:  #: Bound series labels while allowing composite circuit and winding IDs.
            raise ValueError('Series group names must be nonempty strings of at most 160 characters')  #: Reject invalid electrical identities early.
        if not isinstance(members, list) or not members or any(not isinstance(mid, str) or mid not in windings for mid in members):  #: Every member must be an existing physical winding section.
            raise ValueError('Series groups need nonempty lists of known winding IDs')  #: Do not partially apply a missing-member definition.
        if len(set(members)) != len(members) or assigned.intersection(members):  #: Repetition within/across groups would double-count linkage.
            raise ValueError('A winding section may occur in only one series group')  #: Fail before constructing ambiguous connections.
        for mid in members:  #: Apply explicit legacy membership to each physical section.
            winding = windings[mid]  #: Work only on the detached validated source.
            previous = winding.get('series_group') or winding.get('circuit')  #: Detect simultaneous old/new connection definitions.
            if previous and previous != group:  #: Conflicting definitions have no safe automatic interpretation.
                raise ValueError('Conflicting series definitions for winding '+mid)  #: Require a deliberate connection correction instead of guessing.
            winding['series_group'] = group  #: Canonical metadata now drives sweeps, property editing and matrix grouping.
        assigned.update(members)  #: Record ownership after the entire group has been checked.
    owners = {}  #: Separate an independent winding ID from an explicitly shared group with the same text.
    for winding in project['windings']:  #: Check both migrated and already-current source schemas.
        for field in ['series_group', 'circuit']:  #: These are electrical-series fields; logical_circuit_id remains a container label.
            if field in winding and (not isinstance(winding[field], str) or not winding[field] or len(winding[field]) > 160):  #: Reject invalid explicit identity values instead of treating them as missing.
                raise ValueError(field+' must be a nonempty string of at most 160 characters')  #: Keep Python and browser grouping keys predictable.
        if not winding.get('series_group') and winding.get('circuit'):  #: Canonicalise the older per-section series spelling for the existing current editor too.
            winding['series_group'] = winding['circuit']  #: Preserve its declared electrical identity while exposing the same UI metadata as migrated top-level groups.
        key = series_key(winding)  #: Use the same identity later consumed by every static measurement path.
        kind = 'series' if winding.get('series_group') or winding.get('circuit') else 'independent'  #: Identical display labels never create a connection.
        if key in owners and (kind != 'series' or owners[key] != 'series'):  #: A free source and a series group cannot share one output identity.
            raise ValueError('Independent winding ID collides with series group: '+key)  #: Prevent accidental matrix/source merging.
        owners[key] = kind  #: Record this identity's electrical role.
    for group, members in groups.items():  #: Reject legacy maps that omit a section claiming the same group elsewhere.
        if {w['id'] for w in project['windings'] if series_key(w) == group} != set(members):  #: Old and canonical membership must agree exactly.
            raise ValueError('Incomplete legacy series membership: '+group)  #: Never extend a declared connection silently.
    check_series_currents(project, [w['current'] for w in project['windings']])  #: Validate the supplied magnetostatic operating point with unchanged currents.
    project.pop('series_groups', None)  #: Remove only the consumed redundant legacy representation so later edits cannot leave stale duplicate definitions.


def require_static_sources(project):  #: Guard every static action against silently discarding explicit AC-solid sources.
    if project.get('ac_conductors') or any(r.get('ac_conductor') for r in project['regions']):  #: Detect declared groups and dangling assigned regions, including net-zero passive solids.
        raise ValueError('This magnetostatic action cannot use AC solid-conductor definitions; use AC / eddy currents, or explicitly remove those definitions')  #: Require an intentional physics choice; never delete source data or substitute a solve.

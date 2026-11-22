"""Lossless linear open/short characterization of an explicit electrical-port matrix."""
import hashlib  #: Bind exported characterization to the exact supplied matrix and port identities.
import json  #: Preserve finite portable source data without mutating stored field results.
import math  #: Scale inductances and factor the reciprocal magnetic-energy quadratic form.


def reduce_ports(circuits, input_id, shorted_ids):  #: Eliminate only the explicitly shorted electrical ports; all other currents remain zero.
    if not isinstance(circuits,dict):raise ValueError('A solved linear electrical-winding matrix is required')  #: Reject missing/nonlinear/AC result formats before any arithmetic.
    ids=circuits.get('group_ids');names=circuits.get('names');raw=circuits.get('inductance_H')  #: Read canonical electrical keys rather than display-name connections.
    if not isinstance(ids,list) or not 1<=len(ids)<=32 or any(not isinstance(k,str) or not k for k in ids) or len(set(ids))!=len(ids):raise ValueError('Require 1–32 unique nonempty electrical port IDs')  #: Bound work and reject ambiguous or duplicate identities.
    n=len(ids)  #: Keep all matrix indexing tied to the explicit stable port order.
    if not isinstance(names,list) or len(names)!=n or any(not isinstance(k,str) for k in names):raise ValueError('Every electrical port needs a display name')  #: Equal labels remain allowed because they do not define connectivity.
    if not isinstance(raw,list) or len(raw)!=n or any(not isinstance(row,list) or len(row)!=n for row in raw):raise ValueError('Require a square electrical inductance matrix')  #: Reject ragged, missing and mismatched source data.
    if any(type(v) not in (int,float) or not math.isfinite(v) for row in raw for v in row):raise ValueError('Inductance entries must be finite real henries')  #: Refuse booleans, strings and complex/undefined AC equivalents.
    if input_id not in ids or not isinstance(shorted_ids,list) or any(not isinstance(k,str) or k not in ids for k in shorted_ids) or len(set(shorted_ids))!=len(shorted_ids) or input_id in shorted_ids:raise ValueError('Select one input and distinct other shorted port IDs')  #: Prevent duplicate constraints, accidental input shorting and unknown winding selections.
    if any(raw[i][i]<=0 for i in range(n)):raise ValueError('All port self inductances must be positive')  #: A zero-energy or invalid source cannot define an independent characterized port.
    scales=[math.sqrt(raw[i][i]) for i in range(n)]  #: Normalize turn-count and unit-scale disparities before testing numerical independence.
    reciprocity=max(abs(raw[i][j]/scales[i]/scales[j]-raw[j][i]/scales[i]/scales[j]) for i in range(n) for j in range(n))  #: Measure reciprocity in dimensionless port coordinates.
    if reciprocity>1e-6:raise ValueError('Nonreciprocal inductance matrix; re-solve and inspect source/solver accuracy')  #: Do not hide materially inconsistent unit-excitation results.
    normalized=[[(raw[i][j]/scales[i]/scales[j]+raw[j][i]/scales[i]/scales[j])/2 for j in range(n)] for i in range(n)]  #: Explicitly average only reciprocity-qualified roundoff/asymmetric solver error.
    def factor(indices):  #: Test positive magnetic energy and solve without explicit matrix inversion.
        lower=[[0.]*len(indices) for _ in indices];pivots=[]  #: Retain dimensionless Cholesky factors and independence diagnostics.
        for a,i in enumerate(indices):  #: Factor the selected principal block in its exact declared order.
            for b,j in enumerate(indices[:a+1]):  #: Compute only the reciprocal lower triangle.
                value=normalized[i][j]-math.fsum(lower[a][k]*lower[b][k] for k in range(b))  #: Subtract previously resolved quadratic-energy components.
                if a==b:  #: A diagonal pivot tests a new independent source direction.
                    if value<=1e-10:raise ValueError('Matrix is nonpositive or nearly dependent; ideal/redundant ports require a qualified constraint model')  #: Reject singular and ill-conditioned modes instead of inventing a pseudoinverse.
                    pivots.append(value);lower[a][b]=math.sqrt(value)  #: Retain the actual normalized pivot, not an accuracy certificate.
                else:lower[a][b]=value/lower[b][b]  #: Complete this off-diagonal factor coefficient.
        return lower,pivots  #: Preserve factors for substitution and diagnostics for the exported record.
    _,pivots=factor(list(range(n)))  #: Require the entire supplied electrical matrix to describe independent positive-energy ports.
    p=ids.index(input_id);shorts=[ids.index(k) for k in shorted_ids];lower,_=factor(shorts);forward=[]  #: Preserve user-selected short order while retaining exact global IDs.
    for a,s in enumerate(shorts):forward.append((-normalized[s][p]-math.fsum(lower[a][b]*forward[b] for b in range(a)))/lower[a][a])  #: Solve the lower-triangular system for normalized cancellation currents.
    solution=[0.]*len(shorts)  #: Allocate only the selected shorted-current unknowns.
    for a in range(len(shorts)-1,-1,-1):solution[a]=(forward[a]-math.fsum(lower[b][a]*solution[b] for b in range(a+1,len(shorts))))/lower[a][a]  #: Back-substitute to solve C_SS x = -C_Sp.
    currents=[0.]*n;currents[p]=1.  #: Normalize to exactly one input ampere and leave every other open port current zero.
    for s,value in zip(shorts,solution):currents[s]=value*scales[p]/scales[s]  #: Transform the normalized solution back to amperes per input ampere.
    matrix=[[normalized[i][j]*scales[i]*scales[j] for j in range(n)] for i in range(n)]  #: Recover the disclosed reciprocal matrix in physical henries.
    linkage=[math.fsum(v*x for v,x in zip(row,currents)) for row in matrix]  #: Compute every resulting port linkage, including open-port induced linkage.
    effective=linkage[p];energy=.5*math.fsum(x*y for x,y in zip(currents,linkage))  #: Independently evaluate input flux/current and total quadratic magnetic energy at one ampere.
    residual=max((abs(linkage[s])/scales[s]/scales[p] for s in shorts),default=0.)  #: Check actual shorted-port flux cancellation with dimensionless scaling.
    identity=abs(2*energy-effective)/raw[p][p]  #: Check the lossless port/energy identity without dividing by a nearly vanishing short-circuit result.
    if not 0<effective<=raw[p][p]*(1+1e-8) or residual>1e-8 or identity>1e-8:raise ValueError('Short-circuit cancellation or magnetic-energy consistency failed')  #: Refuse a numerically invalid passive reduction.
    source=dict(group_ids=list(ids),names=list(names),inductance_H=[list(row) for row in raw])  #: Retain exact supplied values without rewriting historical solved JSON.
    digest=hashlib.sha256(json.dumps(source,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()  #: Bind the report to original IDs/order/labels and exact input matrix values.
    return dict(format='magnetics-studio.port-reduction/1',source_matrix=source,source_matrix_sha256=digest,input_id=input_id,shorted_ids=list(shorted_ids),open_ids=[k for k in ids if k!=input_id and k not in shorted_ids],input_open_H=raw[p][p],input_inductance_H=effective,cancelled_coupling_H=raw[p][p]-effective,current_A_per_input_A=currents,linkage_Wb_turn_per_input_A=linkage,energy_J_at_1A=energy,normalized_short_flux_residual=residual,relative_energy_identity=identity,normalized_reciprocity_error=reciprocity,minimum_normalized_pivot=min(pivots),conditions='Linear reciprocal lossless magnetostatic matrix; selected shorts have zero incremental linkage, other ports have zero current. Equivalent to ideal sinusoidal shorts at nonzero frequency with no resistance or initial trapped flux. Open-input self inductance and cancelled coupling are not a unique magnetising/leakage T-network split. Mesh/source/domain errors remain those of the supplied model; no nonlinear, eddy-current, load-network, transient or physical accuracy qualification.')  #: Export explicit units, simultaneous-short semantics, numerical diagnostics and physical limits together.

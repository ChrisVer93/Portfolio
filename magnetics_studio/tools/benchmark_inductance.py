"""Recompute source-form inductance study evidence; no external commercial reference."""
import json  #: Save complete actual study responses rather than copied example numbers.
from pathlib import Path  #: Resolve models and caller-selected output location.
import sys  #: Make this delivered source checkout importable from tools/.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))  #: Use the matching delivered engine code.
from engine.analysis import current_sweep, solve_project  #: Run actual magnetostatic sweeps and independent unit-excitation extraction.
from engine.ac import frequency_sweep  #: Run actual frequency-dependent conductor diffusion.
ROOT=Path(__file__).resolve().parents[1]  #: Keep model provenance stable across installations.


def run(output):  #: Produce repeatable actual models and measured outputs for the technical report.
    output=Path(output);output.mkdir(parents=True,exist_ok=True)  #: Create an explicit verification-only result directory.
    studies={}  #: Keep different physical measurement definitions and cases separate.
    for label,name,values in [('linear','transformer_2d',[0,1,2,4]),('nonlinear','nonlinear_2d',[0,2,8,15]),('spatial','air_coil_3d',[0,1,2])]:  #: Exercise both dimensions and the existing reversible nonlinear path.
        p=json.loads((ROOT/'examples'/(name+'.json')).read_text())  #: Load the actual shared source problem.
        p['domain'].update(nx=12,ny=12)  #: Bound report models while retaining fitted geometry/material/gap interfaces.
        if p['mode']=='3d':  #: Keep the vector example small enough for repeatable source tests.
            p['domain'].update(nx=4,ny=4,nz=4)  #: Preserve physical source geometry while controlling real tetrahedron count.
        s=current_sweep(p,p['windings'][0]['id'],values,print)  #: Recompute every requested current's actual field/linkage.
        if label!='nonlinear':  #: Constant self inductance is meaningful for these single-active-port linear examples.
            reference=solve_project(p)['inductance_H'][0][0]  #: Independently run the existing unit-excitation field-port extraction.
            s['verification_self_H']=reference  #: Record the actual same-model linear comparator.
            assert max(abs(r['chord_inductance_H']/reference-1) for r in s['rows'] if r['current_A'])<1e-6  #: Require the sweep linkage curve to reproduce the matrix coefficient.
        else:  #: Reversible saturation should reduce the illustrative ferrite response.
            assert s['rows'][-1]['chord_inductance_H']<s['rows'][1]['chord_inductance_H']  #: Gate the actual nonlinear trend without inventing a constant matrix.
        studies[label]=s  #: Preserve the exact source model, solved linkage, energy and inductance definitions.
    p=json.loads((ROOT/'examples/ac_foil_pair_2d.json').read_text());p['domain'].update(nx=12,ny=12)  #: Select a real forward/return/passive shield model at explicitly limited mesh resolution.
    studies['ac']=frequency_sweep(p,[1000,3000,10000],progress=print)  #: Resolve complex fields and signed series equivalent at each frequency.
    studies['ac']['project']=p  #: Record exact physical geometry/source data alongside the frequency-specific phasors.
    evidence={'passed':True,'studies':studies,'limits':'Internal regression and same-model consistency only. Nonlinear slopes are finite-current intervals. AC Ls is a coupled operating-point series equivalent; no full impedance matrix, mesh convergence or commercial validation.'}  #: Keep all numerical interpretation limits attached to the saved examples.
    (output/'benchmark.json').write_text(json.dumps(evidence,indent=2,allow_nan=False))  #: Persist complete finite JSON only after actual numerical gates pass.
    return evidence  #: Permit separate report formatting without rerunning or modifying the solver.


if __name__=='__main__':  #: Run this verification workload only by explicit source invocation.
    result=run(sys.argv[1] if len(sys.argv)>1 else ROOT/'sample_results/inductance')  #: Use the documented default or caller-selected evidence directory.
    print(json.dumps({'passed':result['passed'],'cases':list(result['studies'])}))  #: Report only completed actual case execution.

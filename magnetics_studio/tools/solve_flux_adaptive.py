"""Solve fixed-source native refinement with explicit signed pickup-flux stability controls."""
import argparse  #: Require explicit distinct physical model and output paths.
import json  #: Retain complete accepted fields and empirical stopping evidence.
from pathlib import Path  #: Resolve the exact delivered engine and input identities.
import sys  #: Import this source checkout rather than another installed version.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))  #: Bind numerical imports to the delivered source.
from engine.flux_adaptive import solve_flux_adaptive  #: Run actual native source-preserving refinement and signed flux monitoring.


def main():  #: Complete physical preflight, native solves and measurements before writing output.
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('model',type=Path);parser.add_argument('output',type=Path);args=parser.parse_args()  #: Expose one explicit SI request and one separate result destination.
    if args.model.resolve()==args.output.resolve():parser.error('Output must differ from input model')  #: Preserve source geometry, currents and pickup definitions.
    result=solve_flux_adaptive(json.loads(args.model.read_text(encoding='utf-8')))  #: Compute genuine accepted mesh/field and all requested pickup histories.
    args.output.write_text(json.dumps(result,allow_nan=False)+'\n',encoding='utf-8')  #: Preserve prior output on computational failure and publish only a complete finite result.
    print(json.dumps(dict(stop_reason=result['stop_reason'],accepted_passes=len(result['history']),flux_stability=result['flux_stability']),allow_nan=False))  #: Present empirical status without asserting design accuracy.


if __name__=='__main__':main()  #: Keep module import free of solver and file-writing side effects.
